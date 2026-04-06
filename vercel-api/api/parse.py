"""
Vercel Serverless Function — /api/parse
=======================================
Triggered by Power Automate when the SharePoint master schedule Excel is modified.

Expected POST body (JSON):
  {
    "fileContent": "<base64-encoded .xlsx bytes>",
    "githubToken": "<optional: override env var>",
    "month": "<optional: e.g. 'May 2026' for logging>"
  }

Environment variables required (set in Vercel project settings):
  GITHUB_TOKEN   — Personal Access Token with repo write scope
  GITHUB_OWNER   — e.g. "upshawam"
  GITHUB_REPO    — e.g. "Lvl2Calendar"
  GITHUB_BRANCH  — e.g. "main"
  SCHEDULE_FILE  — path in repo, e.g. "full_team_schedule.json"
  API_SECRET     — shared secret Power Automate sends in X-API-Secret header

Returns JSON:
  { "ok": true, "message": "...", "counts": {...} }
  { "ok": false, "error": "..." }
"""

import base64
import io
import json
import os
import re
from datetime import datetime

import openpyxl
import requests
from http.server import BaseHTTPRequestHandler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SKIP_NAME_PATTERNS = re.compile(
    r"^(time off|straights|in training|training day|$)",
    re.IGNORECASE
)

LEGEND_SIGNAL_PATTERNS = re.compile(
    r"(TIME OFF|STRAIGHTS|IN TRAINING|TRAINING DAY)",
    re.IGNORECASE
)


def cell_val(cell):
    """Return stripped string value of a cell, or ''."""
    v = cell.value
    if v is None:
        return ""
    return str(v).strip()


def parse_excel_bytes(xlsx_bytes: bytes) -> dict:
    """
    Parse one or more sheets from the Excel workbook.
    Each sheet is expected to follow the master schedule format:
      Row 1: (ignored / section labels)
      Row 2: '', date1, date2, ...    (m/d/yyyy)
      Row 3: '', F, Sa, Su, ...       (day-of-week abbreviations)
      Row 4+: name, shift1, shift2, ... (D / N / blank)
    Returns a dict keyed by YYYY-MM-DD date string, each value is a dict:
      { "PersonName": "D" | "N" | None, ... }
    """
    wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), data_only=True, read_only=True)
    
    # Accumulate across all sheets — later sheets override earlier ones for same date
    schedule_by_date = {}
    team_members_ordered = []
    seen_names = set()

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = list(ws.iter_rows())

        if len(rows) < 4:
            continue  # not a schedule sheet

        # --- Find date row (the row whose second non-empty cell parses as a date) ---
        date_row_idx = None
        col_dates = []  # YYYY-MM-DD strings, one per column (col 1+)

        for i, row in enumerate(rows[:6]):  # date row is always in first 6 rows
            vals = [cell_val(c) for c in row]
            # Look for m/d/yyyy or datetime objects
            dates_found = []
            for v in vals[1:]:  # skip column 0 (name column)
                parsed = _try_parse_date(v, row[vals.index(v) + 1] if vals.index(v) + 1 < len(vals) else None)
                # Also try the cell value directly as a datetime object
                raw_cell = row[vals.index(v) + 1] if vals.index(v) + 1 < len(row) else None
                parsed = _try_parse_date_cell(raw_cell)
                dates_found.append(parsed)

            filled = [d for d in dates_found if d is not None]
            if len(filled) >= 20:  # expect at least 20 dates in a month sheet
                date_row_idx = i
                col_dates = dates_found
                break

        if date_row_idx is None:
            continue  # couldn't find date row

        # --- Parse person rows ---
        for row in rows[date_row_idx + 2:]:  # skip date row and day-of-week row
            raw_name = cell_val(row[0])
            
            # Stop at legend/blank section
            if LEGEND_SIGNAL_PATTERNS.search(raw_name):
                break

            if not raw_name or SKIP_NAME_PATTERNS.match(raw_name):
                continue

            shifts = []
            for i, col_date in enumerate(col_dates):
                if col_date is None:
                    continue
                cell_idx = i + 1  # +1 because col 0 is the name
                if cell_idx >= len(row):
                    shift = None
                else:
                    v = cell_val(row[cell_idx]).upper()
                    shift = v if v in ("D", "N") else None
                shifts.append((col_date, shift))

            # Record team member order (first appearance across all sheets)
            if raw_name not in seen_names:
                team_members_ordered.append(raw_name)
                seen_names.add(raw_name)

            # Merge into schedule_by_date
            for date_str, shift in shifts:
                if date_str not in schedule_by_date:
                    schedule_by_date[date_str] = {}
                schedule_by_date[date_str][raw_name] = shift

    wb.close()
    return {
        "scheduleByDate": schedule_by_date,
        "teamMembers": team_members_ordered
    }


def _try_parse_date_cell(cell):
    """Try to parse a date from an openpyxl cell (may already be a datetime)."""
    if cell is None:
        return None
    v = cell.value
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d")
    s = str(v).strip()
    # Try m/d/yyyy or m/d/yy
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%-m/%-d/%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def _try_parse_date(s: str, cell=None):
    """Wrapper that also checks the raw cell value."""
    if cell is not None:
        result = _try_parse_date_cell(cell)
        if result:
            return result
    for fmt in ("%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass
    return None


def build_output_json(parsed: dict) -> dict:
    """Convert parsed schedule into the canonical full_team_schedule.json structure."""
    schedule_by_date = parsed["scheduleByDate"]
    team_members = parsed["teamMembers"]
    
    sorted_dates = sorted(schedule_by_date.keys())
    
    # Group by year-month
    months = {}
    for d in sorted_dates:
        ym = d[:7]  # YYYY-MM
        if ym not in months:
            months[ym] = []
        months[ym].append(d)
    
    month_list = []
    for ym, dates in sorted(months.items()):
        y, m = int(ym[:4]), int(ym[5:7])
        month_name = datetime(y, m, 1).strftime("%B %Y")
        days_list = []
        for d in sorted(dates):
            day_assignments = schedule_by_date.get(d, {})
            # Ensure all team members have an entry
            full_day = {name: day_assignments.get(name, None) for name in team_members}
            days_list.append({"date": d, "assignments": full_day})
        month_list.append({
            "year": y,
            "month": m,
            "monthName": month_name,
            "days": days_list
        })
    
    # Compute shift counts per person
    counts = {}
    for name in team_members:
        d_count = sum(1 for day in schedule_by_date.values() if day.get(name) == "D")
        n_count = sum(1 for day in schedule_by_date.values() if day.get(name) == "N")
        counts[name] = {"D": d_count, "N": n_count, "off": len(sorted_dates) - d_count - n_count}
    
    return {
        "name": "STE II Full Team Schedule",
        "lastUpdated": datetime.utcnow().isoformat() + "Z",
        "startDate": sorted_dates[0] if sorted_dates else None,
        "endDate": sorted_dates[-1] if sorted_dates else None,
        "totalDays": len(sorted_dates),
        "teamMembers": team_members,
        "counts": counts,
        "months": month_list
    }


def commit_to_github(json_content: str) -> dict:
    """Commit the JSON file to GitHub via API. Returns response dict."""
    token = os.environ.get("GITHUB_TOKEN", "")
    owner = os.environ.get("GITHUB_OWNER", "upshawam")
    repo = os.environ.get("GITHUB_REPO", "Lvl2Calendar")
    branch = os.environ.get("GITHUB_BRANCH", "main")
    file_path = os.environ.get("SCHEDULE_FILE", "full_team_schedule.json")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Get current file SHA (needed to update an existing file)
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
    get_resp = requests.get(url, headers=headers, params={"ref": branch}, timeout=15)
    sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None

    encoded = base64.b64encode(json_content.encode("utf-8")).decode("utf-8")
    payload = {
        "message": f"Auto-update schedule from Power Automate [{datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC]",
        "content": encoded,
        "branch": branch
    }
    if sha:
        payload["sha"] = sha

    put_resp = requests.put(url, headers=headers, json=payload, timeout=15)
    return {"status": put_resp.status_code, "body": put_resp.json()}


# ---------------------------------------------------------------------------
# Vercel entry point
# ---------------------------------------------------------------------------

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        # --- Validate secret ---
        expected_secret = os.environ.get("API_SECRET", "")
        received_secret = self.headers.get("X-API-Secret", "")
        if expected_secret and received_secret != expected_secret:
            self._respond(401, {"ok": False, "error": "Unauthorized"})
            return

        # --- Read body ---
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._respond(400, {"ok": False, "error": "Invalid JSON body"})
            return

        file_b64 = payload.get("fileContent", "")
        if not file_b64:
            self._respond(400, {"ok": False, "error": "Missing fileContent (base64 xlsx)"})
            return

        # --- Decode & parse ---
        try:
            xlsx_bytes = base64.b64decode(file_b64)
        except Exception as e:
            self._respond(400, {"ok": False, "error": f"base64 decode failed: {e}"})
            return

        try:
            parsed = parse_excel_bytes(xlsx_bytes)
        except Exception as e:
            self._respond(500, {"ok": False, "error": f"Excel parse failed: {e}"})
            return

        if not parsed["teamMembers"]:
            self._respond(422, {"ok": False, "error": "No team members found in spreadsheet"})
            return

        # --- Build output JSON ---
        output = build_output_json(parsed)
        json_str = json.dumps(output, indent=2)

        # --- Commit to GitHub ---
        try:
            github_result = commit_to_github(json_str)
        except Exception as e:
            self._respond(500, {"ok": False, "error": f"GitHub commit failed: {e}"})
            return

        if github_result["status"] not in (200, 201):
            self._respond(502, {
                "ok": False,
                "error": f"GitHub API returned {github_result['status']}",
                "detail": github_result["body"]
            })
            return

        self._respond(200, {
            "ok": True,
            "message": f"Updated {os.environ.get('SCHEDULE_FILE', 'full_team_schedule.json')} in GitHub",
            "totalDays": output["totalDays"],
            "teamMembers": output["teamMembers"],
            "counts": output["counts"]
        })

    def do_GET(self):
        self._respond(200, {"ok": True, "message": "Schedule parse API is running. Send a POST request."})

    def _respond(self, status: int, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # suppress default logging

import argparse
import json
import subprocess
import sys
from pathlib import Path

from api.parse import parse_excel_bytes, build_output_json


def discover_excel_path() -> Path | None:
    home = Path.home()
    candidates = []

    one_drive_dirs = [p for p in home.glob("OneDrive*") if p.is_dir()]
    filename_patterns = [
        "CURRENT Master Schedule.xlsx",
        "*Master*Schedule*.xlsx",
    ]

    for root in one_drive_dirs:
        for pattern in filename_patterns:
            for match in root.rglob(pattern):
                if match.is_file():
                    candidates.append(match)

    if not candidates:
        return None

    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def run_git(repo_root: Path, args: list[str]) -> str:
    command = ["git", "-C", str(repo_root), *args]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Git command failed: {' '.join(command)}\n{stderr}")
    return (result.stdout or "").strip()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse team schedule Excel and commit full_team_schedule.json to Git."
    )
    parser.add_argument(
        "--excel-path",
        required=False,
        help="Absolute path to the synced master schedule .xlsx file (optional; auto-discovered if omitted)",
    )
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parent),
        help="Path to git repo root (default: this script's folder)",
    )
    parser.add_argument(
        "--output-file",
        default="full_team_schedule.json",
        help="Output JSON path relative to repo root",
    )
    parser.add_argument(
        "--branch",
        default="full-team-dev",
        help="Branch expected for commit/push (default: full-team-dev)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and generate output, but do not commit/push",
    )

    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if args.excel_path:
        if args.excel_path.lower().startswith(("http://", "https://")):
            print("ERROR: --excel-path must be a local synced .xlsx path, not a SharePoint web URL.")
            print("Tip: Use your OneDrive-synced local path for CURRENT Master Schedule.xlsx.")
            return 2
        excel_path = Path(args.excel_path).resolve()
    else:
        found = discover_excel_path()
        if found is None:
            print("ERROR: Could not auto-find CURRENT Master Schedule.xlsx in OneDrive folders.")
            print("Please pass --excel-path with the local synced .xlsx path.")
            return 2
        excel_path = found
        print(f"Auto-detected Excel file: {excel_path}")
    output_path = (repo_root / args.output_file).resolve()

    if not excel_path.exists() or excel_path.suffix.lower() != ".xlsx":
        print(f"ERROR: Excel file not found or not .xlsx: {excel_path}")
        return 2

    if not (repo_root / ".git").exists():
        print(f"ERROR: Not a git repo root: {repo_root}")
        return 2

    try:
        current_branch = run_git(repo_root, ["branch", "--show-current"])
        if current_branch != args.branch:
            print(
                f"ERROR: Current branch is '{current_branch}', expected '{args.branch}'. "
                "Switch branches first to avoid committing to the wrong branch."
            )
            return 2

        xlsx_bytes = excel_path.read_bytes()
        parsed = parse_excel_bytes(xlsx_bytes)
        if not parsed.get("teamMembers"):
            print("ERROR: No team members found in spreadsheet.")
            return 3

        output = build_output_json(parsed)
        json_str = json.dumps(output, indent=2)

        existing = output_path.read_text(encoding="utf-8") if output_path.exists() else None
        if existing == json_str:
            print("No changes detected in full_team_schedule.json. Nothing to commit.")
            return 0

        output_path.write_text(json_str, encoding="utf-8")
        print(
            f"Updated {output_path.name}: {len(output.get('teamMembers', []))} members, "
            f"{output.get('totalDays', 0)} days"
        )

        if args.dry_run:
            print("Dry run complete. Skipping git commit/push.")
            return 0

        rel_output = str(output_path.relative_to(repo_root)).replace("\\", "/")
        run_git(repo_root, ["add", rel_output])

        status = run_git(repo_root, ["status", "--short"])
        if not status:
            print("No staged changes after update. Exiting.")
            return 0

        commit_message = "Auto-update full team schedule JSON from local Excel"
        run_git(repo_root, ["commit", "-m", commit_message])
        run_git(repo_root, ["push", "origin", args.branch])

        print("Commit and push complete.")
        return 0

    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

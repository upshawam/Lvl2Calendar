# Local Schedule Updater (No Power Automate Premium)

This workflow updates `full_team_schedule.json` directly from your local/synced Excel file and pushes to GitHub.

## Files added

- `update_full_team_schedule.py` - parser + git commit/push workflow
- `Update-Schedule.bat` - one-click launcher

## One-time setup

1. In `Update-Schedule.bat`, either:
   - leave `EXCEL_PATH` blank to auto-discover the workbook in OneDrive folders, or
   - set `EXCEL_PATH` to your synced SharePoint/OneDrive `.xlsx` local path.
2. Do **not** use a SharePoint browser URL as `EXCEL_PATH`; it must be a local synced file path.
3. Make sure you are authenticated to Git for this repo (`git push` works manually).
4. Make sure dependencies are installed:
   - `pip install -r requirements.txt`

## Run manually (one-click)

- Double-click `Update-Schedule.bat`

What it does:

1. Verifies branch is `full-team-dev`
2. Parses workbook tabs and builds `full_team_schedule.json`
3. Skips commit if no JSON change
4. Commits and pushes to `origin/full-team-dev`

## Optional: run from command line

```powershell
python update_full_team_schedule.py --excel-path "C:\Path\To\CURRENT Master Schedule.xlsx" --repo-root . --branch full-team-dev
```

## Optional: test parse only (no git changes)

```powershell
python update_full_team_schedule.py --excel-path "C:\Path\To\CURRENT Master Schedule.xlsx" --repo-root . --branch full-team-dev --dry-run
```

## Notes

- PC must be on to run this workflow.
- If internet is unavailable, parsing works but push/commit may fail.
- Script intentionally refuses to run on the wrong branch to avoid bad commits.

@echo off
setlocal

REM -----------------------------------------------------------------
REM Optional: configure this path to your synced SharePoint/OneDrive .xlsx file
REM Leave blank to auto-discover in OneDrive folders.
REM -----------------------------------------------------------------
set "EXCEL_PATH="

REM Optional: set expected branch (default is full-team-dev)
set "BRANCH=full-team-dev"

set "SCRIPT_DIR=%~dp0"
set "PYTHON_CMD=python"

echo Running local schedule update...
if "%EXCEL_PATH%"=="" (
  echo Excel: auto-detect
) else (
  echo Excel: %EXCEL_PATH%
)
echo Branch: %BRANCH%
echo.

if "%EXCEL_PATH%"=="" (
  %PYTHON_CMD% "%SCRIPT_DIR%update_full_team_schedule.py" --repo-root "%SCRIPT_DIR%" --branch "%BRANCH%"
) else (
  %PYTHON_CMD% "%SCRIPT_DIR%update_full_team_schedule.py" --excel-path "%EXCEL_PATH%" --repo-root "%SCRIPT_DIR%" --branch "%BRANCH%"
)
set EXIT_CODE=%ERRORLEVEL%

echo.
if %EXIT_CODE% EQU 0 (
  echo SUCCESS: Schedule update complete.
) else (
  echo FAILED: Script exited with code %EXIT_CODE%.
)

echo.
pause
exit /b %EXIT_CODE%

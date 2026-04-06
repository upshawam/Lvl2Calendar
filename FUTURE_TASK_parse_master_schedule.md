# Future Task: Build reusable master schedule parser

## Goal
Create a reusable Python script that reads the monthly `Current Master Schedule` CSV files and automatically extracts Aaron/Randall-style day assignments into a normalized day-by-day schedule.

## Why
The current schedule page was built from one-off parsing logic. A reusable parser will make future updates much faster and will support expanding this process to other team rotations.

## Proposed script
`parse_master_schedule.py`

## Inputs
- Folder containing monthly `Current Master Schedule` CSV files
- Configurable employee/rotation row labels
- Optional date range override

## Outputs
- Merged daily assignment sequence
- JSON export
- CSV export
- Optional ICS calendar files
- Optional HTML-friendly JS array output

## Requirements
- Detect monthly files by filename month/year
- Normalize bad/inconsistent date rows using filename month/year when needed
- Support named row matching like:
  - `Aaron Upshaw`
  - `Randall Webb`
  - future alternate staff names
- Interpret day cells:
  - Aaron = `0`
  - Randall = `1`
  - both off / neither assigned = `null`
- Flag conflicts across overlapping source files
- Print summary counts for validation

## Nice-to-have
- CLI arguments
- Config file for alternate team rotations
- Generate ICS files directly from parsed output
- Diff report against prior schedule

## Acceptance criteria
- Point script at a folder of monthly CSVs
- Script produces a correct merged sequence without manual edits
- Script can regenerate the current schedule page data and ICS files
- Script is reusable for another team with minimal changes

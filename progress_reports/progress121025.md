# JobApp Progress Report

Date: 2025-12-10

## Overview

JobApp is a small, SQLite-backed CLI for tracking software engineering job applications.
It has been refactored from a single script into a structured Python package with a clear separation of concerns.

## Current Architecture

Project layout:

- `jobapp/` (Python package)
  - `__init__.py`
  - `models.py` – `Application` dataclass
  - `db.py` – SQLite schema, DB connection, CRUD, reporting queries
  - `cli.py` – argparse-based CLI, command dispatch, output formatting
- `jobs_cli.py` – minimal entrypoint that calls `jobapp.cli.main()`
- `~/bin/jobapp` – symlink pointing to `jobs_cli.py`, making `jobapp` a global command

## Data Model

`Application` dataclass (in `jobapp/models.py`):

- `id: int`
- `company: str`
- `role: str`
- `job_link: Optional[str]`
- `location: Optional[str]`
- `date_applied: str` (ISO `YYYY-MM-DD`)
- `source: Optional[str]`
- `status: str`
- `last_action: Optional[str]`
- `priority: Optional[int]` (1=high, 2=medium, 3=low)
- `notes: Optional[str]`

## Database Schema

SQLite database (default: `applications.db`):

- Table: `applications`
  - Columns as in `Application` dataclass
  - Defaults:
    - `status` → `"Applied"`
    - `priority` → `2`
- Indexes:
  - `idx_status` on `status`
  - `idx_date` on `date_applied`
  - `idx_company` on `company`

`init_db(conn)` is idempotent and ensures the schema exists on every run.

## Implemented Commands

All commands support `--db-path PATH` (default: `applications.db`).

### `add`

Add a new application:

- Command: `jobapp add`
- Key options:
  - `--company`
  - `--role`
  - `--link`
  - `--location`
  - `--date-applied`
  - `--source`
  - `--status` (default: `Applied`)
  - `--priority` (1, 2, 3; default 2)
  - `--notes`
- Behavior:
  - Inserts a new row
  - Fills `date_applied` with today if omitted
  - Prints new application ID

### `list`

List stored applications:

- Command: `jobapp list`
- Filters:
  - `--company` (substring match via SQL `LIKE`)
  - `--status` (exact match)
  - `--active-only` (exclude `Rejected`, `Ghosted`, `Withdrawn`)
- Output:
  - Human-readable listing via `print_applications`

### `stats`

Show counts grouped by status:

- Command: `jobapp stats`
- Output:
  - Count of applications per `status` (e.g., `Applied`, `OA`, `Interview`, `Rejected`)

### `followups`

Show older applications that may need follow-up:

- Command: `jobapp followups --days N` (default: 7)
- Logic:
  - `status IN ('Applied', 'Recruiter Screen', 'OA')`
  - `julianday('now') - julianday(date_applied) > days`
- Output:
  - List of candidate applications (or a message if none)

### `update-status`

Update application status:

- Command: `jobapp update-status ID STATUS [--last-action TEXT]`
- Behavior:
  - Updates `status` and `last_action` for the given ID
  - Prints a confirmation or a “no such ID” message

## Command Entry and Usage

- `jobapp` is available globally via symlink in `~/bin`
- Entry script `jobs_cli.py` is a thin wrapper:

  - Imports `jobapp.cli.main`
  - Calls `main()` under `if __name__ == "__main__"` guard

Result: `jobapp` behaves like a first-class CLI tool.

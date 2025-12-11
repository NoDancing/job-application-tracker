# JobApp Next Steps

## Priority 1: Core UX Improvements

### 1. `init` Subcommand

Add a first-class initialization command:

- Command:
  - `jobapp init`
  - `jobapp --db-path /path/to/db init`
- Behavior:
  - If DB file does not exist:
    - Create it and initialize schema
    - Print: `Initialized new database at <path>`
  - If DB exists:
    - Run `init_db` to ensure schema is current
    - Print: `Database already existed at <path>. Ensured schema is up to date.`
- Implementation:
  - Add `run_init(db_path: Path)` to `jobapp/db.py`
  - Add `init` subparser in `jobapp/cli.py`
  - In `cli.main()`, handle `command == "init"` before opening a shared connection

### 2. `search` Subcommand

Free-text search for quick lookups:

- Command:
  - `jobapp search QUERY`
- Behavior:
  - Case-insensitive substring search across:
    - `company`
    - `role`
    - `notes`
  - Display results via `print_applications`
- Implementation:
  - Add `search_applications(conn, query) -> List[Application]` to `jobapp/db.py`
  - Add `search` subparser in `jobapp/cli.py` (positional `query`)
  - In `cli.main()`, call `search_applications` and `print_applications`

### 3. `export` Subcommand (CSV)

Enable easy spreadsheet export:

- Command:
  - `jobapp export FILEPATH`
  - `jobapp export FILEPATH --active-only`
- Behavior:
  - Write all (or only active) applications as CSV to `FILEPATH`
- Implementation:
  - Add `export_applications_to_csv(conn, filepath, active_only=False)` in `jobapp/db.py`
  - Add `export` subparser in `jobapp/cli.py`:
    - Positional `filepath`
    - Flag `--active-only`
  - In `cli.main()`, dispatch to `export_applications_to_csv`

## Priority 2: Workflow & Reporting Enhancements

### 4. `summary` Command

High-level overview:

- Command:
  - `jobapp summary`
- Possible output:
  - Total applications
  - Applications this week
  - Active applications
  - Follow-ups needed (reuse `followups` logic)
  - Status breakdown (reuse `stats_by_status`)
- Implementation:
  - Add helper queries to `jobapp/db.py` as needed
  - Add `summary` subparser and dispatch in `jobapp/cli.py`

### 5. Update-by-Match (Optional)

Reduce reliance on numeric IDs:

- Command:
  - `jobapp update --company "X" --role "Y" --status "Z" [--last-action TEXT]`
- Behavior:
  - Find matching application(s) by company + role
  - Update most recent match, or warn on ambiguity
- Implementation:
  - Add a matching helper in `jobapp/db.py`
  - Add `update` subparser in `jobapp/cli.py`
  - Decide on behavior when multiple rows match

## Priority 3: Polish and Maintainability

### 6. Improve `--help` Output

Make `jobapp --help` self-documenting:

- Use `prog="jobapp"`, `description`, and `epilog` with examples
- Set `formatter_class=argparse.RawDescriptionHelpFormatter`

### 7. Basic Tests

Add a minimal test suite:

- Create `tests/` directory
- Use `pytest` with `tmp_path` for a temporary DB
- Suggested tests:
  - `add_application` inserts correctly
  - `list_applications` filters as expected
  - `followups` returns correct items for given `days`
  - `update_status` updates a known row and handles unknown IDs

### 8. Packaging (Optional)

Move away from manual symlink to `pip install -e .`:

- Add `pyproject.toml`:
  - Define project metadata
  - Add console script entry:

    ```toml
    [project.scripts]
    jobapp = "jobapp.cli:main"
    ```

- Install locally:
  - `pip install -e .`
- Remove or stop relying on the manual `~/bin/jobapp` symlink

---

## Suggested Implementation Order

1. Implement `init` in `db.py` and `cli.py`
2. Implement `search`
3. Implement `export`
4. Add `summary`
5. Improve `--help`
6. Add basic tests
7. (Optional) Add packaging + console script
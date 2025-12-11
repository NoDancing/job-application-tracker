

# JobApp — A Structured Job Application Tracker (CLI + SQLite)

JobApp is a lightweight command-line tool that manages a local SQLite database of your job applications. It replaces ad-hoc spreadsheets with a consistent, queryable, automatable structure.

This tool is designed for:
- Fast data entry
- Zero-dependency local storage
- Easy scripting and automation
- Use with LLMs (via standardized conventions)

All data is stored in a single SQLite file (`applications.db` by default).

---

## Features

- Add new applications with structured fields
- Update statuses and record timeline events
- Search applications by keyword
- List active applications or filter by status/company
- Identify follow-up candidates based on age
- Export to CSV for spreadsheet use
- Fully tested with pytest
- Built to support automation (LLM-friendly)

See **CONVENTIONS.md** for standardized vocabularies and formats used by all commands.

---

## Project Structure

```
app_database/
├─ jobapp/
│   ├─ __init__.py
│   ├─ cli.py          # CLI interface (argparse)
│   ├─ db.py           # Database layer and queries
│   ├─ models.py       # Application dataclass
│
├─ tests/
│   ├─ conftest.py     # pytest fixtures
│   ├─ test_db_basic.py
│
├─ CONVENTIONS.md      # Rules for status, priority, sources, etc.
├─ README.md           # This file
└─ applications.db     # Auto-created at runtime (ignored until you add data)
```

---

## Installation (Development Mode)

Install the CLI as an editable package:

```
pip install -e .
```

Alternatively, use a manual symlink:

```
ln -s /path/to/jobapp/cli.py ~/bin/jobapp
chmod +x ~/bin/jobapp
```

---

## Usage

### Initialize a New Database

```
jobapp init
```

### Add a New Application

```
jobapp add \
  --company "Flatiron Institute" \
  --role "Database & Testing Intern" \
  --source "Company Site" \
  --priority 1 \
  --notes "HPC benchmarking; strong alignment with systems background."
```

Defaults:
- `status = Applied`
- `priority = 2`
- `date_applied = today`

### Search

```
jobapp search flatiron
```

### List

```
jobapp list --active-only
jobapp list --status "Interview"
jobapp list --company "Panic"
```

### Update Status

```
jobapp update-status 12 "Interview" \
  --last-action "2025-12-18 — Scheduled technical screen"
```

### Follow-ups

```
jobapp followups --days 10
```

### Export to CSV

```
jobapp export all_apps.csv
jobapp export active_apps.csv --active-only
```

---

## Conventions

All commands adhere to the rules defined in **CONVENTIONS.md**, including:

- Allowed status values
- Priority scale
- Source vocabulary
- ISO date formats
- Structured `last_action` entries
- Notes format

These conventions ensure consistency and allow LLMs or scripts to construct correct commands.

---

## Running Tests

```
pytest -q
```

Tests cover:
- Adding applications
- Listing & filtering
- Follow-up logic
- Status updates
- CSV exports

---

## Future Extensions

- PyPI packaging (`pyproject.toml`)
- CLI-level tests
- TUI or minimal web dashboard
- Automatic reminders
- Resume & keyword analytics

---

## License

Personal project; license TBD.
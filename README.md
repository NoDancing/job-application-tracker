# JobApp — Structured Job Application Tracker (CLI + SQLite)

[![Build Status](https://github.com/USERNAME/REPO/actions/workflows/tests.yml/badge.svg)](https://github.com/USERNAME/REPO/actions)
[![Test Coverage](https://img.shields.io/codecov/c/github/USERNAME/REPO)](https://app.codecov.io/gh/USERNAME/REPO)
[![License](https://img.shields.io/github/license/USERNAME/REPO)](https://github.com/USERNAME/REPO/blob/main/LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/jobapp)](https://pypi.org/project/jobapp/)
[![PyPI Version](https://img.shields.io/pypi/v/jobapp.svg)](https://pypi.org/project/jobapp/)

> Replace `USERNAME` and `REPO` in the badge URLs above with the actual GitHub username and repository name once this project is hosted on GitHub. The PyPI badges will become accurate once the project is published to PyPI.

JobApp is a command-line tool for managing job applications using a local SQLite database. It provides a structured and queryable workflow in place of ad-hoc spreadsheets, enabling consistent tracking, automation, and integration with developer tooling.

The project is designed to support:
- Fast and reliable data entry  
- Zero external service dependencies  
- Simple scripting and automation  
- Consistent formats for LLM-generated commands  
- Local, portable storage (a single `applications.db` file)

---

## Features

- Add new job applications with standardized fields  
- Update application status and timeline events  
- Search by keyword (company or role)  
- Filter and list active applications  
- Identify stale applications requiring follow-up  
- Export all data to CSV for spreadsheet analysis  
- Tested with `pytest`  
- Extensible structure suitable for future automation or packaging  

See **CONVENTIONS.md** for the authoritative definitions of statuses, priorities, dates, sources, and event formatting.

---

## Project Structure

```text
app_database/
├─ jobapp/
│   ├─ __init__.py
│   ├─ cli.py          # CLI entry point
│   ├─ db.py           # SQLite access layer
│   ├─ models.py       # Application dataclass definitions
│
├─ tests/
│   ├─ conftest.py     # Test fixtures and temporary DB harness
│   ├─ test_db_basic.py
│
├─ CONVENTIONS.md      # Required formatting rules for data entry
├─ README.md
└─ applications.db     # Generated at runtime (not version-controlled)
```

---

## Installation (Development Mode)

Install as an editable package (recommended during development):

```bash
pip install -e .
```

Alternatively, install via a manual symlink:

```bash
ln -s /path/to/jobapp/cli.py ~/bin/jobapp
chmod +x ~/bin/jobapp
```

Ensure `~/bin` is on your `PATH`.

---

## Usage

### Initialize a Database

```bash
jobapp init
```

### Add an Application

```bash
jobapp add \
  --company "Flatiron Institute" \
  --role "Database & Testing Intern" \
  --source "Company Site" \
  --priority 1 \
  --notes "HPC benchmarking; strong alignment with systems background."
```

Default values:
- `status = Applied`  
- `priority = 2`  
- `date_applied = today`

### Search

```bash
jobapp search flatiron
```

### List

```bash
jobapp list --active-only
jobapp list --status "Interview"
jobapp list --company "Panic"
```

### Update Status

```bash
jobapp update-status 12 "Interview" \
  --last-action "2025-12-18 — Scheduled technical screen"
```

### Follow-Up Recommendations

```bash
jobapp followups --days 10
```

### Export to CSV

```bash
jobapp export all_apps.csv
jobapp export active_apps.csv --active-only
```

---

## Testing

Execute the test suite:

```bash
pytest -q
```

The suite currently covers:
- Record creation  
- Filtering behavior  
- Follow-up detection  
- Status updates  
- CSV export integrity  

---

## Planned Enhancements

- Packaging with `pyproject.toml` and publishing to PyPI  
- CLI-level integration tests  
- Optional terminal UI or lightweight web dashboard  
- Automated reminders (email or local notifications)  
- Analytics features (conversion rates, timeline analysis)  

---

## License

Personal project; license to be determined.
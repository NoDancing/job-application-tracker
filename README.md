# JobApp — Structured Job Application Tracker (CLI + SQLite)

Well, the Fall term has come to an end, and it's time to desperately start applying to internships. This is a simple app I put together to avoid having to use a spreadsheet, and prove I can quickly put together a workable, shareable piece of software.

**What it does:**
It keeps track of all the applications you've submitted in a clean, structured way, and makes it easy to review your pipeline, run simple analytics, or export everything to CSV.

**How to use it:**
The `CONVENTIONS.md` file is designed to be shared with an LLM. You can paste in a job description, and it will generate a clean `jobapp add ...` command that records the application in the database with consistent formatting.

**What I'm demonstrating here:**
- Ability to design and build a small but well-structured CLI tool
- Clear separation between database logic, models, and command-line interface
- Use of SQLite for lightweight, durable data storage
- Modern Python packaging (`pyproject.toml`, console scripts)
- Meaningful test coverage and GitHub Actions CI
- Documentation and conventions that support automation and reproducibility

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
- Update any field of an application (company, role, priority, etc.)
- Remove applications by ID
- Search by keyword (company or role)
- Filter and list active applications
- View comprehensive statistics and analytics
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

### Update Application Fields

Update any field(s) of an existing application:

```bash
jobapp update 12 \
  --priority 1 \
  --notes "Updated after positive initial conversation"

jobapp update "Flatiron" \
  --status "Interview" \
  --location "Remote"
```

### Remove an Application

```bash
jobapp remove 12
```

### View Statistics

Display comprehensive analytics about your applications:

```bash
jobapp stats
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

## Why I Built This

I wanted a structured and automatable alternative to the spreadsheets I used to track job applications. Building JobApp gave me the opportunity to practice several engineering skills in a contained, end-to-end project:

- Designing a small but well-structured CLI tool
- Building a normalized SQLite schema and data-access layer
- Separating concerns across modules (models, DB logic, CLI)
- Writing tests around data operations and behaviors
- Using modern Python packaging (`pyproject.toml`, console scripts)
- Establishing conventions suitable for AI-assisted workflows

Beyond being a useful personal tool, this project reflects my focus on clarity, reproducibility, and maintainability in real-world development workflows.

---

## Planned Enhancements

- Packaging with `pyproject.toml` and publishing to PyPI
- CLI-level integration tests
- Optional terminal UI or lightweight web dashboard
- Automated reminders (email or local notifications)
- Analytics features (conversion rates, timeline analysis)

---

## License

This project is released under the MIT License. See the `LICENSE` file for full terms.

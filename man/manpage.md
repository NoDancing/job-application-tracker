% JOBAPP(1) JobApp | User Commands

# NAME
jobapp - structured job application tracking CLI using SQLite

# SYNOPSIS
**jobapp** *command* [*options*]

# DESCRIPTION
**jobapp** is a command-line tool for managing job applications using a local SQLite database.
It provides a structured, queryable alternative to spreadsheets, enabling consistent tracking,
automation, and integration with developer workflows.

The tool enforces strict conventions for application status, priority, sources, dates, and
timeline events. These conventions are designed to support reliable scripting and LLM-assisted
command generation.

All data is stored locally in a single SQLite database file and requires no external services.

# COMMANDS

## init
Initialize a new applications database in the current directory.

```
jobapp init
```

If the database already exists, the command will refuse to overwrite it.

---

## add
Add a new job application record.

```
jobapp add \
  --company "<Company>" \
  --role "<Role>" \
  [--link "<URL>"] \
  [--location "<Location>"] \
  [--date-applied YYYY-MM-DD] \
  --source "<Source>" \
  [--status "Applied"] \
  [--priority <1|2|3>] \
  --notes "<short context>"
```

Required fields:
- **--company**
- **--role**
- **--source**

Defaults:
- `status = Applied`
- `priority = 2`
- `date_applied = today`

All values must conform to the rules defined in **CONVENTIONS.md**.

---

## update-status
Update the status of an existing application and record a timeline event.

```
jobapp update-status <ID> "<Status>" \
  --last-action "<YYYY-MM-DD — event description>"
```

The status must be one of the allowed status values.
The `last_action` field must follow the exact single-line format defined in the conventions file.

---

## update
Update one or more fields of an existing application.

```
jobapp update <ID or company-substring> \
  [--company "<New Company>"] \
  [--role "<New Role>"] \
  [--link "<New URL>"] \
  [--location "<New Location>"] \
  [--date-applied YYYY-MM-DD] \
  [--source "<Source>"] \
  [--status "<Status>"] \
  [--priority <1|2|3>] \
  [--notes "<short context>"]
```

Only fields explicitly passed via flags will be modified.
If a company substring is used, it must match exactly one application.

---

## search
Search applications by company or role keyword.

```
jobapp search <keyword>
```

---

## list
List applications with optional filters.

```
jobapp list
jobapp list --active-only
jobapp list --status "<Status>"
jobapp list --company "<Company>"
```

---

## followups
Identify applications that may require follow-up.

```
jobapp followups --days <N>
```

Lists applications whose last recorded activity is older than the specified number of days.

---

## export
Export application data to CSV.

```
jobapp export <output.csv>
jobapp export <output.csv> --active-only
```

---

# DATA MODEL
Each application record includes:
- Company
- Role
- Application status
- Priority (1–3)
- Application date
- Source
- Optional link and location
- Last action (single-line event)
- Notes (short contextual text)

The authoritative definitions for allowed values and formats are specified in **CONVENTIONS.md**.

# FILES

`applications.db`
: SQLite database containing all application records.

`CONVENTIONS.md`
: Canonical rules for statuses, priorities, sources, dates, and timeline events.

# EXIT STATUS

0
: Command completed successfully.

1
: Invalid command usage or validation failure.

2
: Database error or unexpected internal failure.

# EXAMPLES

Add a new application:

```
jobapp add \
  --company "Flatiron Institute" \
  --role "Database & Testing Intern" \
  --source "Company Site" \
  --priority 1 \
  --notes "HPC benchmarking; strong alignment with systems background."
```

Update status after an interview:

```
jobapp update-status 12 "Interview" \
  --last-action "2025-12-18 — Scheduled technical screen"
```

# DESIGN NOTES
**jobapp** is intentionally opinionated. By enforcing strict conventions, it enables:
- Reliable automation
- Scriptable workflows
- LLM-assisted command generation
- Clean analytics and exports

The project favors clarity and reproducibility over flexibility.

# AUTHOR
Sean Cohan

# LICENSE
MIT License

# SEE ALSO
sqlite3(1),
pandoc(1)
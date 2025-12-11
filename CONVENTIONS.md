# Job Application Command Conventions

This document defines strict conventions for how all job applications should be recorded and updated using the `jobapp` CLI. These rules must be followed exactly so that automated tools (including LLMs) can reliably construct commands.

---

## 1. Allowed Status Values (exact strings)

Use only these status values:

- `Applied`
- `Recruiter Screen`
- `OA`
- `Interview`
- `Offer`
- `Rejected`
- `Ghosted`
- `Withdrawn`

Do NOT invent new statuses. Sub-stage details belong in `last_action`.

---

## 2. Priority Values

Use only these integers:

- `1` = High priority
- `2` = Medium priority (default)
- `3` = Low priority

---

## 3. Source Vocabulary (exact strings)

Use only one of:

- `Company Site`
- `LinkedIn`
- `Handshake`
- `Referral`
- `Career Fair`
- `AngelList`
- `Indeed`
- `Other`

---

## 4. Date Format

Always use ISO format:

`YYYY-MM-DD`

If omitted, the CLI uses today’s date.

---

## 5. last_action Format (strict)

Single-line event description in the following format:

`<YYYY-MM-DD> — <event description>`

Examples:

- `2025-12-14 — Applied via company site`
- `2025-12-18 — Completed recruiter screen`
- `2025-12-20 — Received OA invite (due 2025-12-23)`
- `2025-12-28 — Rejection email`

Do not add multi-line notes here. Use `notes` for longer context.

---

## 6. notes Format

Freeform text, 1–3 sentences max. Used for static context such as:

- motivation (why apply)
- tech stack
- referral info
- fit/alignment notes

Example:

`Referral from OSU alum; strong fit with systems/ML background; team works on HPC cluster tools.`

---

## 7. Command Patterns

### 7.1 Add a new application

Pattern:

`jobapp add \
  --company "<Company>" \
  --role "<Role>" \
  --link "<URL or omit>" \
  --location "<Location or omit>" \
  --date-applied YYYY-MM-DD \
  --source "<Source>" \
  --status "Applied" \
  --priority <1|2|3> \
  --notes "<short context>"`

### 7.2 Update an application's status

Pattern:

`jobapp update-status <ID> "<Status>" \
  --last-action "<YYYY-MM-DD> — <event>"`

Where `<Status>` is one of the allowed status values.

### 7.3 Update any application fields

Use the general-purpose update command when modifying fields other than status.

Pattern:

`jobapp update <ID or company-substring> \
  [--company "<New Company>"] \
  [--role "<New Role>"] \
  [--link "<New URL>"] \
  [--location "<New Location>"] \
  [--date-applied YYYY-MM-DD] \
  [--source "<Source>"] \
  [--status "<Status>"] \
  [--priority <1|2|3>] \
  [--notes "<short context>"]`

Rules:

- `<ID>` is preferred when known.  
- If `<company-substring>` is used and matches exactly one application, it is accepted.  
- If multiple applications match, the command must refuse to proceed.  
- Only the fields explicitly passed via flags will be updated; all others remain unchanged.

---

## 8. Search Guidance for LLMs

When generating `jobapp` commands:

- Always include `--company` and `--role` for `add`.
- Use the exact vocabularies defined in this document for:
  - `status`
  - `priority`
  - `source`
- Use ISO dates (`YYYY-MM-DD`) for `date-applied` and within `last_action`.
- Use the `last_action` format verbatim.
- Prefer explicit, single-purpose commands over complex or ambiguous ones.
- When generating `update` commands, include only the fields that should change; never re-specify unchanged fields.

---

This file defines the canonical protocol for all automated or manual interactions with the `jobapp` database.

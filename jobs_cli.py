#!/usr/bin/env python3
"""
jobs_cli.py — A simple, extensible command-line job-application tracker.

This script maintains a local SQLite database (`applications.db`) that stores
structured information about all job applications you submit. It provides
subcommands for adding new applications, listing them with filters, generating
summary statistics, identifying applications that may require follow-up, and
updating the status of existing entries.

Why this exists:
    - Excel and Google Sheets are tedious to maintain manually.
    - A database provides structure, reliability, and automation potential.
    - This CLI keeps the workflow extremely simple:
          python jobs_cli.py add --company ... --role ...
          python jobs_cli.py list --active-only
          python jobs_cli.py update-status 12 "Technical Interview"

This file is designed to be self-explanatory and easy to maintain.
"""

import argparse
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional, List, Tuple

DEFAULT_DB_PATH = Path("applications.db")


# ---------------------------------------------------------------------------
# Data class representing one application record
# ---------------------------------------------------------------------------

@dataclass
class Application:
    """
    Represents a single job application stored in the database.

    This mirrors the schema of the `applications` table. Using a dataclass
    allows us to return typed objects instead of raw SQLite rows.
    """
    id: int
    company: str
    role: str
    job_link: Optional[str]
    location: Optional[str]
    date_applied: str      # ISO8601 date string (YYYY-MM-DD)
    source: Optional[str]
    status: str
    last_action: Optional[str]
    priority: Optional[int]
    notes: Optional[str]


# ---------------------------------------------------------------------------
# Database initialization utilities
# ---------------------------------------------------------------------------

def get_connection(db_path: Path) -> sqlite3.Connection:
    """
    Open a connection to the SQLite database specified by `db_path`.
    The connection uses row_factory=sqlite3.Row so results behave like dicts.

    Parameters:
        db_path (Path): Path to the SQLite database file.

    Returns:
        sqlite3.Connection: An open connection to the database.
    """
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """
    Create the `applications` table and indexes if they do not already exist.

    This function is idempotent: calling it repeatedly is safe.

    Schema design notes:
        - date_applied is stored as a string in ISO format (YYYY-MM-DD).
          SQLite does not enforce a DATE type, so we store it consistently
          and rely on julianday() for date arithmetic.
        - status defaults to "Applied".
        - priority defaults to 2 (Medium).
    """
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            job_link TEXT,
            location TEXT,
            date_applied TEXT NOT NULL,
            source TEXT,
            status TEXT NOT NULL DEFAULT 'Applied',
            last_action TEXT,
            priority INTEGER DEFAULT 2,
            notes TEXT
        )
        """
    )

    # Indexes significantly improve performance for large datasets.
    cur.execute("CREATE INDEX IF NOT EXISTS idx_status ON applications(status)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_date ON applications(date_applied)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_company ON applications(company)")

    conn.commit()


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------

def add_application(
    conn: sqlite3.Connection,
    company: str,
    role: str,
    job_link: Optional[str],
    location: Optional[str],
    date_applied: Optional[str],
    source: Optional[str],
    status: str,
    priority: Optional[int],
    notes: Optional[str],
) -> int:
    """
    Insert a new job application into the database.

    Parameters:
        company (str): Employer name.
        role (str): Title of the position.
        job_link (str): URL to job posting (optional).
        location (str): Job location or "Remote" (optional).
        date_applied (str): ISO date string. If None, defaults to today's date.
        source (str): Where you found/applied to the job (e.g. LinkedIn).
        status (str): Pipeline status (e.g., "Applied", "OA", "Interview").
        priority (int): Priority level (1 = High, 2 = Medium, 3 = Low).
        notes (str): Freeform notes (referrals, comments, reminders).

    Returns:
        int: The auto-incremented ID of the newly inserted row.
    """
    if date_applied is None:
        date_applied = date.today().isoformat()

    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO applications
            (company, role, job_link, location, date_applied, source, status, priority, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (company, role, job_link, location, date_applied, source, status, priority, notes),
    )
    conn.commit()
    return cur.lastrowid


def list_applications(
    conn: sqlite3.Connection,
    company: Optional[str],
    status: Optional[str],
    active_only: bool,
) -> List[Application]:
    """
    Retrieve job applications with optional filtering.

    Parameters:
        company (str): Substring filter for employer name.
        status (str): Exact match filter for application status.
        active_only (bool): Exclude applications marked Rejected/Ghosted/Withdrawn.

    Returns:
        List[Application]: List of Application dataclass instances.
    """
    sql = "SELECT * FROM applications WHERE 1=1"
    params: Tuple = ()

    if company:
        sql += " AND company LIKE ?"
        params += (f"%{company}%",)

    if status:
        sql += " AND status = ?"
        params += (status,)

    if active_only:
        sql += " AND status NOT IN ('Rejected', 'Ghosted', 'Withdrawn')"

    sql += " ORDER BY date_applied DESC, id DESC"

    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()

    return [
        Application(
            id=row["id"],
            company=row["company"],
            role=row["role"],
            job_link=row["job_link"],
            location=row["location"],
            date_applied=row["date_applied"],
            source=row["source"],
            status=row["status"],
            last_action=row["last_action"],
            priority=row["priority"],
            notes=row["notes"],
        )
        for row in rows
    ]


def update_status(
    conn: sqlite3.Connection,
    app_id: int,
    status: str,
    last_action: Optional[str],
) -> None:
    """
    Update the status (and optionally last_action note) of a job application.

    Parameters:
        app_id (int): ID of the application to update.
        status (str): New pipeline status.
        last_action (str): Optional explanation of the event
                           (e.g. "Spoke with recruiter", "Scheduled OA").
    """
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE applications
        SET status = ?, last_action = ?
        WHERE id = ?
        """,
        (status, last_action, app_id),
    )

    if cur.rowcount == 0:
        print(f"No application with ID {app_id} exists.")
    else:
        conn.commit()
        print(f"Updated application {app_id} to status '{status}'.")


# ---------------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------------

def print_applications(apps: List[Application]) -> None:
    """
    Print a human-readable summary of the provided Application objects.

    Used by the `list` and `followups` subcommands to display results.
    """
    if not apps:
        print("No applications found.")
        return

    for app in apps:
        print("=" * 60)
        print(f"[{app.id}] {app.company} — {app.role}")
        print(f"  Applied on: {app.date_applied}")
        print(f"  Status:     {app.status}")
        if app.priority is not None:
            print(f"  Priority:   {app.priority}")
        if app.location:
            print(f"  Location:   {app.location}")
        if app.source:
            print(f"  Source:     {app.source}")
        if app.job_link:
            print(f"  Link:       {app.job_link}")
        if app.last_action:
            print(f"  Last action: {app.last_action}")
        if app.notes:
            print(f"  Notes:      {app.notes}")

    print("=" * 60)
    print(f"Total applications: {len(apps)}")


def stats_by_status(conn: sqlite3.Connection) -> None:
    """
    Print a count of applications grouped by status.
    Helpful for understanding pipeline distribution at a glance.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT status, COUNT(*) AS count
        FROM applications
        GROUP BY status
        ORDER BY count DESC
        """
    )

    rows = cur.fetchall()
    if not rows:
        print("No applications in database.")
        return

    print("Applications by status:")
    for row in rows:
        print(f"  {row['status']}: {row['count']}")


def followups(conn: sqlite3.Connection, days: int) -> List[Application]:
    """
    Retrieve applications older than `days` days that are still in early statuses
    and therefore likely require a follow-up email.

    "Early statuses" include:
        - Applied
        - Recruiter Screen
        - OA

    Returns:
        List[Application]: Applications that may need follow-up.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM applications
        WHERE status IN ('Applied', 'Recruiter Screen', 'OA')
          AND julianday('now') - julianday(date_applied) > ?
        ORDER BY date_applied ASC
        """,
        (days,),
    )

    rows = cur.fetchall()

    return [
        Application(
            id=row["id"],
            company=row["company"],
            role=row["role"],
            job_link=row["job_link"],
            location=row["location"],
            date_applied=row["date_applied"],
            source=row["source"],
            status=row["status"],
            last_action=row["last_action"],
            priority=row["priority"],
            notes=row["notes"],
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Command-line interface
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    """
    Define all CLI arguments and subcommands.

    Subcommands:
        add            Add a new application.
        list           List applications (with filters).
        stats          Show summary statistics grouped by status.
        followups      Identify stale applications needing follow-up.
        update-status  Update an application's status and optional last_action.

    Returns:
        argparse.Namespace: Parsed CLI arguments.
    """
    parser = argparse.ArgumentParser(
        description="Job application tracker backed by SQLite."
    )

    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Path to SQLite DB file (default: {DEFAULT_DB_PATH}).",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # add
    p_add = subparsers.add_parser("add", help="Add a new job application.")
    p_add.add_argument("--company", required=True)
    p_add.add_argument("--role", required=True)
    p_add.add_argument("--link", dest="job_link")
    p_add.add_argument("--location")
    p_add.add_argument("--date-applied", help="ISO date, default: today.")
    p_add.add_argument("--source", help="LinkedIn, referral, company site, etc.")
    p_add.add_argument(
        "--status",
        default="Applied",
        help="Pipeline stage (default: Applied).",
    )
    p_add.add_argument(
        "--priority",
        type=int,
        choices=[1, 2, 3],
        help="1 = high, 2 = medium (default), 3 = low.",
    )
    p_add.add_argument("--notes")

    # list
    p_list = subparsers.add_parser("list", help="List stored applications.")
    p_list.add_argument("--company", help="Substring match on company name.")
    p_list.add_argument("--status", help="Filter by exact status.")
    p_list.add_argument(
        "--active-only",
        action="store_true",
        help="Exclude Rejected, Ghosted, and Withdrawn applications.",
    )

    # stats
    subparsers.add_parser("stats", help="Show counts by status.")

    # followups
    p_follow = subparsers.add_parser(
        "followups",
        help="List applications older than N days that may require follow-up.",
    )
    p_follow.add_argument(
        "--days",
        type=int,
        default=7,
        help="Days since application before flagging for follow-up (default: 7).",
    )

    # update-status
    p_update = subparsers.add_parser(
        "update-status",
        help="Update status of an application by ID.",
    )
    p_update.add_argument("id", type=int, help="Application ID.")
    p_update.add_argument("status", help="New pipeline status.")
    p_update.add_argument(
        "--last-action",
        help="Explanation of the update (e.g., 'Scheduled phone screen').",
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Dispatch the appropriate command handler based on CLI arguments.
    This is the central orchestration function of the CLI.
    """
    args = parse_args()

    conn = get_connection(args.db_path)
    init_db(conn)

    if args.command == "add":
        app_id = add_application(
            conn=conn,
            company=args.company,
            role=args.role,
            job_link=args.job_link,
            location=args.location,
            date_applied=args.date_applied,
            source=args.source,
            status=args.status,
            priority=args.priority if args.priority is not None else 2,
            notes=args.notes,
        )
        print(f"Added new application with ID {app_id}.")

    elif args.command == "list":
        apps = list_applications(
            conn=conn,
            company=args.company,
            status=args.status,
            active_only=args.active_only,
        )
        print_applications(apps)

    elif args.command == "stats":
        stats_by_status(conn)

    elif args.command == "followups":
        apps = followups(conn, days=args.days)
        if not apps:
            print(f"No applications older than {args.days} days needing follow-up.")
        else:
            print(f"Applications older than {args.days} days needing follow-up:")
            print_applications(apps)

    elif args.command == "update-status":
        update_status(
            conn=conn,
            app_id=args.id,
            status=args.status,
            last_action=args.last_action,
        )

    conn.close()


if __name__ == "__main__":
    main()
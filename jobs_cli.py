#!/usr/bin/env python3
"""
Simple CLI job application tracker using SQLite.

Usage examples:

  # Add a new application
  python jobs_cli.py add \
      --company "Flatiron Institute" \
      --role "Database & Automated Testing Intern" \
      --link "https://example.com/job" \
      --location "New York, NY" \
      --source "Company site" \
      --priority 1 \
      --notes "HPC benchmarks; database + automated testing"

  # List all active (non-rejected) applications
  python jobs_cli.py list --active-only

  # List all applications for a company
  python jobs_cli.py list --company "Flatiron Institute"

  # Show stats by status
  python jobs_cli.py stats

  # Show applications that need follow-up (older than N days)
  python jobs_cli.py followups --days 10
"""

import argparse
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional, List, Tuple

DEFAULT_DB_PATH = Path("applications.db")


@dataclass
class Application:
    id: int
    company: str
    role: str
    job_link: Optional[str]
    location: Optional[str]
    date_applied: str   # ISO string: YYYY-MM-DD
    source: Optional[str]
    status: str
    last_action: Optional[str]
    priority: Optional[int]
    notes: Optional[str]


def get_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create table and indexes if they do not already exist."""
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            job_link TEXT,
            location TEXT,
            date_applied TEXT NOT NULL, -- ISO8601 YYYY-MM-DD
            source TEXT,
            status TEXT NOT NULL DEFAULT 'Applied',
            last_action TEXT,
            priority INTEGER DEFAULT 2,
            notes TEXT
        )
        """
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_status ON applications(status)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_date ON applications(date_applied)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_company ON applications(company)")
    conn.commit()


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


def print_applications(apps: List[Application]) -> None:
    if not apps:
        print("No applications found.")
        return

    for app in apps:
        print("=" * 60)
        print(f"[{app.id}] {app.company} — {app.role}")
        print(f"  Date applied: {app.date_applied}")
        print(f"  Status:      {app.status}")
        if app.priority is not None:
            print(f"  Priority:    {app.priority}")
        if app.location:
            print(f"  Location:    {app.location}")
        if app.source:
            print(f"  Source:      {app.source}")
        if app.job_link:
            print(f"  Link:        {app.job_link}")
        if app.last_action:
            print(f"  Last action: {app.last_action}")
        if app.notes:
            print(f"  Notes:       {app.notes}")
    print("=" * 60)
    print(f"Total: {len(apps)} application(s).")


def stats_by_status(conn: sqlite3.Connection) -> None:
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
    Get applications older than `days` days that are still in early stages
    (Applied / Recruiter Screen / OA) and may need a follow-up.
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


def update_status(
    conn: sqlite3.Connection,
    app_id: int,
    status: str,
    last_action: Optional[str],
) -> None:
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
        print(f"No application found with id {app_id}.")
    else:
        conn.commit()
        print(f"Updated application {app_id} to status '{status}'.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Job application tracker (SQLite-based)."
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Path to SQLite DB file (default: {DEFAULT_DB_PATH})",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # add
    p_add = subparsers.add_parser("add", help="Add a new application.")
    p_add.add_argument("--company", required=True)
    p_add.add_argument("--role", required=True)
    p_add.add_argument("--link", dest="job_link")
    p_add.add_argument("--location")
    p_add.add_argument(
        "--date-applied",
        help="YYYY-MM-DD (default: today)",
    )
    p_add.add_argument("--source", help="e.g. LinkedIn, company site, referral")
    p_add.add_argument(
        "--status",
        default="Applied",
        help="Status (default: Applied)",
    )
    p_add.add_argument(
        "--priority",
        type=int,
        choices=[1, 2, 3],
        help="1=high, 2=medium, 3=low (default: 2)",
    )
    p_add.add_argument("--notes")

    # list
    p_list = subparsers.add_parser("list", help="List applications.")
    p_list.add_argument("--company", help="Filter by company (substring match).")
    p_list.add_argument("--status", help="Filter by exact status.")
    p_list.add_argument(
        "--active-only",
        action="store_true",
        help="Only show non-rejected / non-ghosted applications.",
    )

    # stats
    subparsers.add_parser("stats", help="Show counts by status.")

    # followups
    p_follow = subparsers.add_parser(
        "followups", help="Show applications that may need follow-up."
    )
    p_follow.add_argument(
        "--days",
        type=int,
        default=7,
        help="Threshold in days since application (default: 7).",
    )

    # update-status
    p_update = subparsers.add_parser(
        "update-status", help="Update the status of an application by id."
    )
    p_update.add_argument("id", type=int, help="Application id.")
    p_update.add_argument("status", help="New status.")
    p_update.add_argument(
        "--last-action",
        help="Description of what happened (e.g., 'Spoke with recruiter on 2025-12-10').",
    )

    return parser.parse_args()


def main() -> None:
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
        print(f"Added application with id {app_id}.")
ource 
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
            print(
                f"Applications older than {args.days} days in early stages (likely need follow-up):"
            )
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
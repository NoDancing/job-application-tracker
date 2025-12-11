# jobapp/db.py
"""
Database access layer for the job application tracker.

This module is responsible for:
  - Opening SQLite connections
  - Initializing the schema
  - CRUD operations on the `applications` table
  - Basic reporting queries (stats, followups)
"""

import sqlite3
import csv
from datetime import date
from pathlib import Path
from typing import List, Optional, Tuple

from .models import Application

DEFAULT_DB_PATH = Path("applications.db")


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


def run_init(db_path: Path) -> None:
    """
    Ensure that the job application database exists at `db_path`
    and that the required schema is present.

    This operation is idempotent: running it multiple times is safe.
    """
    # Check whether a file already exists at this path *before* opening it.
    existed_before = db_path.exists()

    conn = get_connection(db_path)
    try:
        init_db(conn)
    finally:
        conn.close()

    if existed_before:
        print(f"Database already existed at {db_path}. Ensured schema is up to date.")
    else:
        print(f"Initialized new database at {db_path}.")


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
        (
            company,
            role,
            job_link,
            location,
            date_applied,
            source,
            status,
            priority,
            notes,
        ),
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


def search_applications(
    conn: sqlite3.Connection,
    query: str,
) -> List[Application]:
    """
    Free-text style search across company, role, and notes.

    Parameters:
        query (str): Substring to match (case-insensitive).

    Returns:
        List[Application]: Matching applications ordered by date and id.
    """
    # Normalize once so we can do a case-insensitive LIKE.
    pattern = f"%{query.lower()}%"

    sql = """
        SELECT *
        FROM applications
        WHERE LOWER(company) LIKE ?
           OR LOWER(role) LIKE ?
           OR LOWER(COALESCE(notes, '')) LIKE ?
        ORDER BY date_applied DESC, id DESC
    """

    cur = conn.cursor()
    cur.execute(sql, (pattern, pattern, pattern))
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


def export_applications_to_csv(
    conn: sqlite3.Connection,
    filepath: str,
    active_only: bool = False,
) -> int:
    """
    Export applications to a CSV file.

    Parameters:
        conn (sqlite3.Connection): Open database connection.
        filepath (str): Destination CSV path.
        active_only (bool): If True, exclude Rejected/Ghosted/Withdrawn.

    Returns:
        int: Number of rows exported.
    """
    sql = "SELECT * FROM applications"
    params: Tuple = ()

    if active_only:
        sql += " WHERE status NOT IN ('Rejected', 'Ghosted', 'Withdrawn')"

    sql += " ORDER BY date_applied DESC, id DESC"

    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()

    fieldnames = [
        "id",
        "company",
        "role",
        "job_link",
        "location",
        "date_applied",
        "source",
        "status",
        "last_action",
        "priority",
        "notes",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row[name] for name in fieldnames})

    return len(rows)

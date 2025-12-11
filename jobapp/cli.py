# jobapp/cli.py
"""
Command-line interface for the job application tracker.

This module:
  - Defines the CLI arguments and subcommands
  - Opens the database connection
  - Delegates to the database layer for actual work
  - Handles human-readable printing of results
"""

import argparse
from pathlib import Path
from typing import List

from .db import (
    DEFAULT_DB_PATH,
    add_application,
    export_applications_to_csv,
    followups,
    get_connection,
    init_db,
    list_applications,
    run_init,
    search_applications,
    stats_by_status,
    update_status,
)
from .models import Application


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


def parse_args() -> argparse.Namespace:
    """
    Define all CLI arguments and subcommands.

    Subcommands:
        add            Add a new application.
        list           List applications (with filters).
        stats          Show summary statistics grouped by status.
        followups      Identify stale applications needing follow-up.
        update-status  Update an application's status and optional last_action.
        update         Update fields of an application by ID or company name.
    """
    parser = argparse.ArgumentParser(
        prog="jobapp",
        description="Job application tracker backed by SQLite.",
    )

    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Path to SQLite DB file (default: {DEFAULT_DB_PATH}).",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    subparsers.add_parser(
        "init",
        help="Initialize the job application database at the selected path.",
    )

    # search
    p_search = subparsers.add_parser(
        "search",
        help="Search applications by substring in company, role, or notes.",
    )
    p_search.add_argument(
        "query",
        help="Search string (case-insensitive).",
    )

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

    # export
    p_export = subparsers.add_parser(
        "export",
        help="Export applications to a CSV file.",
    )

    p_export.add_argument(
        "filepath",
        help="Destination CSV file path.",
    )

    p_export.add_argument(
        "--active-only",
        action="store_true",
        help="Only export non-rejected / non-ghosted / non-withdrawn applications.",
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
        help="Update status of an application by ID or company name.",
    )
    p_update.add_argument(
        "target",
        help="Application ID (integer) OR substring of the company name.",
    )
    p_update.add_argument("status", help="New pipeline status.")
    p_update.add_argument(
        "--last-action",
        help="Explanation of the update (e.g., 'Scheduled phone screen').",
    )

    # update (general field editing)
    p_update_app = subparsers.add_parser(
        "update",
        help="Update one or more fields of an application by ID or company name.",
    )
    p_update_app.add_argument(
        "target",
        help="Application ID (integer) OR substring of the company name.",
    )
    p_update_app.add_argument("--company")
    p_update_app.add_argument("--role")
    p_update_app.add_argument("--link", dest="job_link")
    p_update_app.add_argument("--location")
    p_update_app.add_argument("--date-applied")
    p_update_app.add_argument("--source")
    p_update_app.add_argument("--status")
    p_update_app.add_argument("--priority", type=int)
    p_update_app.add_argument("--notes")

    return parser.parse_args()


def main() -> None:
    """
    Dispatch the appropriate command handler based on CLI arguments.
    This is the central orchestration function of the CLI.
    """
    args = parse_args()

    # Special-case: `init` manages its own connection and exits early.
    if args.command == "init":
        run_init(args.db_path)
        return

    conn = get_connection(args.db_path)
    init_db(conn)

    try:
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

        elif args.command == "search":
            apps = search_applications(conn, query=args.query)
            print_applications(apps)

        elif args.command == "export":
            count = export_applications_to_csv(
                conn=conn,
                filepath=args.filepath,
                active_only=args.active_only,
            )
            print(f"Exported {count} applications to {args.filepath}")

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
            # Try to interpret target as an integer ID first.
            try:
                app_id = int(args.target)
                # Normal ID-based update
                update_status(
                    conn=conn,
                    app_id=app_id,
                    status=args.status,
                    last_action=args.last_action,
                )
            except ValueError:
                # Not an integer: treat as company-name query
                from jobapp.db import (
                    find_applications_by_company,  # top-level import is fine too
                )

                matches = find_applications_by_company(conn, args.target)

                if not matches:
                    print(f'No applications match company query "{args.target}".')
                elif len(matches) > 1:
                    print(f'Multiple applications match "{args.target}":')
                    for app in matches:
                        print(
                            f"[{app.id}] {app.company} — {app.role} "
                            f"(applied {app.date_applied})"
                        )
                    print("Please refine your query or use an explicit ID.")
                else:
                    app = matches[0]
                    print(
                        f"Updating application [{app.id}] {app.company} — {app.role} "
                        f'to status "{args.status}".'
                    )
                    update_status(
                        conn=conn,
                        app_id=app.id,
                        status=args.status,
                        last_action=args.last_action,
                    )
        elif args.command == "update":
            # Determine app ID: try integer first, else resolve by company name.
            try:
                app_id = int(args.target)
                cur = conn.cursor()
                cur.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
                row = cur.fetchone()
                if row is None:
                    print(f"No application with ID {app_id} exists.")
                    return
            except ValueError:
                from jobapp.db import find_applications_by_company

                matches = find_applications_by_company(conn, args.target)

                if not matches:
                    print(f'No applications match company query "{args.target}".')
                    return
                if len(matches) > 1:
                    print(f'Multiple applications match "{args.target}":')
                    for app in matches:
                        print(
                            f"[{app.id}] {app.company} — {app.role} "
                            f"(applied {app.date_applied})"
                        )
                    print("Please refine your query or use an explicit ID.")
                    return

                app = matches[0]
                app_id = app.id
                row = {
                    "id": app.id,
                    "company": app.company,
                    "role": app.role,
                }

            # Collect fields to update from provided arguments
            fields = {}
            if getattr(args, "company", None) is not None:
                fields["company"] = args.company
            if getattr(args, "role", None) is not None:
                fields["role"] = args.role
            if getattr(args, "job_link", None) is not None:
                fields["job_link"] = args.job_link
            if getattr(args, "location", None) is not None:
                fields["location"] = args.location
            if getattr(args, "date_applied", None) is not None:
                fields["date_applied"] = args.date_applied
            if getattr(args, "source", None) is not None:
                fields["source"] = args.source
            if getattr(args, "status", None) is not None:
                fields["status"] = args.status
            if getattr(args, "priority", None) is not None:
                fields["priority"] = args.priority
            if getattr(args, "notes", None) is not None:
                fields["notes"] = args.notes

            if not fields:
                print("No fields specified to update; nothing to do.")
                return

            # Print context before applying update
            print(
                f"Updating application [{row['id']}] {row['company']} — {row['role']} "
                f"with updated fields: {', '.join(fields.keys())}."
            )

            # Apply the partial update with a dynamic UPDATE statement
            assignments = ", ".join(f"{col} = ?" for col in fields.keys())
            params = list(fields.values()) + [app_id]
            cur = conn.cursor()
            cur.execute(
                f"UPDATE applications SET {assignments} WHERE id = ?",
                params,
            )
            conn.commit()
    finally:
        conn.close()

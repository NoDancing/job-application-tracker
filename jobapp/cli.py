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
    get_connection,
    init_db,
    add_application,
    list_applications,
    stats_by_status,
    followups,
    update_status,
    run_init,
    search_applications,
    export_applications_to_csv,
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

    Returns:
        argparse.Namespace: Parsed CLI arguments.
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
        help ="Export applications to a CSV file.",
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
        help="Update status of an application by ID.",
    )
    p_update.add_argument("id", type=int, help="Application ID.")
    p_update.add_argument("status", help="New pipeline status.")
    p_update.add_argument(
        "--last-action",
        help="Explanation of the update (e.g., 'Scheduled phone screen').",
    )

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
            update_status(
                conn=conn,
                app_id=args.id,
                status=args.status,
                last_action=args.last_action,
            )
    finally:
        conn.close()
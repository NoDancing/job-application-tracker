import sys
from pathlib import Path

from jobapp import cli
from jobapp.db import add_application, get_connection, init_db, list_applications


def test_cli_update_status_by_company_name(tmp_path: Path, capsys) -> None:
    """
    When update-status is called with a non-integer target, the CLI should
    treat it as a company substring, resolve a unique match, and update that
    application's status.

    We avoid relying on argparse/sys.argv by monkeypatching parse_args()
    to return a fake Namespace that represents the desired CLI invocation.
    """
    db_path = tmp_path / "cli_update_name.db"

    # Set up a temp DB with one Flatiron application
    conn = get_connection(db_path)
    init_db(conn)
    add_application(
        conn=conn,
        company="Flatiron Institute",
        role="Database & Testing Intern",
        job_link=None,
        location="New York, NY",
        date_applied="2025-01-01",
        source="Company Site",
        status="Applied",
        priority=1,
        notes=None,
    )
    conn.close()

    # Simulate CLI call using sys.argv
    sys.argv = [
        "jobapp",
        "--db-path",
        str(db_path),
        "update-status",
        "Flatiron",
        "Rejected",
        "--last-action",
        "2025-01-02 — Rejection email",
    ]

    # Run the CLI entry point
    cli.main()
    captured = capsys.readouterr()

    # Optional: check that some informative text was printed
    assert "Flatiron Institute" in captured.out
    assert "Rejected" in captured.out

    # Verify the row in the DB was actually updated
    conn = get_connection(db_path)
    try:
        apps = list_applications(
            conn, company="Flatiron", status=None, active_only=False
        )
        assert len(apps) == 1
        app = apps[0]
        assert app.company == "Flatiron Institute"
        assert app.status == "Rejected"
        assert app.last_action == "2025-01-02 — Rejection email"
    finally:
        conn.close()


def test_cli_update_by_id_edits_selected_fields(tmp_path: Path, capsys) -> None:
    """`jobapp update <id> ...` should update only the specified fields for that ID.
    Other fields must remain unchanged.
    """
    db_path = tmp_path / "cli_update_by_id.db"

    # Seed a single application
    conn = get_connection(db_path)
    init_db(conn)
    app_id = add_application(
        conn=conn,
        company="Cisco",
        role="Software Engineer Intern",
        job_link="https://example.com/cisco",
        location="Hillsboro, OR",
        date_applied="2025-12-07",
        source="LinkedIn",
        status="Applied",
        priority=3,
        notes="Initial notes",
    )
    conn.close()

    # CLI: jobapp --db-path <db> update <id> --role ... --priority ... --notes ...
    sys.argv = [
        "jobapp",
        "--db-path",
        str(db_path),
        "update",
        str(app_id),
        "--role",
        "Software Engineer Intern (Full Stack)",
        "--priority",
        "1",
        "--notes",
        "Updated after recruiter call",
    ]
    cli.main()
    captured = capsys.readouterr()
    # Optional: ensure something was printed
    assert "Updating application" in captured.out

    # Verify DB contents
    conn = get_connection(db_path)
    try:
        apps = list_applications(conn, company="Cisco", status=None, active_only=False)
        assert len(apps) == 1
        app = apps[0]
        # Unchanged fields
        assert app.company == "Cisco"
        assert app.location == "Hillsboro, OR"
        assert app.status == "Applied"
        # Updated fields
        assert app.role == "Software Engineer Intern (Full Stack)"
        assert app.priority == 1
        assert app.notes == "Updated after recruiter call"
    finally:
        conn.close()


def test_cli_update_by_company_name_edits_unique_match(tmp_path: Path, capsys) -> None:
    """`jobapp update <company_substring> ...` should resolve a unique company
    match and update that record when there is exactly one matching application.
    """
    db_path = tmp_path / "cli_update_by_name.db"

    # Seed one Flatiron application
    conn = get_connection(db_path)
    init_db(conn)
    add_application(
        conn=conn,
        company="Flatiron Institute",
        role="Database & Testing Intern",
        job_link=None,
        location="New York, NY",
        date_applied="2025-01-01",
        source="Company Site",
        status="Applied",
        priority=2,
        notes=None,
    )
    conn.close()

    # CLI: jobapp update Flatiron --location "Remote" --priority 1
    sys.argv = [
        "jobapp",
        "--db-path",
        str(db_path),
        "update",
        "Flatiron",
        "--location",
        "Remote",
        "--priority",
        "1",
    ]
    cli.main()
    captured = capsys.readouterr()
    assert "Updating application" in captured.out
    assert "Flatiron Institute" in captured.out

    # Verify DB contents
    conn = get_connection(db_path)
    try:
        apps = list_applications(
            conn, company="Flatiron", status=None, active_only=False
        )
        assert len(apps) == 1
        app = apps[0]
        assert app.company == "Flatiron Institute"
        assert app.location == "Remote"
        assert app.priority == 1
    finally:
        conn.close()


def test_cli_update_ambiguous_company_refuses_to_guess(tmp_path: Path, capsys) -> None:
    """If `jobapp update <company_substring> ...` matches multiple applications,
    the CLI should list the matches and refuse to update anything.
    """
    db_path = tmp_path / "cli_update_ambiguous.db"

    conn = get_connection(db_path)
    init_db(conn)
    # Two Meta roles -> ambiguous
    add_application(
        conn=conn,
        company="Meta",
        role="SWE Intern",
        job_link=None,
        location=None,
        date_applied="2025-01-01",
        source="LinkedIn",
        status="Applied",
        priority=2,
        notes=None,
    )
    add_application(
        conn=conn,
        company="Meta",
        role="ML Intern",
        job_link=None,
        location=None,
        date_applied="2025-01-02",
        source="Company Site",
        status="Applied",
        priority=2,
        notes=None,
    )
    conn.close()

    # CLI: jobapp update Meta --priority 1
    sys.argv = [
        "jobapp",
        "--db-path",
        str(db_path),
        "update",
        "Meta",
        "--priority",
        "1",
    ]
    cli.main()
    captured = capsys.readouterr()

    # Should warn and not perform an update
    assert 'Multiple applications match "Meta"' in captured.out
    assert "Please refine your query" in captured.out

    # Verify that neither record was updated
    conn = get_connection(db_path)
    try:
        apps = list_applications(conn, company="Meta", status=None, active_only=False)
        assert len(apps) == 2
        # Both priorities should remain 2
        assert {app.priority for app in apps} == {2}
    finally:
        conn.close()


def test_cli_remove_by_id_deletes_row(tmp_path: Path, capsys) -> None:
    """`jobapp remove <id>` should delete the selected application."""
    db_path = tmp_path / "cli_remove_by_id.db"

    # Seed a single application
    conn = get_connection(db_path)
    init_db(conn)
    app_id = add_application(
        conn=conn,
        company="DeleteMeCo",
        role="Intern",
        job_link=None,
        location=None,
        date_applied="2025-01-10",
        source=None,
        status="Applied",
        priority=2,
        notes=None,
    )
    conn.close()

    # CLI: jobapp --db-path <db> remove <id>
    sys.argv = [
        "jobapp",
        "--db-path",
        str(db_path),
        "remove",
        str(app_id),
    ]
    cli.main()
    captured = capsys.readouterr()

    # Should print an informative message
    assert f"Removed application {app_id}." in captured.out

    # Verify DB contents: row is gone
    conn = get_connection(db_path)
    try:
        apps = list_applications(conn, company=None, status=None, active_only=False)
        assert len(apps) == 0
    finally:
        conn.close()


def test_cli_remove_nonexistent_id_prints_message(tmp_path: Path, capsys) -> None:
    """`jobapp remove <id>` should not crash for missing IDs and should print a message."""
    db_path = tmp_path / "cli_remove_missing.db"

    # Empty DB
    conn = get_connection(db_path)
    init_db(conn)
    conn.close()

    # CLI: jobapp --db-path <db> remove 999
    sys.argv = [
        "jobapp",
        "--db-path",
        str(db_path),
        "remove",
        "999",
    ]
    cli.main()
    captured = capsys.readouterr()

    assert "No application with ID 999 exists." in captured.out

    # DB should remain empty
    conn = get_connection(db_path)
    try:
        apps = list_applications(conn, company=None, status=None, active_only=False)
        assert len(apps) == 0
    finally:
        conn.close()

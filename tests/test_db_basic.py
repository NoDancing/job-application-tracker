# tests/test_db_basic.py
from pathlib import Path
import csv

from jobapp.db import (
    add_application,
    list_applications,
    followups,
    update_status,
    export_applications_to_csv,
)
from jobapp.models import Application


def test_add_and_list_basic(conn) -> None:
    """
    Adding a single application should make it appear in an unfiltered list.
    """
    app_id = add_application(
        conn=conn,
        company="TestCo",
        role="Software Engineer Intern",
        job_link=None,
        location="Remote",
        date_applied="2025-01-01",
        source="Unit Test",
        status="Applied",
        priority=2,
        notes="Initial test application",
    )

    apps = list_applications(conn, company=None, status=None, active_only=False)
    assert len(apps) == 1

    app = apps[0]
    assert isinstance(app, Application)
    assert app.id == app_id
    assert app.company == "TestCo"
    assert app.role == "Software Engineer Intern"
    assert app.status == "Applied"
    assert app.priority == 2


def test_list_filters_active_only(conn) -> None:
    """
    active_only=True should exclude Rejected/Ghosted/Withdrawn applications.
    """
    # Active application
    add_application(
        conn=conn,
        company="ActiveCo",
        role="Backend Intern",
        job_link=None,
        location=None,
        date_applied="2025-01-02",
        source=None,
        status="Applied",
        priority=1,
        notes=None,
    )

    # Rejected application
    add_application(
        conn=conn,
        company="RejectCo",
        role="Backend Intern",
        job_link=None,
        location=None,
        date_applied="2025-01-03",
        source=None,
        status="Rejected",
        priority=3,
        notes=None,
    )

    all_apps = list_applications(conn, company=None, status=None, active_only=False)
    active_only_apps = list_applications(conn, company=None, status=None, active_only=True)

    assert len(all_apps) == 2
    # Only the non-rejected one should remain when active_only=True
    assert len(active_only_apps) == 1
    assert active_only_apps[0].company == "ActiveCo"


def test_followups_returns_only_old_early_stage(conn) -> None:
    """
    followups() should return only early-stage applications older than N days.
    """
    # Old Applied application (should be flagged)
    add_application(
        conn=conn,
        company="OldCo",
        role="Intern",
        job_link=None,
        location=None,
        date_applied="2000-01-01",  # very old
        source=None,
        status="Applied",
        priority=2,
        notes=None,
    )

    # New Applied application (should NOT be flagged)
    add_application(
        conn=conn,
        company="NewCo",
        role="Intern",
        job_link=None,
        location=None,
        date_applied="2099-01-01",  # future-ish, definitely not old
        source=None,
        status="Applied",
        priority=2,
        notes=None,
    )

    # Old Rejected application (should NOT be flagged; not early status)
    add_application(
        conn=conn,
        company="OldRejectedCo",
        role="Intern",
        job_link=None,
        location=None,
        date_applied="2000-01-01",
        source=None,
        status="Rejected",
        priority=2,
        notes=None,
    )

    candidates = followups(conn, days=7)

    # Only the old, early-stage application should be present
    assert len(candidates) == 1
    assert candidates[0].company == "OldCo"


def test_update_status_changes_row(conn) -> None:
    """
    update_status() should change the status and last_action of a specific row.
    """
    app_id = add_application(
        conn=conn,
        company="StatusCo",
        role="Intern",
        job_link=None,
        location=None,
        date_applied="2025-01-04",
        source=None,
        status="Applied",
        priority=2,
        notes=None,
    )

    update_status(
        conn=conn,
        app_id=app_id,
        status="OA",
        last_action="Received online assessment link",
    )

    # Verify directly via a query
    cur = conn.cursor()
    cur.execute("SELECT status, last_action FROM applications WHERE id = ?", (app_id,))
    row = cur.fetchone()
    assert row is not None
    assert row["status"] == "OA"
    assert row["last_action"] == "Received online assessment link"


def test_export_applications_to_csv(tmp_path: Path, conn) -> None:
    """
    export_applications_to_csv() should write a CSV with a header and all rows.
    """
    add_application(
        conn=conn,
        company="ExportCo1",
        role="Intern",
        job_link=None,
        location=None,
        date_applied="2025-01-05",
        source=None,
        status="Applied",
        priority=2,
        notes=None,
    )

    add_application(
        conn=conn,
        company="ExportCo2",
        role="Intern",
        job_link=None,
        location=None,
        date_applied="2025-01-06",
        source=None,
        status="Applied",
        priority=2,
        notes=None,
    )

    csv_path = tmp_path / "export.csv"
    count = export_applications_to_csv(
        conn=conn,
        filepath=str(csv_path),
        active_only=False,
    )

    assert count == 2
    assert csv_path.exists()

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    companies = {row["company"] for row in rows}
    assert companies == {"ExportCo1", "ExportCo2"}
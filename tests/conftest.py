# tests/conftest.py
import sqlite3
import sys
from pathlib import Path
from typing import Iterator

import pytest

# Ensure the project root (the directory containing the `jobapp` package)
# is on sys.path so `import jobapp` works when running tests.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from jobapp.db import get_connection, init_db  # noqa: E402


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """
    Path to a temporary SQLite database file for a single test.
    """
    return tmp_path / "test_applications.db"


@pytest.fixture
def conn(db_path: Path) -> Iterator[sqlite3.Connection]:
    """
    Open a SQLite connection to a fresh test database and initialize schema.

    Yields:
        sqlite3.Connection: Initialized connection ready for use in tests.
    """
    connection = get_connection(db_path)
    init_db(connection)
    try:
        yield connection
    finally:
        connection.close()

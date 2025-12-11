# jobapp/models.py
"""
Data models for the job application tracker.

Currently this module defines the Application dataclass, which mirrors the
schema of the `applications` table in the SQLite database.
"""

from dataclasses import dataclass
from typing import Optional


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
    date_applied: str  # ISO8601 date string (YYYY-MM-DD)
    source: Optional[str]
    status: str
    last_action: Optional[str]
    priority: Optional[int]
    notes: Optional[str]

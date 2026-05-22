"""
database.py
-----------
SQLite persistence layer for loan applications.
Creates and manages the `applications` table.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "loan_records.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # allows dict-like access
    return conn


def init_db() -> None:
    """Create the applications table if it doesn't exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                applicant_name  TEXT    NOT NULL,
                income          REAL    NOT NULL,
                credit_score    INTEGER NOT NULL,
                loan_amount     REAL    NOT NULL,
                duration_months INTEGER NOT NULL,
                purpose         TEXT,
                decision        TEXT    NOT NULL,
                probability     REAL    NOT NULL,
                monthly_est     REAL    NOT NULL,
                dti_ratio       REAL    NOT NULL,
                reason          TEXT,
                applied_at      TEXT    NOT NULL
            )
        """)
        conn.commit()


def save_application(applicant_name: str,
                     income: float,
                     credit_score: int,
                     loan_amount: float,
                     duration_months: int,
                     purpose: str,
                     result: dict) -> int:
    """Insert a new application record. Returns the new row ID."""
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO applications
                (applicant_name, income, credit_score, loan_amount,
                 duration_months, purpose, decision, probability,
                 monthly_est, dti_ratio, reason, applied_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            applicant_name,
            income,
            credit_score,
            loan_amount,
            duration_months,
            purpose,
            result["decision"],
            result["probability"],
            result["monthly_est"],
            result["dti_ratio"],
            result["reason"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ))
        conn.commit()
        return cursor.lastrowid


def fetch_all_applications() -> list[dict]:
    """Return all applications ordered by most recent first."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM applications ORDER BY id DESC
        """).fetchall()
    return [dict(row) for row in rows]


def fetch_stats() -> dict:
    """Return aggregate statistics across all applications."""
    with get_connection() as conn:
        row = conn.execute("""
            SELECT
                COUNT(*)                                    AS total,
                SUM(CASE WHEN decision='APPROVED' THEN 1 ELSE 0 END) AS approved,
                SUM(CASE WHEN decision='REJECTED' THEN 1 ELSE 0 END) AS rejected,
                ROUND(AVG(loan_amount), 2)                  AS avg_loan,
                ROUND(AVG(income), 2)                       AS avg_income,
                ROUND(AVG(credit_score), 1)                 AS avg_credit,
                ROUND(AVG(probability), 4)                  AS avg_probability
            FROM applications
        """).fetchone()
    return dict(row) if row else {}


def clear_all_applications() -> None:
    """Delete all records (for testing/reset)."""
    with get_connection() as conn:
        conn.execute("DELETE FROM applications")
        conn.commit()
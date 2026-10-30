"""SQLite persistence layer (CRUD)."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime

import config


class DuplicateEmailError(Exception):
    """Raised when an email address already exists in the database."""


@contextmanager
def get_connection():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS patients (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name    TEXT NOT NULL,
                dob          TEXT NOT NULL,
                email        TEXT NOT NULL UNIQUE COLLATE NOCASE,
                glucose      REAL NOT NULL,
                haemoglobin  REAL NOT NULL,
                cholesterol  REAL NOT NULL,
                remarks      TEXT,
                created_at   TEXT NOT NULL,
                updated_at   TEXT NOT NULL
            )
            """
        )


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_patient(data: dict, remarks: str) -> int:
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """INSERT INTO patients
                   (full_name, dob, email, glucose, haemoglobin, cholesterol, remarks, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (data["full_name"], data["dob"], data["email"], data["glucose"],
                 data["haemoglobin"], data["cholesterol"], remarks, _now(), _now()),
            )
            return cur.lastrowid
    except sqlite3.IntegrityError:
        raise DuplicateEmailError(f"A record with email '{data['email']}' already exists.") from None


def get_all_patients() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM patients ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def get_patient(patient_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    return dict(row) if row else None


def update_patient(patient_id: int, data: dict, remarks: str) -> None:
    try:
        with get_connection() as conn:
            conn.execute(
                """UPDATE patients
                   SET full_name=?, dob=?, email=?, glucose=?, haemoglobin=?, cholesterol=?,
                       remarks=?, updated_at=?
                   WHERE id=?""",
                (data["full_name"], data["dob"], data["email"], data["glucose"],
                 data["haemoglobin"], data["cholesterol"], remarks, _now(), patient_id),
            )
    except sqlite3.IntegrityError:
        raise DuplicateEmailError(f"A record with email '{data['email']}' already exists.") from None


def delete_patient(patient_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        return cur.rowcount > 0

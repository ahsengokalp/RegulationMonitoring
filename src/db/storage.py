from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

from src.core.models import GazetteItem

DB_DIR = Path.cwd() / "data"
DB_PATH = DB_DIR / "items.db"


def _connect() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _connect()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date    TEXT    NOT NULL,
            title       TEXT    NOT NULL,
            url         TEXT    NOT NULL,
            section     TEXT    DEFAULT '',
            subsection  TEXT    DEFAULT '',
            is_pdf      INTEGER DEFAULT 0,
            dept_muhasebe  INTEGER DEFAULT 0,
            dept_isg       INTEGER DEFAULT 0,
            dept_ik        INTEGER DEFAULT 0,
            dept_lojistik  INTEGER DEFAULT 0,
            inserted_at TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS run_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            check_time  TEXT    NOT NULL,
            run_date    TEXT    NOT NULL,
            items_found INTEGER DEFAULT 0
        );
        """
    )
    # Migration: add columns that may be missing in older databases
    for col in ("is_pdf", "dept_muhasebe", "dept_isg", "dept_ik", "dept_lojistik"):
        try:
            conn.execute(f"ALTER TABLE items ADD COLUMN {col} INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # column already exists
    try:
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_items_date_url ON items(run_date, url)"
        )
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()


def save_items(
    run_day: date,
    items: Iterable[GazetteItem],
    dept_map: Optional[Dict[str, Set[str]]] = None,
) -> None:
    """Persist gazette items with optional department hit flags.

    ``dept_map`` maps item URL → set of department names that matched.
    """
    init_db()
    conn = _connect()
    now = datetime.utcnow().isoformat()
    dept_map = dept_map or {}

    for it in items:
        depts = dept_map.get(it.url, set())
        is_pdf = 1 if it.url.lower().endswith(".pdf") else 0
        conn.execute(
            """
            INSERT INTO items
                (run_date, title, url, section, subsection, is_pdf,
                 dept_muhasebe, dept_isg, dept_ik, dept_lojistik, inserted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_date, url) DO UPDATE SET
                dept_muhasebe = excluded.dept_muhasebe,
                dept_isg      = excluded.dept_isg,
                dept_ik       = excluded.dept_ik,
                dept_lojistik = excluded.dept_lojistik,
                inserted_at   = excluded.inserted_at
            """,
            (
                run_day.isoformat(),
                it.title,
                it.url,
                it.section or "",
                it.subsection or "",
                is_pdf,
                1 if "muhasebe" in depts else 0,
                1 if "isg" in depts else 0,
                1 if "ik" in depts else 0,
                1 if "lojistik" in depts else 0,
                now,
            ),
        )
    conn.commit()
    conn.close()


def save_run_log(run_day: date, items_found: int) -> None:
    init_db()
    conn = _connect()
    conn.execute(
        "INSERT INTO run_log (check_time, run_date, items_found) VALUES (?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), run_day.isoformat(), items_found),
    )
    conn.commit()
    conn.close()


def get_items(limit: int = 100) -> List[dict]:
    init_db()
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM items ORDER BY run_date DESC, id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_last_check_time() -> Optional[str]:
    init_db()
    conn = _connect()
    row = conn.execute(
        "SELECT check_time FROM run_log ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return row["check_time"] if row else None


def get_department_counts(items: List[dict]) -> dict:
    counts = {"muhasebe": 0, "isg": 0, "ik": 0, "lojistik": 0}
    for it in items:
        if it.get("dept_muhasebe"):
            counts["muhasebe"] += 1
        if it.get("dept_isg"):
            counts["isg"] += 1
        if it.get("dept_ik"):
            counts["ik"] += 1
        if it.get("dept_lojistik"):
            counts["lojistik"] += 1
    return counts

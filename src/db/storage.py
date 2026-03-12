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
            detail_text TEXT    DEFAULT '',
            dept_muhasebe  INTEGER DEFAULT 0,
            dept_isg       INTEGER DEFAULT 0,
            dept_ik        INTEGER DEFAULT 0,
            dept_lojistik  INTEGER DEFAULT 0,
            dept_it_siber  INTEGER DEFAULT 0,
            dept_kvkk      INTEGER DEFAULT 0,
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
    for col in ("is_pdf", "dept_muhasebe", "dept_isg", "dept_ik", "dept_lojistik", "dept_it_siber", "dept_kvkk"):
        try:
            conn.execute(f"ALTER TABLE items ADD COLUMN {col} INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # column already exists
    try:
        conn.execute("ALTER TABLE items ADD COLUMN detail_text TEXT DEFAULT ''")
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
    text_map: Optional[Dict[str, str]] = None,
) -> None:
    """Persist gazette items with optional department hit flags.

    ``dept_map`` maps item URL → set of department names that matched.
    ``text_map`` maps item URL → fetched detail text content.
    """
    init_db()
    conn = _connect()
    now = datetime.utcnow().isoformat()
    dept_map = dept_map or {}
    text_map = text_map or {}

    for it in items:
        depts = dept_map.get(it.url, set())
        detail = text_map.get(it.url, "")
        is_pdf = 1 if (it.url.lower().endswith(".pdf") or "--- EK PDF ---" in detail) else 0
        conn.execute(
            """
            INSERT INTO items
                (run_date, title, url, section, subsection, is_pdf,
                 detail_text,
                 dept_muhasebe, dept_isg, dept_ik, dept_lojistik,
                 dept_it_siber, dept_kvkk, inserted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_date, url) DO UPDATE SET
                is_pdf        = MAX(items.is_pdf, excluded.is_pdf),
                detail_text   = CASE WHEN length(excluded.detail_text) > length(COALESCE(items.detail_text, '')) THEN excluded.detail_text ELSE items.detail_text END,
                dept_muhasebe = excluded.dept_muhasebe,
                dept_isg      = excluded.dept_isg,
                dept_ik       = excluded.dept_ik,
                dept_lojistik = excluded.dept_lojistik,
                dept_it_siber = excluded.dept_it_siber,
                dept_kvkk     = excluded.dept_kvkk,
                inserted_at   = excluded.inserted_at
            """,
            (
                run_day.isoformat(),
                it.title,
                it.url,
                it.section or "",
                it.subsection or "",
                is_pdf,
                detail,
                1 if "muhasebe" in depts else 0,
                1 if "isg" in depts else 0,
                1 if "ik" in depts else 0,
                1 if "lojistik" in depts else 0,
                1 if "it_siber" in depts else 0,
                1 if "kvkk" in depts else 0,
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


def get_items(limit: int = 100, search: Optional[str] = None, dept: Optional[str] = None) -> List[dict]:
    init_db()
    conn = _connect()

    valid_depts = {"muhasebe", "isg", "ik", "lojistik", "it_siber", "kvkk"}
    conditions: List[str] = []
    params: list = []

    if search:
        like = f"%{search}%"
        conditions.append("(title LIKE ? OR section LIKE ? OR subsection LIKE ? OR detail_text LIKE ?)")
        params.extend([like, like, like, like])

    if dept and dept in valid_depts:
        conditions.append(f"dept_{dept} = 1")

    where = ""
    if conditions:
        where = "WHERE " + " AND ".join(conditions)

    query = f"SELECT * FROM items {where} ORDER BY run_date DESC, id DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
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
    counts = {"muhasebe": 0, "isg": 0, "ik": 0, "lojistik": 0, "it_siber": 0, "kvkk": 0}
    for it in items:
        if it.get("dept_muhasebe"):
            counts["muhasebe"] += 1
        if it.get("dept_isg"):
            counts["isg"] += 1
        if it.get("dept_ik"):
            counts["ik"] += 1
        if it.get("dept_lojistik"):
            counts["lojistik"] += 1
        if it.get("dept_it_siber"):
            counts["it_siber"] += 1
        if it.get("dept_kvkk"):
            counts["kvkk"] += 1
    return counts

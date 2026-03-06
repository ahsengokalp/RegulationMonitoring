from __future__ import annotations

import sqlite3
from dataclasses import asdict
from datetime import datetime, date
from pathlib import Path
from typing import Iterable, List

from src.core.models import GazetteItem


DB_PATH = Path("/app/data/items.db")


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date TEXT,
            title TEXT,
            url TEXT,
            section TEXT,
            subsection TEXT,
            inserted_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_items(run_day: date, items: Iterable[GazetteItem]) -> None:
    init_db()
    conn = _connect()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    for it in items:
        cur.execute(
            "INSERT INTO items (run_date, title, url, section, subsection, inserted_at) VALUES (?, ?, ?, ?, ?, ?)",
            (run_day.isoformat(), it.title, it.url, it.section or "", it.subsection or "", now),
        )
    conn.commit()
    conn.close()


def get_latest_items(limit: int = 100) -> List[dict]:
    init_db()
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT run_date, title, url, section, subsection, inserted_at FROM items ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

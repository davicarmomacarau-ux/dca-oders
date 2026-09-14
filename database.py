import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
SQLITE_DB = BASE_DIR / os.getenv("SQLITE_DB", "dca_orders.sqlite3")
SCHEMA_SQL = BASE_DIR / "schema.sql"


def _ensure_sqlite_schema():
    if not SQLITE_DB.exists():
        conn = sqlite3.connect(SQLITE_DB)
        try:
            conn.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))
            conn.commit()
        finally:
            conn.close()

    conn = sqlite3.connect(SQLITE_DB)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                restaurant_id INTEGER NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
                title VARCHAR(180) NOT NULL,
                channel VARCHAR(30) NOT NULL DEFAULT 'whatsapp',
                objective VARCHAR(40) NOT NULL DEFAULT 'pedido',
                audience VARCHAR(150),
                message TEXT,
                budget NUMERIC(10,2) NOT NULL DEFAULT 0,
                expected_revenue NUMERIC(10,2) NOT NULL DEFAULT 0,
                status VARCHAR(30) NOT NULL DEFAULT 'active',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                restaurant_id INTEGER NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
                title VARCHAR(180) NOT NULL,
                message TEXT,
                audience VARCHAR(150),
                discount NUMERIC(10,2) NOT NULL DEFAULT 0,
                channel VARCHAR(30) NOT NULL DEFAULT 'whatsapp',
                whatsapp_url TEXT,
                forecast_score NUMERIC(10,2) NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def get_db():
    _ensure_sqlite_schema()
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_one(query, params=()):
    conn = get_db()
    try:
        row = conn.execute(query, params).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def fetch_all(query, params=()):
    conn = get_db()
    try:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def execute(query, params=()):
    conn = get_db()
    try:
        cur = conn.execute(query, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

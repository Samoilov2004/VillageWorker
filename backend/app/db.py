from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "database" / "job_ads.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_tables() -> None:
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_jobs (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                title         TEXT NOT NULL,
                description   TEXT,
                company       TEXT,
                city          TEXT,
                salary_min    INTEGER,
                salary_max    INTEGER,
                experience_min INTEGER DEFAULT 0,
                experience_max INTEGER DEFAULT 0,
                label         TEXT,
                mod_status    TEXT DEFAULT 'ok',
                risk_score    REAL DEFAULT 0,
                mod_reasons   TEXT DEFAULT '',
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id     INTEGER,
                job_title  TEXT,
                user_name  TEXT,
                phone      TEXT,
                message    TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()
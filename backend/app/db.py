from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "database" / "job_ads.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
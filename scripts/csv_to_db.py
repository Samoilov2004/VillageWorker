import os
import csv
import json
import time
import sqlite3
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "id",
    "title",
    "salary",
    "experience",
    "description",
    "key_skills",
    "company",
    "type",
    "address_info",
    "meta",
    "label",
]


def detect_delimiter(file_path: str, sample_size: int = 65536) -> str:
    """Автоопределение разделителя CSV."""
    with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(sample_size)

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except Exception:
        return ","


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Чистим имена колонок и убираем мусорные Unnamed."""
    df.columns = [str(c).strip().lstrip(",") for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains(r"^Unnamed", regex=True)]
    df = df.loc[:, df.columns != ""]
    return df


def empty_to_none(value):
    if value is None:
        return None
    if pd.isna(value):
        return None
    value = str(value).strip()
    return value if value != "" else None


def safe_int(value):
    value = empty_to_none(value)
    if value is None:
        return None
    try:
        return int(float(value))
    except Exception:
        return None


def safe_float(value):
    value = empty_to_none(value)
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def parse_json_field(value, field_name: str, error_stats: dict):
    """
    Парсим JSON из CSV.
    Возвращаем:
      - нормализованный JSON-строку для хранения в SQLite
      - dict с данными
    """
    value = empty_to_none(value)
    if value is None:
        return None, {}

    try:
        obj = json.loads(value)
        normalized = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        return normalized, obj
    except Exception:
        error_stats[field_name] = error_stats.get(field_name, 0) + 1
        return None, {}


def create_schema(conn: sqlite3.Connection):
    conn.execute("DROP TABLE IF EXISTS jobs")

    conn.execute("""
    CREATE TABLE jobs (
        id INTEGER PRIMARY KEY,
        title TEXT,
        salary TEXT CHECK (salary IS NULL OR json_valid(salary)),
        experience TEXT CHECK (experience IS NULL OR json_valid(experience)),
        description TEXT,
        key_skills TEXT,
        company TEXT,
        type TEXT,
        address_info TEXT CHECK (address_info IS NULL OR json_valid(address_info)),
        meta TEXT CHECK (meta IS NULL OR json_valid(meta)),
        label TEXT,

        salary_min INTEGER,
        salary_max INTEGER,
        salary_currency TEXT,

        experience_min INTEGER,
        experience_max INTEGER,

        country TEXT,
        region TEXT,
        state TEXT,
        city TEXT,
        latitude REAL,
        longitude REAL,
        geo_status TEXT,

        publication_time INTEGER,
        last_edit_time INTEGER,
        total_views INTEGER,
        views_last_week INTEGER
    )
    """)
    conn.commit()


def create_indexes(conn: sqlite3.Connection):
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(type)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_label ON jobs(label)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_city ON jobs(city)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_state ON jobs(state)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_region ON jobs(region)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_salary_min ON jobs(salary_min)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_salary_max ON jobs(salary_max)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_experience_min ON jobs(experience_min)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_publication_time ON jobs(publication_time)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_total_views ON jobs(total_views)",
    ]

    for sql in indexes:
        conn.execute(sql)

    conn.commit()


def create_fts(conn: sqlite3.Connection):
    """
    Полнотекстовый поиск по title/description/company/key_skills/label.
    Если FTS5 недоступен в сборке SQLite — просто пропустим.
    """
    try:
        conn.execute("DROP TABLE IF EXISTS jobs_fts")
        conn.execute("""
        CREATE VIRTUAL TABLE jobs_fts USING fts5(
            title,
            description,
            company,
            key_skills,
            label,
            content='jobs',
            content_rowid='id'
        )
        """)
        conn.execute("""
        INSERT INTO jobs_fts(rowid, title, description, company, key_skills, label)
        SELECT id, title, description, company, key_skills, label
        FROM jobs
        """)
        conn.commit()
        print("✅ Создан FTS5 индекс для полнотекстового поиска")
    except sqlite3.OperationalError as e:
        print(f"⚠️ FTS5 недоступен: {e}")


def prepare_row(row: dict, error_stats: dict):
    salary_json, salary_obj = parse_json_field(row.get("salary"), "salary", error_stats)
    exp_json, exp_obj = parse_json_field(row.get("experience"), "experience", error_stats)
    addr_json, addr_obj = parse_json_field(row.get("address_info"), "address_info", error_stats)
    meta_json, meta_obj = parse_json_field(row.get("meta"), "meta", error_stats)

    return (
        safe_int(row.get("id")),
        empty_to_none(row.get("title")),
        salary_json,
        exp_json,
        empty_to_none(row.get("description")),
        empty_to_none(row.get("key_skills")),
        empty_to_none(row.get("company")),
        empty_to_none(row.get("type")),
        addr_json,
        meta_json,
        empty_to_none(row.get("label")),

        safe_int(salary_obj.get("min")),
        safe_int(salary_obj.get("max")),
        empty_to_none(salary_obj.get("currency")),

        safe_int(exp_obj.get("min")),
        safe_int(exp_obj.get("max")),

        empty_to_none(addr_obj.get("country")),
        empty_to_none(addr_obj.get("region")),
        empty_to_none(addr_obj.get("state")),
        empty_to_none(addr_obj.get("city")),
        safe_float(addr_obj.get("latitude")),
        safe_float(addr_obj.get("longitude")),
        empty_to_none(addr_obj.get("status")),

        safe_int(meta_obj.get("publication_time")),
        safe_int(meta_obj.get("last_edit_time")),
        safe_int(meta_obj.get("total_views")),
        safe_int(meta_obj.get("views_last_week")),
    )


INSERT_SQL = """
INSERT OR REPLACE INTO jobs (
    id,
    title,
    salary,
    experience,
    description,
    key_skills,
    company,
    type,
    address_info,
    meta,
    label,

    salary_min,
    salary_max,
    salary_currency,

    experience_min,
    experience_max,

    country,
    region,
    state,
    city,
    latitude,
    longitude,
    geo_status,

    publication_time,
    last_edit_time,
    total_views,
    views_last_week
) VALUES (
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?,
    ?, ?,
    ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?
)
"""


def csv_to_sqlite(
    csv_path: str,
    db_path: str,
    chunksize: int = 5000,
):
    if not os.path.exists(csv_path):
        print(f"❌ CSV не найден: {csv_path}")
        return False

    start = time.time()
    delimiter = detect_delimiter(csv_path)
    print(f"📄 CSV: {csv_path}")
    print(f"🗂 DB:  {db_path}")
    print(f"🔎 Определён разделитель: {repr(delimiter)}")

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA cache_size=-200000")

    create_schema(conn)

    total_inserted = 0
    error_stats = {}

    try:
        reader = pd.read_csv(
            csv_path,
            sep=delimiter,
            encoding="utf-8-sig",
            dtype=str,
            keep_default_na=False,
            chunksize=chunksize,
            low_memory=False,
        )

        for chunk_idx, chunk in enumerate(reader, start=1):
            chunk = clean_columns(chunk)

            missing = [col for col in REQUIRED_COLUMNS if col not in chunk.columns]
            if missing:
                raise ValueError(f"В CSV отсутствуют обязательные колонки: {missing}")

            records = chunk.to_dict(orient="records")
            batch = [prepare_row(row, error_stats) for row in records]

            with conn:
                conn.executemany(INSERT_SQL, batch)

            total_inserted += len(batch)
            print(f"✅ Chunk {chunk_idx}: загружено {len(batch)} строк (всего {total_inserted})")

        create_indexes(conn)
        create_fts(conn)

        conn.execute("ANALYZE")
        conn.commit()
        conn.close()

        elapsed = time.time() - start
        db_size_mb = os.path.getsize(db_path) / (1024 * 1024)

        print("\n🎉 Готово")
        print(f"📊 Всего загружено строк: {total_inserted}")
        print(f"📦 Размер БД: {db_size_mb:.2f} MB")
        print(f"⏱ Время: {elapsed:.2f} сек")

        if error_stats:
            print("⚠️ Некорректный JSON встретился в полях:")
            for field, count in error_stats.items():
                print(f"   - {field}: {count}")

        return True

    except Exception as e:
        conn.close()
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent
    csv_file = (BASE_DIR / "../database/job_ads.csv").resolve()
    db_file = (BASE_DIR / "../database/job_ads.db").resolve()

    print("CSV файл:", csv_file)
    print("CSV существует:", csv_file.exists())

    ok = csv_to_sqlite(str(csv_file), str(db_file), chunksize=5000)

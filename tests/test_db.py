import sqlite3
from pathlib import Path

import pytest


EXPECTED_COLUMNS = {
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
    "salary_min",
    "salary_max",
    "salary_currency",
    "experience_min",
    "experience_max",
    "country",
    "region",
    "state",
    "city",
    "latitude",
    "longitude",
    "geo_status",
    "publication_time",
    "last_edit_time",
    "total_views",
    "views_last_week",
}


def get_db_path() -> Path:
    return (Path(__file__).resolve().parents[1] / "database" / "job_ads.db").resolve()


@pytest.fixture(scope="session")
def db_path():
    path = get_db_path()
    if not path.exists():
        pytest.skip(f"Файл базы не найден: {path}")
    return path


@pytest.fixture(scope="session")
def conn(db_path):
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    yield connection
    connection.close()


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name=?
        """,
        (table_name,),
    ).fetchone()
    return row is not None


def has_json_support(conn: sqlite3.Connection) -> bool:
    try:
        row = conn.execute("SELECT json_valid('{\"a\":1}')").fetchone()
        return row is not None
    except sqlite3.OperationalError:
        return False


def test_db_file_exists(db_path):
    assert db_path.exists(), f"DB не найдена: {db_path}"
    assert db_path.is_file(), f"Путь не является файлом: {db_path}"


def test_integrity_check(conn):
    result = conn.execute("PRAGMA integrity_check").fetchone()[0]
    assert result == "ok", f"integrity_check вернул: {result}"


def test_jobs_table_exists(conn):
    assert table_exists(conn, "jobs"), "Таблица jobs отсутствует"


def test_jobs_table_not_empty(conn):
    count = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    assert count > 0, "Таблица jobs пустая"


def test_jobs_has_expected_columns(conn):
    rows = conn.execute("PRAGMA table_info(jobs)").fetchall()
    actual_columns = {row["name"] for row in rows}

    missing = EXPECTED_COLUMNS - actual_columns
    assert not missing, f"Отсутствуют колонки: {sorted(missing)}"


def test_id_is_unique(conn):
    total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    unique_ids = conn.execute("SELECT COUNT(DISTINCT id) FROM jobs").fetchone()[0]

    assert unique_ids == total, (
        f"id не уникальны: всего строк={total}, уникальных id={unique_ids}"
    )


def test_id_not_null(conn):
    null_ids = conn.execute("SELECT COUNT(*) FROM jobs WHERE id IS NULL").fetchone()[0]
    assert null_ids == 0, f"Найдено строк с NULL id: {null_ids}"


def test_some_titles_are_present(conn):
    count = conn.execute("""
        SELECT COUNT(*)
        FROM jobs
        WHERE title IS NOT NULL AND TRIM(title) != ''
    """).fetchone()[0]

    assert count > 0, "Нет ни одной строки с заполненным title"


@pytest.mark.parametrize("column_name", ["salary", "experience", "address_info", "meta"])
def test_json_columns_are_valid_or_null(conn, column_name):
    if not has_json_support(conn):
        pytest.skip("SQLite собрана без JSON-функций")

    query = f"""
        SELECT COUNT(*)
        FROM jobs
        WHERE {column_name} IS NOT NULL
          AND TRIM({column_name}) != ''
          AND json_valid({column_name}) = 0
    """
    invalid_count = conn.execute(query).fetchone()[0]

    assert invalid_count == 0, (
        f"В колонке {column_name} найдено невалидных JSON-значений: {invalid_count}"
    )


def test_salary_projection_columns_work(conn):
    rows = conn.execute("""
        SELECT id, title, salary_min, salary_max, salary_currency
        FROM jobs
        ORDER BY id
        LIMIT 10
    """).fetchall()

    assert rows is not None
    assert len(rows) > 0


def test_sample_filter_query_works(conn):
    rows = conn.execute("""
        SELECT id, title, company, city, salary_min
        FROM jobs
        WHERE salary_min IS NOT NULL
        ORDER BY salary_min DESC
        LIMIT 5
    """).fetchall()

    assert rows is not None
    assert len(rows) > 0


def test_json_extract_query_works(conn):
    if not has_json_support(conn):
        pytest.skip("SQLite собрана без JSON-функций")

    rows = conn.execute("""
        SELECT
            id,
            title,
            json_extract(salary, '$.currency') AS currency,
            json_extract(meta, '$.total_views') AS views
        FROM jobs
        WHERE salary IS NOT NULL
        LIMIT 5
    """).fetchall()

    assert rows is not None
    assert len(rows) > 0


def test_can_read_some_real_data(conn):
    row = conn.execute("""
        SELECT id, title, company
        FROM jobs
        LIMIT 1
    """).fetchone()

    assert row is not None
    assert row["id"] is not None
    assert row["title"] is not None


def test_fts_query_if_exists(conn):
    if not table_exists(conn, "jobs_fts"):
        pytest.skip("Таблица jobs_fts отсутствует")

    try:
        rows = conn.execute("""
            SELECT rowid, title
            FROM jobs_fts
            WHERE jobs_fts MATCH 'механик'
            LIMIT 5
        """).fetchall()
    except sqlite3.OperationalError as e:
        pytest.fail(f"FTS-запрос завершился ошибкой: {e}")

    assert rows is not None


def test_views_columns_are_readable(conn):
    rows = conn.execute("""
        SELECT id, total_views, views_last_week
        FROM jobs
        ORDER BY total_views DESC
        LIMIT 10
    """).fetchall()

    assert rows is not None
    assert len(rows) > 0

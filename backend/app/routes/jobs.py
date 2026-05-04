from fastapi import APIRouter, HTTPException, Query
from backend.app.db import get_connection
from backend.app.utils import normalize_job, serialize_job_card

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("")
def get_jobs(
    limit: int = 20,
    offset: int = 0,
    q: str | None = Query(default=None, description="Поисковый запрос")
):
    conn = get_connection()
    try:
        cursor = conn.cursor()

        if q and q.strip():
            search = f"%{q.strip()}%"
            cursor.execute(
                """
                SELECT *
                FROM jobs
                WHERE title LIKE ?
                   OR description LIKE ?
                   OR company LIKE ?
                   OR city LIKE ?
                   OR label LIKE ?
                LIMIT ? OFFSET ?
                """,
                (search, search, search, search, search, limit, offset)
            )
        else:
            cursor.execute(
                "SELECT * FROM jobs LIMIT ? OFFSET ?",
                (limit, offset)
            )

        rows = cursor.fetchall()

        return {
            "count": len(rows),
            "items": [serialize_job_card(dict(row)) for row in rows]
        }
    finally:
        conn.close()


@router.get("/{job_id}")
def get_job_by_id(job_id: int):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM jobs WHERE id = ?",
            (job_id,)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Вакансия не найдена")

        return normalize_job(dict(row))
    finally:
        conn.close()
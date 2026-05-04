from fastapi import APIRouter, HTTPException, Query
import httpx

from backend.app.db import get_connection
from backend.app.utils import normalize_job, serialize_job_card

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

ML_BASE_URL = "http://127.0.0.1:8001"
ML_SIMILAR_ENDPOINT = f"{ML_BASE_URL}/api/ml/recommend/similar"


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


def extract_keywords(title: str | None) -> list[str]:
    if not title:
        return []

    stop_words = {
        "и", "в", "на", "по", "для", "с", "без", "под", "от", "до",
        "г", "склад", "работа", "специалист", "менеджер"
    }

    words = []
    for raw_word in title.lower().replace("(", " ").replace(")", " ").replace(",", " ").split():
        word = raw_word.strip()
        if len(word) < 4:
            continue
        if word in stop_words:
            continue
        words.append(word)

    seen = set()
    result = []
    for word in words:
        if word not in seen:
            seen.add(word)
            result.append(word)

    return result[:5]


def get_fallback_similar_jobs(source_job: dict, top_k: int) -> list[dict]:
    conn = get_connection()
    try:
        cursor = conn.cursor()

        source_id = source_job.get("id")
        label = source_job.get("label")
        city = source_job.get("city")
        keywords = extract_keywords(source_job.get("title"))

        candidates = []
        seen_ids = set()

        # 1. Сначала ищем по той же категории
        if label:
            cursor.execute(
                """
                SELECT *
                FROM jobs
                WHERE id != ? AND label = ?
                LIMIT 20
                """,
                (source_id, label)
            )
            for row in cursor.fetchall():
                row_dict = dict(row)
                if row_dict["id"] not in seen_ids:
                    candidates.append(serialize_job_card(row_dict))
                    seen_ids.add(row_dict["id"])

        # 2. Потом по тому же городу
        if len(candidates) < top_k and city:
            cursor.execute(
                """
                SELECT *
                FROM jobs
                WHERE id != ? AND city = ?
                LIMIT 20
                """,
                (source_id, city)
            )
            for row in cursor.fetchall():
                row_dict = dict(row)
                if row_dict["id"] not in seen_ids:
                    candidates.append(serialize_job_card(row_dict))
                    seen_ids.add(row_dict["id"])
                if len(candidates) >= top_k:
                    break

        # 3. Потом по ключевым словам из названия
        if len(candidates) < top_k and keywords:
            for keyword in keywords:
                cursor.execute(
                    """
                    SELECT *
                    FROM jobs
                    WHERE id != ?
                      AND (title LIKE ? OR description LIKE ?)
                    LIMIT 20
                    """,
                    (source_id, f"%{keyword}%", f"%{keyword}%")
                )
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    if row_dict["id"] not in seen_ids:
                        candidates.append(serialize_job_card(row_dict))
                        seen_ids.add(row_dict["id"])
                    if len(candidates) >= top_k:
                        break
                if len(candidates) >= top_k:
                    break

        return candidates[:top_k]
    finally:
        conn.close()


@router.get("/{job_id}/similar")
async def get_similar_jobs(job_id: int, top_k: int = 5):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM jobs WHERE id = ?",
            (job_id,)
        )
        source_row = cursor.fetchone()

        if not source_row:
            raise HTTPException(status_code=404, detail="Вакансия не найдена")

        source_job = normalize_job(dict(source_row))
    finally:
        conn.close()

    payload = {
        "entity_type": "job",
        "item": {
            "id": str(source_job.get("id")),
            "title": source_job.get("title"),
            "description": source_job.get("description"),
            "metadata": {
                "company": source_job.get("company"),
                "city": source_job.get("city"),
                "region": source_job.get("region"),
                "label": source_job.get("label"),
                "salary_min": source_job.get("salary_min"),
                "salary_max": source_job.get("salary_max"),
                "salary_currency": source_job.get("salary_currency"),
            }
        },
        "top_k": top_k
    }

    ml_items = []

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(ML_SIMILAR_ENDPOINT, json=payload)
            response.raise_for_status()
            ml_data = response.json()

        raw_results = ml_data.get("results", [])
        similar_ids = []

        for item in raw_results:
            item_id = item.get("id") or item.get("item_id")
            if item_id is None:
                continue

            try:
                parsed_id = int(item_id)
            except (TypeError, ValueError):
                continue

            if parsed_id != job_id:
                similar_ids.append(parsed_id)

        if similar_ids:
            conn = get_connection()
            try:
                cursor = conn.cursor()

                placeholders = ",".join(["?"] * len(similar_ids))
                cursor.execute(
                    f"SELECT * FROM jobs WHERE id IN ({placeholders})",
                    similar_ids
                )
                rows = cursor.fetchall()

                jobs_by_id = {dict(row)["id"]: serialize_job_card(dict(row)) for row in rows}
                ml_items = [jobs_by_id[jid] for jid in similar_ids if jid in jobs_by_id]
            finally:
                conn.close()
    except Exception:
        ml_items = []

    if ml_items:
        return {
            "count": len(ml_items),
            "items": ml_items[:top_k],
            "source": "ml"
        }

    fallback_items = get_fallback_similar_jobs(source_job, top_k)

    return {
        "count": len(fallback_items),
        "items": fallback_items,
        "source": "fallback"
    }
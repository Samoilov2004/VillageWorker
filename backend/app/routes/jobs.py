import logging

from fastapi import APIRouter, HTTPException, Query
import httpx

from backend.app.db import get_connection
from backend.app.utils import normalize_job, serialize_job_card

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

ML_BASE_URL = "http://127.0.0.1:8001"
ML_SEARCH_ENDPOINT = f"{ML_BASE_URL}/api/ml/search"
ML_SIMILAR_ENDPOINT = f"{ML_BASE_URL}/api/ml/recommend/similar"

# ML search: pagination работает через top_k = limit + offset; ограничено схемой ML-сервиса
_ML_SEARCH_MAX_TOP_K = 100


# ─── helpers ──────────────────────────────────────────────────────────────────

def _sql_browse(limit: int, offset: int) -> list[dict]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs LIMIT ? OFFSET ?", (limit, offset))
        return [serialize_job_card(dict(row)) for row in cursor.fetchall()]
    finally:
        conn.close()


def _sql_search(query: str, limit: int, offset: int) -> list[dict]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        like = f"%{query}%"
        cursor.execute(
            """
            SELECT * FROM jobs
            WHERE title       LIKE ?
               OR description LIKE ?
               OR company     LIKE ?
               OR city        LIKE ?
               OR label       LIKE ?
            LIMIT ? OFFSET ?
            """,
            (like, like, like, like, like, limit, offset),
        )
        return [serialize_job_card(dict(row)) for row in cursor.fetchall()]
    finally:
        conn.close()


def _fetch_jobs_by_ids(ordered_ids: list[int]) -> list[dict]:
    """Вернуть вакансии из БД в том же порядке, что ordered_ids."""
    if not ordered_ids:
        return []
    conn = get_connection()
    try:
        cursor = conn.cursor()
        placeholders = ",".join(["?"] * len(ordered_ids))
        cursor.execute(
            f"SELECT * FROM jobs WHERE id IN ({placeholders})",
            ordered_ids,
        )
        by_id = {dict(row)["id"]: serialize_job_card(dict(row)) for row in cursor.fetchall()}
        return [by_id[jid] for jid in ordered_ids if jid in by_id]
    finally:
        conn.close()


# ─── ML calls ─────────────────────────────────────────────────────────────────

async def _ml_search(query: str, limit: int, offset: int) -> list[dict] | None:
    """
    Вернуть список job-карточек через ML-поиск или None при ошибке/недоступности.
    Пагинация: запрашиваем top_k = limit + offset, срезаем [offset:offset+limit].
    """
    top_k = limit + offset
    if top_k > _ML_SEARCH_MAX_TOP_K:
        logger.debug(
            "search q=%r: top_k=%d превышает лимит ML (%d), пропускаем ML",
            query, top_k, _ML_SEARCH_MAX_TOP_K,
        )
        return None

    payload = {"entity_type": "job", "query": query, "top_k": top_k}
    logger.debug("search q=%r: запрос к ML-сервису (top_k=%d)", query, top_k)

    try:
        async with httpx.AsyncClient(timeout=5.0) as http_client:
            response = await http_client.post(ML_SEARCH_ENDPOINT, json=payload)
            response.raise_for_status()
            raw = response.json().get("results", [])

        # парсим ID и смещаем страницу
        all_ids: list[int] = []
        for item in raw:
            try:
                all_ids.append(int(item["id"]))
            except (KeyError, TypeError, ValueError):
                continue

        page_ids = all_ids[offset: offset + limit]
        items = _fetch_jobs_by_ids(page_ids)

        logger.info(
            "search q=%r: ML вернул %d результатов, в БД найдено %d (offset=%d limit=%d)",
            query, len(raw), len(items), offset, limit,
        )
        return items

    except httpx.TimeoutException:
        logger.warning("search q=%r: ML-сервис не ответил за 5 с, fallback", query)
    except httpx.HTTPStatusError as exc:
        logger.warning("search q=%r: ML-сервис HTTP %s, fallback", query, exc.response.status_code)
    except httpx.RequestError as exc:
        logger.warning("search q=%r: ML-сервис недоступен (%s: %s), fallback", query, type(exc).__name__, exc)
    except Exception as exc:
        logger.warning("search q=%r: неожиданная ошибка ML (%s: %s), fallback", query, type(exc).__name__, exc)

    return None


# ─── routes ───────────────────────────────────────────────────────────────────

@router.get("")
async def get_jobs(
    limit: int = 20,
    offset: int = 0,
    q: str | None = Query(default=None, description="Поисковый запрос"),
):
    if q and q.strip():
        query = q.strip()
        ml_items = await _ml_search(query, limit, offset)
        if ml_items is not None:
            return {"count": len(ml_items), "items": ml_items, "source": "ml"}

        fallback_items = _sql_search(query, limit, offset)
        logger.debug("search q=%r: возвращаем SQL fallback (%d)", query, len(fallback_items))
        return {"count": len(fallback_items), "items": fallback_items, "source": "fallback"}

    items = _sql_browse(limit, offset)
    return {"count": len(items), "items": items}


@router.get("/{job_id}")
def get_job_by_id(job_id: int):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Вакансия не найдена")
        return normalize_job(dict(row))
    finally:
        conn.close()


# ─── similar ──────────────────────────────────────────────────────────────────

def extract_keywords(title: str | None) -> list[str]:
    if not title:
        return []
    stop_words = {
        "и", "в", "на", "по", "для", "с", "без", "под", "от", "до",
        "г", "склад", "работа", "специалист", "менеджер",
    }
    seen, result = set(), []
    for raw in title.lower().replace("(", " ").replace(")", " ").replace(",", " ").split():
        w = raw.strip()
        if len(w) < 4 or w in stop_words or w in seen:
            continue
        seen.add(w)
        result.append(w)
    return result[:5]


def get_fallback_similar_jobs(source_job: dict, top_k: int) -> list[dict]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        source_id = source_job.get("id")
        label = source_job.get("label")
        city = source_job.get("city")
        keywords = extract_keywords(source_job.get("title"))

        candidates, seen_ids = [], set()

        if label:
            cursor.execute(
                "SELECT * FROM jobs WHERE id != ? AND label = ? LIMIT 20",
                (source_id, label),
            )
            for row in cursor.fetchall():
                d = dict(row)
                if d["id"] not in seen_ids:
                    candidates.append(serialize_job_card(d))
                    seen_ids.add(d["id"])

        if len(candidates) < top_k and city:
            cursor.execute(
                "SELECT * FROM jobs WHERE id != ? AND city = ? LIMIT 20",
                (source_id, city),
            )
            for row in cursor.fetchall():
                d = dict(row)
                if d["id"] not in seen_ids:
                    candidates.append(serialize_job_card(d))
                    seen_ids.add(d["id"])
                if len(candidates) >= top_k:
                    break

        if len(candidates) < top_k and keywords:
            for kw in keywords:
                cursor.execute(
                    """
                    SELECT * FROM jobs
                    WHERE id != ? AND (title LIKE ? OR description LIKE ?)
                    LIMIT 20
                    """,
                    (source_id, f"%{kw}%", f"%{kw}%"),
                )
                for row in cursor.fetchall():
                    d = dict(row)
                    if d["id"] not in seen_ids:
                        candidates.append(serialize_job_card(d))
                        seen_ids.add(d["id"])
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
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        source_row = cursor.fetchone()
        if not source_row:
            raise HTTPException(status_code=404, detail="Вакансия не найдена")
        source_job = normalize_job(dict(source_row))
    finally:
        conn.close()

    address_info = source_job.get("address_info")
    lat = address_info.get("latitude") if isinstance(address_info, dict) else None
    lon = address_info.get("longitude") if isinstance(address_info, dict) else None

    payload = {
        "entity_type": "job",
        "item": {
            "id": str(source_job.get("id")),
            "title": source_job.get("title") or "",
            "description": source_job.get("description") or "",
            "metadata": {
                "company": source_job.get("company"),
                "city": source_job.get("city"),
                "region": source_job.get("region"),
                "label": source_job.get("label"),
                "lat": lat,
                "lon": lon,
            },
        },
        "top_k": top_k,
    }

    ml_items = []

    logger.debug(
        "similar job_id=%s: запрос к ML-сервису (top_k=%s, geo=%s)",
        job_id, top_k, "да" if lat and lon else "нет",
    )

    try:
        async with httpx.AsyncClient(timeout=5.0) as http_client:
            response = await http_client.post(ML_SIMILAR_ENDPOINT, json=payload)
            response.raise_for_status()
            raw_results = response.json().get("results", [])

        similar_ids = []
        for item in raw_results:
            try:
                pid = int(item.get("id") or item.get("item_id"))
            except (TypeError, ValueError):
                continue
            if pid != job_id:
                similar_ids.append(pid)

        ml_items = _fetch_jobs_by_ids(similar_ids)

        logger.info(
            "similar job_id=%s: ML вернул %d результатов, в БД найдено %d",
            job_id, len(raw_results), len(ml_items),
        )

    except httpx.TimeoutException:
        logger.warning("similar job_id=%s: ML-сервис не ответил за 5 с, fallback", job_id)
    except httpx.HTTPStatusError as exc:
        logger.warning("similar job_id=%s: ML HTTP %s, fallback", job_id, exc.response.status_code)
    except httpx.RequestError as exc:
        logger.warning("similar job_id=%s: ML недоступен (%s: %s), fallback", job_id, type(exc).__name__, exc)
    except Exception as exc:
        logger.warning("similar job_id=%s: ошибка ML (%s: %s), fallback", job_id, type(exc).__name__, exc)

    if ml_items:
        logger.debug("similar job_id=%s: возвращаем ML-результаты", job_id)
        return {"count": len(ml_items), "items": ml_items[:top_k], "source": "ml"}

    fallback_items = get_fallback_similar_jobs(source_job, top_k)
    logger.debug("similar job_id=%s: возвращаем fallback (%d)", job_id, len(fallback_items))
    return {"count": len(fallback_items), "items": fallback_items, "source": "fallback"}

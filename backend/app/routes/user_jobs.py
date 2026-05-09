import logging
from typing import Optional

import httpx
from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.db import get_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user-jobs", tags=["user-jobs"])

ML_BASE_URL = "http://127.0.0.1:8001"


class JobCreateRequest(BaseModel):
    title: str
    description: str
    company: str
    city: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    experience_min: int = 0
    experience_max: int = 0


@router.post("")
async def create_user_job(body: JobCreateRequest):
    label: Optional[str] = None
    mod_status = "ok"
    risk_score = 0.0
    mod_reasons: list[str] = []

    async with httpx.AsyncClient(timeout=5.0) as client:
        # predict category
        try:
            res = await client.post(
                f"{ML_BASE_URL}/api/ml/label/predict",
                json={"title": body.title, "description": body.description},
            )
            label = res.json().get("label")
        except Exception as exc:
            logger.warning("label predict failed: %s", exc)

        # moderation check
        try:
            res = await client.post(
                f"{ML_BASE_URL}/api/ml/moderation/check",
                json={"content_type": "job", "title": body.title, "description": body.description},
            )
            data = res.json()
            decision = data.get("decision", "allow")
            risk_score = data.get("risk_score", 0.0)
            mod_reasons = data.get("reasons", [])
            if decision == "reject":
                mod_status = "reject"
            elif decision == "review":
                mod_status = "review"
        except Exception as exc:
            logger.warning("moderation check failed: %s", exc)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO user_jobs
                (title, description, company, city,
                 salary_min, salary_max, experience_min, experience_max,
                 label, mod_status, risk_score, mod_reasons)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                body.title, body.description, body.company, body.city,
                body.salary_min, body.salary_max, body.experience_min, body.experience_max,
                label, mod_status, risk_score, ", ".join(mod_reasons),
            ),
        )
        conn.commit()
        new_id = cursor.lastrowid
    finally:
        conn.close()

    logger.info("user_job created id=%s label=%s mod=%s", new_id, label, mod_status)
    return {
        "id": new_id,
        "label": label,
        "mod_status": mod_status,
        "risk_score": round(risk_score, 3),
        "mod_reasons": mod_reasons,
    }


@router.get("")
def list_user_jobs():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_jobs ORDER BY created_at DESC")
        return {"items": [dict(r) for r in cursor.fetchall()]}
    finally:
        conn.close()

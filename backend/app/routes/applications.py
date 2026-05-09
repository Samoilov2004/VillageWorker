from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.db import get_connection

router = APIRouter(prefix="/api/applications", tags=["applications"])


class ApplicationRequest(BaseModel):
    job_id: int
    job_title: str
    user_name: str
    phone: str
    message: Optional[str] = ""


@router.post("")
def create_application(body: ApplicationRequest):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO applications (job_id, job_title, user_name, phone, message)
            VALUES (?, ?, ?, ?, ?)
            """,
            (body.job_id, body.job_title, body.user_name, body.phone, body.message),
        )
        conn.commit()
        return {"id": cursor.lastrowid, "status": "ok"}
    finally:
        conn.close()


@router.get("")
def list_applications():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications ORDER BY created_at DESC")
        return {"items": [dict(r) for r in cursor.fetchall()]}
    finally:
        conn.close()

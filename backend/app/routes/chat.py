import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.app.db import get_connection


router = APIRouter(prefix="/api/chat", tags=["chat"])


class DialogStartRequest(BaseModel):
    job_id: int
    job_title: str = "Вакансия"
    applicant_id: int = 1
    applicant_name: str = "Соискатель"
    employer_id: int = 2
    employer_name: str = "Работодатель"


class MessageCreateRequest(BaseModel):
    sender_id: int
    text: str


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, dialog_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(dialog_id, []).append(websocket)

    def disconnect(self, dialog_id: int, websocket: WebSocket):
        connections = self.active_connections.get(dialog_id, [])

        if websocket in connections:
            connections.remove(websocket)

        if not connections and dialog_id in self.active_connections:
            del self.active_connections[dialog_id]

    async def broadcast(self, dialog_id: int, payload: dict):
        connections = self.active_connections.get(dialog_id, []).copy()

        for connection in connections:
            try:
                await connection.send_json(payload)
            except Exception:
                self.disconnect(dialog_id, connection)


manager = ConnectionManager()


def row_to_dict(row) -> Optional[dict]:
    if row is None:
        return None

    return dict(row)


def get_message(message_id: int) -> Optional[dict]:
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chat_messages WHERE id = ?", (message_id,))
        return row_to_dict(cursor.fetchone())
    finally:
        conn.close()


def is_dialog_participant(dialog_id: int, user_id: int) -> bool:
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id
            FROM chat_dialogs
            WHERE id = ?
              AND (applicant_id = ? OR employer_id = ?)
        """, (dialog_id, user_id, user_id))

        return cursor.fetchone() is not None
    finally:
        conn.close()


def create_message_in_db(dialog_id: int, sender_id: int, text: str) -> dict:
    clean_text = text.strip()

    if not clean_text:
        raise HTTPException(status_code=400, detail="Сообщение не может быть пустым")

    if len(clean_text) > 1000:
        raise HTTPException(status_code=400, detail="Сообщение слишком длинное")

    if not is_dialog_participant(dialog_id, sender_id):
        raise HTTPException(status_code=403, detail="Нет доступа к этому диалогу")

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO chat_messages (dialog_id, sender_id, text)
            VALUES (?, ?, ?)
        """, (dialog_id, sender_id, clean_text))

        conn.commit()
        message_id = cursor.lastrowid
    finally:
        conn.close()

    message = get_message(message_id)

    return {
        "id": message["id"],
        "dialog_id": message["dialog_id"],
        "sender_id": message["sender_id"],
        "text": message["text"],
        "created_at": message["created_at"],
        "is_read": message["is_read"],
    }


@router.post("/dialogs/start")
def start_dialog(body: DialogStartRequest):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM chat_dialogs
            WHERE job_id = ?
              AND applicant_id = ?
              AND employer_id = ?
        """, (body.job_id, body.applicant_id, body.employer_id))

        existing_dialog = cursor.fetchone()

        if existing_dialog:
            return {
                "status": "exists",
                "dialog": dict(existing_dialog),
            }

        cursor.execute("""
            INSERT INTO chat_dialogs (
                job_id,
                job_title,
                applicant_id,
                applicant_name,
                employer_id,
                employer_name
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            body.job_id,
            body.job_title,
            body.applicant_id,
            body.applicant_name,
            body.employer_id,
            body.employer_name,
        ))

        conn.commit()

        dialog_id = cursor.lastrowid

        cursor.execute("SELECT * FROM chat_dialogs WHERE id = ?", (dialog_id,))
        dialog = cursor.fetchone()

        return {
            "status": "created",
            "dialog": dict(dialog),
        }
    finally:
        conn.close()


@router.get("/dialogs")
def list_dialogs(user_id: int = Query(...)):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                d.*,
                (
                    SELECT m.text
                    FROM chat_messages m
                    WHERE m.dialog_id = d.id
                    ORDER BY m.created_at DESC, m.id DESC
                    LIMIT 1
                ) AS last_message,
                (
                    SELECT m.created_at
                    FROM chat_messages m
                    WHERE m.dialog_id = d.id
                    ORDER BY m.created_at DESC, m.id DESC
                    LIMIT 1
                ) AS last_message_at
            FROM chat_dialogs d
            WHERE d.applicant_id = ? OR d.employer_id = ?
            ORDER BY COALESCE(last_message_at, d.created_at) DESC
        """, (user_id, user_id))

        dialogs = []

        for row in cursor.fetchall():
            dialog = dict(row)

            if user_id == dialog["applicant_id"]:
                dialog["role"] = "applicant"
                dialog["companion_id"] = dialog["employer_id"]
                dialog["companion_name"] = dialog["employer_name"]
            else:
                dialog["role"] = "employer"
                dialog["companion_id"] = dialog["applicant_id"]
                dialog["companion_name"] = dialog["applicant_name"]

            dialogs.append(dialog)

        return {"items": dialogs}
    finally:
        conn.close()


@router.get("/dialogs/{dialog_id}/messages")
def list_messages(dialog_id: int, user_id: int = Query(...)):
    if not is_dialog_participant(dialog_id, user_id):
        raise HTTPException(status_code=403, detail="Нет доступа к этому диалогу")

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM chat_messages
            WHERE dialog_id = ?
            ORDER BY created_at ASC, id ASC
        """, (dialog_id,))

        return {"items": [dict(row) for row in cursor.fetchall()]}
    finally:
        conn.close()


@router.post("/dialogs/{dialog_id}/messages")
async def create_message(dialog_id: int, body: MessageCreateRequest):
    message = create_message_in_db(
        dialog_id=dialog_id,
        sender_id=body.sender_id,
        text=body.text,
    )

    await manager.broadcast(dialog_id, {
        "type": "message",
        "message": message,
    })

    return message


@router.websocket("/ws/{dialog_id}")
async def chat_websocket(websocket: WebSocket, dialog_id: int, user_id: int):
    if not is_dialog_participant(dialog_id, user_id):
        await websocket.close(code=1008)
        return

    await manager.connect(dialog_id, websocket)

    try:
        while True:
            raw_data = await websocket.receive_text()

            try:
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Некорректный формат сообщения",
                })
                continue

            text = str(data.get("text", "")).strip()

            if not text:
                await websocket.send_json({
                    "type": "error",
                    "message": "Сообщение не может быть пустым",
                })
                continue

            message = create_message_in_db(
                dialog_id=dialog_id,
                sender_id=user_id,
                text=text,
            )

            await manager.broadcast(dialog_id, {
                "type": "message",
                "message": message,
            })

    except WebSocketDisconnect:
        manager.disconnect(dialog_id, websocket)
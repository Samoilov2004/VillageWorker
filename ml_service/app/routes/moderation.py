from fastapi import APIRouter, Request

from ml_service.app.schemas import ModerationRequest, ModerationResponse


router = APIRouter(prefix="/moderation", tags=["moderation"])


@router.post("/check", response_model=ModerationResponse)
def moderation_check(payload: ModerationRequest, request: Request):
    service = request.app.state.moderation_service
    result = service.check(
        title=payload.title,
        description=payload.description,
    )
    return result

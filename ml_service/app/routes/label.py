from fastapi import APIRouter, Request

from ml_service.app.schemas import LabelRequest, LabelResponse


router = APIRouter(prefix="/label", tags=["label"])


@router.post("/predict", response_model=LabelResponse)
def label_predict(payload: LabelRequest, request: Request):
    service = request.app.state.label_service
    label = service.predict(title=payload.title, description=payload.description)
    return {"label": label}

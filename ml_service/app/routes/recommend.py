from fastapi import APIRouter, HTTPException, Request

from ml_service.app.schemas import (
    RecommendMatchRequest,
    RecommendResponse,
    RecommendSimilarRequest,
)


router = APIRouter(prefix="/recommend", tags=["recommend"])


@router.post("/similar", response_model=RecommendResponse)
def recommend_similar(payload: RecommendSimilarRequest, request: Request):
    service = request.app.state.recommendation_service

    try:
        results = service.similar(
            entity_type=payload.entity_type,
            item_id=payload.item_id,
            item=payload.item.model_dump() if payload.item else None,
            top_k=payload.top_k,
            filters=payload.filters,
        )
        return {"results": results}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/match", response_model=RecommendResponse)
def recommend_match(payload: RecommendMatchRequest, request: Request):
    service = request.app.state.recommendation_service
    results = service.match(
        source_item=payload.item.model_dump(),
        target_entity_type=payload.target_entity_type,
        top_k=payload.top_k,
        filters=payload.filters,
    )
    return {"results": results}

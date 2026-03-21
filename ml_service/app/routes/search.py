from fastapi import APIRouter, Request

from ml_service.app.schemas import RerankRequest, SearchRequest, SearchResponse


router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search(payload: SearchRequest, request: Request):
    service = request.app.state.search_service
    results = service.search(
        entity_type=payload.entity_type,
        query=payload.query,
        top_k=payload.top_k,
        filters=payload.filters,
    )
    return {"results": results}


@router.post("/rerank", response_model=SearchResponse)
def rerank(payload: RerankRequest, request: Request):
    service = request.app.state.search_service
    items = [item.model_dump() for item in payload.items]
    results = service.rerank(
        query=payload.query,
        items=items,
        top_k=payload.top_k,
    )
    return {"results": results}

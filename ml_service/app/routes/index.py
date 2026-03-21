from fastapi import APIRouter, Request

from ml_service.app.schemas import IndexDeleteRequest, IndexStatsResponse, IndexUpsertRequest


router = APIRouter(prefix="/index", tags=["index"])


@router.post("/upsert")
def upsert_index(payload: IndexUpsertRequest, request: Request):
    store = request.app.state.index_store
    count = store.upsert(
        payload.entity_type,
        [item.model_dump() for item in payload.items]
    )
    return {
        "status": "ok",
        "entity_type": payload.entity_type,
        "upserted": count
    }


@router.post("/delete")
def delete_from_index(payload: IndexDeleteRequest, request: Request):
    store = request.app.state.index_store
    removed = store.delete(payload.entity_type, payload.ids)
    return {
        "status": "ok",
        "entity_type": payload.entity_type,
        "deleted": removed
    }


@router.get("/stats", response_model=IndexStatsResponse)
def get_index_stats(request: Request):
    store = request.app.state.index_store
    return {"entities": store.stats()}

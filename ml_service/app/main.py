from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ml_service.app.core.config import get_settings
from ml_service.app.core.logger import setup_logger
from ml_service.app.routes.index import router as index_router
from ml_service.app.routes.moderation import router as moderation_router
from ml_service.app.routes.recommend import router as recommend_router
from ml_service.app.routes.search import router as search_router
from ml_service.app.schemas import HealthResponse, ReadyResponse
from ml_service.app.services.embedding_service import EmbeddingService
from ml_service.app.services.index_store import IndexStore
from ml_service.app.services.moderation_service import ModerationService
from ml_service.app.services.recommendation_service import RecommendationService
from ml_service.app.services.search_service import SearchService


logger = setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.index_dir.mkdir(parents=True, exist_ok=True)
    settings.models_dir.mkdir(parents=True, exist_ok=True)

    index_store = IndexStore(settings.index_dir)
    embedding_service = EmbeddingService()
    moderation_service = ModerationService()
    search_service = SearchService(index_store, embedding_service)
    recommendation_service = RecommendationService(index_store, embedding_service)

    app.state.settings = settings
    app.state.index_store = index_store
    app.state.embedding_service = embedding_service
    app.state.moderation_service = moderation_service
    app.state.search_service = search_service
    app.state.recommendation_service = recommendation_service

    logger.info("ML service started")
    logger.info("API prefix: %s", settings.api_prefix)
    logger.info("Index dir: %s", settings.index_dir)
    logger.info("Models dir: %s", settings.models_dir)

    yield

    logger.info("ML service stopped")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # локально ок, если будет не локально, то поменяю
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(index_router, prefix=settings.api_prefix)
    app.include_router(search_router, prefix=settings.api_prefix)
    app.include_router(recommend_router, prefix=settings.api_prefix)
    app.include_router(moderation_router, prefix=settings.api_prefix)

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    def health():
        return {"status": "ok"}

    @app.get("/ready", response_model=ReadyResponse, tags=["system"])
    def ready():
        stats = app.state.index_store.stats() if hasattr(app.state, "index_store") else {}
        return {
            "status": "ready",
            "models_loaded": True,
            "index_available": True,
            "indexed_entities": stats,
        }

    return app


app = create_app()

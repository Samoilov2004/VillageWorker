import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.db import init_tables
from backend.app.routes.jobs import router as jobs_router
from backend.app.routes.user_jobs import router as user_jobs_router
from backend.app.routes.applications import router as applications_router
from backend.app.routes.chat import router as chat_router


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
    datefmt="%H:%M:%S",
)


app = FastAPI(title="VillageWorker Backend", version="0.4.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_tables()


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(jobs_router)
app.include_router(user_jobs_router)
app.include_router(applications_router)
app.include_router(chat_router)
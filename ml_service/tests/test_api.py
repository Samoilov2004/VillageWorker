import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ml_service.app.core.config import get_settings
from ml_service.app.main import create_app


@pytest.fixture
def client(tmp_path: Path):
    os.environ["ML_DATA_DIR"] = str(tmp_path / "data")
    os.environ["ML_API_PREFIX"] = "/api/ml"

    get_settings.cache_clear()
    app = create_app()

    with TestClient(app) as test_client:
        yield test_client


def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_index_and_search_flow(client: TestClient):
    payload = {
        "entity_type": "job",
        "items": [
            {
                "id": "1",
                "title": "Главный механик",
                "description": "Ремонт техники и обслуживание оборудования",
                "metadata": {
                    "city": "Владивосток",
                    "label": "Производство/инженерия"
                }
            },
            {
                "id": "2",
                "title": "Слесарь КИПиА",
                "description": "Сборка и настройка измерительных приборов",
                "metadata": {
                    "city": "Санкт-Петербург",
                    "label": "Производство/инженерия"
                }
            }
        ]
    }

    r1 = client.post("/api/ml/index/upsert", json=payload)
    assert r1.status_code == 200
    assert r1.json()["upserted"] == 2

    r2 = client.post("/api/ml/search", json={
        "entity_type": "job",
        "query": "механик техника",
        "top_k": 5,
        "filters": {}
    })
    assert r2.status_code == 200

    results = r2.json()["results"]
    assert len(results) >= 1
    assert results[0]["id"] == "1"


def test_moderation(client: TestClient):
    r = client.post("/api/ml/moderation/check", json={
        "content_type": "announcement",
        "title": "Быстрые деньги без опыта!!!",
        "description": "Пишите в telegram, доход 500000 в день",
        "metadata": {}
    })

    assert r.status_code == 200
    data = r.json()
    assert data["decision"] in {"review", "reject"}


def test_ready(client: TestClient):
    r = client.get("/ready")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ready"
    assert data["index_available"] is True

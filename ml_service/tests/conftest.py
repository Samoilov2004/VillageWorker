import os
import sys
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # VillageWorker
MODELS_DIR = PROJECT_ROOT / "ml_service" / "models"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def client(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("ml_data")
    os.environ["ML_DATA_DIR"] = str(tmp)
    os.environ["ML_MODELS_DIR"] = str(MODELS_DIR)
    os.environ["ML_API_PREFIX"] = "/api/ml"

    from ml_service.app.core.config import get_settings
    get_settings.cache_clear()

    from ml_service.app.main import create_app
    with TestClient(create_app()) as c:
        yield c


@pytest.fixture(scope="session")
def vacancy_id_with_geo():
    """Первая вакансия с заполненными lat/lon из metadata рекомендаций."""
    meta = pd.read_csv(MODELS_DIR / "vacancy_recomendation" / "recommend_sbert_geo_metadata.csv")
    row = meta[meta[["lat", "lon"]].notna().all(axis=1)].iloc[0]
    return str(row["id"])


@pytest.fixture(scope="session")
def vacancy_id_any():
    """Первая вакансия из metadata рекомендаций."""
    meta = pd.read_csv(MODELS_DIR / "vacancy_recomendation" / "recommend_sbert_geo_metadata.csv")
    return str(meta.iloc[0]["id"])

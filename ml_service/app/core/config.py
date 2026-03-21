from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import os


@dataclass
class Settings:
    app_name: str
    app_version: str
    api_prefix: str
    host: str
    port: int
    debug: bool
    base_dir: Path
    data_dir: Path
    index_dir: Path
    models_dir: Path


@lru_cache
def get_settings() -> Settings:
    base_dir = Path(__file__).resolve().parents[2]

    data_dir = Path(os.getenv("ML_DATA_DIR", base_dir / "data")).resolve()
    index_dir = Path(os.getenv("ML_INDEX_DIR", data_dir / "indexes")).resolve()
    models_dir = Path(os.getenv("ML_MODELS_DIR", data_dir / "models")).resolve()

    return Settings(
        app_name=os.getenv("ML_APP_NAME", "rural-hub-ml-service"),
        app_version=os.getenv("ML_APP_VERSION", "0.1.0"),
        api_prefix=os.getenv("ML_API_PREFIX", "/api/ml"),
        host=os.getenv("ML_HOST", "127.0.0.1"),
        port=int(os.getenv("ML_PORT", "8000")),
        debug=os.getenv("ML_DEBUG", "true").lower() == "true",
        base_dir=base_dir,
        data_dir=data_dir,
        index_dir=index_dir,
        models_dir=models_dir,
    )

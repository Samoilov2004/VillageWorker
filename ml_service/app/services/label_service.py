import re
from pathlib import Path

import joblib
import pandas as pd


class LabelService:
    def __init__(self, models_dir: Path):
        artifact = joblib.load(models_dir / "label_guess" / "job_label_model.joblib")
        self._features = artifact["features"]
        self._clf = artifact["clf"]
        self._title_weight: int = artifact.get("title_weight", 3)

    @staticmethod
    def _clean_text(s) -> str:
        if s is None or (isinstance(s, float) and pd.isna(s)):
            return ""
        s = re.sub(r"\s+", " ", str(s).lower()).strip()
        return s

    def predict(self, title: str, description: str) -> str:
        text = (self._clean_text(title) + " ") * self._title_weight + self._clean_text(description)
        return str(self._clf.predict(self._features.transform([text]))[0])

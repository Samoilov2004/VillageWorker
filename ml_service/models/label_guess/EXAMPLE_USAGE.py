import joblib
import re
import pandas as pd

import warnings

warnings.filterwarnings("ignore")

def clean_text(s: str) -> str:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    s = str(s).lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s

artifact = joblib.load("job_label_model.joblib")

features = artifact["features"]
clf = artifact["clf"]
TITLE_WEIGHT = artifact.get("title_weight", 3)

title = "Слесарь КИПиА"
description = "Сборка, ремонт, настройка манометров и термометров, подготовка измерительного оборудования."

text = ((clean_text(title) + " ") * TITLE_WEIGHT) + clean_text(description)

Xv = features.transform([text])
pred = clf.predict(Xv)[0]

print("Prediction:", pred)
import math
import re
from pathlib import Path
from typing import Dict, List

import joblib
from scipy.sparse import hstack


class ModerationService:
    FRAUD_PATTERNS = [
        r"переведи.*деньги",
        r"предоплата",
        r"гарантированный заработок",
        r"пишите в telegram",
        r"whatsapp",
        r"crypto",
        r"крипт",
    ]

    DRUG_PATTERNS = [
        r"закладк",
        r"меф",
        r"амф",
        r"марихуан",
        r"соль",
        r"наркот",
    ]

    TOXIC_PATTERNS = [
        r"идиот",
        r"тупой",
        r"ненавижу",
        r"урод",
    ]

    URL_PATTERN = re.compile(r"https?://|www\.|t\.me/|telegram", re.IGNORECASE)

    def __init__(self, models_dir: Path):
        spam_dir = models_dir / "spam_filtration"
        self._word_tfidf = joblib.load(spam_dir / "word_tfidf.pkl")
        self._char_tfidf = joblib.load(spam_dir / "char_tfidf.pkl")
        self._svm = joblib.load(spam_dir / "linear_svc_spam.pkl")

    @staticmethod
    def _clean_for_spam(text: str) -> str:
        text = text.lower()
        text = re.sub(r"http\S+|www\S+", " URL ", text)
        text = re.sub(r"@\w+", " USERNAME ", text)
        text = re.sub(r"\+?\d[\d\-\(\) ]{7,}\d", " PHONE ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _ml_spam_score(self, text: str) -> float:
        cleaned = self._clean_for_spam(text)
        X_word = self._word_tfidf.transform([cleaned])
        X_char = self._char_tfidf.transform([cleaned])
        X = hstack([X_word, X_char])
        decision = float(self._svm.decision_function(X)[0])
        return round(1.0 / (1.0 + math.exp(-decision)), 4)

    def _score_patterns(self, text: str, patterns: List[str], weight: float = 0.3) -> float:
        score = 0.0
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += weight
        return min(score, 1.0)

    def check(self, title: str, description: str) -> dict:
        text = f"{title}\n{description}".strip()

        labels: Dict[str, float] = {
            "spam": self._ml_spam_score(text),
            "fraud": 0.0,
            "drugs": 0.0,
            "toxicity": 0.0,
        }

        labels["fraud"] += self._score_patterns(text, self.FRAUD_PATTERNS, 0.35)
        if self.URL_PATTERN.search(text):
            labels["fraud"] = min(labels["fraud"] + 0.15, 1.0)

        labels["drugs"] += self._score_patterns(text, self.DRUG_PATTERNS, 0.5)
        labels["toxicity"] += self._score_patterns(text, self.TOXIC_PATTERNS, 0.4)

        labels = {k: round(min(v, 1.0), 4) for k, v in labels.items()}

        reasons = []
        if labels["spam"] >= 0.6:
            reasons.append("обнаружены признаки спама")
        if labels["fraud"] >= 0.5:
            reasons.append("обнаружены признаки мошеннического контента")
        if labels["drugs"] >= 0.5:
            reasons.append("обнаружены признаки запрещённых веществ")
        if labels["toxicity"] >= 0.4:
            reasons.append("обнаружены признаки токсичного контента")

        risk_score = round(max(labels.values()), 4)

        if labels["drugs"] >= 0.5 or labels["fraud"] >= 0.8 or risk_score >= 0.85:
            decision = "reject"
        elif risk_score >= 0.4:
            decision = "review"
        else:
            decision = "allow"

        return {
            "decision": decision,
            "risk_score": risk_score,
            "labels": labels,
            "reasons": reasons,
        }

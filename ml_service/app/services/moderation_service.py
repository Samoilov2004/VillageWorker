import re
from typing import Dict, List


class ModerationService:
    """
    Временная rule-based пре-модерация.
    Потом сюда что-то лучше добавлю
    """

    SPAM_PATTERNS = [
        r"быстрые деньги",
        r"доход \d+",
        r"без опыта",
        r"срочно",
        r"!!!",
        r"100% доход",
        r"легкий заработок",
    ]

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

    def _score_patterns(self, text: str, patterns: List[str], weight: float = 0.3) -> float:
        score = 0.0
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += weight
        return min(score, 1.0)

    def _caps_score(self, text: str) -> float:
        letters = [ch for ch in text if ch.isalpha()]
        if not letters:
            return 0.0
        upper = sum(1 for ch in letters if ch.isupper())
        ratio = upper / len(letters)
        return 0.6 if ratio > 0.6 and len(letters) > 20 else 0.0

    def _repetition_score(self, text: str) -> float:
        if "!!!" in text or "???" in text:
            return 0.3
        return 0.0

    def check(self, title: str, description: str) -> dict:
        text = f"{title}\n{description}".strip()

        labels: Dict[str, float] = {
            "spam": 0.0,
            "fraud": 0.0,
            "drugs": 0.0,
            "toxicity": 0.0,
        }

        labels["spam"] += self._score_patterns(text, self.SPAM_PATTERNS, 0.2)
        labels["spam"] += self._caps_score(text)
        labels["spam"] += self._repetition_score(text)

        labels["fraud"] += self._score_patterns(text, self.FRAUD_PATTERNS, 0.35)
        if self.URL_PATTERN.search(text):
            labels["fraud"] = min(labels["fraud"] + 0.15, 1.0)

        labels["drugs"] += self._score_patterns(text, self.DRUG_PATTERNS, 0.5)
        labels["toxicity"] += self._score_patterns(text, self.TOXIC_PATTERNS, 0.4)

        labels = {k: round(min(v, 1.0), 4) for k, v in labels.items()}

        reasons = []
        if labels["spam"] >= 0.4:
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

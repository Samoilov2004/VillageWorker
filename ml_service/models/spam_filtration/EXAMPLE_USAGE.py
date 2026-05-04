import joblib
import re
from scipy.sparse import hstack

import warnings

warnings.filterwarnings("ignore")

def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"http\S+|www\S+", " URL ", text)
    text = re.sub(r"@\w+", " USERNAME ", text)
    text = re.sub(r"\+?\d[\d\-\(\) ]{7,}\d", " PHONE ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

word_tfidf_loaded = joblib.load("word_tfidf.pkl")
char_tfidf_loaded = joblib.load("char_tfidf.pkl")
svm_loaded = joblib.load("linear_svc_spam.pkl")

sample_texts = [
    "Требуется продавец в продуктовый магазин, официальное оформление.",
    "Зарабатывай 100000 в день без опыта, пиши в Telegram прямо сейчас!"
]

sample_texts_clean = [clean_text(x) for x in sample_texts]

X_word_sample = word_tfidf_loaded.transform(sample_texts_clean)
X_char_sample = char_tfidf_loaded.transform(sample_texts_clean)
X_sample_combined = hstack([X_word_sample, X_char_sample])

preds_svm = svm_loaded.predict(X_sample_combined)

for text, pred in zip(sample_texts, preds_svm):
    print("=" * 80)
    print("TEXT:", text)
    print("PRED:", pred)
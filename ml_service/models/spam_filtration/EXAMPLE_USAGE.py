from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import re
import numpy as np

import warnings

warnings.filterwarnings("ignore")

rubert_tokenizer = AutoTokenizer.from_pretrained("./rubert_spam_model_best")
rubert_model = AutoModelForSequenceClassification.from_pretrained("./rubert_spam_model_best")
rubert_model.eval()

device = "cuda" if torch.cuda.is_available() else "cpu"
rubert_model.to(device)

sample_texts = [
    "Требуется продавец в продуктовый магазин, официальное оформление.",
    "Зарабатывай 100000 в день без опыта, пиши в Telegram прямо сейчас!"
]

def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"http\S+|www\S+", " URL ", text)
    text = re.sub(r"@\w+", " USERNAME ", text)
    text = re.sub(r"\+?\d[\d\-\(\) ]{7,}\d", " PHONE ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

sample_texts_clean = [clean_text(x) for x in sample_texts]

def predict_rubert(texts, tokenizer, model, device="cpu", max_length=128):
    inputs = tokenizer(
        texts,
        truncation=True,
        padding=True,
        max_length=max_length,
        return_tensors="pt"
    )

    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1).cpu().numpy()
        preds = np.argmax(probs, axis=1)

    return preds, probs[:, 1]

preds_rubert, probs_rubert = predict_rubert(
    sample_texts_clean,
    rubert_tokenizer,
    rubert_model,
    device=device
)

for text, pred, prob in zip(sample_texts, preds_rubert, probs_rubert):
    print("=" * 80)
    print("TEXT:", text)
    print("PRED:", int(pred), "SPAM_PROBA:", round(float(prob), 4))
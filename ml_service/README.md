# ML Service

ML-микросервис для платформы цифрового хаба сельских территорий.  
Запускается отдельно от backend'а и предоставляет HTTP API для поиска, рекомендаций, модерации и классификации вакансий.

---

## Ноутбуки обучения

- [label-guess — выбор модели и метрики](https://www.kaggle.com/code/samoilovmikhail/label-guess-model-training)

---

## Модели

Файлы находятся в `ml_service/models/`. SBERT-энкодер (`paraphrase-multilingual-MiniLM-L12-v2`) загружается один раз и используется совместно поиском и рекомендациями.

| Папка | Артефакты | Что делает |
|---|---|---|
| `spam_filtration/` | `word_tfidf.pkl`, `char_tfidf.pkl`, `linear_svc_spam.pkl` | Классификация спама (LinearSVC + TF-IDF) |
| `relevant_search/` | `search_bm25.pkl`, `search_sbert_embeddings.npy`, конфиги, метаданные | Гибридный поиск: BM25 + SBERT (α=0.5) |
| `vacancy_recomendation/` | `recommend_sbert_geo_embeddings.npy`, конфиг, метаданные | SBERT + гео-бонус Haversine |
| `label_guess/` | `job_label_model.joblib` | Предсказание категории вакансии |

---

## API

Все ML-методы публикуются под префиксом `/api/ml`.

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/index/upsert` | Добавить / обновить сущности во внутреннем индексе |
| `POST` | `/index/delete` | Удалить сущности из индекса |
| `GET`  | `/index/stats`  | Количество сущностей по типам |
| `POST` | `/search`       | Поиск (hybrid BM25 + SBERT) по предобученному индексу |
| `POST` | `/search/rerank`| Переранжировать готовый список по запросу |
| `POST` | `/recommend/similar` | Похожие вакансии: по ID из индекса или по произвольному item |
| `POST` | `/recommend/match`   | Подбор вакансий под резюме (SBERT + гео) |
| `POST` | `/moderation/check`  | Пре-модерация: spam / fraud / drugs / toxicity |
| `POST` | `/label/predict`     | Предсказание категории вакансии по заголовку и описанию |

Служебные (без префикса):

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/health` | Liveness-check |
| `GET` | `/ready`  | Readiness-check: статус моделей и индекса |

Интерактивная документация после запуска: `http://127.0.0.1:8001/docs`

---

## Запуск

```bash
python3 -m venv .mlvenv
source .mlvenv/bin/activate
pip install -r ml_service/requirements.txt

uvicorn ml_service.app.main:app --reload --host 127.0.0.1 --port 8001
```

Первый запуск автоматически скачивает SBERT (~470 MB). Все модели загружаются при старте.

Переменные окружения (опционально):

| Переменная | По умолчанию | Описание |
|---|---|---|
| `ML_MODELS_DIR` | `ml_service/models/` | Путь к папке с моделями |
| `ML_DATA_DIR`   | `ml_service/data/`   | Путь к данным и индексам |
| `ML_HOST`       | `127.0.0.1`          | Хост |
| `ML_PORT`       | `8000`               | Порт |
| `ML_API_PREFIX` | `/api/ml`            | Префикс API |

---

## Тесты

```bash
pytest ml_service/tests -v
```

Фикстура `client` имеет `scope="session"` — модели загружаются один раз для всего прогона.  
При первом запуске тестов SBERT скачивается автоматически.

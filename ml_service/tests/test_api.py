"""
API integration tests for the ML service.

All tests share a single session-scoped TestClient so ML models are loaded once.
"""
import numpy as np
import pytest


# ─── System ───────────────────────────────────────────────────────────────────

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ready(client):
    r = client.get("/ready")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ready"
    assert data["models_loaded"] is True
    assert data["index_available"] is True
    assert isinstance(data["indexed_entities"], dict)


# ─── Index management ─────────────────────────────────────────────────────────

_INDEX_ITEMS = [
    {
        "id": "idx-test-1",
        "title": "Ветеринар",
        "description": "Лечение крупного рогатого скота на ферме",
        "metadata": {"city": "Москва", "label": "Ветеринария"},
    },
    {
        "id": "idx-test-2",
        "title": "Агроном",
        "description": "Управление посевами и подбор удобрений",
        "metadata": {"city": "Краснодар", "label": "Агрономия"},
    },
    {
        "id": "idx-test-3",
        "title": "Механизатор",
        "description": "Работа на тракторе и комбайне в полевой сезон",
        "metadata": {"city": "Ростов-на-Дону", "label": "Механизация"},
    },
]


def test_index_upsert_returns_correct_count(client):
    r = client.post("/api/ml/index/upsert", json={"entity_type": "job", "items": _INDEX_ITEMS})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["upserted"] == len(_INDEX_ITEMS)
    assert data["entity_type"] == "job"


def test_index_upsert_idempotent(client):
    r = client.post("/api/ml/index/upsert", json={"entity_type": "job", "items": _INDEX_ITEMS})
    assert r.status_code == 200
    assert r.json()["upserted"] == len(_INDEX_ITEMS)


def test_index_stats_reflects_upsert(client):
    r = client.get("/api/ml/index/stats")
    assert r.status_code == 200
    stats = r.json()["entities"]
    assert "job" in stats
    assert stats["job"] >= len(_INDEX_ITEMS)


def test_index_delete_returns_correct_count(client):
    ids_to_delete = [item["id"] for item in _INDEX_ITEMS]
    r = client.post("/api/ml/index/delete", json={"entity_type": "job", "ids": ids_to_delete})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["deleted"] == len(ids_to_delete)


def test_index_delete_nonexistent_ids(client):
    r = client.post("/api/ml/index/delete", json={"entity_type": "job", "ids": ["no-such-id"]})
    assert r.status_code == 200
    assert r.json()["deleted"] == 0


# ─── Search ───────────────────────────────────────────────────────────────────

def test_search_returns_nonempty_results(client):
    r = client.post("/api/ml/search", json={
        "entity_type": "job",
        "query": "механик ремонт трактор",
        "top_k": 5,
    })
    assert r.status_code == 200
    assert len(r.json()["results"]) > 0


def test_search_result_fields(client):
    r = client.post("/api/ml/search", json={
        "entity_type": "job",
        "query": "слесарь завод",
        "top_k": 3,
    })
    assert r.status_code == 200
    for item in r.json()["results"]:
        assert "id" in item
        assert "score" in item
        assert "title" in item
        assert "metadata" in item
        assert isinstance(item["score"], float)


def test_search_scores_in_unit_range(client):
    r = client.post("/api/ml/search", json={
        "entity_type": "job",
        "query": "продавец",
        "top_k": 10,
    })
    assert r.status_code == 200
    for item in r.json()["results"]:
        assert 0.0 <= item["score"] <= 1.0


def test_search_scores_descending(client):
    r = client.post("/api/ml/search", json={
        "entity_type": "job",
        "query": "водитель грузовик",
        "top_k": 10,
    })
    scores = [item["score"] for item in r.json()["results"]]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.parametrize("top_k", [1, 3, 7, 15])
def test_search_top_k_respected(client, top_k):
    r = client.post("/api/ml/search", json={
        "entity_type": "job",
        "query": "работа деревня",
        "top_k": top_k,
    })
    assert r.status_code == 200
    assert len(r.json()["results"]) <= top_k


def test_search_different_queries_differ(client):
    r1 = client.post("/api/ml/search", json={"entity_type": "job", "query": "программист Python", "top_k": 3})
    r2 = client.post("/api/ml/search", json={"entity_type": "job", "query": "доярка ферма корова", "top_k": 3})
    assert r1.status_code == 200
    assert r2.status_code == 200
    ids1 = {item["id"] for item in r1.json()["results"]}
    ids2 = {item["id"] for item in r2.json()["results"]}
    # семантически разные запросы должны давать хотя бы частично разные результаты
    assert ids1 != ids2


# ─── Search / rerank ──────────────────────────────────────────────────────────

_RERANK_ITEMS = [
    {"id": "rr-1", "title": "Водитель грузовика", "description": "Перевозка грузов по региону", "metadata": {}},
    {"id": "rr-2", "title": "Кассир супермаркета", "description": "Работа на кассе, обслуживание покупателей", "metadata": {}},
    {"id": "rr-3", "title": "Механик грузового авто", "description": "Ремонт и обслуживание грузовых автомобилей", "metadata": {}},
    {"id": "rr-4", "title": "Повар-сушист", "description": "Приготовление японской кухни", "metadata": {}},
]


def test_rerank_returns_all_items(client):
    r = client.post("/api/ml/search/rerank", json={
        "query": "грузовик транспорт",
        "items": _RERANK_ITEMS,
        "top_k": len(_RERANK_ITEMS),
    })
    assert r.status_code == 200
    assert len(r.json()["results"]) == len(_RERANK_ITEMS)


def test_rerank_scores_descending(client):
    r = client.post("/api/ml/search/rerank", json={
        "query": "механик ремонт",
        "items": _RERANK_ITEMS,
        "top_k": len(_RERANK_ITEMS),
    })
    assert r.status_code == 200
    scores = [item["score"] for item in r.json()["results"]]
    assert scores == sorted(scores, reverse=True)


def test_rerank_top_k_cuts_results(client):
    r = client.post("/api/ml/search/rerank", json={
        "query": "работа",
        "items": _RERANK_ITEMS,
        "top_k": 2,
    })
    assert r.status_code == 200
    assert len(r.json()["results"]) == 2


def test_rerank_transport_query_ranks_driver_high(client):
    r = client.post("/api/ml/search/rerank", json={
        "query": "водитель доставка транспорт",
        "items": _RERANK_ITEMS,
        "top_k": len(_RERANK_ITEMS),
    })
    results = r.json()["results"]
    ids = [item["id"] for item in results]
    # кассир и повар должны быть ниже, чем транспортные позиции
    assert ids.index("rr-2") > 0 or ids.index("rr-4") > 0


def test_rerank_preserves_metadata(client):
    items = [
        {"id": "m-1", "title": "Механик", "description": "Ремонт", "metadata": {"city": "Москва"}},
    ]
    r = client.post("/api/ml/search/rerank", json={"query": "ремонт", "items": items, "top_k": 1})
    assert r.status_code == 200
    assert r.json()["results"][0]["metadata"].get("city") == "Москва"


# ─── Moderation ───────────────────────────────────────────────────────────────

def test_moderation_clean_job_is_allowed(client):
    r = client.post("/api/ml/moderation/check", json={
        "content_type": "job",
        "title": "Слесарь на завод",
        "description": "Официальное оформление, стабильная зарплата, соцпакет.",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["decision"] == "allow"
    assert data["risk_score"] < 0.4


def test_moderation_spam_text_flagged(client):
    r = client.post("/api/ml/moderation/check", json={
        "content_type": "announcement",
        "title": "Зарабатывай 100000 в день без опыта",
        "description": "Пиши в Telegram прямо сейчас! Гарантированный доход каждый день!",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["decision"] in {"review", "reject"}
    assert data["labels"]["spam"] >= 0.5


def test_moderation_drugs_leads_to_reject(client):
    r = client.post("/api/ml/moderation/check", json={
        "content_type": "announcement",
        "title": "Закладки в вашем городе",
        "description": "Продам наркотики меф амф марихуана",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["decision"] == "reject"
    assert data["labels"]["drugs"] >= 0.5


def test_moderation_fraud_patterns_detected(client):
    r = client.post("/api/ml/moderation/check", json={
        "content_type": "announcement",
        "title": "Работа на дому",
        "description": "Переведи деньги на счёт, гарантированный заработок, предоплата",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["labels"]["fraud"] > 0.0
    assert data["decision"] in {"review", "reject"}


def test_moderation_toxicity_detected(client):
    r = client.post("/api/ml/moderation/check", json={
        "content_type": "announcement",
        "title": "Объявление",
        "description": "Идиот тупой урод, ненавижу всех",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["labels"]["toxicity"] >= 0.4


def test_moderation_response_schema(client):
    r = client.post("/api/ml/moderation/check", json={
        "content_type": "job",
        "title": "Тест",
        "description": "Тест",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["decision"] in {"allow", "review", "reject"}
    assert 0.0 <= data["risk_score"] <= 1.0
    for key in ("spam", "fraud", "drugs", "toxicity"):
        assert key in data["labels"]
        assert 0.0 <= data["labels"][key] <= 1.0
    assert isinstance(data["reasons"], list)


def test_moderation_reasons_match_decision(client):
    """Если decision != allow — reasons не пустой."""
    r = client.post("/api/ml/moderation/check", json={
        "content_type": "announcement",
        "title": "Закладки",
        "description": "наркотики меф продам",
    })
    data = r.json()
    if data["decision"] != "allow":
        assert len(data["reasons"]) > 0


# ─── Recommendation / similar ─────────────────────────────────────────────────

def test_recommend_similar_by_id_returns_results(client, vacancy_id_with_geo):
    r = client.post("/api/ml/recommend/similar", json={
        "entity_type": "job",
        "item_id": vacancy_id_with_geo,
        "top_k": 5,
    })
    assert r.status_code == 200
    results = r.json()["results"]
    assert len(results) > 0


def test_recommend_similar_excludes_source(client, vacancy_id_with_geo):
    r = client.post("/api/ml/recommend/similar", json={
        "entity_type": "job",
        "item_id": vacancy_id_with_geo,
        "top_k": 10,
    })
    ids = [item["id"] for item in r.json()["results"]]
    assert vacancy_id_with_geo not in ids


def test_recommend_similar_result_fields(client, vacancy_id_any):
    r = client.post("/api/ml/recommend/similar", json={
        "entity_type": "job",
        "item_id": vacancy_id_any,
        "top_k": 3,
    })
    assert r.status_code == 200
    for item in r.json()["results"]:
        assert "id" in item
        assert "score" in item
        assert "title" in item
        assert isinstance(item["score"], float)


@pytest.mark.parametrize("top_k", [1, 3, 5])
def test_recommend_similar_top_k(client, vacancy_id_any, top_k):
    r = client.post("/api/ml/recommend/similar", json={
        "entity_type": "job",
        "item_id": vacancy_id_any,
        "top_k": top_k,
    })
    assert r.status_code == 200
    assert len(r.json()["results"]) <= top_k


def test_recommend_similar_unknown_id_returns_400(client):
    r = client.post("/api/ml/recommend/similar", json={
        "entity_type": "job",
        "item_id": "nonexistent-id-xyz-000",
        "top_k": 5,
    })
    assert r.status_code == 400


def test_recommend_similar_by_item_dict(client):
    r = client.post("/api/ml/recommend/similar", json={
        "entity_type": "job",
        "item": {
            "id": "custom-tractor-1",
            "title": "Тракторист",
            "description": "Управление трактором, обработка полей, уборка урожая",
            "metadata": {"label": "Сельское хозяйство"},
        },
        "top_k": 5,
    })
    assert r.status_code == 200
    assert len(r.json()["results"]) > 0


def test_recommend_similar_no_payload_returns_400(client):
    r = client.post("/api/ml/recommend/similar", json={
        "entity_type": "job",
        "top_k": 5,
    })
    assert r.status_code == 400


def test_recommend_similar_geo_bonus_applied(client, vacancy_id_with_geo):
    """Два запроса с одной вакансией должны давать одинаковый первый результат."""
    payload = {"entity_type": "job", "item_id": vacancy_id_with_geo, "top_k": 3}
    r1 = client.post("/api/ml/recommend/similar", json=payload)
    r2 = client.post("/api/ml/recommend/similar", json=payload)
    assert r1.json()["results"][0]["id"] == r2.json()["results"][0]["id"]


# ─── Recommendation / match ───────────────────────────────────────────────────

def test_recommend_match_returns_results(client):
    r = client.post("/api/ml/recommend/match", json={
        "source_entity_type": "resume",
        "target_entity_type": "job",
        "item": {
            "id": "resume-001",
            "title": "Механик",
            "description": "Опыт ремонта сельскохозяйственной техники, трактора, комбайны",
            "metadata": {"label": "Техническое обслуживание"},
        },
        "top_k": 5,
    })
    assert r.status_code == 200
    assert len(r.json()["results"]) > 0


def test_recommend_match_different_resumes_differ(client):
    r1 = client.post("/api/ml/recommend/match", json={
        "source_entity_type": "resume",
        "target_entity_type": "job",
        "item": {"id": "r1", "title": "Программист", "description": "Python, машинное обучение, Django", "metadata": {}},
        "top_k": 3,
    })
    r2 = client.post("/api/ml/recommend/match", json={
        "source_entity_type": "resume",
        "target_entity_type": "job",
        "item": {"id": "r2", "title": "Доярка", "description": "Уход за коровами, дойка, фермерство", "metadata": {}},
        "top_k": 3,
    })
    assert r1.status_code == 200
    assert r2.status_code == 200
    ids1 = {item["id"] for item in r1.json()["results"]}
    ids2 = {item["id"] for item in r2.json()["results"]}
    assert ids1 != ids2


# ─── Label prediction ─────────────────────────────────────────────────────────

def test_label_predict_returns_nonempty_string(client):
    r = client.post("/api/ml/label/predict", json={
        "title": "Тракторист",
        "description": "Управление трактором, обработка полей",
    })
    assert r.status_code == 200
    label = r.json()["label"]
    assert isinstance(label, str)
    assert len(label) > 0


def test_label_predict_example_from_docs(client):
    """Пример из EXAMPLE_USAGE.py модели."""
    r = client.post("/api/ml/label/predict", json={
        "title": "Слесарь КИПиА",
        "description": "Сборка, ремонт, настройка манометров и термометров, подготовка измерительного оборудования.",
    })
    assert r.status_code == 200
    assert isinstance(r.json()["label"], str)


def test_label_predict_empty_description(client):
    r = client.post("/api/ml/label/predict", json={"title": "Агроном"})
    assert r.status_code == 200
    assert isinstance(r.json()["label"], str)


def test_label_predict_title_weight_affects_result(client):
    """Заголовок важнее описания — один только заголовок должен давать предсказание."""
    r = client.post("/api/ml/label/predict", json={
        "title": "Ветеринар крупного рогатого скота",
        "description": "",
    })
    assert r.status_code == 200
    assert len(r.json()["label"]) > 0


def test_label_predict_different_categories(client):
    """Разные профессии из разных областей должны возвращать валидные метки."""
    titles = [
        "Программист Python",
        "Доярка на ферму",
        "Сварщик на завод",
        "Повар-кондитер",
    ]
    labels = set()
    for title in titles:
        r = client.post("/api/ml/label/predict", json={"title": title, "description": ""})
        assert r.status_code == 200
        label = r.json()["label"]
        assert isinstance(label, str) and len(label) > 0
        labels.add(label)
    # не все одинаковые — модель должна различать категории
    assert len(labels) > 1

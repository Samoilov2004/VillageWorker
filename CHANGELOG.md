# Changelog

## [2026-05-09]

### Backend
- `serialize_job_card` теперь возвращает `latitude` и `longitude` вакансии
- `GET /api/jobs` принимает фильтры: `label[]`, `experience[]`, `salary_min`
- Фильтры применяются и к SQL-browse, и к SQL-search, и к ML-результатам

### Frontend (job_search.html)
- Фильтры реально работают: категория (19 штук), опыт работы, зарплата от
- Кнопка «Сбросить» очищает все фильтры и перезагружает список
- Карта: кастомные цветные маркеры по категории + кластеризация (markercluster)
- Карта: тёмные попапы с инфо о вакансии и кнопкой «Подробнее»
- Карта: легенда категорий в правом нижнем углу
- Карта: пунктирный круг радиуса фильтрует маркеры по дистанции
- Баннер определения города: геолокация → Nominatim → «Ваш город — X?»
- Баннер: «Да, верно» сохраняет в localStorage, «Изменить» → поиск по названию
- Карта центрируется на определённом городе пользователя

### ML-сервис
- Добавлен `faiss-cpu` в `ml_service/requirements.txt`
- Новый класс `FaissIndex` (`app/services/faiss_index.py`) — обёртка над `IndexFlatIP`
- `SearchService`: SBERT-часть гибридного поиска переведена с `np.dot` на `FaissIndex.search_all`
- `RecommendationService`: `np.dot + np.argsort` заменены на `FaissIndex.search_top_k(candidate_k)` — heap-отбор вместо полной сортировки
- Для перехода на приближённый поиск при росте базы достаточно заменить `IndexFlatIP` на `IndexIVFFlat` в одном месте

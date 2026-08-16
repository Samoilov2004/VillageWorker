# ЭТС — Электронная Трудовая Система

> Веб-платформа для поиска работы в сельских территориях России

![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat&logo=sqlite&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3-06B6D4?style=flat&logo=tailwindcss&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.6-F7931E?style=flat&logo=scikitlearn&logoColor=white)
![FAISS](https://img.shields.io/badge/FAISS-cpu-00599C?style=flat&logo=meta&logoColor=white)
![Leaflet](https://img.shields.io/badge/Leaflet.js-1.9-199900?style=flat&logo=leaflet&logoColor=white)

---

## Быстрый старт

Нужно **3 терминала** — backend, ML-сервис и frontend. Если не получается на одном из терминалов запуститься и ловите ошибки, это решается через ChatGPT в 2 секунды!

### 1. Backend (порт 8000)

```bash
# macOS / Linux
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

```powershell
# Windows
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. ML-сервис (порт 8001)

```bash
# macOS / Linux
python3 -m venv .mlvenv && source .mlvenv/bin/activate
pip install -r ml_service/requirements.txt
uvicorn ml_service.app.main:app --reload --host 127.0.0.1 --port 8001
```

```powershell
# Windows
python -m venv .mlvenv
.\.mlvenv\Scripts\Activate.ps1
pip install -r ml_service\requirements.txt
uvicorn ml_service.app.main:app --reload --host 127.0.0.1 --port 8001
```

### 3. Frontend (порт 5500)

```bash
# macOS / Linux
python3 -m http.server 5500 --directory frontend
```

```powershell
# Windows
python -m http.server 5500 --directory frontend
```

Открыть в браузере: **http://127.0.0.1:5500/main.html**

---

## Проверка работоспособности

| Сервис | URL |
|--------|-----|
| Backend health | http://127.0.0.1:8000/health |
| Backend API docs | http://127.0.0.1:8000/docs |
| ML-сервис health | http://127.0.0.1:8001/health |
| Главная | http://127.0.0.1:5500/main.html |
| Поиск вакансий | http://127.0.0.1:5500/html/job_search.html |

---

## Git LFS

База данных `database/job_ads.db` хранится через Git LFS. После клонирования:

```bash
git lfs install && git lfs pull
```

---

## Требования

- Python 3.13+
- Git LFS

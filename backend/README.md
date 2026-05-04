# VillageWorker

MVP веб-платформы для поиска вакансий и поддержки трудоустройства в сельских территориях.

## Что уже реализовано

- локальный frontend на HTML/CSS/JS
- backend на FastAPI
- SQLite-база вакансий
- поиск вакансий по запросу
- просмотр вакансии в модальном окне
- похожие вакансии через endpoint `/api/jobs/{id}/similar`
- fallback-рекомендации из базы, если ML не вернул результаты
- базовая навигация между страницами:
  - `main.html`
  - `main_log.html`
  - `job_search.html`
  - `profile.html`
  - `log_in.html`
  - `create.html`

## Структура проекта

```text
VillageWorker/
├── backend/
│   ├── __init__.py
│   ├── requirements.txt
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── db.py
│       ├── utils.py
│       └── routes/
│           ├── __init__.py
│           └── jobs.py
│
├── database/
│   └── job_ads.db
│
├── frontend/
│   ├── main.html
│   ├── main_log.html
│   ├── main.css
│   ├── main_log.css
│   ├── css/
│   ├── js/
│   ├── files/
│   └── html/
│       ├── job_search.html
│       ├── log_in.html
│       ├── profile.html
│       └── create.html
│
├── ml_service/
│   ├── requirements.txt
│   └── ...
│
├── .venv/
├── .mlvenv/
└── README.md
```

## Важный момент про Git LFS

В проекте используются большие файлы, включая SQLite-базу `database/job_ads.db`.

Если после клонирования файл базы слишком маленький, значит реальные данные не подтянулись через Git LFS.

Используйте:

```bash
git lfs install
git clone <URL_репозитория>
cd VillageWorker
git lfs pull
```

## Требования

- Python 3.13+  
- Git  
- Git LFS  

---

## Запуск на Windows

### 1. Backend

```powershell
cd C:\VillageWorker
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Проверка:

```text
http://127.0.0.1:8000/health
```

### 2. ML-service

```powershell
cd C:\VillageWorker
python -m venv .mlvenv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.mlvenv\Scripts\Activate.ps1
pip install -r ml_service\requirements.txt
uvicorn ml_service.app.main:app --reload --host 127.0.0.1 --port 8001
```

Проверка:

```text
http://127.0.0.1:8001/health
```

### 3. Frontend

```powershell
cd C:\VillageWorker
python -m http.server 5500 --directory frontend
```

Открыть:

```text
http://127.0.0.1:5500/main.html
http://127.0.0.1:5500/main_log.html
http://127.0.0.1:5500/html/job_search.html
```

---

## Запуск на macOS

### 1. Backend

```bash
cd ~/VillageWorker
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. ML-service

```bash
cd ~/VillageWorker
python3 -m venv .mlvenv
source .mlvenv/bin/activate
pip install -r ml_service/requirements.txt
uvicorn ml_service.app.main:app --reload --host 127.0.0.1 --port 8001
```

### 3. Frontend

```bash
cd ~/VillageWorker
python3 -m http.server 5500 --directory frontend
```

Открыть:

```text
http://127.0.0.1:5500/main.html
http://127.0.0.1:5500/main_log.html
http://127.0.0.1:5500/html/job_search.html
```

---

## Что должно быть запущено одновременно

Для полной работы проекта нужны 3 процесса:

1. Backend — `127.0.0.1:8000`
2. ML-service — `127.0.0.1:8001`
3. Frontend — `127.0.0.1:5500`

---

## Полезные URL

### Backend
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/api/jobs`
- `http://127.0.0.1:8000/api/jobs?q=грузчик`
- `http://127.0.0.1:8000/api/jobs/37744881`
- `http://127.0.0.1:8000/api/jobs/37744881/similar`

### ML-service
- `http://127.0.0.1:8001/health`
- `http://127.0.0.1:8001/docs`

### Frontend
- `http://127.0.0.1:5500/main.html`
- `http://127.0.0.1:5500/main_log.html`
- `http://127.0.0.1:5500/html/job_search.html`
- `http://127.0.0.1:5500/html/profile.html`
- `http://127.0.0.1:5500/html/log_in.html`
- `http://127.0.0.1:5500/html/create.html`

---

## Быстрая проверка

1. Открыть `main.html`
2. Перейти на `job_search.html`
3. Убедиться, что вакансии загружаются
4. Ввести запрос `грузчик`
5. Нажать **Найти**
6. Нажать **Подробнее**
7. Проверить модальное окно
8. Проверить блок **Похожие вакансии**

---

## Если что-то не работает

### База не открывается
Скорее всего не подтянулся `job_ads.db` через Git LFS.

Решение:

```bash
git lfs install
git lfs pull
```

### `ModuleNotFoundError`
Не установлены зависимости.

Решение:

```bash
pip install -r backend/requirements.txt
pip install -r ml_service/requirements.txt
```

### Frontend открылся, но вакансии не грузятся
Проверь, запущен ли backend:

```text
http://127.0.0.1:8000/health
```

### Не работают похожие вакансии
Проверь:

```text
http://127.0.0.1:8001/health
http://127.0.0.1:8000/api/jobs/37744881/similar
```

---

## Кратко

Нужно открыть 3 терминала:

### Backend

Windows:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

macOS:

```bash
source .venv/bin/activate
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### ML-service

Windows:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.mlvenv\Scripts\Activate.ps1
uvicorn ml_service.app.main:app --reload --host 127.0.0.1 --port 8001
```

macOS:

```bash
source .mlvenv/bin/activate
uvicorn ml_service.app.main:app --reload --host 127.0.0.1 --port 8001
```

### Frontend

Windows:

```powershell
python -m http.server 5500 --directory frontend
```

macOS:

```bash
python3 -m http.server 5500 --directory frontend
```

После этого открыть:

```text
http://127.0.0.1:5500/main.html
```

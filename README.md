# VillageWorker

Система папок и как идет разработка. Пока будем локально тестировать и без никакого докера. 

```
VillageWorker/
│
├── frontend/                  # Фронтенд (React/Vue)
│   ├── index.html
│   ├── src/
│   └── package.json          # npm start - запуск фронтенда
│
├── backend/                   # Бэкенд (Node.js/Express)
│   ├── index.js
│   └── package.json          # npm start - запуск бэкенда
│
├── ml-service/                # ML-сервис (Python/FastAPI) - Samoilov2004
│   ├── main.py
│   └── requirements.txt      # pip install -r requirements.txt
│
├── databases/                
│   ├── main-db.sql           # Скрипт создания таблиц
│   └── ml-data.json          # Данные для ML (будет допиливаться)
│
├── scripts/                   # Вспомогательные скрипты
│   ├── install-deps.bat      # Установка всех зависимостей (Windows)
│   ├── install-deps.sh       # Установка всех зависимостей (Mac/Linux)
│   ├── start-project.bat     # Запуск всего проекта (Windows)
│   └── start-project.sh      # Запуск всего проекта (Mac/Linux)
│
├── README.md
└── .env.example
```

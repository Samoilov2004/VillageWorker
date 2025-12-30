# VillageWorker

Система папок и как идет разработка. Пока будем локально тестировать и без никакого докера. 

```
VillageWorker/
│
├── frontend/                  # Фронтенд (React/Vue/напишите че будет)
│   ├── index.html
│   ├── src/
│   └── package.json          # npm start - запуск фронтенда
│
├── backend/                   # Бэкенд (Node.js/Express/напишите че будет)
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
├── start-project.bat          # Скрипт запуска ВСЕГО (для Windows)
├── start-project.sh           # Скрипт запуска ВСЕГО (для Mac/Linux)
├── README.md
└── .env.example
```

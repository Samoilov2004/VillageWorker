# VillageWorker

Система папок и как идет разработка. Пока будем локально тестировать и без никакого докера.

```
VillageWorker/
│
├── frontend/ (В работе)
│   ├── index.html
│   ├── src/
│   └── package.json
│
├── backend/  (В работе)
│   ├── index.js
│   └── package.json
│
├── ml-service/ (В работе)
│   ├── main.py
│   └── requirements.txt
│
├── databases/           
│   ├── jobs_ads.csv - изначальный датасет с прикрученными фичами
│   ├── jobs_ads.db  - SQLite версия
│   └── mini_jobs.csv  - версия на 100 строк, для тестирования
│
├── scripts/   (В работе)
│   ├── install-deps.bat      # Установка всех зависимостей (Windows)
│   ├── install-deps.sh       # Установка всех зависимостей (Mac/Linux)
│   ├── start-project.bat     # Запуск всего проекта (Windows)
│   └── start-project.sh      # Запуск всего проекта (Mac/Linux)
│
├── other/
│   ├── pics/
│   └── requirements.txt
│
├── README.md
└── .env.example
```

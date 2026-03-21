# VillageWorker

Сайт - описание позже.

# Гайд по запуску проекта
Сайт реализован локально, так что распишем подряд как поднять каждый компонент.

## ml_service
Написан на Python 3.14 и нужны зависимости, подготовим включение микросервиса. Из корня проекта необходимо выполнить
```bash
python3 -m venv .mlvenv
source .mlvenv/bin/activate
pip install -r ml_service/requirements.txt

uvicorn ml_service.app.main:app --reload --host 127.0.0.1 --port 8001
```

После запуска будут доступны:

- Swagger UI: http://127.0.0.1:8001/docs
- ReDoc: http://127.0.0.1:8001/redoc
- Health-check: http://127.0.0.1:8001/health

Из корня репозитория запустить тесты, если что-то не так, то плакать
```bash
pytest ml_service/tests -v
```

Запустить тесты проекта
```bash
pytest ml_service/tests -v
```

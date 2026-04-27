# Сервис для проведения квизов (Django)

## Описание
Онлайн-платформа для создания и проведения викторин с синхронным участием.

## Стек технологий
- **Backend:** Django 4.2 + Django REST Framework
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **WebSocket:** Django Channels
- **Frontend:** HTML5 + Bootstrap 5 + JavaScript

## Требования
- Python 3.10+
- PostgreSQL 14+
- Redis 6+
- Gunicorn/Daphne
- Nginx

## Генерация документации

```bash
cd docs
make html
# Документация будет в docs/_build/html/index.html

## Установка
```bash

# Клонировать репозиторий
git clone <repository-url>
cd quiz-service

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Скопировать .env.example
cp .env.example .env
# Отредактировать .env с production-значениями

# Применить миграции
python manage.py migrate

# Собрать статику
python manage.py collectstatic --noinput

# Запустить через Daphne (для WebSocket)
daphne -b 0.0.0.0 -p 8000 sapere_aude.asgi:application
```
## WebSocket API

Для интерактивного взаимодействия с викториной в реальном времени используется протокол WebSocket.

### Эндпоинт
ws://<host>:8000/ws/quiz/<session_code>/
- `<session_code>` – уникальный код сессии (строка, например `abc123`).

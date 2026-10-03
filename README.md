# Shift Tracker

Telegram-сообщения со сменами сохраняются в PostgreSQL, фото — в MinIO. Модератор и администратор работают через веб-интерфейс: сводка, проверка, сообщения, смены и справочники.

## Архитектура

Telegram → backend → PostgreSQL и MinIO → frontend.

Браузер открывает frontend. Запросы к `/api` nginx отправляет в backend. Ссылки на фото подписываются адресом MinIO, который открывается с машины пользователя.

## Stack

- Backend: Python, FastAPI, SQLAlchemy, Alembic
- Frontend: React, TypeScript, Vite
- Infrastructure: PostgreSQL, MinIO, Docker Compose

## Local development

Поднять только базу и хранилище:

```bash
docker compose up -d postgres minio minio-init
```

PostgreSQL снаружи доступен на `localhost:5433`. MinIO API — `localhost:9000`, консоль — `localhost:9001`.

Backend на хосте:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

В корневом `.env` для этого режима укажите `DATABASE_URL` на `localhost:5433` и `S3_ENDPOINT_URL=http://localhost:9000`. Если фото должны открываться в браузере с той же машины, `S3_PUBLIC_ENDPOINT_URL` тоже должен быть `http://localhost:9000`.

Frontend на хосте:

```bash
cd frontend
npm install
npm run dev
```

Интерфейс разработки: http://127.0.0.1:5173. В `frontend/.env` задайте `VITE_API_BASE_URL=http://127.0.0.1:8000`.

## Full Docker start

```bash
docker compose up -d --build
```

Команда поднимает PostgreSQL, MinIO, создаёт bucket, применяет миграции и запускает backend с frontend. Telegram-бот в этот набор не входит. Его можно добавить отдельно, если в `.env` указан `BOT_TOKEN`:

```bash
docker compose --profile bot up -d bot
```

## Create first admin

```bash
docker compose exec backend python -m app.scripts.create_admin
```

Команда спрашивает email, имя и пароль в терминале. Пароль не печатается и не пишется в репозиторий. Если администратор уже есть, скрипт попросит подтверждение.

Для backend, запущенного на хосте из каталога `backend`:

```bash
python -m app.scripts.create_admin
```

## URLs

- Frontend: http://localhost:8080
- Backend: http://localhost:8000
- Swagger: http://localhost:8000/docs
- MinIO console: http://localhost:9001

## Run tests

```bash
cd backend
pytest
```

```bash
cd frontend
npm run build
npm run lint
```

## Telegram configuration

В `.env` задайте `BOT_TOKEN`. Группу, из которой бот читает сообщения, нужно зарегистрировать в интерфейсе как Telegram Group и привязать к объекту. Webhook для локального запуска не обязателен: бот в профиле `bot` работает через polling.

## Environment variables

Скопируйте `.env.example` в `.env` и замените `JWT_SECRET_KEY` на длинную случайную строку. Остальные значения в примере подходят для локального Docker и локального MinIO, это не production-секреты.

`S3_ENDPOINT_URL` — адрес MinIO для backend. Внутри compose это `http://minio:9000`. `S3_PUBLIC_ENDPOINT_URL` — адрес, который откроет браузер, локально `http://localhost:9000`. Загрузка идёт по внутреннему адресу, подписанная ссылка на фото строится по публичному.

`CORS_ORIGINS` нужен для frontend на Vite (`http://localhost:5173` и `http://127.0.0.1:5173`). Через nginx на порту 8080 запросы same-origin, отдельный CORS для них не требуется.

## Security notes

- Замените `JWT_SECRET_KEY` перед любой общей демонстрацией.
- Users API доступен только администратору.
- Bucket MinIO не публичный. Фото открываются по временной подписанной ссылке.
- Файл `.env` не коммитится.

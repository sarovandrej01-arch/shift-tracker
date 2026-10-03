# Shift Tracker

Shift Tracker — сервис для автоматической регистрации рабочих смен сотрудников по сообщениям в Telegram.

Сотрудник отправляет фотографию в рабочую Telegram-группу. Система определяет объект, сотрудника и дату смены, после чего автоматически создаёт смену либо отправляет сообщение на ручную проверку.

Фотографии сохраняются в S3-совместимое хранилище MinIO, данные — в PostgreSQL. Администратор и модератор работают через веб-интерфейс.

---

## Основной сценарий

```text
Telegram group
    ↓
Telegram bot
    ↓
Получение сообщения и фотографии
    ↓
Определение рабочего объекта
    ↓
Определение сотрудника
    ↓
Определение даты смены
    ↓
Проверка дублей
    ↓
Создание смены / ручная проверка
    ↓
PostgreSQL + MinIO
    ↓
Web-интерфейс
```

---

## Возможности

### Telegram

- получение сообщений из Telegram-групп;
- работа через polling;
- поддержка HTTP, SOCKS4 и SOCKS5 proxy;
- сохранение Telegram chat ID и message ID;
- сохранение текста и подписи сообщения;
- получение и сохранение фотографии;
- защита от повторной обработки одного Telegram-сообщения.

### Определение сотрудника

Сотрудник определяется последовательно по:

1. Telegram user ID;
2. табельному номеру;
3. позывному;
4. ФИО.

Если сотрудник не найден или найдено несколько подходящих сотрудников, система не принимает решение автоматически и отправляет сообщение на ручную проверку.

### Определение объекта

Каждая зарегистрированная Telegram-группа привязывается к рабочему объекту.

Для объекта задаются:

- название;
- время начала смены;
- допустимое время отметки до начала смены;
- допустимое время отметки после начала смены;
- часовой пояс;
- активность объекта.

### Определение смены

Дата смены определяется по времени Telegram-сообщения и настройкам объекта.

Учитываются:

- часовой пояс объекта;
- начало смены;
- допустимое окно до и после начала смены;
- переход смены через полночь.

Например, сообщение, отправленное после полуночи, может относиться к смене предыдущего календарного дня.

### Защита от дублей

Система не позволяет создать две смены для одной комбинации:

```text
employee + work object + shift date
```

На уровне базы данных используется уникальное ограничение:

```text
(employee_id, object_id, shift_date)
```

Также уникальной является пара:

```text
telegram_chat_id + telegram_message_id
```

### Ручная проверка

Сообщение попадает в `Review`, если автоматическое решение принять нельзя.

Например:

- сотрудник не найден;
- найдено несколько сотрудников;
- объект или группа требуют проверки;
- сообщение пришло вне допустимого окна смены.

Модератор или администратор может:

- выбрать сотрудника;
- выбрать объект;
- указать дату смены;
- подтвердить сообщение;
- отклонить сообщение;
- оставить комментарий при отклонении.

При ручном подтверждении сохраняются:

- признак ручного подтверждения;
- пользователь, выполнивший подтверждение;
- запись в журнале обработки.

### Журнал обработки

Для Telegram-сообщения сохраняется история обработки.

Примеры событий:

```text
message_received
work_object_resolved
employee_matched
shift_date_detected
accepted
review_required
duplicate_detected
manual_confirm
manual_reject
processing_error
```

Автоматические действия имеют `user_id = null`.

Для ручных действий сохраняется пользователь, выполнивший действие.

### Web-интерфейс

В интерфейсе доступны:

- Dashboard;
- Reviews;
- Messages;
- Shifts;
- Employees;
- Work Objects;
- Telegram Groups;
- Users.

Поддерживаются фильтрация, просмотр деталей сообщений, смен и журналов обработки.

---

## Статусы сообщений

Telegram-сообщение может иметь один из следующих статусов:

```text
new
processing
accepted
review
rejected
duplicate
error
```

Основные причины:

```text
no_photo
employee_not_found
employee_ambiguous
group_not_configured
outside_shift_window
shift_already_exists
message_already_processed
internal_error
```

---

## Соответствие тестовому заданию

Реализован основной бизнес-сценарий тестового задания.

1. Telegram-бот принимает сообщения из зарегистрированных групп.
2. Сообщение без фотографии отклоняется.
3. Telegram-группа сопоставляется с рабочим объектом.
4. Сотрудник определяется по Telegram ID, табельному номеру, позывному или ФИО.
5. При неоднозначном результате система не делает предположение автоматически.
6. Дата смены определяется с учётом часового пояса и временного окна объекта.
7. Поддерживаются смены, пересекающие границу календарных суток.
8. При успешной обработке создаётся смена.
9. Повторная смена для одного сотрудника, объекта и даты не создаётся.
10. Одно Telegram-сообщение не обрабатывается повторно.
11. Неоднозначные случаи попадают на ручную проверку.
12. Сообщение может быть вручную подтверждено или отклонено.
13. Для ручных действий сохраняется пользователь.
14. Все этапы обработки фиксируются в журнале.
15. Фотографии сохраняются в MinIO.
16. Доступ к фотографиям осуществляется через временные подписанные ссылки.
17. Реализованы справочники сотрудников, объектов и Telegram-групп.
18. Реализована авторизация пользователей.
19. Реализованы роли администратора и модератора.
20. Приложение разворачивается через Docker Compose.
21. Изменения схемы базы данных управляются через Alembic.

---

## Ограничения первой версии

Проект реализован как MVP.

На текущем этапе:

- табель представлен цифровым списком смен без отдельного месячного представления в виде матрицы `сотрудник × дни месяца`;
- изменения и удаления уже обработанных Telegram-сообщений отдельно не отслеживаются;
- отдельная read-only роль руководителя не реализована;
- при необходимости обработки высокой нагрузки обработку Telegram-сообщений можно вынести в отдельную очередь;
- правила сопоставления сотрудников имеют фиксированный приоритет и пока не настраиваются через интерфейс.

Архитектура позволяет расширить эти возможности без изменения основной модели данных.

---

## Стек

### Backend

- Python 3.12+
- FastAPI
- SQLAlchemy 2
- PostgreSQL
- Alembic
- Pydantic v2
- asyncpg
- PyJWT
- pwdlib / Argon2

### Telegram

- Aiogram 3
- aiohttp-socks

### Storage

- MinIO / S3-compatible storage
- aioboto3

### Frontend

- React 19
- TypeScript
- Vite
- React Router
- TanStack Query
- Axios
- Tailwind CSS

### Infrastructure

- Docker
- Docker Compose
- nginx
- PostgreSQL
- MinIO

---

## Структура проекта

```text
shift-tracker/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── api/
│   │   ├── bot/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   └── services/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── routes/
│   │   └── types/
│   └── Dockerfile
│
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
└── README.md
```

---

## Быстрый запуск через Docker

Скопируйте пример переменных окружения:

```bash
cp .env.example .env
```

Перед запуском обязательно замените секретные значения, прежде всего:

```env
JWT_SECRET_KEY=
BOT_TOKEN=
S3_ACCESS_KEY=
S3_SECRET_KEY=
MINIO_ROOT_USER=
MINIO_ROOT_PASSWORD=
```

После этого запустите приложение:

```bash
docker compose up -d --build
```

Команда запускает:

- PostgreSQL;
- MinIO;
- инициализацию bucket;
- Alembic migrations;
- backend;
- frontend.

Telegram-бот запускается отдельно через профиль:

```bash
docker compose --profile bot up -d bot
```

---

## Создание администратора

После запуска backend:

```bash
docker compose exec backend python -m app.scripts.create_admin
```

Скрипт запросит:

- email;
- имя;
- пароль.

Пароль вводится интерактивно и не сохраняется в репозитории.

---

## URLs

При стандартном локальном запуске:

```text
Frontend:
http://localhost:8080

Backend:
http://localhost:8000

Swagger:
http://localhost:8000/docs

MinIO console:
http://localhost:9001
```

---

## Telegram configuration

В `.env` необходимо указать:

```env
BOT_TOKEN=
```

Telegram-группа должна быть зарегистрирована через web-интерфейс и привязана к рабочему объекту.

Бот работает через polling.

Запуск:

```bash
docker compose --profile bot up -d bot
```

Просмотр логов:

```bash
docker compose logs -f bot
```

---

## Telegram proxy

Если сервер не может напрямую подключиться к:

```text
api.telegram.org
```

можно указать proxy:

```env
TELEGRAM_PROXY_URL=socks5://user:password@host:1080
```

Поддерживаются:

```text
http
socks4
socks5
```

После изменения конфигурации:

```bash
docker compose --profile bot up -d --force-recreate bot
```

Реальные proxy credentials не должны храниться в Git.

В логах выводится только факт использования proxy:

```text
Telegram proxy configured
```

---

## Environment variables

Пример находится в:

```text
.env.example
```

Основные параметры:

```env
DATABASE_URL=
JWT_SECRET_KEY=
BOT_TOKEN=

S3_ENDPOINT_URL=
S3_PUBLIC_ENDPOINT_URL=
S3_ACCESS_KEY=
S3_SECRET_KEY=
S3_BUCKET=
S3_REGION=

MINIO_ROOT_USER=
MINIO_ROOT_PASSWORD=

CORS_ORIGINS=
TELEGRAM_PROXY_URL=
```

### S3_ENDPOINT_URL

Внутренний адрес MinIO, который использует backend.

В Docker Compose:

```env
S3_ENDPOINT_URL=http://minio:9000
```

### S3_PUBLIC_ENDPOINT_URL

Адрес MinIO, доступный браузеру пользователя.

Для локального запуска:

```env
S3_PUBLIC_ENDPOINT_URL=http://localhost:9000
```

Backend использует внутренний endpoint для загрузки фотографий, а подписанные ссылки создаются с публичным endpoint.

---

## Local development

Для разработки можно поднять только PostgreSQL и MinIO:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.dev.yml   up -d postgres minio minio-init
```

`docker-compose.dev.yml` публикует PostgreSQL на:

```text
localhost:5433
```

В базовом production Compose PostgreSQL наружу не публикуется.

---

## Backend development

Перейдите в backend:

```bash
cd backend
```

Создайте виртуальное окружение:

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

Установите зависимости:

```bash
pip install -r requirements.txt
```

Примените миграции:

```bash
alembic upgrade head
```

Запустите FastAPI:

```bash
uvicorn app.main:app --reload
```

---

## Frontend development

```bash
cd frontend
npm install
npm run dev
```

Vite будет доступен по адресу:

```text
http://localhost:5173
```

Для локального frontend можно указать:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

## Миграции базы данных

Применить все миграции:

```bash
cd backend
alembic upgrade head
```

Создать новую миграцию:

```bash
alembic revision --autogenerate -m "migration description"
```

Откатить последнюю миграцию:

```bash
alembic downgrade -1
```

---

## Тесты

Backend:

```bash
cd backend
pytest
```

Frontend build:

```bash
cd frontend
npm run build
```

Frontend lint:

```bash
npm run lint
```

---

## Проверка рабочего сценария

Пример end-to-end сценария:

1. Создать администратора.
2. Войти в web-интерфейс.
3. Создать рабочий объект.
4. Создать сотрудника.
5. Добавить Telegram-группу и привязать её к объекту.
6. Добавить Telegram-бота в группу.
7. Отправить фотографию с подписью, содержащей данные сотрудника.
8. Бот получит сообщение.
9. Фото будет сохранено в MinIO.
10. Сотрудник будет определён.
11. Будет определена дата смены.
12. Если все условия выполнены, смена будет создана автоматически.
13. Результат появится в разделах `Messages` и `Shifts`.

Если система не может однозначно определить смену:

```text
Messages → status=review
```

и сообщение появится в:

```text
Reviews
```

после чего его можно обработать вручную.

---

## Security

- `.env` не хранится в Git.
- Пароли пользователей хранятся в виде Argon2 hash.
- JWT используется для авторизации API.
- Users API доступен только администратору.
- MinIO bucket не является публичным.
- Фотографии выдаются через временные presigned URLs.
- PostgreSQL в базовом Docker Compose не публикуется наружу.
- Реальные Telegram tokens и proxy credentials не должны попадать в репозиторий.
- Перед публичной демонстрацией необходимо заменить `JWT_SECRET_KEY` и остальные секреты.

---

## Production

Для production рекомендуется:

- использовать отдельный домен;
- включить HTTPS;
- разместить frontend/backend за reverse proxy;
- закрыть прямой внешний доступ к PostgreSQL и MinIO Console;
- использовать отдельные production credentials;
- настроить резервное копирование PostgreSQL и MinIO;
- при высокой нагрузке вынести обработку Telegram events в очередь.

Текущая версия приложения полностью запускается через Docker Compose и подходит для демонстрации основного бизнес-сценария тестового задания.

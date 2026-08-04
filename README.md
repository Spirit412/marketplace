# Multi-Vendor Marketplace Backend

> Демонстрационный проект на FastAPI.
>
> Полнофункциональный бекенд маркетплейса с разделением на продавцов и покупателей, складским учётом, платежами, уведомлениями, отчётами и CSV-импортом.

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://postgresql.org)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3.13-orange.svg)](https://rabbitmq.com)
[![Redis](https://img.shields.io/badge/Redis-7-red.svg)](https://redis.io)

---

## Архитектура

**10 микросервисов** + **API Gateway (BFF)** на FastAPI + uvicorn. Каждый сервис — изолированный домен со своей схемой БД, слоистой архитектурой и независимым деплоем.

```
Клиенты (Web / Mobile)
        │
        ▼
┌───────────────────────────────────────────────┐
│  api-service (BFF)  :8100                     │
│  Агрегация: /storefront, /orders/{id}/full    │
└───────────────┬───────────────────────────────┘
                │
    ┌───────────┼───────────┬───────────┬──────────┐
    ▼           ▼           ▼           ▼          ▼
┌──────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│ Auth │  │Catalog │  │ Order  │  │Payment │  │  ...   │
│:8110 │  │ :8120  │  │ :8130  │  │ :8140  │  │        │
└──┬───┘  └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘
   │          │           │           │            │
   ▼          ▼           ▼           ▼            ▼
┌─────────────────────────────────────────────────────┐
│  PostgreSQL 16  │  Redis 7  │  RabbitMQ 3.13        │
│  (схема/сервис) │  (кэш/блокировки/сессии)         │
└─────────────────────────────────────────────────────┘
```

### Сервисы

| Сервис | Порт | Назначение |
|--------|------|------------|
| **auth-service** | 8110 | JWT-аутентификация, RBAC (роли → группы → права), rate-limit, сессии |
| **api-service** | 8100 | BFF: агрегация /storefront, /orders/{id}/full, graceful degradation |
| **catalog-service** | 8120 | Товары, категории, полнотекстовый поиск, JSONB-фильтры, Query Sets |
| **order-service** | 8130 | Корзина (Redis), заказы, state machine, idempotency, события RMQ |
| **payment-service** | 8140 | Платёжные шлюзы (Stripe/YooKassa), возвраты, webhooks |
| **inventory-service** | 8180 | Склады, остатки, резервирование, отгрузка, движения |
| **notification-service** | 8150 | Email/WebSocket/SMS/Push, Jinja2-шаблоны, история |
| **report-service** | 8170 | Генерация CSV/Excel/PDF, local/S3-хранилище |
| **scheduler-service** | 8160 | APScheduler: отмена заказов, отчёты, прогрев кэша, алерты |
| **import-service** | 8101 | CSV-импорт товаров/цен/остатков, валидация, маппинг колонок |
| **dictionary-service** | 8190 | Справочники: валюты, страны, таймзоны, единицы измерения |

## Технологический стек

| Категория | Технологии |
|-----------|-----------|
| **Framework** | FastAPI 0.111, uvicorn, Pydantic v2, ORJSON |
| **БД** | PostgreSQL 16, SQLAlchemy 2.0 (async), Alembic |
| **Кэш / очереди** | Redis 7, RabbitMQ 3.13 (FastStream) |
| **Аутентификация** | JWT (access + refresh), bcrypt, refresh-token rotation |
| **Планировщик** | APScheduler |
| **DI** | Rodi |
| **Тестирование** | pytest, pytest-asyncio, httpx (E2E) |
| **Качество кода** | ruff, mypy (strict), pre-commit |
| **Контейнеризация** | Docker, docker compose |
| **CI/CD** | GitHub Actions (в планах) |

## Архитектурные паттерны

| Паттерн | Где применяется |
|---------|----------------|
| **Strategy** | Платёжные шлюзы, каналы уведомлений, форматы экспорта, типы импорта, налоговые стратегии, хеширование паролей |
| **Registry** | Реестры шлюзов, шаблонов, типов отчётов, стратегий импорта, справочников |
| **Builder** | OrderBuilder, NotificationBuilder, ReportBuilder, ProductFromRowBuilder, PaymentPayloadBuilder |
| **Unit of Work** | OrderUnitOfWork, InventoryUnitOfWork, ImportUnitOfWork |
| **State Machine** | Статусы заказа, платежа, отчёта, импорта |
| **BFF (Backend-for-Frontend)** | api-service агрегирует данные из нескольких сервисов |
| **Middleware** | AuthMiddleware с Redis-кэшем проверок доступа |

## Быстрый старт

```bash
# 1. Поднять инфраструктуру
docker compose -f docker-compose.infra.yml up -d

# 2. Поднять все сервисы
docker compose up -d --build

# 3. Накатить миграции
./manage.sh migrate all

# 4. Заполнить БД (RBAC, справочники, тестовые данные)
docker exec mp-auth-service python -m src.seeds.rbac
docker exec mp-dictionary-service python -m src.seeds.dictionary
docker exec mp-catalog-service python -m src.seeds.catalog

# 5. Проверить
curl http://localhost:8110/health   # auth-service
curl http://localhost:8110/docs     # Swagger UI

# 6. Запустить E2E-тесты
cd e2e && python3 -m pytest -q
```

## Тестовые пользователи

| Email | Пароль | Роль |
|-------|--------|------|
| `superadmin@marketplace.local` | `SuperAdmin123!` | super_admin |
| `admin@marketplace.local` | `Admin123!` | admin |
| `seller@marketplace.local` | `Seller123!` | seller |
| `customer@marketplace.local` | `Customer123!` | customer |

## E2E-тесты

```bash
cd e2e
python3 -m pytest -q                  # все тесты (202 passed)
python3 -m pytest -q -m "not writes"  # только чтение
```

Тесты проверяют: CRUD-операции, бизнес-сценарии (buyer journey, seller journey), безопасность (IDOR/BOLA, RBAC, валидация), контракты сервисов.

## Структура сервиса (типовая)

```
service-name/
├── src/
│   ├── routers/          # FastAPI роутеры (тонкие)
│   ├── services/         # Бизнес-логика + стратегии + билдеры
│   ├── repositories/     # Доступ к данным
│   ├── models/           # SQLAlchemy модели
│   ├── schemes/          # Pydantic схемы (request/response/internal)
│   ├── core/             # Инфраструктура: БД, конфиг, UoW, state machine
│   ├── enums/            # Перечисления
│   ├── engines/          # Клиенты: Redis, RabbitMQ, PostgreSQL
│   ├── facades/          # HTTP-клиенты к другим сервисам
│   ├── config/           # Настройки (pydantic-settings)
│   ├── alembic/          # Миграции
│   └── seeds/            # Наполнение БД тестовыми данными
├── tests/                # Unit + интеграционные тесты
├── pyproject.toml
├── Dockerfile
└── README.md
```


## Лицензия

MIT

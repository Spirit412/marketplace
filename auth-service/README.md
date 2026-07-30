# Auth Service

Микросервис аутентификации и авторизации для Multi-Vendor Marketplace.

## Функциональность

- Регистрация / логин / логаут
- JWT access + refresh токены
- RBAC: роли → группы → права (app_id + method + path)
- Проверка доступа через `POST /auth/check-access` (path-level)
- Rate-limit через Redis
- Блокировка пользователей
- Управление ролями, правами, группами (CRUD)
- Интроспекция токенов

## API

### Аутентификация

| Метод | Путь | Доступ | Описание |
|-------|------|--------|----------|
| `POST` | `/auth/register` | public | Регистрация |
| `POST` | `/auth/login` | public | Вход |
| `POST` | `/auth/refresh` | public | Обновление токенов |
| `POST` | `/auth/logout` | bearer | Выход |
| `POST` | `/auth/logout-all` | bearer | Выход со всех устройств |
| `GET` | `/auth/sessions` | bearer | Активные сессии |

### Проверка доступа

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/auth/check_credentials` | Интроспекция токена (user_uuid, role, is_admin) |
| `POST` | `/auth/check-access` | Проверка (token, method, path, app) → allowed |

### RBAC (только admin)

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/auth/roles` | Список ролей |
| `POST` | `/auth/roles` | Создать роль |
| `GET` | `/auth/roles/{uuid}` | Получить роль |
| `PUT` | `/auth/roles/{uuid}` | Обновить роль |
| `DELETE` | `/auth/roles/{uuid}` | Удалить роль |
| `GET` | `/auth/permissions` | Список прав |
| `POST` | `/auth/permissions` | Создать право |
| `GET` | `/auth/permissions/{uuid}` | Получить право |
| `PUT` | `/auth/permissions/{uuid}` | Обновить право |
| `DELETE` | `/auth/permissions/{uuid}` | Удалить право |
| `GET` | `/auth/groups` | Список групп |
| `POST` | `/auth/groups` | Создать группу |
| `GET` | `/auth/groups/{uuid}` | Получить группу |
| `PUT` | `/auth/groups/{uuid}` | Обновить группу |
| `DELETE` | `/auth/groups/{uuid}` | Удалить группу |

### Пользователи

| Метод | Путь | Доступ | Описание |
|-------|------|--------|----------|
| `POST` | `/auth/users/{uuid}/block` | admin | Блокировка |
| `POST` | `/auth/users/{uuid}/unblock` | admin | Разблокировка |
| `PUT` | `/auth/users/{uuid}/access` | admin | Назначить роль/права |
| `GET` | `/auth/users/{uuid}/access` | admin | Права пользователя |
| `GET` | `/auth/users/{uuid}/permissions` | admin | Разрешённые permissions |

## JWT

```json
{
  "type": "access",
  "user_uuid": "11111111-...",
  "role": "admin",
  "is_admin": true,
  "jti": "...",
  "iat": 1700000000,
  "exp": 1700000900
}
```

Access token: 15 минут. Refresh token: 7 дней.
При протухании access token клиент получает `401 {"error": "token_expired"}` и обновляет через `/auth/refresh`.

## Проверка доступа в других сервисах

Каждый сервис использует `AuthMiddleware`:

```python
from src.auth_middleware import AuthMiddleware, init_auth

init_auth(
    jwt_secret=settings.jwt.SECRET_KEY,
    jwt_algorithm=settings.jwt.ALGORITHM,
    auth_service_url=settings.AUTH_SERVICE_URL,
    app_id=settings.APP_ID,
)
app.add_middleware(AuthMiddleware)
```

Middleware валидирует JWT локально, при протухании возвращает `401 token_expired`.
Для path-level проверок: `Depends(check_access("POST", "/products"))` — вызывает `POST /auth/check-access`.

## Заполнение БД (seed)

```bash
# После миграций
poetry run python -m src.seeds.rbac
```

Скрипт идемпотентный — можно запускать многократно. Данные в `src/seeds/data/*.json`.

## Тестовые пользователи

| Email | Пароль | Роль | Права |
|-------|--------|------|-------|
| `superadmin@marketplace.local` | `SuperAdmin123!` | super_admin | Все сервисы, все методы |
| `admin@marketplace.local` | `Admin123!` | admin | Все сервисы (DICTIONARY без DELETE, PAYMENT только read) |
| `moderator@marketplace.local` | `Moderator123!` | moderator | CATALOG (write), ORDER (read) |
| `seller@marketplace.local` | `Seller123!` | seller | CATALOG, INVENTORY, IMPORT (all), ORDER, REPORT (read) |
| `customer@marketplace.local` | `Customer123!` | customer | ORDER (all) |
| `customer2@marketplace.local` | `Customer123!` | customer | ORDER (all) |

## Роли и группы

| Роль | Группа | Сервисы |
|------|--------|---------|
| super_admin | super_admin_full_access | Все 10 сервисов, все методы |
| admin | admin_full_access | Все сервисы, DICTIONARY без DELETE, PAYMENT без DELETE |
| moderator | moderator_access | CATALOG (GET/POST/PUT/PATCH), ORDER (GET) |
| seller | seller_access | CATALOG (all), ORDER (GET), INVENTORY (all), IMPORT (all), REPORT (GET) |
| customer | customer_orders | ORDER (all) |

## Запуск

```bash
docker compose up -d
```

Или через корневой `manage.sh`:

```bash
cd .. && ./manage.sh
```

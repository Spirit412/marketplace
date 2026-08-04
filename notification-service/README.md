# Notification Service

Микросервис уведомлений.

## Функциональность

- Мультиканальная отправка: email, WebSocket (real-time), SMS, push
- Шаблоны уведомлений (Jinja2) с реестром шаблонов
- NotificationBuilder — построение уведомлений по событиям
- Подписка на все события RabbitMQ: заказы, платежи, остатки, отчёты, импорт
- История уведомлений в PostgreSQL
- WebSocket-эндпоинт для real-time уведомлений фронтенду
- Отправка email через SMTP

## API

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/notifications` | Уведомления пользователя (unread/all) |
| `GET` | `/notifications/history` | История уведомлений |
| `POST` | `/notifications/{id}/mark-read` | Отметить как прочитанное |
| `POST` | `/notifications/mark-all-read` | Отметить все как прочитанные |
| `POST` | `/notifications/send` | Отправить уведомление вручную |
| `WS` | `/ws/{user_id}` | WebSocket-канал уведомлений |

## Каналы доставки

| Канал | Реализация | Описание |
|-------|-----------|----------|
| `email` | SMTP | Шаблоны Jinja2 → HTML-письмо |
| `websocket` | FastAPI WebSocket | Real-time уведомления в браузер |
| `sms` | Заглушка | Для будущей интеграции |
| `push` | Заглушка | Для будущей интеграции |

Выбор канала — Strategy Pattern через `ChannelRegistry`.

## События RabbitMQ (подписка)

Сервис слушает **все** события маркетплейса и формирует уведомления:

| Событие | Шаблон |
|---------|--------|
| `order.created` | `order_created.jinja2` |
| `order.cancelled` | Системный шаблон |
| `payment.succeeded` | `payment_succeeded.jinja2` |
| `payment.failed` | Системный шаблон |
| `stock.depleted` | `stock_depleted.jinja2` |
| `report.ready` | Системный шаблон |
| `import.completed` | Системный шаблон |
| `import.failed` | Системный шаблон |

## Порты

- API: `8150`
- Swagger: `/docs`, `/redoc`

## Запуск

```bash
docker compose up -d
cd .. && ./manage.sh up notification-service
```

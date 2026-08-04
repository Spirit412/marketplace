# Payment Service

Микросервис платежей.

## Функциональность

- Создание платежа с idempotency key
- Стратегии платёжных шлюзов: Stripe, YooKassa, Mock (для разработки)
- Реестр шлюзов (`PaymentGatewayRegistry`) — выбор по `payment_method`
- State machine статусов платежа
- Webhook-эндпоинты для callback'ов от внешних шлюзов
- Возвраты (refund)
- Публикация событий `payment.succeeded` / `payment.failed` в RabbitMQ

## API

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/payments` | Создать платёж |
| `GET` | `/payments/by-order/{order_id}` | Получить платёж по заказу |
| `GET` | `/payments/{id}` | Получить платёж по ID |
| `POST` | `/payments/{id}/refund` | Возврат платежа |
| `POST` | `/webhooks/stripe` | Webhook Stripe |
| `POST` | `/webhooks/yookassa` | Webhook YooKassa |

## Платёжные шлюзы

| Шлюз | Метод оплаты | Описание |
|------|-------------|----------|
| `StripeGateway` | `stripe` | Боевой шлюз Stripe |
| `YooKassaGateway` | `yookassa` | Боевой шлюз YooKassa |
| `MockGateway` | `mock` | Имитация успешного платежа (dev) |

Шлюз выбирается через `PaymentGatewayRegistry.get(method)` → Strategy Pattern.

## Статусы платежа

```
pending → processing → succeeded
                    ↘ failed
succeeded → refunded
```

## События RabbitMQ

| Событие | Описание |
|---------|----------|
| `payment.succeeded` | Платёж прошёл успешно |
| `payment.failed` | Платёж не прошёл |

## Порты

- API: `8140`
- Swagger: `/docs`, `/redoc`

## Запуск

```bash
docker compose up -d
cd .. && ./manage.sh up payment-service
```

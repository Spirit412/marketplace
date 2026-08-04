# Order Service

Микросервис заказов и корзины.

## Функциональность

- Корзина покупателя в Redis (с TTL)
- Оформление заказа с резервированием товаров на складе
- Idempotency key для безопасного повторного создания заказа
- State machine статусов заказа
- Отмена неоплаченных заказов (через scheduler-service)
- OrderBuilder с расчётом налогов, скидок и итоговой суммы
- Подписка на события оплаты через RabbitMQ (`payment.succeeded`, `payment.failed`)
- Rate-limit на создание заказа

## API

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/cart` | Получить корзину |
| `POST` | `/cart` | Добавить товар в корзину |
| `DELETE` | `/cart/{product_id}` | Удалить товар из корзины |
| `POST` | `/orders` | Создать заказ |
| `GET` | `/orders` | Список заказов пользователя |
| `GET` | `/orders/{id}` | Получить заказ по ID |
| `POST` | `/orders/{id}/cancel` | Отменить заказ |
| `GET` | `/orders/internal/pending` | Внутренний: неподтверждённые заказы старше N минут |

## Статусы заказа

```
pending → confirmed → shipped → delivered
                  ↘ cancelled
```

Переходы управляются `StateMachine` (`src/core/state_machine.py`).

## События RabbitMQ

| Событие | Направление | Описание |
|---------|-------------|----------|
| `order.created` | Публикация | Заказ создан, ожидается оплата |
| `order.cancelled` | Публикация | Заказ отменён (таймаут или вручную) |
| `payment.succeeded` | Подписка | Платёж прошёл → подтверждение заказа |
| `payment.failed` | Подписка | Платёж не прошёл → отмена заказа |

## Порты

- API: `8130`
- Swagger: `/docs`, `/redoc`

## Запуск

```bash
docker compose up -d
cd .. && ./manage.sh up order-service
```

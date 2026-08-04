# Scheduler Service

Микросервис планировщика.

## Функциональность

- Отмена неоплаченных заказов (периодическая задача)
- Ежедневная генерация отчётов
- Прогрев кэша каталога (популярные товары)
- Алерты по низким остаткам на складе
- Управление задачами через API (ручной запуск, статус)

## Задачи (jobs)

| Задача | Периодичность | Описание |
|--------|--------------|----------|
| `cancel_unpaid_orders` | Каждые 15 минут | Отменяет заказы старше 30 минут в статусе `pending` |
| `daily_report` | Ежедневно в 00:00 | Запускает генерацию отчёта за сутки |
| `cache_warmup` | Каждые 30 минут | Прогревает кэш Redis популярными товарами |
| `inventory_alert` | Каждые 30 минут | Проверяет остатки ниже порога на всех складах |

## API

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/jobs/{job_name}/run` | Запустить задачу вручную |
| `GET` | `/jobs/{job_name}/status` | Статус последнего запуска |

## Взаимодействие с другими сервисами

```
Scheduler → Order Service   (HTTP: poll pending orders)
Scheduler → Inventory       (HTTP: check low stock)
Scheduler → Catalog         (HTTP: get popular products)
Scheduler → Report Service  (HTTP: generate daily report)
Scheduler → RabbitMQ        (publish: order.cancelled, stock.depleted)
```

## Порты

- API: `8160`
- Swagger: `/docs`, `/redoc`

## Запуск

```bash
docker compose up -d
cd .. && ./manage.sh up scheduler-service
```

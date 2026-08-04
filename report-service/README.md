# Report Service

Микросервис отчётов.

## Функциональность

- Генерация отчётов по расписанию и по запросу
- Форматы экспорта: CSV, Excel, PDF (стратегии через `FormatStrategy`)
- ReportBuilder — построение SQL-запросов по шаблонам
- Реестр типов отчётов (`REPORT_TYPE_REGISTRY`)
- State machine статусов генерации
- Файловое хранилище: локальное / S3 (MinIO)
- Подписка на `report.generate.*` события через RabbitMQ
- Ежедневные отчёты через scheduler-service

## API

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/reports` | Запустить генерацию отчёта (async) |
| `GET` | `/reports` | Список отчётов пользователя |
| `GET` | `/reports/{id}` | Получить отчёт по ID |
| `GET` | `/reports/{id}/download` | Скачать сгенерированный файл |

## Статусы отчёта

```
pending → processing → completed
                    ↘ failed
```

## Типы отчётов

| Тип | Источник данных | Форматы |
|-----|----------------|---------|
| `sales_summary` | PostgreSQL (order-service) | CSV, Excel |
| `inventory_status` | PostgreSQL (inventory-service) | CSV, Excel |
| `seller_performance` | PostgreSQL (order-service) | CSV, Excel, PDF |

## Хранилище файлов

| Стратегия | Описание |
|-----------|----------|
| `local` | Файлы в `/tmp/reports` (по умолчанию) |
| `s3` | S3-совместимое хранилище (MinIO) |

Имена файлов — хеш содержимого. Human-readable имена хранятся в БД.

## Порты

- API: `8170`
- Swagger: `/docs`, `/redoc`

## Запуск

```bash
docker compose up -d
cd .. && ./manage.sh up report-service
```

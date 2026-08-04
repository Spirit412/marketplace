# Dictionary Service

Микросервис справочников.

## Функциональность

- Управление справочными данными (валюты, единицы измерения, страны, таймзоны)
- Источники данных: БД (своя схема) и внешние API
- Реестр справочников (`DictionaryRegistry`)
- Кэширование в Redis с инвалидацией по типу справочника
- CRUD с мягким удалением
- Справочник таймзон IANA

## Типы справочников

| Тип | Источник | Описание |
|-----|----------|----------|
| `currencies` | БД | Валюты (ISO 4217) |
| `units` | БД | Единицы измерения |
| `countries` | БД | Страны (ISO 3166-1) |
| `timezones` | External API / БД | Таймзоны IANA |
| `payment_methods` | БД | Способы оплаты |
| `tax_strategies` | БД | Налоговые стратегии |

## API

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/dictionaries/{type}` | Получить записи справочника |
| `POST` | `/dictionaries/{type}` | Создать запись справочника |
| `PUT` | `/dictionaries/{type}/{id}` | Обновить запись |
| `DELETE` | `/dictionaries/{type}/{id}` | Удалить запись (soft delete) |

Где `{type}` — одно из значений `DictionaryType`: `currencies`, `units`, `countries`, `timezones`, `payment_methods`, `tax_strategies`.

## Паттерны

- **DictionaryRegistry** — реестр источников данных: `DBDictionarySource` (БД), `ExternalAPISource` (внешний API)
- **Strategy** — выбор источника для каждого типа справочника
- Кэш в Redis: ключ `{prefix}:dict:{type}`, сброс при любом изменении записей

## Порты

- API: `8190`
- Swagger: `/docs`, `/redoc`

## Запуск

```bash
docker compose up -d
cd .. && ./manage.sh up dictionary-service
```

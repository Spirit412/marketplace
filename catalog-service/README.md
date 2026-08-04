# Catalog Service

Микросервис каталога товаров.

## Функциональность

- Управление товарами: создание, редактирование, удаление, поиск
- Дерево категорий с динамическими свойствами (JSONB)
- Сохранённые наборы фильтров (Query Sets) — избранное, теги, системные выборки
- Полнотекстовый поиск по товарам (PostgreSQL `tsvector`)
- Динамическая фильтрация по JSONB-атрибутам (`custom_properties`)
- Сортировка: по цене, рейтингу, новизне, релевантности
- Кэширование товаров и категорий через Redis
- Мягкое удаление (soft delete)

## API

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/products` | Создать товар |
| `GET` | `/products` | Список товаров с фильтрацией и поиском |
| `GET` | `/products/{id}` | Получить товар по ID |
| `PUT` | `/products/{id}` | Обновить товар |
| `DELETE` | `/products/{id}` | Удалить товар (soft delete) |
| `POST` | `/categories` | Создать категорию |
| `GET` | `/categories` | Дерево категорий |
| `GET` | `/categories/{id}` | Получить категорию по ID |
| `PUT` | `/categories/{id}` | Обновить категорию |
| `DELETE` | `/categories/{id}` | Удалить категорию |
| `POST` | `/query-sets` | Создать набор фильтров |
| `GET` | `/query-sets` | Список наборов фильтров продавца |
| `GET` | `/query-sets/{id}` | Получить набор фильтров |
| `PUT` | `/query-sets/{id}` | Обновить набор фильтров |
| `DELETE` | `/query-sets/{id}` | Удалить набор фильтров |

## Динамические атрибуты товаров

Атрибуты товаров хранятся в JSONB-поле `custom_properties`. Состав определяется категорией товара:

```json
{
  "color": "red",
  "size": "XL",
  "material": "cotton"
}
```

Фильтрация: `?color=red&size__in=XL,L&price__gte=1000&price__lte=5000`

Операторы: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `contains`, `icontains`, `in`

## Порты

- API: `8120`
- Swagger: `/docs`, `/redoc`

## Запуск

```bash
docker compose up -d
cd .. && ./manage.sh up catalog-service
```

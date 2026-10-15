# Marketplace Frontend

Фронтенд для Multi-Vendor Marketplace — платформы с продавцами и покупателями.

## Стек

| Категория | Библиотека |
|---|---|
| Runtime | **React 19** + **TypeScript 5.7** |
| Сборка | **Vite 8** (Rolldown) |
| UI | **shadcn/ui** + **Tailwind CSS v4** |
| Роутинг | **TanStack Router v1** (file-based, типобезопасный) |
| Серверный стейт | **TanStack Query v5** |
| Клиентский стейт | **Redux Toolkit** + redux-persist |
| Формы | **React Hook Form v7** + **Zod v4** |
| HTTP | **Axios v1** (10 клиентов — по одному на микросервис) |
| Анимации | **Framer Motion** |
| Иконки | **Lucide React** |
| Тесты | **Vitest** + **Playwright** |

## Быстрый старт

```bash
cd frontend

# Проверить окружение
./setup.sh check

# Установить зависимости и создать проект
./setup.sh install

# Запустить dev-сервер
npm run dev
```

Открыть: **http://localhost:5173**

## Скрипты

| Команда | Описание |
|---|---|
| `npm run dev` | Dev-сервер с HMR |
| `npm run build` | Production-сборка (`tsc` + `vite build`) |
| `npm run preview` | Предпросмотр production-сборки |
| `npm run typecheck` | `tsc --noEmit` |
| `npm run lint` | ESLint (max-warnings 0) |
| `npm run format` | Prettier |
| `npm run code-review` | `typecheck` + `lint` + `format --check` |
| `npm run add-component` | Добавить shadcn/ui компонент |
| `npx playwright test` | E2E-тесты |

## Структура

```
src/
├── main.tsx                    # Точка входа (Provider + Router + QueryClient)
├── index.css                   # Tailwind v4 + CSS-переменные
├── routes/                     # File-based роутинг (TanStack Router)
│   ├── __root.tsx              # Корневой layout + auth guard
│   ├── index.tsx               # Главная (hero / дашборд)
│   ├── login.tsx / register.tsx
│   ├── products/               # Каталог
│   ├── cart.tsx                # Корзина
│   ├── orders/                 # Заказы
│   ├── seller/                 # Панель продавца
│   └── admin/                  # Панель администратора
├── components/
│   ├── ui/                     # shadcn/ui (20+ компонентов)
│   ├── layout/                 # AppLayout, Header, Sidebar
│   ├── blocks/                 # Страничные блоки (Hero, Pricing, Stats, Footer)
│   └── shared/                 # ProductCard, PriceTag, StatusBadge, SearchBar, …
├── features/                   # Feature-based модули
│   ├── auth/                   # LoginForm, RegisterForm, auth-service
│   ├── catalog/                # ProductList, CategoryTree, catalog-service
│   ├── orders/                 # OrderList, OrderDetail, order-service
│   ├── cart/                   # CartDrawer
│   └── payments/               # payment-service
├── store/                      # Redux Toolkit
│   ├── index.ts                # configureStore + persist
│   ├── auth-slice.ts           # JWT-токены, профиль
│   ├── cart-slice.ts           # Корзина
│   └── ui-slice.ts             # Тема, UI-состояние
├── lib/
│   ├── api-client.ts           # Axios-клиенты (10 шт) + interceptors
│   ├── env.ts                  # URL всех микросервисов
│   └── utils.ts                # cn(), format_price(), format_date()
├── hooks/                      # use-auth, use-websocket, use-debounce
└── types/                      # Product, Order, Payment, …
```

## Переменные окружения

Скопируйте `.env.example` в `.env.local` (локальная разработка) или `.env` (Docker):

```bash
cp .env.example .env.local
```

Все URL микросервисов настраиваются в `.env`:

```env
VITE_API_URL=http://localhost:8100          # api-service (BFF)
VITE_AUTH_URL=http://localhost:8110         # auth-service
VITE_CATALOG_URL=http://localhost:8120      # catalog-service
VITE_ORDER_URL=http://localhost:8130        # order-service
# …и так далее для каждого из 11 микросервисов
```

При запуске в Docker Compose используются имена контейнеров (`mp-auth-service:8110`, …).

## Docker

```bash
# Dev (hot-reload, volume mounts)
docker compose up mp-frontend

# Production
docker build -t marketplace-frontend .
docker run -p 80:80 marketplace-frontend
```

## Бекенд

11 микросервисов на FastAPI. Фронтенд обращается к каждому напрямую (не через Gateway — `api-service` это BFF с 3 эндпоинтами).

Подробнее: [[../Детальная архитектура]] и [[../C4 — Архитектура системы]]

## Авторизация

| email                      | пароль         | роль        |
| -------------------------- | -------------- | ----------- |
| moderator@marketplace.dev  | Moderator123!  | moderator   |
| seller@marketplace.dev     | Seller123!     | seller      |
| customer@marketplace.dev   | Customer123!   | customer    |
| customer2@marketplace.dev  | Customer123!   | customer    |

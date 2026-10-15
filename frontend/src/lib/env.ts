/**
 * Централизованная конфигурация URL всех микросервисов.
 * В dev-режиме (Vite) используется прокси /api/* → backend.
 * В Docker Compose значения берутся из .env (переменные VITE_*).
 */
const IS_DEV = import.meta.env.DEV;

export const SERVICE_URLS = {
    api: import.meta.env.VITE_API_URL ?? (IS_DEV ? "/api" : "http://localhost:8100"),
    auth: import.meta.env.VITE_AUTH_URL ?? (IS_DEV ? "/api/auth" : "http://localhost:8110"),
    catalog: import.meta.env.VITE_CATALOG_URL ?? (IS_DEV ? "/api/catalog" : "http://localhost:8120"),
    order: import.meta.env.VITE_ORDER_URL ?? (IS_DEV ? "/api/order" : "http://localhost:8130"),
    payment: import.meta.env.VITE_PAYMENT_URL ?? (IS_DEV ? "/api/payment" : "http://localhost:8140"),
    notification: import.meta.env.VITE_NOTIFICATION_URL ?? (IS_DEV ? "/api/notification" : "http://localhost:8150"),
    scheduler: import.meta.env.VITE_SCHEDULER_URL ?? (IS_DEV ? "/api" : "http://localhost:8160"),
    report: import.meta.env.VITE_REPORT_URL ?? (IS_DEV ? "/api/report" : "http://localhost:8170"),
    inventory: import.meta.env.VITE_INVENTORY_URL ?? (IS_DEV ? "/api/inventory" : "http://localhost:8180"),
    dictionary: import.meta.env.VITE_DICTIONARY_URL ?? (IS_DEV ? "/api/dictionary" : "http://localhost:8190"),
    import: import.meta.env.VITE_IMPORT_URL ?? (IS_DEV ? "/api/import" : "http://localhost:8101"),
    ws: import.meta.env.VITE_WS_URL ?? "ws://localhost:8150/ws",
} as const;

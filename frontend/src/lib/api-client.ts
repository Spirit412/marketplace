import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import { store } from "@/store";
import { clearAuth, setTokens } from "@/store/auth-slice";
import { SERVICE_URLS } from "./env";

// ── Auth client (прямой доступ — токенов ещё нет) ──

export const auth_client = axios.create({
    baseURL: SERVICE_URLS.auth,
    timeout: 10_000,
    headers: { "Content-Type": "application/json" },
});

// ── Клиенты для каждого микросервиса ──

function create_service_client(base_url: string) {
    return axios.create({
        baseURL: base_url,
        timeout: 15_000,
        headers: { "Content-Type": "application/json" },
    });
}

export const api_client = create_service_client(SERVICE_URLS.api);
export const catalog_client = create_service_client(SERVICE_URLS.catalog);
export const order_client = create_service_client(SERVICE_URLS.order);
export const payment_client = create_service_client(SERVICE_URLS.payment);
export const inventory_client = create_service_client(SERVICE_URLS.inventory);
export const dictionary_client = create_service_client(SERVICE_URLS.dictionary);
export const import_client = create_service_client(SERVICE_URLS.import);
export const report_client = create_service_client(SERVICE_URLS.report);
export const notification_client = create_service_client(SERVICE_URLS.notification);

// ── Interceptor: добавляет access-токен ко всем запросам ──

const ALL_CLIENTS = [
    api_client,
    auth_client,
    catalog_client,
    order_client,
    payment_client,
    inventory_client,
    dictionary_client,
    import_client,
    report_client,
    notification_client,
];

// Проверка: не протух ли токен (без верификации подписи — только exp из payload)
export function is_token_expired(token: string): boolean {
    try {
        const payload = JSON.parse(atob(token.split(".")[1] ?? ""));
        return (payload.exp ?? 0) * 1000 < Date.now();
    } catch {
        return true;
    }
}


function attach_token(config: InternalAxiosRequestConfig) {
    // НЕ добавляем токен к запросу refresh (он public, принимает refresh_token в body)
    if (config.url?.includes("/auth/refresh")) {
        return config;
    }
    const token = store.getState().auth.access_token;
    if (import.meta.env.DEV) {
        const full_url = `${config.baseURL ?? ""}${config.url ?? ""}`;
        console.debug(
            `[api-client] attach_token | url=${full_url} | has_token=${!!token}`,
        );
    }
    if (token && !is_token_expired(token)) {
        config.headers.Authorization = `Bearer ${token}`;
    } else if (import.meta.env.DEV) {
        if (!token) {
            console.warn(`[api-client] attach_token | NO token in store for ${config.url}`);
        } else {
            console.warn(`[api-client] attach_token | token EXPIRED for ${config.url}`);
        }
    }
    return config;
}

for (const client of ALL_CLIENTS) {
    client.interceptors.request.use(attach_token);
    attach_refresh_interceptor(client);
}

// ── Interceptor: при 401 пытается обновить токен ──

let refresh_promise: Promise<string | null> | null = null;

async function try_refresh(): Promise<string | null> {
    const state = store.getState().auth;
    if (!state.refresh_token) {
        if (import.meta.env.DEV) {
            console.warn("[api-client] try_refresh | no refresh_token in store");
        }
        return null;
    }

    try {
        if (import.meta.env.DEV) {
            console.debug("[api-client] try_refresh | attempting token refresh");
        }
        const { data } = await auth_client.post<{ access_token: string; refresh_token: string }>(
            "/auth/refresh",
            { refresh_token: state.refresh_token },
        );
        store.dispatch(setTokens({ access: data.access_token, refresh: data.refresh_token }));
        if (import.meta.env.DEV) {
            console.info("[api-client] try_refresh | token refreshed successfully");
        }
        return data.access_token;
    } catch (refresh_error) {
        if (import.meta.env.DEV) {
            console.error("[api-client] try_refresh | refresh failed", refresh_error);
        }
        store.dispatch(clearAuth());
        return null;
    }
}

function attach_refresh_interceptor(client: ReturnType<typeof create_service_client>) {
    client.interceptors.response.use(
        (response) => response,
        async (error: AxiosError) => {
            const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
            if (error.response?.status !== 401 || original._retry) {
                return Promise.reject(error);
            }

            if (import.meta.env.DEV) {
                const full_url = `${original.baseURL ?? ""}${original.url ?? ""}`;
                console.warn(
                    `[api-client] 401 intercepted for ${full_url}, attempting refresh`,
                );
            }

            original._retry = true;

            if (!refresh_promise) {
                refresh_promise = try_refresh().finally(() => {
                    refresh_promise = null;
                });
            }

            const new_token = await refresh_promise;
            if (new_token && original.headers) {
                original.headers.Authorization = `Bearer ${new_token}`;
                if (import.meta.env.DEV) {
                    console.info("[api-client] retrying request with new token");
                }
                return client(original);
            }

            if (import.meta.env.DEV) {
                console.error("[api-client] refresh failed, redirecting to /login");
            }
            window.location.href = "/login";
            return Promise.reject(error);
        },
    );
}

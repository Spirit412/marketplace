import { createRootRoute, Outlet, redirect } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/router-devtools";
import { Toaster } from "@/components/ui/sonner";
import { AppLayout } from "@/components/layout/AppLayout";
import { store } from "@/store";
import { clearAuth } from "@/store/auth-slice";
import { is_token_expired } from "@/lib/api-client";
// Публичные маршруты — доступны без токена
const PUBLIC_PATHS = ["/", "/login", "/register"];

export const Route = createRootRoute({
    beforeLoad: ({ location }) => {
        const state = store.getState();
        const { is_authenticated, access_token } = state.auth;
        const current_path = location.pathname;

        // /login и /register — если уже залогинен и токен валиден, редирект на главную
        if ((current_path === "/login" || current_path === "/register") && is_authenticated) {
            if (access_token && !is_token_expired(access_token)) {
                throw redirect({ to: "/" });
            }
        }

        // Публичные маршруты — пропускаем без проверки
        if (PUBLIC_PATHS.includes(current_path)) {
            return;
        }

        // Защищённые маршруты — без токена или токен протух → логин
        if (!is_authenticated || !access_token || is_token_expired(access_token)) {
            // Сбрасываем auth state если токен протух, чтобы не застрять в цикле
            if (is_authenticated && access_token && is_token_expired(access_token)) {
                store.dispatch(clearAuth());
            }
            throw redirect({ to: "/login" });
        }
    },
    component: RootComponent,
});

function RootComponent() {
    const is_authenticated = store.getState().auth.is_authenticated;

    // На публичных страницах (login/register) — без layout
    const current_path = window.location.pathname;
    const is_public = PUBLIC_PATHS.includes(current_path);

    return (
        <>
            <Toaster richColors closeButton />
            {is_public || !is_authenticated ? (
                <Outlet />
            ) : (
                <AppLayout>
                    <Outlet />
                </AppLayout>
            )}
            {import.meta.env.DEV && <TanStackRouterDevtools position="bottom-right" />}
        </>
    );
}

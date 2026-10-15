import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { Provider } from "react-redux";
import { PersistGate } from "redux-persist/integration/react";
import { createRouter, RouterProvider } from "@tanstack/react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { persistor, store } from "./store";
import { routeTree } from "./routeTree.gen";
import "./index.css";

const query_client = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 30_000,
            gcTime: 5 * 60_000,
            retry: 1,
            refetchOnWindowFocus: false,
        },
        mutations: { retry: 0 },
    },
});

const router = createRouter({
    routeTree,
    context: { query_client },
    defaultPreload: "intent",
    defaultPreloadStaleTime: 0,
});

declare module "@tanstack/react-router" {
    interface Register {
        router: typeof router;
    }
}

const root = document.getElementById("root");
if (!root) throw new Error("Root element not found");

createRoot(root).render(
    <StrictMode>
        <Provider store={store}>
            <PersistGate
                loading={<div className="flex min-h-screen items-center justify-center text-muted-foreground">Загрузка…</div>}
                persistor={persistor}
            >
                <QueryClientProvider client={query_client}>
                    <RouterProvider router={router} />
                </QueryClientProvider>
            </PersistGate>
        </Provider>
    </StrictMode>,
);

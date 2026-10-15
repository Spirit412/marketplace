import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { TanStackRouterVite } from "@tanstack/router-plugin/vite";
import path from "node:path";
export default defineConfig({
    plugins: [
        tailwindcss(),
        TanStackRouterVite({ target: "react", autoCodeSplitting: true }),
        react(),
    ],
    resolve: {
        alias: {
            "@": path.resolve(import.meta.dirname, "./src"),
        },
    },
    server: {
        port: 5173,
        proxy: {
            "/api/auth": {
                target: "http://localhost:8110",
                changeOrigin: true,
                rewrite: (path: string) => path.replace(/^\/api\/auth/, ""),
            },
            "/api/catalog": {
                target: "http://localhost:8120",
                changeOrigin: true,
                rewrite: (path: string) => path.replace(/^\/api\/catalog/, ""),
            },
            "/api/order": {
                target: "http://localhost:8130",
                changeOrigin: true,
                rewrite: (path: string) => path.replace(/^\/api\/order/, ""),
            },
            "/api/payment": {
                target: "http://localhost:8140",
                changeOrigin: true,
                rewrite: (path: string) => path.replace(/^\/api\/payment/, ""),
            },
            "/api/inventory": {
                target: "http://localhost:8180",
                changeOrigin: true,
                rewrite: (path: string) => path.replace(/^\/api\/inventory/, ""),
            },
            "/api/dictionary": {
                target: "http://localhost:8190",
                changeOrigin: true,
                rewrite: (path: string) => path.replace(/^\/api\/dictionary/, ""),
            },
            "/api/import": {
                target: "http://localhost:8101",
                changeOrigin: true,
                rewrite: (path: string) => path.replace(/^\/api\/import/, ""),
            },
            "/api/report": {
                target: "http://localhost:8170",
                changeOrigin: true,
                rewrite: (path: string) => path.replace(/^\/api\/report/, ""),
            },
            "/api/notification": {
                target: "http://localhost:8150",
                changeOrigin: true,
                rewrite: (path: string) => path.replace(/^\/api\/notification/, ""),
            },
            "/api": {
                target: "http://localhost:8100",
                changeOrigin: true,
                rewrite: (path: string) => path.replace(/^\/api/, ""),
            },
        },
    },
    build: {
        outDir: "dist",
        sourcemap: false,
        chunkSizeWarningLimit: 500,
    },
});

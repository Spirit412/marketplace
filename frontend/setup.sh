#!/usr/bin/env bash
# =============================================================================
# Marketplace Frontend — Setup Script
# =============================================================================
# Назначение: Проверка, установка и настройка окружения для React-фронтенда
#   Multi-Vendor Marketplace.
#
# Использование:
#   ./setup.sh                  Интерактивное меню
#   ./setup.sh check            Только проверка окружения
#   ./setup.sh install          Установка зависимостей и создание проекта
#   ./setup.sh full             Полный цикл: check → install → configure
#   ./setup.sh help             Справка
#
# Требования к системе:
#   - Linux (протестировано: Ubuntu 22.04+, Debian 12+, Fedora 39+)
#   - Доступ в интернет (npm registry, GitHub)
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Конфигурация (редактировать под проект)
# -----------------------------------------------------------------------------

readonly PROJECT_NAME="marketplace-frontend"
readonly PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
readonly NODE_MIN_MAJOR=20
readonly NPM_MIN_MAJOR=10
readonly NODE_MAX_MAJOR=24

# Цвета для терминала
readonly CLR_RESET='\033[0m'
readonly CLR_BOLD='\033[1m'
readonly CLR_RED='\033[31m'
readonly CLR_GREEN='\033[32m'
readonly CLR_YELLOW='\033[33m'
readonly CLR_BLUE='\033[34m'
readonly CLR_CYAN='\033[36m'
readonly CLR_DIM='\033[2m'

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

info()    { printf "  ${CLR_BLUE}ℹ${CLR_RESET} %s\n" "$*"; }
success() { printf "  ${CLR_GREEN}✓${CLR_RESET} %s\n" "$*"; }
warn()    { printf "  ${CLR_YELLOW}⚠${CLR_RESET} %s\n" "$*"; }
error()   { printf "  ${CLR_RED}✗${CLR_RESET} %s\n" "$*" >&2; }
header()  { printf "\n${CLR_BOLD}${CLR_CYAN}═══ %s ═══${CLR_RESET}\n\n" "$*"; }
dim()     { printf "  ${CLR_DIM}%s${CLR_RESET}\n" "$*"; }

die() {
    error "$*"
    exit 1
}

press_enter() {
    printf "\n  ${CLR_DIM}Нажмите Enter чтобы продолжить...${CLR_RESET}"
    read -r _
}

# -----------------------------------------------------------------------------
# Справка
# -----------------------------------------------------------------------------

show_help() {
    cat << 'HELPEOF'

Marketplace Frontend — Setup Script
═══════════════════════════════════════

НАЗНАЧЕНИЕ
  Проверяет системные требования, устанавливает Node.js-окружение,
  создаёт React-проект на Vite + TypeScript и настраивает весь стек:
  Tailwind CSS v4, shadcn/ui, TanStack Router, TanStack Query, Zustand,
  React Hook Form + Zod, Axios.

ИСПОЛЬЗОВАНИЕ
  ./setup.sh                 → интерактивное меню
  ./setup.sh check           → только проверка окружения
  ./setup.sh install         → создать проект и установить зависимости
  ./setup.sh configure       → только настройка конфигов (после install)
  ./setup.sh full            → check → install → configure (всё сразу)
  ./setup.sh verify          → прогнать tsc + lint
  ./setup.sh help            → эта справка

СОСТАВ СТЕКА (React, 2026)
  • Vite 7                    сборка (HMR < 50ms)
  • React 19 + TypeScript 5.7
  • Tailwind CSS v4            utility-first CSS
  • shadcn/ui                  компоненты (Radix + Tailwind)
  • TanStack Router v1         типобезопасный роутинг
  • TanStack Query v5          серверный стейт + кэширование
  • Zustand v5                 клиентский стейт (корзина, ui)
  • React Hook Form v7 + Zod   формы + валидация
  • Axios v1                   HTTP-клиент (interceptors, retry)
  • Lucide React               иконки (бесплатно, tree-shakeable)

СИСТЕМНЫЕ ТРЕБОВАНИЯ
  • node   ≥ 20.0.0  (LTS)
  • npm    ≥ 10.0.0
  • git    ≥ 2.30

ФАЙЛЫ, СОЗДАВАЕМЫЕ СКРИПТОМ
  package.json, tsconfig.json, tsconfig.app.json, tsconfig.node.json
  vite.config.ts, index.html, tailwind.config.ts, components.json
  src/ (полная структура: routes, components, features, lib, store, hooks, types)
  .env.example, .eslintrc.cjs, .prettierrc

ПРИМЕЧАНИЯ
  • Скрипт идемпотентен: можно перезапускать, не ломая существующие файлы.
  • При повторном запуске install уже существующие файлы НЕ перезаписываются.
  • Для ручной установки Node.js: https://nodejs.org или через nvm.

HELPEOF
}

# -----------------------------------------------------------------------------
# Проверка версии утилиты
# -----------------------------------------------------------------------------

check_version() {
    # check_version <binary> <min_major> <friendly_name> [max_major]
    local binary="$1"
    local min_major="$2"
    local name="$3"
    local max_major="${4:-99}"

    if ! command -v "$binary" &>/dev/null; then
        error "$name не найден (команда '$binary' отсутствует в PATH)"
        return 1
    fi

    local version
    version=$("$binary" --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1)
    if [[ -z "$version" ]]; then
        # fallback: попробовать -v
        version=$("$binary" -v 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1)
    fi

    if [[ -z "$version" ]]; then
        warn "$name: не удалось определить версию (установлен, но --version не дал x.y.z)"
        return 0
    fi

    local major
    major=$(echo "$version" | cut -d. -f1)

    if (( major < min_major )); then
        error "$name: версия $version (требуется ≥ ${min_major}.0.0)"
        return 1
    fi

    if (( major > max_major )); then
        warn "$name: версия $version новее ожидаемой (макс. ${max_major}.x) — может работать, но не проверялось"
        return 0
    fi

    success "$name $version"
    return 0
}

# -----------------------------------------------------------------------------
# Проверка всего окружения
# -----------------------------------------------------------------------------

check_environment() {
    header "Проверка окружения"
    local errors=0

    check_version node "$NODE_MIN_MAJOR" "Node.js" "$NODE_MAX_MAJOR" || ((errors++))
    check_version npm  "$NPM_MIN_MAJOR"  "npm"                            || ((errors++))

    if command -v git &>/dev/null; then
        local git_ver
        git_ver=$(git --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1)
        success "git ${git_ver:-установлен}"
    else
        error "git не найден — нужен для загрузки зависимостей"
        ((errors++))
    fi

    # Проверка доступности npm registry
    if command -v npm &>/dev/null; then
        if npm ping --loglevel silent &>/dev/null; then
            success "npm registry доступен"
        else
            error "npm registry недоступен — проверьте интернет"
            ((errors++))
        fi
    fi

    # Проверка свободного места (> 2 GB)
    local free_mb
    free_mb=$(df -BM "$PROJECT_DIR" 2>/dev/null | awk 'NR==2 {print $4}' | sed 's/M//')
    if [[ -n "$free_mb" ]] && (( free_mb < 2048 )); then
        warn "Свободного места: ${free_mb} MB (рекомендуется ≥ 2048 MB для node_modules)"
    else
        success "Свободного места: ${free_mb:-?} MB"
    fi

    if (( errors > 0 )); then
        echo ""
        error "Найдено проблем: $errors. Устраните и перезапустите."
        return 1
    fi

    echo ""
    success "Окружение готово!"
    return 0
}

# -----------------------------------------------------------------------------
# Создание package.json
# -----------------------------------------------------------------------------

write_package_json() {
    local pkg_path="$PROJECT_DIR/package.json"
    if [[ -f "$pkg_path" ]]; then
        warn "package.json уже существует — пропускаю"
        return 0
    fi

    info "Создаю package.json..."
    cat > "$pkg_path" << 'PKGJSON'
{
  "name": "marketplace-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "lint": "eslint . --max-warnings 0",
    "format": "prettier --write \"src/**/*.{ts,tsx,css,json}\"",
    "typecheck": "tsc --noEmit",
    "add-component": "npx shadcn@latest add"
  },
  "dependencies": {
    "@hookform/resolvers": "^5.7.0",
    "@radix-ui/react-avatar": "^1.2.0",
    "@radix-ui/react-dialog": "^1.1.0",
    "@radix-ui/react-dropdown-menu": "^2.1.0",
    "@radix-ui/react-label": "^2.1.0",
    "@radix-ui/react-select": "^2.3.0",
    "@radix-ui/react-separator": "^1.1.0",
    "@radix-ui/react-slot": "^1.3.0",
    "@radix-ui/react-tabs": "^1.1.0",
    "@radix-ui/react-toast": "^1.2.0",
    "@radix-ui/react-toggle": "^1.1.0",
    "@radix-ui/react-tooltip": "^1.2.0",
    "@tanstack/react-query": "^5.101.0",
    "@tanstack/react-router": "^1.170.0",
    "axios": "^1.19.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "lucide-react": "^1.28.0",
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "react-hook-form": "^7.84.0",
    "tailwind-merge": "^3.6.0",
    "tailwindcss-animate": "^1.0.7",
    "zod": "^4.4.0",
    "@reduxjs/toolkit": "^2.12.0",
    "react-redux": "^9.3.0",
    "redux-persist": "^6.0.0"
  },
  "devDependencies": {
    "@eslint/js": "^10.0.0",
    "@tanstack/router-devtools": "^1.167.0",
    "@tanstack/router-plugin": "^1.168.0",
    "@types/react": "^19.2.0",
    "@types/react-dom": "^19.2.0",
    "@vitejs/plugin-react": "^6.0.0",
    "autoprefixer": "^10.5.0",
    "eslint": "^10.8.0",
    "eslint-plugin-react-hooks": "^7.1.0",
    "eslint-plugin-react-refresh": "^0.5.0",
    "globals": "^17.9.0",
    "postcss": "^8.5.0",
    "prettier": "^3.9.0",
    "prettier-plugin-tailwindcss": "^0.8.0",
    "tailwindcss": "^4.3.0",
    "typescript": "~5.7.0",
    "typescript-eslint": "^8.66.0",
    "vite": "^8.2.0"
  }
}
PKGJSON
    success "package.json создан"
}

# -----------------------------------------------------------------------------
# Создание конфигурационных файлов
# -----------------------------------------------------------------------------

write_tsconfigs() {
    local ts_main="$PROJECT_DIR/tsconfig.json"

    if [[ -f "$ts_main" ]]; then
        warn "tsconfig.json уже существует — пропускаю"
        return 0
    fi

    info "Создаю TypeScript-конфиги..."

    # Главный tsconfig.json — ссылается на дочерние
    cat > "$ts_main" << 'TSCMAIN'
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ],
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
TSCMAIN

    # tsconfig.app.json — для исходников приложения
    cat > "$PROJECT_DIR/tsconfig.app.json" << 'TSCAPP'
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "verbatimModuleSyntax": true,
    "skipLibCheck": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"]
}
TSCAPP

    # tsconfig.node.json — для vite.config.ts
    cat > "$PROJECT_DIR/tsconfig.node.json" << 'TSCNODE'
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "skipLibCheck": true
  },
  "include": ["vite.config.ts"]
}
TSCNODE

    success "TypeScript-конфиги созданы"
}

write_vite_config() {
    local cfg_path="$PROJECT_DIR/vite.config.ts"
    if [[ -f "$cfg_path" ]]; then
        warn "vite.config.ts уже существует — пропускаю"
        return 0
    fi

    info "Создаю vite.config.ts..."
    cat > "$cfg_path" << 'VITECFG'
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { TanStackRouterVite } from "@tanstack/router-plugin/vite";
import path from "node:path";

export default defineConfig({
    plugins: [
        TanStackRouterVite({ target: "react", autoCodeSplitting: true }),
        react(),
    ],
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
        },
    },
    server: {
        port: 5173,
        proxy: {
            // Прокси к API Gateway (сервисы бекенда)
            "/api": {
                target: "http://localhost:8100",
                changeOrigin: true,
                rewrite: (p: string) => p.replace(/^\/api/, ""),
            },
            // WebSocket-уведомления — напрямую к notification-service
            "/ws": {
                target: "ws://localhost:8150",
                ws: true,
            },
        },
    },
});
VITECFG
    success "vite.config.ts создан"
}

write_tailwind_config() {
    local cfg_path="$PROJECT_DIR/tailwind.config.ts"
    if [[ -f "$cfg_path" ]]; then
        warn "tailwind.config.ts уже существует — пропускаю"
        return 0
    fi

    info "Создаю tailwind.config.ts (Tailwind CSS v4)..."
    cat > "$cfg_path" << 'TWCSS'
import type { Config } from "tailwindcss";
import tailwindcssAnimate from "tailwindcss-animate";
export default {
    content: ["./index.html", "./src/**/*.{ts,tsx}"],
    theme: {
        extend: {
            colors: {
                border: "hsl(var(--border))",
                input: "hsl(var(--input))",
                ring: "hsl(var(--ring))",
                background: "hsl(var(--background))",
                foreground: "hsl(var(--foreground))",
                primary: {
                    DEFAULT: "hsl(var(--primary))",
                    foreground: "hsl(var(--primary-foreground))",
                },
                secondary: {
                    DEFAULT: "hsl(var(--secondary))",
                    foreground: "hsl(var(--secondary-foreground))",
                },
                destructive: {
                    DEFAULT: "hsl(var(--destructive))",
                    foreground: "hsl(var(--destructive-foreground))",
                },
                muted: {
                    DEFAULT: "hsl(var(--muted))",
                    foreground: "hsl(var(--muted-foreground))",
                },
                accent: {
                    DEFAULT: "hsl(var(--accent))",
                    foreground: "hsl(var(--accent-foreground))",
                },
                card: {
                    DEFAULT: "hsl(var(--card))",
                    foreground: "hsl(var(--card-foreground))",
                },
            },
            borderRadius: {
                lg: "var(--radius)",
                md: "calc(var(--radius) - 2px)",
                sm: "calc(var(--radius) - 4px)",
            },
            fontFamily: {
                sans: ["Inter", "system-ui", "sans-serif"],
                mono: ["JetBrains Mono", "monospace"],
            },
        },
    },
    plugins: [tailwindcssAnimate],
} satisfies Config;
TWCSS
    success "tailwind.config.ts создан"
}

write_postcss_config() {
    local cfg_path="$PROJECT_DIR/postcss.config.js"
    if [[ -f "$cfg_path" ]]; then
        warn "postcss.config.js уже существует — пропускаю"
        return 0
    fi

    info "Создаю postcss.config.js..."
    cat > "$cfg_path" << 'POSTCSS'
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
POSTCSS
    success "postcss.config.js создан"
}

write_components_json() {
    local cfg_path="$PROJECT_DIR/components.json"
    if [[ -f "$cfg_path" ]]; then
        warn "components.json уже существует — пропускаю"
        return 0
    fi

    info "Создаю components.json (shadcn/ui)..."
    cat > "$cfg_path" << 'COMPJSON'
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "src/index.css",
    "baseColor": "neutral",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib"
  },
  "iconLibrary": "lucide"
}
COMPJSON
    success "components.json создан"
}

write_index_html() {
    local html_path="$PROJECT_DIR/index.html"
    if [[ -f "$html_path" ]]; then
        warn "index.html уже существует — пропускаю"
        return 0
    fi

    info "Создаю index.html..."
    cat > "$html_path" << 'HTML'
<!doctype html>
<html lang="ru">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="Multi-Vendor Marketplace — платформа для продавцов и покупателей" />
    <title>Marketplace</title>
  </head>
  <body class="min-h-screen bg-background font-sans text-foreground antialiased">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
HTML
    success "index.html создан"
}

write_env_example() {
    local env_path="$PROJECT_DIR/.env.example"
    if [[ -f "$env_path" ]]; then
        warn ".env.example уже существует — пропускаю"
        return 0
    fi

    info "Создаю .env.example..."
    cat > "$env_path" << 'ENV'
# =============================================================================
# Marketplace Frontend — Environment Variables
# =============================================================================
# Скопируйте этот файл в .env и заполните значениями:
#   cp .env.example .env

# API Gateway (backend)
VITE_API_BASE_URL=http://localhost:8100

# Auth service (прямой доступ для login/register/refresh)
VITE_AUTH_URL=http://localhost:8110

# Notification WebSocket
VITE_WS_URL=ws://localhost:8150/ws

# Время жизни access-токена в минутах (для упреждающего refresh)
VITE_TOKEN_REFRESH_MARGIN_MIN=2

# Фича-флаги
VITE_ENABLE_WEBSOCKET=true
VITE_ENABLE_ANALYTICS=false
ENV
    success ".env.example создан"
}

write_eslint_config() {
    local cfg_path="$PROJECT_DIR/eslint.config.js"
    if [[ -f "$cfg_path" ]]; then
        warn "eslint.config.js уже существует — пропускаю"
        return 0
    fi

    info "Создаю eslint.config.js (flat config, ESLint v10)..."
    cat > "$cfg_path" << 'ESLINT'
import js from "@eslint/js";
import tseslint from "typescript-eslint";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import globals from "globals";

export default tseslint.config(
    { ignores: ["dist"] },
    {
        extends: [js.configs.recommended, ...tseslint.configs.recommended],
        files: ["**/*.{ts,tsx}"],
        languageOptions: {
            ecmaVersion: 2022,
            globals: globals.browser,
        },
        plugins: {
            "react-hooks": reactHooks,
            "react-refresh": reactRefresh,
        },
        rules: {
            ...reactHooks.configs.recommended.rules,
            "react-refresh/only-export-components": ["warn", { allowConstantExport: true }],
            "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
        },
    },
);
ESLINT
    success "eslint.config.js создан"
}

write_prettier_config() {
    local cfg_path="$PROJECT_DIR/.prettierrc"
    if [[ -f "$cfg_path" ]]; then
        warn ".prettierrc уже существует — пропускаю"
        return 0
    fi

    info "Создаю .prettierrc..."
    cat > "$cfg_path" << 'PRETTIER'
{
  "semi": true,
  "singleQuote": false,
  "tabWidth": 4,
  "trailingComma": "all",
  "printWidth": 100,
  "plugins": ["prettier-plugin-tailwindcss"]
}
PRETTIER
    success ".prettierrc создан"
}

write_gitignore() {
    local cfg_path="$PROJECT_DIR/.gitignore"
    if [[ -f "$cfg_path" ]]; then
        warn ".gitignore уже существует — пропускаю"
        return 0
    fi

    info "Создаю .gitignore..."
    cat > "$cfg_path" << 'GITIGN'
node_modules/
dist/
.env
.env.local
*.log
.DS_Store
.vite/
tsconfig.tsbuildinfo
GITIGN
    success ".gitignore создан"
}

# -----------------------------------------------------------------------------
# Структура src/
# -----------------------------------------------------------------------------

scaffold_src() {
    info "Создаю структуру src/..."

    # Директории
    mkdir -p "$PROJECT_DIR/src"/{components/{ui,layout,shared},features/{auth,catalog,orders,cart,payments,inventory,notifications,reports,imports,admin},lib,store,hooks,types,routes}
    mkdir -p "$PROJECT_DIR/public"

    # Главная точка входа
    cat > "$PROJECT_DIR/src/main.tsx" << 'MAINTSX'
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { Provider } from "react-redux";
import { PersistGate } from "redux-persist/integration/react";
import { RouterProvider, createRouter } from "@tanstack/react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { store, persistor } from "./store";
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
        mutations: {
            retry: 0,
        },
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

createRoot(document.getElementById("root")!).render(
    <StrictMode>
        <Provider store={store}>
            <PersistGate loading={null} persistor={persistor}>
                <QueryClientProvider client={query_client}>
                    <RouterProvider router={router} />
                </QueryClientProvider>
            </PersistGate>
        </Provider>
    </StrictMode>,
);
MAINTSX

    # Глобальные стили (Tailwind v4 + shadcn/ui CSS-переменные)
    cat > "$PROJECT_DIR/src/index.css" << 'CSSINDEX'
@import "tailwindcss";

/* shadcn/ui — CSS-переменные для темизации */
@theme inline {
    --color-background: var(--background);
    --color-foreground: var(--foreground);
    --color-card: var(--card);
    --color-card-foreground: var(--card-foreground);
    --color-primary: var(--primary);
    --color-primary-foreground: var(--primary-foreground);
    --color-secondary: var(--secondary);
    --color-secondary-foreground: var(--secondary-foreground);
    --color-muted: var(--muted);
    --color-muted-foreground: var(--muted-foreground);
    --color-accent: var(--accent);
    --color-accent-foreground: var(--accent-foreground);
    --color-destructive: var(--destructive);
    --color-destructive-foreground: var(--destructive-foreground);
    --color-border: var(--border);
    --color-input: var(--input);
    --color-ring: var(--ring);
    --radius-sm: calc(var(--radius) - 4px);
    --radius-md: calc(var(--radius) - 2px);
    --radius-lg: var(--radius);
}

@layer base {
    :root {
        --background: 0 0% 100%;
        --foreground: 0 0% 3.9%;
        --card: 0 0% 100%;
        --card-foreground: 0 0% 3.9%;
        --primary: 0 0% 9%;
        --primary-foreground: 0 0% 98%;
        --secondary: 0 0% 96.1%;
        --secondary-foreground: 0 0% 9%;
        --muted: 0 0% 96.1%;
        --muted-foreground: 0 0% 45.1%;
        --accent: 0 0% 96.1%;
        --accent-foreground: 0 0% 9%;
        --destructive: 0 84.2% 60.2%;
        --destructive-foreground: 0 0% 98%;
        --border: 0 0% 89.8%;
        --input: 0 0% 89.8%;
        --ring: 0 0% 3.9%;
        --radius: 0.5rem;
    }

    .dark {
        --background: 0 0% 3.9%;
        --foreground: 0 0% 98%;
        --card: 0 0% 3.9%;
        --card-foreground: 0 0% 98%;
        --primary: 0 0% 98%;
        --primary-foreground: 0 0% 9%;
        --secondary: 0 0% 14.9%;
        --secondary-foreground: 0 0% 98%;
        --muted: 0 0% 14.9%;
        --muted-foreground: 0 0% 63.9%;
        --accent: 0 0% 14.9%;
        --accent-foreground: 0 0% 98%;
        --destructive: 0 62.8% 40.6%;
        --destructive-foreground: 0 0% 98%;
        --border: 0 0% 14.9%;
        --input: 0 0% 14.9%;
        --ring: 0 0% 83.1%;
    }
}
CSSINDEX

    # utils.ts для shadcn/ui (cn-хелпер)
    cat > "$PROJECT_DIR/src/lib/utils.ts" << 'UTILSTS'
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/** Объединяет CSS-классы с поддержкой Tailwind-конфликтов */
export function cn(...inputs: ClassValue[]): string {
    return twMerge(clsx(inputs));
}

/** Форматирует цену в рублях */
export function format_price(price: number, currency: string = "RUB"): string {
    return new Intl.NumberFormat("ru-RU", {
        style: "currency",
        currency,
        minimumFractionDigits: 2,
    }).format(price);
}

/** Форматирует дату в российском локале */
export function format_date(date: string | Date): string {
    return new Intl.DateTimeFormat("ru-RU", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    }).format(new Date(date));
}

/** Обрезает строку с многоточием */
export function truncate(text: string, max_length: number): string {
    if (text.length <= max_length) return text;
    return text.slice(0, max_length - 1) + "…";
}
UTILSTS

    # API-клиент
    cat > "$PROJECT_DIR/src/lib/api-client.ts" << 'APICLIENT'
import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import { store } from "@/store";
import { setTokens, clearAuth } from "@/store/auth-slice";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8100";
const AUTH_URL = import.meta.env.VITE_AUTH_URL ?? "http://localhost:8110";

/** API-клиент к Gateway */
export const api_client = axios.create({
    baseURL: API_BASE,
    timeout: 15_000,
    headers: { "Content-Type": "application/json" },
});

/** Клиент к auth-service (login/register/refresh — без gateway) */
export const auth_client = axios.create({
    baseURL: AUTH_URL,
    timeout: 10_000,
    headers: { "Content-Type": "application/json" },
});

// ---------------------------------------------------------------------------
// Interceptor: добавляет access-токен ко всем запросам
// ---------------------------------------------------------------------------

api_client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    const token = store.getState().auth.access_token;
    if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

auth_client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    const token = store.getState().auth.access_token;
    if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// ---------------------------------------------------------------------------
// Interceptor: при 401 пытается обновить токен, иначе — logout
// ---------------------------------------------------------------------------

let refresh_promise: Promise<string | null> | null = null;

async function try_refresh(): Promise<string | null> {
    const state = store.getState().auth;
    if (!state.refresh_token) return null;

    try {
        const { data } = await auth_client.post<{ access_token: string; refresh_token: string }>(
            "/auth/refresh",
            { refresh_token: state.refresh_token },
        );
        store.dispatch(setTokens({ access: data.access_token, refresh: data.refresh_token }));
        return data.access_token;
    } catch {
        store.dispatch(clearAuth());
        return null;
    }
}

api_client.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
        const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
        if (error.response?.status !== 401 || original._retry) {
            return Promise.reject(error);
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
            return api_client(original);
        }

        window.location.href = "/login";
        return Promise.reject(error);
    },
);
APICLIENT

    # Типы
    cat > "$PROJECT_DIR/src/types/index.ts" << 'TYPESINDEX'
// =============================================================================
// Общие типы, зеркалирующие backend-контракты
// =============================================================================

/** UUID v7 (time-sortable) */
export type UUID = string;

/** Пагинация */
export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    page_size: number;
    pages: number;
}

// ---------- Auth ----------

export type Role = "customer" | "seller" | "moderator" | "admin" | "super_admin";

export interface LoginRequest {
    email: string;
    password: string;
}

export interface RegisterRequest {
    email: string;
    password: string;
    role?: Role;
    timezone?: string;
}

export interface TokenPair {
    access_token: string;
    refresh_token: string;
}

export interface UserProfile {
    id: UUID;
    email: string;
    role: Role;
    is_admin: boolean;
    timezone: string;
    is_blocked: boolean;
}

// ---------- Catalog ----------

export interface Product {
    id: UUID;
    seller_id: UUID;
    category_id: UUID;
    name: string;
    slug: string;
    description: string | null;
    price: number;
    compare_at_price: number | null;
    currency: string;
    stock_visible: number;
    images: string[];
    custom_properties: Record<string, unknown>;
    is_active: boolean;
    is_moderated: boolean;
    created_at: string;
    updated_at: string;
}

export interface Category {
    id: UUID;
    name: string;
    slug: string;
    parent_id: UUID | null;
    depth: number;
    image_url: string | null;
    is_active: boolean;
    children: Category[];
}

// ---------- Orders ----------

export type OrderStatus = "pending" | "confirmed" | "shipped" | "delivered" | "cancelled";

export interface CartItem {
    product_id: UUID;
    name: string;
    price: number;
    quantity: number;
    image_url: string | null;
}

export interface Order {
    id: UUID;
    user_id: UUID;
    status: OrderStatus;
    items: OrderItem[];
    total_amount: number;
    currency: string;
    created_at: string;
    updated_at: string;
}

export interface OrderItem {
    product_id: UUID;
    name: string;
    price: number;
    quantity: number;
}

// ---------- Inventory ----------

export interface Warehouse {
    id: UUID;
    name: string;
    address: string | null;
    is_active: boolean;
}

export interface Stock {
    product_id: UUID;
    warehouse_id: UUID;
    quantity: number;
    reserved: number;
}

// ---------- Payment ----------

export type PaymentStatus = "pending" | "processing" | "succeeded" | "failed" | "refunded";

export interface Payment {
    id: UUID;
    order_id: UUID;
    amount: number;
    currency: string;
    status: PaymentStatus;
    payment_method: string;
    created_at: string;
}

// ---------- Notification ----------

export interface Notification {
    id: UUID;
    user_id: UUID;
    type: string;
    title: string;
    body: string;
    is_read: boolean;
    created_at: string;
}

// ---------- Report ----------

export type ReportStatus = "pending" | "processing" | "completed" | "failed";

export interface Report {
    id: UUID;
    user_id: UUID;
    report_type: string;
    status: ReportStatus;
    file_url: string | null;
    created_at: string;
}

// ---------- Import ----------

export type ImportStatus = "pending" | "processing" | "completed" | "failed";

export interface ImportTask {
    id: UUID;
    seller_id: UUID;
    import_type: string;
    status: ImportStatus;
    errors: ImportError[];
    created_at: string;
}

export interface ImportError {
    row: number;
    field: string;
    message: string;
}
TYPESINDEX

    # Типы для TanStack Router (авто-генерируются плагином)
    cat > "$PROJECT_DIR/src/routeTree.gen.ts" << 'ROUTETREE'
// This file is auto-generated by @tanstack/router-plugin.
// Run `npm run dev` to regenerate after changing routes.
// For now — placeholder that will be overwritten.

import { rootRoute } from "./routes/__root";

export const routeTree = rootRoute;
ROUTETREE

    # Redux Toolkit store
    mkdir -p "$PROJECT_DIR/src/store"

    cat > "$PROJECT_DIR/src/store/index.ts" << 'STOREINDEX'
import { configureStore, combineReducers } from "@reduxjs/toolkit";
import { persistStore, persistReducer } from "redux-persist";
import storage from "redux-persist/lib/storage";
import authReducer from "./auth-slice";
import cartReducer from "./cart-slice";
import uiReducer from "./ui-slice";

const rootReducer = combineReducers({
    auth: authReducer,
    cart: cartReducer,
    ui: uiReducer,
});

const persistConfig = {
    key: "marketplace",
    storage,
    whitelist: ["auth", "ui"],
};

const persistedReducer = persistReducer(persistConfig, rootReducer);

export const store = configureStore({
    reducer: persistedReducer,
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware({ serializableCheck: false }),
});

export const persistor = persistStore(store);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
STOREINDEX

    cat > "$PROJECT_DIR/src/store/auth-slice.ts" << 'AUTHSLICE'
import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type { UserProfile } from "@/types";

interface AuthState {
    access_token: string | null;
    refresh_token: string | null;
    profile: UserProfile | null;
    is_authenticated: boolean;
}

const initialState: AuthState = {
    access_token: null,
    refresh_token: null,
    profile: null,
    is_authenticated: false,
};

const authSlice = createSlice({
    name: "auth",
    initialState,
    reducers: {
        setTokens(state, action: PayloadAction<{ access: string; refresh: string }>) {
            state.access_token = action.payload.access;
            state.refresh_token = action.payload.refresh;
            state.is_authenticated = true;
        },
        setProfile(state, action: PayloadAction<UserProfile>) {
            state.profile = action.payload;
        },
        clearAuth(state) {
            state.access_token = null;
            state.refresh_token = null;
            state.profile = null;
            state.is_authenticated = false;
        },
    },
});

export const { setTokens, setProfile, clearAuth } = authSlice.actions;
export default authSlice.reducer;
AUTHSLICE

    cat > "$PROJECT_DIR/src/store/cart-slice.ts" << 'CARTSLICE'
import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type { CartItem } from "@/types";

interface CartState {
    items: CartItem[];
}

const initialState: CartState = { items: [] };

const cartSlice = createSlice({
    name: "cart",
    initialState,
    reducers: {
        addItem(state, action: PayloadAction<CartItem>) {
            const existing = state.items.find(
                (i) => i.product_id === action.payload.product_id,
            );
            if (existing) {
                existing.quantity += action.payload.quantity;
            } else {
                state.items.push(action.payload);
            }
        },
        removeItem(state, action: PayloadAction<string>) {
            state.items = state.items.filter((i) => i.product_id !== action.payload);
        },
        updateQuantity(state, action: PayloadAction<{ product_id: string; quantity: number }>) {
            const item = state.items.find((i) => i.product_id === action.payload.product_id);
            if (item) {
                if (action.payload.quantity <= 0) {
                    state.items = state.items.filter((i) => i.product_id !== action.payload.product_id);
                } else {
                    item.quantity = action.payload.quantity;
                }
            }
        },
        clearCart(state) {
            state.items = [];
        },
    },
});

export const { addItem, removeItem, updateQuantity, clearCart } = cartSlice.actions;

export const selectCartItems = (state: { cart: CartState }) => state.cart.items;
export const selectCartTotal = (state: { cart: CartState }) =>
    state.cart.items.reduce((sum, i) => sum + i.price * i.quantity, 0);
export const selectCartCount = (state: { cart: CartState }) =>
    state.cart.items.reduce((sum, i) => sum + i.quantity, 0);

export default cartSlice.reducer;
CARTSLICE

    cat > "$PROJECT_DIR/src/store/ui-slice.ts" << 'UISLICE'
import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

type Theme = "light" | "dark" | "system";

interface UIState {
    theme: Theme;
    sidebar_open: boolean;
    active_modal: string | null;
}

const initialState: UIState = {
    theme: "system",
    sidebar_open: true,
    active_modal: null,
};

const uiSlice = createSlice({
    name: "ui",
    initialState,
    reducers: {
        setTheme(state, action: PayloadAction<Theme>) {
            state.theme = action.payload;
        },
        toggleSidebar(state) {
            state.sidebar_open = !state.sidebar_open;
        },
        openModal(state, action: PayloadAction<string>) {
            state.active_modal = action.payload;
        },
        closeModal(state) {
            state.active_modal = null;
        },
    },
});

export const { setTheme, toggleSidebar, openModal, closeModal } = uiSlice.actions;
export const selectTheme = (state: { ui: UIState }) => state.ui.theme;
export default uiSlice.reducer;
UISLICE

    # Root route
    cat > "$PROJECT_DIR/src/routes/__root.tsx" << 'ROOTROUTE'
import { createRootRoute, Outlet } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/router-devtools";

export const Route = createRootRoute({
    component: () => (
        <>
            <Outlet />
            {import.meta.env.DEV && <TanStackRouterDevtools position="bottom-right" />}
        </>
    ),
});
ROOTROUTE

    # Index route (заглушка)
    cat > "$PROJECT_DIR/src/routes/index.tsx" << 'INDEXROUTE'
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
    component: IndexPage,
});

function IndexPage() {
    return (
        <div className="flex min-h-screen items-center justify-center">
            <div className="text-center">
                <h1 className="text-4xl font-bold tracking-tight">Marketplace</h1>
                <p className="mt-2 text-muted-foreground">
                    Multi-Vendor Marketplace — фронтенд готов к разработке.
                </p>
            </div>
        </div>
    );
}
INDEXROUTE

    # App.tsx (резервный, основной вход через main.tsx + RouterProvider)
    cat > "$PROJECT_DIR/src/App.tsx" << 'APPTSX'
// Основной вход — main.tsx (использует RouterProvider напрямую).
// Этот файл оставлен для совместимости, но не используется.
export default function App() {
    return null;
}
APPTSX

    # vite.svg (favicon-заглушка)
    cat > "$PROJECT_DIR/public/vite.svg" << 'VITESVG'
<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="6" fill="#18181b"/>
  <text x="16" y="22" text-anchor="middle" font-size="18" font-family="sans-serif" fill="#fafafa">M</text>
</svg>
VITESVG

    success "Структура src/ создана"
}

# -----------------------------------------------------------------------------
# Установка зависимостей
# -----------------------------------------------------------------------------

install_dependencies() {
    header "Установка npm-зависимостей"

    cd "$PROJECT_DIR"

    info "Устанавливаю пакеты (это может занять пару минут)..."
    if npm install --loglevel warn; then
        success "Зависимости установлены"
    else
        die "Ошибка при npm install. Проверьте интернет и права доступа."
    fi
}

# -----------------------------------------------------------------------------
# Шаг 1: Проверка
# -----------------------------------------------------------------------------

step_check() {
    check_environment
}

# -----------------------------------------------------------------------------
# Шаг 2: Установка
# -----------------------------------------------------------------------------

step_install() {
    header "Создание проекта"

    write_package_json
    write_tsconfigs
    write_vite_config
    write_tailwind_config
    write_postcss_config
    write_components_json
    write_index_html
    write_env_example
    write_eslint_config
    write_prettier_config
    write_gitignore
    scaffold_src
    install_dependencies

    header "Установка завершена"
    success "Проект '$PROJECT_NAME' создан в $PROJECT_DIR"
    echo ""
    info "Дальнейшие шаги:"
    dim "  1. Скопируйте .env:  cp .env.example .env"
    dim "  2. Запустите dev-сервер:  npm run dev"
    dim "  3. Откройте:  http://localhost:5173"
}

# -----------------------------------------------------------------------------
# Шаг 3: Конфигурация (пост-установка)
# -----------------------------------------------------------------------------

step_configure() {
    header "Пост-установочная конфигурация"

    if [[ ! -f "$PROJECT_DIR/package.json" ]]; then
        die "package.json не найден — сначала запустите './setup.sh install'"
    fi

    # Проверяем, установлены ли зависимости
    if [[ ! -d "$PROJECT_DIR/node_modules" ]]; then
        warn "node_modules отсутствует — устанавливаю..."
        install_dependencies
    fi

    # Копируем .env если его нет
    if [[ ! -f "$PROJECT_DIR/.env" ]]; then
        if [[ -f "$PROJECT_DIR/.env.example" ]]; then
            cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
            success ".env скопирован из .env.example"
        fi
    else
        info ".env уже существует"
    fi

    # Даём рекомендации по shadcn/ui компонентам
    echo ""
    info "Рекомендуемые shadcn/ui компоненты для первичной установки:"
    dim "  npx shadcn@latest add button card input label separator dropdown-menu avatar tabs dialog toast tooltip"
    echo ""
    info "Для запуска dev-сервера:"
    dim "  npm run dev"
}

# -----------------------------------------------------------------------------
# Шаг 4: Полный цикл
# -----------------------------------------------------------------------------

step_full() {
    header "Marketplace Frontend — Полная установка"
    echo ""

    if ! step_check; then
        die "Проверка окружения не пройдена. Исправьте ошибки и повторите."
    fi

    press_enter
    step_install
    step_configure

    header "Полная установка завершена"
    success "Фронтенд marketplace готов к разработке!"
    echo ""
    info "Быстрый старт:"
    dim "  cd $PROJECT_DIR"
    dim "  npm run dev"
    dim "  # Откройте http://localhost:5173"
}

# -----------------------------------------------------------------------------
# Шаг 5: Верификация
# -----------------------------------------------------------------------------

step_verify() {
    header "Верификация проекта"

    cd "$PROJECT_DIR"

    if [[ ! -f "package.json" ]]; then
        die "Проект не найден — запустите './setup.sh install' сначала"
    fi

    info "TypeScript-проверка (tsc --noEmit)..."
    if npx tsc --noEmit 2>&1; then
        success "TypeScript: ошибок нет"
    else
        warn "TypeScript: есть ошибки (возможно, ожидаемо на начальном этапе)"
    fi

    if [[ -f "node_modules/.bin/eslint" ]]; then
        info "ESLint..."
        npx eslint src/ --ext ts,tsx --max-warnings 10 2>&1 || warn "ESLint: есть предупреждения"
    fi

    echo ""
    success "Верификация завершена"
}

# -----------------------------------------------------------------------------
# Интерактивное меню
# -----------------------------------------------------------------------------

show_menu() {
    clear
    cat << 'MENUEOF'

   ╔══════════════════════════════════════════════╗
   ║        Marketplace Frontend — Setup          ║
   ║            React 19 + shadcn/ui              ║
   ╚══════════════════════════════════════════════╝

   Выберите действие:

     1  🩺  Проверить окружение (check)
     2  📦  Установить проект и зависимости (install)
     3  ⚙️   Настроить конфиги (configure)
     4  🚀  Полный цикл: check → install → configure (full)
     5  ✅  Верификация (tsc + lint)
     6  ❓  Справка (help)
     0  🚪  Выход

MENUEOF
    printf "  Ваш выбор [0-6]: "
}

interactive_menu() {
    while true; do
        show_menu
        read -r choice

        case "${choice:-0}" in
            1) step_check;          press_enter ;;
            2) step_install;        press_enter ;;
            3) step_configure;      press_enter ;;
            4) step_full;           press_enter ;;
            5) step_verify;         press_enter ;;
            6) show_help | less -R; press_enter ;;
            0) echo ""; info "Выход."; exit 0 ;;
            *) warn "Неверный выбор. Введите число 0-6."; sleep 1 ;;
        esac
    done
}

# -----------------------------------------------------------------------------
# Точка входа
# -----------------------------------------------------------------------------

main() {
    # Баннер
    printf "${CLR_CYAN}${CLR_BOLD}"
    printf "  Marketplace Frontend Setup  |  React 19 + shadcn/ui + TanStack\n"
    printf "${CLR_RESET}\n"

    case "${1:-menu}" in
        check)     step_check ;;
        install)   step_install ;;
        configure) step_configure ;;
        full)      step_full ;;
        verify)    step_verify ;;
        help|--help|-h)
            show_help
            ;;
        menu|"")
            interactive_menu
            ;;
        *)
            error "Неизвестная команда: '$1'"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"

import js from "@eslint/js";
import tseslint from "typescript-eslint";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import globals from "globals";

export default tseslint.config(
    { ignores: ["dist", "node_modules", "src/components/ui/**", "src/routeTree.gen.ts"] },

    // Основной конфиг — все TypeScript-файлы
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

            // ── TypeScript: базовые правила (не требуют type info) ──
            "@typescript-eslint/no-unused-vars": ["error", {
                argsIgnorePattern: "^_",
                varsIgnorePattern: "^_",
                caughtErrorsIgnorePattern: "^_",
            }],
            "@typescript-eslint/no-explicit-any": "error",
            "@typescript-eslint/explicit-function-return-type": "off",
            "@typescript-eslint/consistent-type-imports": ["error", {
                prefer: "type-imports",
                fixStyle: "separate-type-imports",
            }],
            "@typescript-eslint/no-non-null-assertion": "warn",

            // ── Общие правила ──
            "no-console": ["warn", { allow: ["warn", "error"] }],
            "no-debugger": "error",
            "no-alert": "error",
            "prefer-const": "error",
            "no-var": "error",
            "eqeqeq": ["error", "always", { null: "ignore" }],
            "no-duplicate-imports": "error",
            "sort-imports": ["warn", {
                ignoreCase: true,
                ignoreDeclarationSort: true,
            }],
        },
    },

    // Типизированные правила (требуют parserOptions.project)
    {
        files: ["src/**/*.{ts,tsx}"],
        languageOptions: {
            parserOptions: {
                project: ["./tsconfig.app.json", "./tsconfig.node.json"],
                tsconfigRootDir: import.meta.dirname,
            },
        },
        rules: {
            "@typescript-eslint/prefer-optional-chain": "warn",
            "@typescript-eslint/no-unnecessary-condition": "warn",
            "@typescript-eslint/no-floating-promises": "error",
            "@typescript-eslint/no-misused-promises": "error",
            "@typescript-eslint/await-thenable": "error",
        },
    },

    // Строже для production-кода (не тестов)
    {
        files: ["src/**/*.{ts,tsx}"],
        ignores: ["**/__tests__/**", "**/*.test.{ts,tsx}", "**/*.spec.{ts,tsx}"],
        rules: {
            "no-console": "error",
        },
    },

    // Route-файлы: разрешаем экспорт Route + component
    {
        files: ["src/routes/**/*.{ts,tsx}"],
        rules: {
            "react-refresh/only-export-components": "off",
        },
    },
);

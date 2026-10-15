# Multi-stage build for Marketplace Frontend
# Stage 1: build
FROM node:22-alpine AS build
WORKDIR /app

# Копируем только файлы зависимостей для кэширования слоя
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts \
 && npm ci --ignore-scripts \
 && npx vite --version

# Копируем исходники и собираем
COPY . .
RUN npm run build

# Stage 2: serve
FROM nginx:1.27-alpine

# Копируем кастомный nginx.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Копируем собранное приложение
COPY --from=build /app/dist /usr/share/nginx/html

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/health || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

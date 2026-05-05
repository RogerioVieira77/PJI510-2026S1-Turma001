# ── Stage 1: build Vite ─────────────────────────────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --prefer-offline

COPY . .
RUN npm run build

# ── Stage 2: serve via NGINX ─────────────────────────────────────────────────
FROM nginx:1.27-alpine AS runtime

# Remove config padrão
RUN rm /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.frontend.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

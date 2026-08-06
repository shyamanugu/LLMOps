# syntax=docker/dockerfile:1

# --- Stage 1: build the static assets -------------------------------------
FROM node:20-alpine AS build
WORKDIR /app

# Install dependencies first for better layer caching.
COPY package.json package-lock.json* ./
RUN npm ci || npm install

# Copy source and build. VITE_API_BASE can be overridden at build time.
COPY . .
ARG VITE_API_BASE=http://localhost:8000/api/v1
ENV VITE_API_BASE=${VITE_API_BASE}
RUN npm run build

# --- Stage 2: serve with nginx --------------------------------------------
FROM nginx:1.27-alpine AS runtime
LABEL org.opencontainers.image.title="LLMOps Console"
LABEL org.opencontainers.image.description="Static SPA served by nginx."

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost/ >/dev/null 2>&1 || exit 1

CMD ["nginx", "-g", "daemon off;"]

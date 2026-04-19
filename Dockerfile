# Stage 1: Build Next.js
FROM node:20-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Combined runtime
FROM python:3.13-slim

# Install Node.js + supervisord
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl supervisor \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend source
COPY app/ ./app/

# Frontend build output + production deps
COPY --from=frontend-builder /frontend /app/frontend
RUN cd /app/frontend && npm ci --omit=dev

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 8000 3000

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

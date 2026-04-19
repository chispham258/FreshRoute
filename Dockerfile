FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl supervisor nodejs npm \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Backend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/

# Frontend
COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN cd frontend && npm ci
COPY frontend/ ./frontend/
RUN cd frontend && npm run build

# Supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 8001 3000

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y openssl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system infostorage \
    && useradd --system --gid infostorage --create-home infostorage

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY --chown=infostorage:infostorage pyproject.toml README.md ./
COPY --chown=infostorage:infostorage python/ ./python/
COPY --chown=infostorage:infostorage web/ ./web/
COPY --chown=infostorage:infostorage web_frontend/ ./web_frontend/
COPY --chown=infostorage:infostorage docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

ENV INFOSTORAGE_WEB_DATA=/app/web/data \
    INFOSTORAGE_API_URL=https://127.0.0.1:8000 \
    INFOSTORAGE_FRONTEND_HOST=0.0.0.0 \
    INFOSTORAGE_FRONTEND_PORT=22 \
    INFOSTORAGE_COOKIE_SECURE=1 \
    INFOSTORAGE_TLS_CERT=/app/certs/cert.pem \
    INFOSTORAGE_TLS_KEY=/app/certs/key.pem \
    INFOSTORAGE_API_CA=/app/certs/cert.pem

RUN mkdir -p /app/web/data /app/certs \
    && chown -R infostorage:infostorage /app/web /app/certs \
    && chmod 0755 /usr/local/bin/docker-entrypoint.sh

USER infostorage

VOLUME ["/app/web/data", "/app/certs"]
EXPOSE 8000 22

ENTRYPOINT ["docker-entrypoint.sh"]
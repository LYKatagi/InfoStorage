#!/bin/sh
set -eu

TLS_CERT="${INFOSTORAGE_TLS_CERT:-/app/certs/cert.pem}"
TLS_KEY="${INFOSTORAGE_TLS_KEY:-/app/certs/key.pem}"

mkdir -p "$(dirname "$TLS_CERT")" "$(dirname "$TLS_KEY")"

if [ ! -f "$TLS_CERT" ] || [ ! -f "$TLS_KEY" ]; then
    openssl req -x509 -newkey rsa:2048 -nodes -sha256 -days 365 \
        -keyout "$TLS_KEY" \
        -out "$TLS_CERT" \
        -subj "/CN=localhost" \
        -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
fi

python -m uvicorn info_storage.web.main:app \
    --app-dir /app/python \
    --host 0.0.0.0 \
    --port 8000 \
    --ssl-certfile "$TLS_CERT" \
    --ssl-keyfile "$TLS_KEY" &
api_pid=$!

python -m web_frontend &
frontend_pid=$!

shutdown() {
    kill -TERM "$frontend_pid" "$api_pid" 2>/dev/null || true
    wait "$frontend_pid" 2>/dev/null || true
    wait "$api_pid" 2>/dev/null || true
    exit 0
}

trap shutdown TERM INT

while kill -0 "$api_pid" 2>/dev/null && kill -0 "$frontend_pid" 2>/dev/null; do
    sleep 1
done

kill -TERM "$frontend_pid" "$api_pid" 2>/dev/null || true
wait "$frontend_pid" 2>/dev/null || true
wait "$api_pid" 2>/dev/null || true
exit 1

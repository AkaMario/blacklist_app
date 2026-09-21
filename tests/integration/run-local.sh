#!/usr/bin/env bash
set -euo pipefail

# Requiere PostgreSQL (initdb, pg_ctl, createdb), Gunicorn, Newman, curl y OpenSSL.
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"
integration_tmp="$(mktemp -d /tmp/blacklist-integration.XXXXXX)"
db_port="${INTEGRATION_DB_PORT:-55432}"
api_port="${INTEGRATION_API_PORT:-5501}"
api_pid=""
cleanup() {
  if [ -n "$api_pid" ]; then
    kill "$api_pid" 2>/dev/null || true
    wait "$api_pid" 2>/dev/null || true
  fi
  pg_ctl -D "$integration_tmp/db" -m fast -w stop > /dev/null 2>&1 || true
  rm -rf "$integration_tmp"
}
trap cleanup EXIT

initdb -D "$integration_tmp/db" -U postgres -A trust > "$integration_tmp/initdb.log"
pg_ctl -D "$integration_tmp/db" -l "$integration_tmp/postgres.log" \
  -o "-h 127.0.0.1 -p $db_port -k $integration_tmp" -w start
createdb -h 127.0.0.1 -p "$db_port" -U postgres blacklist_integration
export DATABASE_URL="postgresql://postgres@127.0.0.1:$db_port/blacklist_integration"
export BEARER_TOKEN=integration-test-token

openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout "$integration_tmp/api.key" -out "$integration_tmp/api.crt" \
  -days 1 -subj '/CN=localhost' \
  -addext 'subjectAltName=DNS:localhost,IP:127.0.0.1' 2> "$integration_tmp/openssl.log"
gunicorn --workers 1 --bind "127.0.0.1:$api_port" \
  --certfile "$integration_tmp/api.crt" --keyfile "$integration_tmp/api.key" \
  src.main:app > "$integration_tmp/api.log" 2>&1 &
api_pid=$!

ready=false
for attempt in {1..30}; do
  if curl --fail --silent --max-time 2 --cacert "$integration_tmp/api.crt" \
    "https://localhost:$api_port/blacklists/ping" > /dev/null; then
    ready=true
    break
  fi
  if ! kill -0 "$api_pid" 2>/dev/null; then break; fi
  sleep 1
done
if [ "$ready" != true ]; then
  cat "$integration_tmp/api.log"
  exit 1
fi

mkdir -p reports
newman run tests/integration/postman/Black_list.postman_collection.json \
  --env-var "base_url=https://localhost:$api_port" \
  --env-var "bearer_token=$BEARER_TOKEN" \
  --ssl-extra-ca-certs "$integration_tmp/api.crt" \
  --timeout 300000 --timeout-request 15000 --timeout-script 10000 \
  --color off --reporters cli,junit \
  --reporter-junit-export reports/newman.xml

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
if [[ ${1:-} != "" && ${1:-} != --ingress ]]; then
  echo 'Uso: bash scripts/deploy-k8s.sh [--ingress]' >&2
  exit 2
fi

if command -v kubectl >/dev/null 2>&1; then
  kube=(kubectl)
else
  kube=(minikube kubectl --)
fi

"${kube[@]}" apply -f k8s/00-namespace.yaml
if ! "${kube[@]}" -n curso get secret blacklist-secret -o name >/dev/null 2>&1; then
  # Generar las credenciales sin guardarlas en archivos ni imprimirlas.
  python3 - <<'PY' | "${kube[@]}" create -f -
import json
import os
import secrets
from urllib.parse import quote

password = os.environ.get('POSTGRES_PASSWORD') or secrets.token_urlsafe(24)
token = os.environ.get('BEARER_TOKEN') or secrets.token_urlsafe(32)
print(json.dumps({
    'apiVersion': 'v1', 'kind': 'Secret',
    'metadata': {'name': 'blacklist-secret', 'namespace': 'curso'},
    'type': 'Opaque',
    'stringData': {
        'POSTGRES_PASSWORD': password,
        'BEARER_TOKEN': token,
        'DATABASE_URL': f'postgresql://postgres:{quote(password, safe="")}@postgres:5432/blacklist_db',
    },
}))
PY
fi

"${kube[@]}" apply -f k8s/10-postgres-config.yaml -f k8s/20-postgres.yaml \
  -f k8s/30-app-deployment.yaml -f k8s/31-app-service.yaml
"${kube[@]}" -n curso rollout status statefulset/postgres --timeout=300s
"${kube[@]}" -n curso rollout status deployment/blacklist-app --timeout=300s
"${kube[@]}" -n curso get pods,pvc,services
if [[ ${1:-} == --ingress ]]; then
  "${kube[@]}" apply -f k8s/40-ingress.yaml
fi

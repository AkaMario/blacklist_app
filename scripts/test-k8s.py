#!/usr/bin/env python3
"""Pruebas reales contra el laboratorio Kubernetes; usa solo la biblioteca estándar."""
import argparse
import base64
import json
import shutil
import socket
import subprocess
import tempfile
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def kube(*args):
    return subprocess.check_output(KUBE + ['-n', 'curso', *args], text=True)


def resource(*args):
    output = kube('get', *args, '-o', 'json')
    return json.loads(output) if output.strip() else {}


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f'PASS: {message}', flush=True)


def request(method, path, status, payload=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token is not None:
        headers['Authorization'] = f'Bearer {token}'
    data = None if payload is None else json.dumps(payload).encode()
    req = Request(BASE + path, data=data, headers=headers, method=method)
    try:
        response = urlopen(req, timeout=10)
    except HTTPError as error:
        response = error
    with response:
        body = json.load(response)
        check(response.code == status, f'{method} {path}: HTTP {status}')
        return body


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--persistence', action='store_true', help='Recrear el Pod postgres-0 y comprobar que el registro persiste')
parser.add_argument('--rollout', action='store_true', help='Reiniciar el Deployment y comprobar recuperación y datos')
options = parser.parse_args()
KUBE = ['kubectl'] if shutil.which('kubectl') else ['minikube', 'kubectl', '--']

print(kube('rollout', 'status', 'statefulset/postgres', '--timeout=300s'), end='')
print(kube('rollout', 'status', 'deployment/blacklist-app', '--timeout=300s'), end='')
deployment = resource('deployment', 'blacklist-app')
check(deployment['spec']['replicas'] == deployment['status'].get('readyReplicas') == 2, 'Dos réplicas listas')
pods = resource('pods', '-l', 'app=blacklist-app')['items']
for pod in pods:
    uid = kube('exec', pod['metadata']['name'], '-c', 'blacklist-app', '--', 'id', '-u').strip()
    check(uid == '10001', f"{pod['metadata']['name']} ejecuta con UID 10001")
slices = resource('endpointslices', '-l', 'kubernetes.io/service-name=blacklist-app')['items']
addresses = {addr for s in slices for e in s.get('endpoints', []) if e.get('conditions', {}).get('ready') for addr in e['addresses']}
check(len(addresses) == 2, 'Service publica dos direcciones listas')
check(resource('service', 'postgres')['spec']['clusterIP'] == 'None', 'Service de PostgreSQL es headless')
pvc = resource('pvc', 'data-postgres-0')
check(pvc['status']['phase'] == 'Bound', 'Volumen persistente enlazado')
token = base64.b64decode(resource('secret', 'blacklist-secret')['data']['BEARER_TOKEN']).decode()

with socket.socket() as sock:
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
BASE = f'http://127.0.0.1:{port}'
with tempfile.TemporaryFile(mode='w+') as log:
    forward = subprocess.Popen(KUBE + ['-n', 'curso', 'port-forward', 'service/blacklist-app', f'{port}:80'], stdout=log, stderr=log)
    try:
        for attempt in range(60):
            try:
                with urlopen(BASE + '/blacklists/ping', timeout=2) as response:
                    check(json.load(response) == {'message': 'pong'}, 'Health check sin autenticación')
                break
            except (URLError, TimeoutError):
                if forward.poll() is not None:
                    log.seek(0)
                    raise RuntimeError(log.read())
                time.sleep(1)
        else:
            raise TimeoutError('La API no respondió por port-forward')
        email = f'k8s-{uuid.uuid4().hex}@example.com'
        payload = {'email': email, 'app_uuid': str(uuid.uuid4()), 'blocked_reason': 'Prueba Kubernetes'}
        request('POST', '/blacklists', 201, payload, token)
        check(request('GET', f'/blacklists/{email}', 200, token=token)['is_blacklisted'] is True, 'Registro creado consultable')
        request('POST', '/blacklists', 409, payload, token)
        request('GET', f'/blacklists/{email}', 401)
        request('GET', f'/blacklists/{email}', 401, token=token + '-incorrecto')
        request('POST', '/blacklists', 401, payload)
        request('POST', '/blacklists', 400, {'email': 'invalido', 'app_uuid': 'invalido'}, token)
        request('GET', '/blacklists/not-an-email', 400, token=token)
        missing = f'ausente-{uuid.uuid4().hex}@example.com'
        check(request('GET', f'/blacklists/{missing}', 200, token=token)['is_blacklisted'] is False, 'Correo ausente no está bloqueado')
        if options.persistence:
            print('Recreando postgres-0 para verificar persistencia...', flush=True)
            old_uid = resource('pod', 'postgres-0')['metadata']['uid']
            kube('delete', 'pod', 'postgres-0', '--wait=true', '--timeout=120s')
            for attempt in range(60):
                pod = resource('pod', 'postgres-0', '--ignore-not-found')
                if pod and pod['metadata']['uid'] != old_uid:
                    break
                time.sleep(1)
            else:
                raise TimeoutError('PostgreSQL no fue recreado')
            kube('wait', '--for=condition=Ready', 'pod/postgres-0', '--timeout=300s')
            for attempt in range(30):
                try:
                    body = request('GET', f'/blacklists/{email}', 200, token=token)
                    check(body['is_blacklisted'] is True, 'Registro conservado tras recrear PostgreSQL')
                    break
                except (AssertionError, URLError, TimeoutError):
                    if attempt == 29:
                        raise
                    time.sleep(2)
            check(resource('pvc', 'data-postgres-0')['metadata']['uid'] == pvc['metadata']['uid'], 'Se conserva el mismo volumen')
    finally:
        forward.terminate()
        forward.wait(timeout=15)

if options.rollout:
    print('Reiniciando las réplicas de la aplicación...', flush=True)
    kube('rollout', 'restart', 'deployment/blacklist-app')
    print(kube('rollout', 'status', 'deployment/blacklist-app', '--timeout=300s'), end='')
    check(resource('deployment', 'blacklist-app')['status'].get('readyReplicas') == 2, 'Dos réplicas listas tras rolling update')
    # Consultar desde un contenedor nuevo evita reutilizar el port-forward al Pod anterior.
    code = 'import json,os,urllib.request; r=urllib.request.Request("http://127.0.0.1:8080/blacklists/' + email + '",headers={"Authorization":"Bearer "+os.environ["BEARER_TOKEN"]}); assert json.load(urllib.request.urlopen(r))["is_blacklisted"] is True; print("ok")'
    check(kube('exec', 'deployment/blacklist-app', '-c', 'blacklist-app', '--', 'python', '-c', code).strip() == 'ok', 'Registro consultable desde una réplica nueva')
print('Todas las pruebas Kubernetes completadas.', flush=True)

# Laboratorio Kubernetes: blacklist_app

[Resultados de la ejecución local](resultados_kubernetes.md).

Los manifiestos siguen la guía del laboratorio con el namespace `curso`.
PostgreSQL 14 usa un StatefulSet, Service headless y PVC de 1 GiB; la API tiene
dos réplicas, probes, recursos y UID 10001. Se conserva además una startupProbe
y el Ingress opcional de la configuración anterior.

## Preparar el clúster y la imagen

Requisitos: Docker corriendo, Minikube, Python 3 y Bash. Si no tienes `kubectl`,
puedes usar `minikube kubectl --` en su lugar; los scripts lo detectan.

```bash
minikube start --driver=docker --cpus=2 --memory=4096
minikube addons enable metrics-server
minikube addons enable ingress
docker build --target runner -t blacklist-app:1.0 .
minikube image load blacklist-app:1.0
```

Es necesario `--target runner`: la última etapa del Dockerfile es `test` y
ejecuta pytest. Para versiones posteriores, cambia el tag tanto al construir
como en `k8s/30-app-deployment.yaml`.

## Desplegar

```bash
bash scripts/deploy-k8s.sh
```

El script crea primero el namespace y después genera el Secret `blacklist-secret`
con contraseña y token aleatorios. No escribe credenciales en el repositorio ni
las imprime. Si el Secret ya existe, lo conserva, para no cambiar la contraseña
de una base inicializada. También admite `POSTGRES_PASSWORD` y `BEARER_TOKEN`
por variables de entorno en el primer despliegue. No cambies solo el Secret
para rotar una contraseña de PostgreSQL: debes actualizar también la BD.

Consulta los recursos sin cambiar el namespace de tu contexto:

```bash
minikube kubectl -- -n curso get pods,pvc,svc
minikube kubectl -- -n curso rollout status deployment/blacklist-app
minikube kubectl -- -n curso get endpointslices -l kubernetes.io/service-name=blacklist-app
minikube kubectl -- -n curso exec deployment/blacklist-app -c blacklist-app -- id
```

## Probar

```bash
python3 scripts/test-k8s.py
python3 scripts/test-k8s.py --persistence --rollout
```

La prueba básica verifica dos réplicas listas, dos direcciones en el Service,
UID 10001, Service headless, volumen enlazado, ping sin token, alta y consulta,
duplicados, autenticación y validación de datos. Genera correos únicos.

`--persistence` elimina únicamente el Pod `postgres-0` del laboratorio y espera
su recreación, conservando el volumen y comprobando el registro creado.
`--rollout` reinicia las réplicas de la API y comprueba el mismo registro desde
una réplica nueva. Estas opciones producen reinicios locales y conservan los
registros de prueba. No borran el PVC ni el namespace.

Para acceso manual, deja abierta una terminal:

```bash
minikube kubectl -- -n curso port-forward service/blacklist-app 8080:80
```

En otra terminal:

```bash
curl http://localhost:8080/blacklists/ping
```

Para Postman importa `tests/integration/postman/Black_list.postman_collection.json`.
Usa `base_url=http://localhost:8080` y `bearer_token` con el valor del Secret.
Puedes recuperarlo localmente con el siguiente comando; no lo compartas ni lo
guardes en Git:

```bash
minikube kubectl -- -n curso get secret blacklist-secret -o jsonpath='{.data.BEARER_TOKEN}' | base64 --decode
```

Con Newman instalado, la colección completa se ejecuta sobre el mismo túnel:

```bash
export BEARER_TOKEN="$(minikube kubectl -- -n curso get secret blacklist-secret -o jsonpath='{.data.BEARER_TOKEN}' | base64 --decode)"
newman run tests/integration/postman/Black_list.postman_collection.json \
  --env-var base_url=http://localhost:8080 \
  --env-var "bearer_token=$BEARER_TOKEN" \
  --reporters cli,junit --reporter-junit-export reports/newman-k8s.xml
unset BEARER_TOKEN
```

El Ingress requiere el addon NGINX y resolver `blacklist.local` a una dirección
accesible del controlador. Una vez listo el addon, se aplica con
`bash scripts/deploy-k8s.sh --ingress`. El despliegue básico y el port-forward
no dependen de esa configuración.

La aplicación ejecuta `create_all` al arrancar; en el primer despliegue puede
haber una carrera entre réplicas o workers. Si ocurre, revisar los logs y la
recuperación. Una migración coordinada con un Job sería un cambio adicional
para un entorno de producción.

## Pruebas unitarias

```bash
docker build --target test -t blacklist-app:test .
docker run --rm -e DATABASE_URL=sqlite:///:memory: -e BEARER_TOKEN=test-token blacklist-app:test
```

Las unitarias usan SQLite en memoria. Las pruebas Kubernetes y Postman anteriores
usan el PostgreSQL 14 desplegado en Minikube.

## Detener

```bash
minikube stop
```

Esto detiene el laboratorio sin pedir que se borren los datos. No elimines el
PVC ni el clúster si necesitas conservar los registros.

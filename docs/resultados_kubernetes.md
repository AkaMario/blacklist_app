# Resultados del laboratorio Kubernetes

Fecha: 19 de octubre de 2026, zona America/Bogota.

Entorno real: Docker Desktop, Minikube con driver Docker, Kubernetes v1.37.0,
PostgreSQL 14 y aplicación `blacklist-app:1.0` construida desde la etapa `runner`.
Namespace: `curso`. Addons Ingress NGINX y metrics-server en ejecución.

| Comprobación | Resultado |
|---|---|
| Validación de manifiestos, dry-run de cliente y servidor | Correcta |
| Unitarias existentes con SQLite en memoria | 26 aprobadas |
| Cobertura de código con ramas | 92,69 %, supera el mínimo de 90 % |
| Colección Postman contra Kubernetes y PostgreSQL | 20 peticiones y 58 aserciones, cero fallos |
| Dos réplicas listas y dos direcciones en el Service | Correcto |
| UID de ambas réplicas | 10001 |
| Service headless y PVC enlazado | Correcto |
| Ping sin token, alta, consulta y duplicados | Correcto |
| Rechazo sin token y con token incorrecto | HTTP 401 |
| Campos inválidos y consulta de correo inválido | HTTP 400 |
| Recreación de postgres-0 | Registro conservado y mismo UID del PVC |
| Reinicio del Deployment con RollingUpdate | Dos réplicas listas y registro consultable desde una nueva |
| NodePort 30080 desde el nodo | HTTP 200 y pong |
| Ingress, Host blacklist.local, a través de túnel al controlador | HTTP 200 y pong |
| Metrics API | `kubectl top nodes` y métricas de Pods disponibles |
| Repetir el script de despliegue | Conserva el Secret existente |

## Corrección encontrada por las pruebas

La primera ejecución de pytest detectó un fallo existente: consultar
`/blacklists/not-an-email` devolvía HTTP 200 en lugar de HTTP 400. Se reutilizó
la validación de email del esquema de creación y se añadió la respuesta de
error de validación en la ruta GET. Se repitieron las unitarias con el código
corregido montado en modo de solo lectura en la imagen de pruebas; todas pasaron.
La imagen de aplicación se reconstruyó con esa corrección antes de las pruebas
de Postman y Kubernetes.

## Observaciones del entorno

Durante la preparación hubo errores y demoras de descarga de imágenes de los
addons. Se descargaron mediante Docker y se cargaron con `minikube image load`.
También se reinició el kubelet local y se recrearon los Pods iniciales de la API
para recuperar el arranque. El estado final del clúster y los addons es operativo.

El primer arranque de la aplicación registró un reinicio. La guía advierte que
`create_all` puede competir entre réplicas/workers sobre una base vacía. Las
réplicas posteriores y el rolling update finalizaron sin reinicios. No se
implementó una migración coordinada; queda como mejora de producción.

La prueba de Ingress validó el enrutamiento por NGINX enviando el encabezado
Host a través de un port-forward. No se configuró el DNS ni `/etc/hosts` del
equipo para abrir `blacklist.local` directamente en el navegador.

Los datos de prueba, el namespace y el clúster se conservan. Los túneles de las
pruebas se cerraron automáticamente. No se eliminaron los volúmenes.

## Evidencia local y repetición

- `reports/pytest-k8s.txt`
- `reports/newman-k8s.txt`
- `reports/newman-k8s.xml`
- `reports/kubernetes-tests.txt`
- `reports/kubernetes-resources.txt`

`reports/` está excluido de Git; estos archivos permanecen como evidencia local.
Para repetir el laboratorio y las pruebas, ver
[laboratorio Kubernetes](laboratorio_kubernetes.md).

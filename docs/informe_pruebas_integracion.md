# Informe de pruebas de integración de blacklist_email

## Repositorio y alcance

- Repositorio: [AkaMario/blacklist_app](https://github.com/AkaMario/blacklist_app).
- Workflow: [Postman integration](https://github.com/AkaMario/blacklist_app/actions/workflows/integration.yml).
- Colección: [Black_list.postman_collection.json](../tests/integration/postman/Black_list.postman_collection.json).
- Job: `pruebas_integracion`, en [integration.yml](../.github/workflows/integration.yml).

La colección se generó a partir de las rutas, esquemas y comportamiento del código
fuente. No se tuvo acceso a la colección privada de la extensión Postman de VS Code.
El JSON entregado es compatible con Postman Collection v2.1 y Newman; la importación
visual y posterior exportación desde Postman quedan como pasos manuales, no como
acciones ya realizadas en la cuenta del usuario.

## 1. Crear la colección de capacidades

Se creó `Black_list` con autenticación Bearer heredada y las variables `base_url`,
`bearer_token` y `app_uuid`. Cada petición contiene aserciones de estado HTTP y
respuesta JSON. Los casos pertinentes también verifican los datos devueltos.

| Peticiones | Capacidad | Resultado esperado |
| --- | --- | --- |
| 01 | Salud sin autenticación | 200 y `pong` |
| 02 | Consulta de correo no registrado | 200, `is_blacklisted=false` |
| 03–04 | Registro con motivo y consulta posterior | 201; 200 con correo y motivo persistidos |
| 05 | Registro duplicado | 409 |
| 06–07 | Registro sin motivo y consulta | 201; 200 con motivo nulo |
| 08–09 | Registro con motivo nulo y consulta | 201; 200 con motivo nulo |
| 10–13 | POST y GET sin token o con token incorrecto | 401 |
| 14–19 | Email y UUID inválidos o ausentes; motivo demasiado largo o de tipo incorrecto | 400 con detalle del campo |
| 20 | Cuerpo JSON vacío | 400 |

La primera petición genera correos únicos. Las consultas posteriores comprueban
la persistencia real a través de la API y PostgreSQL, sin mocks. Ejecutar la colección
completa en orden; no usa filtros de carpetas ni scripts que salten peticiones.

Para abrirla en Postman: **Import → File**, seleccionar el JSON y ejecutar la
colección `Black_list`. Si ya existe otra colección con ese nombre, importarla
como copia para conservar la original.

## 2. Archivo JSON y exportación desde Postman

El archivo entregado es `tests/integration/postman/Black_list.postman_collection.json`.
Para obtener una exportación desde la interfaz después de importarlo:

1. Abrir el workspace en Postman web o escritorio.
2. En **Collections**, abrir el menú de `Black_list`.
3. Seleccionar **More → Export collection → Export JSON** (el nombre puede variar
   por versión); elegir **Collection v2.1** si se solicita el formato.
4. Guardar el JSON en la ruta anterior, conservando las variables y aserciones.

No se requiere una API key de Postman para ejecutar el archivo local.

## 3. Instalación y ejecución local

Requisitos: Linux, Python compatible con el proyecto, Node.js 22, npm, PostgreSQL
con `initdb`, `pg_ctl` y `createdb` en el PATH, curl y OpenSSL. Ejecutar como usuario
normal, ya que PostgreSQL no permite inicializar una base como root.

Desde la raíz del repositorio:

```sh
python -m venv /tmp/blacklist-integration-venv
/tmp/blacklist-integration-venv/bin/pip install .
npm install --prefix /tmp/blacklist-newman --cache /tmp/blacklist-npm-cache \
  --no-audit --no-fund newman@6.2.1
PATH=/tmp/blacklist-integration-venv/bin:/tmp/blacklist-newman/node_modules/.bin:$PATH \
  bash tests/integration/run-local.sh
```

El script crea un clúster PostgreSQL temporal, inicia la API con Gunicorn y un
certificado HTTPS temporal, espera `/blacklists/ping` y ejecuta Newman. Usa
`https://localhost:5501` y el puerto 55432 para PostgreSQL. Se pueden cambiar con
`INTEGRATION_API_PORT` e `INTEGRATION_DB_PORT`. Al terminar detiene ambos procesos
y elimina la base temporal. No utiliza la base configurada en el archivo `.env`.
El certificado se confía explícitamente mediante `--ssl-extra-ca-certs`.

El comando Newman ejecutado por el script equivale a:

```sh
newman run tests/integration/postman/Black_list.postman_collection.json \
  --env-var 'base_url=https://localhost:5501' \
  --env-var 'bearer_token=integration-test-token' \
  --ssl-extra-ca-certs /ruta/al/certificado/temporal/api.crt \
  --timeout 300000 --timeout-request 15000 --timeout-script 10000 \
  --color off --reporters cli,junit \
  --reporter-junit-export reports/newman.xml
```

El token es exclusivo de pruebas. Los resultados locales se guardan en
`reports/newman.xml`, excluido de Git. Las aserciones fallidas o errores de Newman
producen una salida distinta de cero.

### Resultado local

Ejecución local completada con salida **0**:

| Métrica | Ejecutadas | Fallidas |
| --- | ---: | ---: |
| Iteraciones | 1 | 0 |
| Peticiones HTTPS | 20 | 0 |
| Scripts de pruebas | 20 | 0 |
| Scripts previos | 1 | 0 |
| Aserciones | 58 | 0 |

Duración reportada por Newman: **487 ms**, sin incluir el arranque de servicios.
Se ejecutó con Newman 6.2.1, Node.js 22.14.0 y PostgreSQL local 18.6.
GitHub está configurado con PostgreSQL 14 y Python 3.11; esa combinación remota
queda pendiente de validar en Actions. El reporte JUnit local está en
`reports/newman.xml`. También se validó la sintaxis JSON, JavaScript de los
scripts, YAML del workflow y Bash.

## 4. Job de GitHub Actions

Se añadió el job `pruebas_integracion` en un workflow independiente del job de
pruebas unitarias existente. Se activa al cerrar un pull request dirigido a `main`
y solo ejecuta el job si el PR fue fusionado. También permite ejecución manual
con `workflow_dispatch`. Un PR cerrado sin merge no ejecuta estas pruebas;
un push directo a `main` tampoco activa este workflow.

Pasos del job:

1. Descargar el código integrado y comprobar que existe la colección.
2. Iniciar PostgreSQL 14 como servicio y esperar su health check.
3. Configurar Python 3.11 e instalar las dependencias con Poetry.
4. Configurar Node.js 22 e instalar Newman 6.2.1.
5. Generar un certificado HTTPS temporal e iniciar la API en el puerto 5001.
6. Esperar la respuesta del endpoint de salud.
7. Ejecutar las 20 peticiones y sus aserciones con Newman.
8. Publicar el reporte JUnit como artefacto `black-list-newman-report` durante 7 días,
   incluso si las pruebas fallan y existe un reporte.
9. Mostrar logs en caso de fallo y detener la API.

El límite total del job es 15 minutos y el de Newman, 5 minutos. No se usa
`--bail`: una aserción fallida no impide evaluar las peticiones siguientes.

## 5. Verificación en GitHub

Los archivos están preparados localmente. No se ha hecho commit, push ni merge,
y no se afirma haber ejecutado el workflow en GitHub Actions.

Después de subir los cambios y fusionar el PR en `main`, abrir el enlace del
workflow, comprobar el resultado de `pruebas_integracion` y descargar el artefacto
JUnit. La evidencia de esa ejecución remota queda pendiente de ese merge.

## Referencias

- [Newman: ejecución, opciones y reportes](https://github.com/postmanlabs/newman).
- [Exportar datos de Postman](https://learning.postman.com/docs/getting-started/importing-and-exporting/exporting-data/).
- [Eventos de GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).

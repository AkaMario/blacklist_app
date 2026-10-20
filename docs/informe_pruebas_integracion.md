# Informe de pruebas de integración de blacklist_email

## Objetivo del ejercicio

Construir una colección de pruebas de las capacidades del servicio, entregarla
en JSON, ejecutarla localmente con Newman y automatizar su ejecución mediante
el job `pruebas_integracion` de GitHub Actions al fusionar cambios en `main`.
Este documento registra el procedimiento realizado, sus resultados y los pasos
para reproducirlo.

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

Primero se revisaron las rutas de `src/routes/blacklist_router.py`, las reglas
de `src/models/blacklist.py`, la autenticación de
`src/middleware/auth_middleware.py` y la persistencia del servicio en PostgreSQL.
Se identificaron estas operaciones para construir los escenarios:

| Método | Ruta | Función |
| --- | --- | --- |
| GET | `/blacklists/ping` | Verificar disponibilidad |
| POST | `/blacklists` | Registrar un correo en la lista negra |
| GET | `/blacklists/{email}` | Consultar si un correo está bloqueado |

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

Se comprobó que el commit
[`4cf8e0b`](https://github.com/AkaMario/blacklist_app/commit/4cf8e0bcb003d445bfeb3b1d35700cbfb8bf004a)
con la colección y el workflow ya estaba publicado en la rama remota `main`.
En la consulta realizada durante el ejercicio, GitHub devolvió **0 ejecuciones**
para `integration.yml`. Posteriormente se intentó iniciarlo manualmente, pero
la operación fue interrumpida antes de obtener una confirmación. Por ello,
este informe no acredita una ejecución remota ni un resultado aprobado en Actions.

### Ejecución manual desde el navegador

1. Abrir [Postman integration en GitHub Actions](https://github.com/AkaMario/blacklist_app/actions/workflows/integration.yml).
2. Pulsar **Run workflow**.
3. Seleccionar la rama **main** y confirmar con **Run workflow**.
4. Abrir la ejecución y revisar el job **pruebas_integracion**.
5. Comprobar el paso **Run every request in Black_list** y descargar el artefacto
   **black-list-newman-report** para consultar el reporte JUnit.

### Ejecución manual desde la terminal

Con GitHub CLI (`gh`) instalado y una cuenta con permisos para ejecutar Actions:

```sh
gh auth login
gh workflow run integration.yml --repo AkaMario/blacklist_app --ref main
gh run list --repo AkaMario/blacklist_app --workflow integration.yml --limit 1
```

Para seguir una ejecución específica, reemplazar `ID_DE_EJECUCION` por el ID que
muestre el último comando:

```sh
gh run watch ID_DE_EJECUCION --repo AkaMario/blacklist_app --exit-status
gh run download ID_DE_EJECUCION --repo AkaMario/blacklist_app \
  --name black-list-newman-report --dir reports/github
```

También se ejecutará automáticamente al fusionar un próximo pull request en
`main`. Para completar la evidencia remota, registrar el enlace de la ejecución,
su conclusión y el reporte generado; el resultado local no sustituye esa evidencia.

## 6. Entregables y cumplimiento

| Objetivo solicitado | Entregable o evidencia | Estado |
| --- | --- | --- |
| Crear colección de capacidades | `Black_list`, con 20 peticiones y scripts de validación | Creada como JSON importable; importación en la cuenta de Postman pendiente |
| Exportar JSON de la colección | `tests/integration/postman/Black_list.postman_collection.json` | Archivo generado; exportación desde la interfaz de Postman pendiente |
| Ejecutar Newman localmente | 20 peticiones y 58 aserciones, 0 fallos | Completado |
| Añadir job `pruebas_integracion` | `.github/workflows/integration.yml` | Publicado; resultado remoto pendiente de confirmar |
| Incluir enlace del repositorio y paso a paso | Secciones de este informe | Completado |
| Entregar informe Markdown en `/docs` | `docs/informe_pruebas_integracion.md` | Completado |

Archivos auxiliares:

- [Script de ejecución local](../tests/integration/run-local.sh): inicia y detiene
  los servicios temporales, ejecuta Newman y devuelve su código de salida.
- [Guía de la colección](../tests/integration/postman/README.md): variables e importación.
- [README principal](../README.md): enlaza este informe y la guía de pruebas.

## Conclusión

La integración local de la API con PostgreSQL se validó mediante 20 peticiones
HTTPS y 58 aserciones exitosas. La colección JSON y la automatización están
publicadas en el repositorio. Queda pendiente incorporar la evidencia de una
ejecución de GitHub Actions y, si el ejercicio exige realizar esos pasos en la
interfaz de Postman, importar y exportar allí la colección entregada.

## Referencias

- [Newman: ejecución, opciones y reportes](https://github.com/postmanlabs/newman).
- [Exportar datos de Postman](https://learning.postman.com/docs/getting-started/importing-and-exporting/exporting-data/).
- [Eventos de GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).

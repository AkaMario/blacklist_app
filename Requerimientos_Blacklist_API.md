# Documento de Requerimientos y Especificación Técnica
## Proyecto: Microservicio de Gestión de Lista Negra Global de Emails (Blacklist API)

---

## 1. Resumen Ejecutivo
El presente documento establece los requerimientos funcionales, no funcionales, arquitectónicos y de despliegue para el desarrollo del microservicio centralizado de **Gestión de Lista Negra Global de Emails** (*Global Email Blacklist Service*). 

Este microservicio tiene como objetivo principal proporcionar a los diferentes sistemas y aplicaciones internas de la compañía una solución centralizada, confiable y de alta disponibilidad para consultar y registrar direcciones de correo electrónico restringidas o en lista negra, mitigando así riesgos legales y demandas asociadas a la mala gestión de comunicaciones.

---

## 2. Contexto y Alcance del Proyecto

### 2.1. Problema de Negocio
Actualmente, la compañía multinacional opera múltiples aplicaciones independientes. La falta de un mecanismo centralizado de gestión de listas negras ha ocasionado que se envíen correos no deseados o prohibidos a clientes, derivando en sanciones legales y afectación a la reputación corporativa.

### 2.2. Alcance Funcional
El alcance de la presente entrega contempla:
* Desarrollo de una API RESTful en **Python / Flask**.
* Persistencia relacional sobre **PostgreSQL**.
* Autenticación y seguridad mediante **JSON Web Tokens (JWT)**.
* Endpoints para adición y consulta de emails en la lista negra.
* Despliegue en un proveedor de **Nube Pública** (AWS / GCP / Azure).
* Cobertura de pruebas unitarias y de integración de **al menos el 90%**.
* Documentación paso a paso del proceso de aprovisionamiento y despliegue.

---

## 3. Stack Tecnológico Mandatorio

El proyecto debe ser desarrollado utilizando estrictamente el siguiente stack tecnológico:

| Componente | Tecnología | Versión / Detalle |
| :--- | :--- | :--- |
| **Lenguaje de Programación** | Python | 3.8 o superior |
| **Framework Web** | Flask | 1.1.x (Microframework web) |
| **ORM** | Flask-SQLAlchemy | Extensión Flask para mapeo objeto-relacional (SQLAlchemy) |
| **Arquitectura de API** | Flask-RESTful | Extensión para diseño de APIs REST orientado a objetos |
| **Serialización / Validación** | Flask-Marshmallow | Extensión para serialización, deserialización y validación de esquemas |
| **Autenticación y Seguridad** | Flask-JWT-Extended | Soporte para protección de vistas y gestión de tokens JWT |
| **Motor de Base de Datos** | PostgreSQL | Motor SQL de código abierto para producción |
| **Infraestructura** | Nube Pública | AWS, GCP o Azure (con o sin contenedores Docker) |

---

## 4. Requerimientos Funcionales (RF)

### **RF-01: Autenticación y Seguridad de la API**
* **Descripción:** Todos los endpoints de la API (con excepción de la autenticación inicial si aplica) deben estar protegidos mediante JWT (*Bearer Tokens*).
* **Criterio de Aceptación:** Cualquier solicitud enviada sin un encabezado `Authorization: Bearer <token>` válido debe retornar un código de estado `HTTP 401 Unauthorized`.

---

### **RF-02: Agregar Email a la Lista Negra Global (POST)**
* **Método HTTP:** `POST`
* **Ruta de Acceso:** `/blacklists`
* **Descripción:** Permite a los sistemas clientes registrar una dirección de correo electrónico en la lista negra global de la multinacional.
* **Parámetros de Entrada (Payload JSON):**
  * `email` *(String, Obligatorio)*: Dirección de correo electrónico a añadir a la lista negra. Debe cumplir con formato de email válido.
  * `app_uuid` *(UUID, Obligatorio)*: Identificador único universal de la aplicación cliente que realiza el registro.
  * `blocked_reason` *(String, Opcional)*: Motivo de la inclusión en la lista negra. Longitud máxima: 255 caracteres.
* **Metadatos Internos Capturados (Automáticos):**
  * `ip_address` *(String)*: Dirección IP de origen desde la cual proviene la solicitud HTTP.
  * `createdAt` / `timestamp` *(DateTime)*: Fecha y hora exacta (UTC) en la que se registra la solicitud.
* **Respuestas del Servicio:**
  * `201 Created`: El email fue registrado exitosamente en la lista negra.
  * `400 Bad Request`: Faltan campos obligatorios, formato de email inválido, el motivo supera los 255 caracteres o UUID inválido.
  * `412 Precondition Failed` / `409 Conflict`: El email ya se encuentra en la lista negra global.
  * `401 Unauthorized`: Token JWT ausente o inválido.

---

### **RF-03: Consultar Estado de Email en Lista Negra (GET)**
* **Método HTTP:** `GET`
* **Ruta de Acceso:** `/blacklists/<string:email>`
* **Descripción:** Permite verificar si una dirección de correo electrónico específica se encuentra en la lista negra global de la empresa.
* **Parámetros de Entrada:**
  * `email` *(Path Parameter, Obligatorio)*: Dirección de correo a consultar.
* **Estructura de Respuesta (JSON):**
  * `is_blacklisted` *(Boolean)*: `true` si el email existe en la lista negra, `false` en caso contrario.
  * `blocked_reason` *(String, Opcional)*: Motivo asignado al momento del bloqueo (si aplica).
* **Respuestas del Servicio:**
  * `200 OK`: Consulta realizada exitosamente (retorna si está o no en la lista).
  * `400 Bad Request`: Formato de email inválido.
  * `401 Unauthorized`: Token JWT ausente o inválido.

---

## 5. Requerimientos No Funcionales (RNF)

### **RNF-01: Calidad de Código y Cobertura de Pruebas**
* El código debe estructurarse aplicando patrones de diseño orientados a objetos con `Flask-RESTful`.
* Se exige una cobertura de pruebas unitarias e integración de **al menos el 90%** (`coverage.py` o `pytest-cov`).
* Se debe garantizar la validación rigurosa de entradas mediante esquemas de `Flask-Marshmallow`.

### **RNF-02: Escalabilidad y Rendimiento**
* La arquitectura debe permitir respuesta rápida a las consultas `GET` de los sistemas clientes (baja latencia).
* Las consultas por columna `email` en la base de datos deben contar con un índice optimizado (`INDEX`).

### **RNF-03: Despliegue en la Nube**
* La aplicación debe estar desplegada en un proveedor de Nube Pública reconocido (AWS, GCP o Azure).
* La base de datos PostgreSQL puede desplegarse administrada (ej. AWS RDS / Cloud SQL) o en contenedor/instancia EC2.
* Se permite despliegue mediante contenedores (Docker / App Runner / ECS / Cloud Run) o Servidor / PaaS (Elastic Beanstalk / App Service).

---

## 6. Modelo de Datos Proyectado

### Tabla: `blacklist`

| Campo | Tipo de Dato | Restricciones | Descripción |
| :--- | :--- | :--- | :--- |
| `id` | UUID / Integer | PRIMARY KEY, AUTO | Identificador único del registro |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | Email registrado en la lista negra |
| `app_uuid` | UUID | NOT NULL | UUID de la aplicación cliente que solicita el registro |
| `blocked_reason` | VARCHAR(255) | NULLABLE | Motivo del bloqueo (máx 255 caracteres) |
| `ip_address` | VARCHAR(45) | NOT NULL | Dirección IP del cliente que realiza la solicitud |
| `created_at` | TIMESTAMP (UTC) | NOT NULL, DEFAULT NOW() | Fecha y hora de creación de la entrada |

---

## 7. Estructura de Entregables Requerida (Documento Final)

El documento final de entrega debe elaborarse y entregarse incluyendo los siguientes puntos y evidencias:

### 7.1. Código Fuente y Cobertura de Tests
1. Repositorio de código fuente con la estructura del proyecto en Flask.
2. Evidencia ejecutada de pruebas automatizadas que certifique una **cobertura superior o igual al 90%** (Captura del reporte HTML/CLI de `coverage.py`).

### 7.2. Guía de Despliegue Paso a Paso (Con Capturas de Pantalla)
A. **Configuración de Base de Datos:**
   * Creación y provisión de la instancia PostgreSQL en la nube.
   * Ejecución de migraciones/tablas iniciales y reglas de acceso/seguridad.
B. **Configuración y Despliegue del Proyecto en Nube:**
   * Creación de variables de entorno (cadenas de conexión, llaves secretas JWT).
   * Aprovisionamiento del servicio de cómputo (Docker, App Runner, EC2, Cloud Run, PaaS).
   * Verificación de la aplicación en ejecución (*Health check* y llamados desde Postman / cURL).

---

## 8. Matriz de Criterios de Evaluación

| Criterio | Peso | Indicador de Cumplimiento |
| :--- | :---: | :--- |
| **Stack Tecnológico** | 20% | Uso correcto de Python 3.8+, Flask 1.1.x, SQLAlchemy, RESTful, Marshmallow, JWT Extended y PostgreSQL. |
| **Endpoints y Lógica** | 30% | Funcionalidad completa de POST (captura IP, fecha, UUID, motivo) y GET (consulta por email). |
| **Cobertura de Pruebas** | 20% | Tests unitarios e integración ejecutados con cobertura mínima del 90% comprobada. |
| **Despliegue en Nube** | 20% | Aplicación funcional y accesible en Nube Pública con base de datos PostgreSQL conectada. |
| **Documentación** | 10% | Guía paso a paso estructurada con capturas de pantalla de la nube y configuración. |

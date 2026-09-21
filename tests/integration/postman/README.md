# Black_list

La colección `Black_list.postman_collection.json` contiene 20 peticiones con
aserciones sobre las capacidades del servicio blacklist_email. Está en formato
Postman Collection v2.1 y se puede importar desde **Import → File** en Postman.
Se creó desde el código de este repositorio; no es una exportación de la
colección privada que estaba en la extensión de VS Code.

Variables: `base_url` (URL de la API) y `bearer_token` (token de prueba).
La primera petición genera correos únicos para ejecutar la colección completa
en orden varias veces sin conflictos con registros anteriores.

Para ejecutar con una base PostgreSQL temporal y HTTPS:

```sh
bash tests/integration/run-local.sh
```

Requisitos, instalación, resultados y configuración de GitHub Actions:
[informe de integración](../../../docs/informe_pruebas_integracion.md).

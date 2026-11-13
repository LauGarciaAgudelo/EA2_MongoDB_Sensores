# Guía para tomar las capturas de pantalla reales (Fase 5)

Esta guía explica, paso a paso, cómo ejecutar manualmente la colección de Postman
([postman/EA2-MongoDB-Sensores-CRUD.postman_collection.json](../postman/EA2-MongoDB-Sensores-CRUD.postman_collection.json))
para completar las evidencias reales que quedaron pendientes en la Fase 5. La colección
ya fue verificada con Newman (19 solicitudes, 30 aserciones, 0 fallos; ver
[resultados_newman_cli.txt](./resultados_newman_cli.txt)); esta guía es solo para repetir
esa misma secuencia **desde la aplicación Postman**, con capturas de pantalla reales.

No se modificó el código de la API ni la lógica de la colección para preparar esta guía.

## 0. Antes de empezar

1. Dejar la API corriendo en una terminal:

   ```powershell
   .venv\Scripts\python.exe API.py
   ```

2. Abrir Postman e importar la colección (`Import` → seleccionar el archivo
   `.postman_collection.json`).
3. Confirmar que la variable de colección `base_url` sea `http://127.0.0.1:5000`
   (pestaña "Variables" de la colección).
4. (Opcional, recomendado) Abrir MongoDB Compass y conectar a
   `mongodb://localhost:27017/`, para tener a la mano la vista de
   `monitoreo_industrial > sensores`.

## 1. Lo prioritario (si el tiempo es limitado, capturar al menos esto)

El profesor pidió especialmente: las **5 operaciones CRUD básicas**, **una validación
HTTP 400**, y **evidencia de persistencia en MongoDB**. Estos son los 7 pasos mínimos:

| Orden | Solicitud (nombre exacto en Postman) | Método y URL | Código esperado | Captura |
|---|---|---|---|---|
| 1 | `1. POST Crear sensor - Temperatura` | `POST {{base_url}}/sensores/` | `201` | `01_post_crear_sensor.png` |
| 2 | `4. GET Consultar todos los sensores` | `GET {{base_url}}/sensores/` | `200` | `02_get_todos_sensores.png` |
| 3 | `5. GET Filtrar por tipo (temperatura)` | `GET {{base_url}}/sensores/?tipo=temperatura` | `200` | `03_get_filtrar_tipo.png` |
| 4 | `6. PUT Actualizar sensor por tipo (temperatura)` | `PUT {{base_url}}/sensores/temperatura` | `200` | `04_put_actualizar_sensor.png` |
| 5 | `7. DELETE Eliminar sensor por tipo (presion)` *(requiere haber corrido antes la solicitud 2, que crea el sensor de presión)* | `DELETE {{base_url}}/sensores/presion` | `200` | `05_delete_eliminar_sensor.png` |
| 6 | `10. POST Sensor invalido - tipo no permitido` | `POST {{base_url}}/sensores/` | `400` | `08_validacion_tipo.png` |
| 7 | **MongoDB Compass** — ver sección 4 | — | — | `12_mongodb_compass_persistencia.png` |

Para la fila 5 hace falta haber ejecutado antes la solicitud `2. POST Crear sensor -
Presion` (no está en esta tabla reducida porque no requiere captura propia, solo crea el
dato). Lo más simple es seguir el orden completo de la sección 2, que ya incluye esto.

## 2. Orden exacto y completo de ejecución (las 19 solicitudes de la colección)

Ejecutar **en este orden**, una por una, con el botón "Send" de Postman. El orden importa
porque varias solicitudes dependen de datos creados por solicitudes anteriores.

| # | Carpeta | Nombre exacto de la solicitud en Postman | Método | URL | Depende de / variable | Código esperado | Captura recomendada |
|---|---|---|---|---|---|---|---|
| 1 | 01 | `1. POST Crear sensor - Temperatura` | POST | `{{base_url}}/sensores/` | — | `201` | `01_post_crear_sensor.png` ⭐ |
| 2 | 01 | `2. POST Crear sensor - Presion` | POST | `{{base_url}}/sensores/` | — | `201` | *(sin captura propia)* |
| 3 | 01 | `3. POST Crear sensor - Vibracion` | POST | `{{base_url}}/sensores/` | Captura `_id` → `sensor_id` | `201` | *(sin captura propia; ver nota de Compass)* |
| 4 | 01 | `4. GET Consultar todos los sensores` | GET | `{{base_url}}/sensores/` | Requiere 1-3 ya creados | `200` | `02_get_todos_sensores.png` ⭐ |
| 5 | 01 | `5. GET Filtrar por tipo (temperatura)` | GET | `{{base_url}}/sensores/?tipo=temperatura` | Requiere 1 | `200` | `03_get_filtrar_tipo.png` ⭐ |
| 6 | 01 | `6. PUT Actualizar sensor por tipo (temperatura)` | PUT | `{{base_url}}/sensores/temperatura` | Requiere exactamente 1 sensor de temperatura (de 1) | `200` | `04_put_actualizar_sensor.png` ⭐ |
| 7 | 01 | `7. DELETE Eliminar sensor por tipo (presion)` | DELETE | `{{base_url}}/sensores/presion` | Requiere exactamente 1 sensor de presión (de 2) | `200` | `05_delete_eliminar_sensor.png` ⭐ |
| 8 | 02 | `8. PUT Actualizar sensor por ID` | PUT | `{{base_url}}/sensores/id/{{sensor_id}}` | Usa `sensor_id` capturado en el paso 3 | `200` | `06_put_por_id.png` |
| 9 | 02 | `9. DELETE Eliminar sensor por ID` | DELETE | `{{base_url}}/sensores/id/{{sensor_id}}` | Usa `sensor_id`; al terminar, la pone en `""` | `200` | `07_delete_por_id.png` |
| 10 | 03 | `10. POST Sensor invalido - tipo no permitido` | POST | `{{base_url}}/sensores/` | — | `400` | `08_validacion_tipo.png` ⭐ |
| 11 | 03 | `11. POST Sensor invalido - valor fuera de rango` | POST | `{{base_url}}/sensores/` | — | `400` | `09_validacion_rango.png` |
| 12 | 03 | `12. PUT Sensor inexistente (404)` | PUT | `{{base_url}}/sensores/vibracion` | Requiere que el paso 9 ya haya eliminado el sensor de vibración | `404` | `10_sensor_inexistente.png` |
| 13 | 03 | `13a. POST Crear sensor conflicto A (presion)` | POST | `{{base_url}}/sensores/` | Captura `_id` → `sensor_id` (estaba vacía desde el paso 9) | `201` | *(sin captura propia)* |
| 14 | 03 | `13b. POST Crear sensor conflicto B (presion)` | POST | `{{base_url}}/sensores/` | Captura `_id` → `sensor_id_extra` | `201` | *(sin captura propia)* |
| 15 | 03 | `13. DELETE con multiples coincidencias (409)` | DELETE | `{{base_url}}/sensores/presion` | Requiere exactamente 2 sensores de presión (de 13a/13b) | `409` | `11_conflicto_409.png` ⭐ |
| 16 | 04 | `14. DELETE Eliminar sensor por tipo (temperatura) - limpieza` | DELETE | `{{base_url}}/sensores/temperatura` | Elimina el sensor del paso 1/6 | `200` | *(sin captura; es limpieza)* |
| 17 | 04 | `15. DELETE Eliminar sensor por ID (conflicto A) - limpieza` | DELETE | `{{base_url}}/sensores/id/{{sensor_id}}` | Usa `sensor_id` del paso 13a | `200` | *(sin captura; es limpieza)* |
| 18 | 04 | `16. DELETE Eliminar sensor por ID (conflicto B) - limpieza` | DELETE | `{{base_url}}/sensores/id/{{sensor_id_extra}}` | Usa `sensor_id_extra` del paso 13b | `200` | *(sin captura; es limpieza)* |
| 19 | 04 | `17. GET Verificar coleccion vacia - limpieza` | GET | `{{base_url}}/sensores/` | Requiere 16-18 ya ejecutados | `200`, body `[]` | *(sin captura; es verificación final)* |

⭐ = parte del conjunto prioritario de la sección 1.

Cada captura de pantalla debe mostrar, dentro de la misma imagen: el método HTTP y la URL
(parte superior de Postman), el cuerpo de la solicitud si aplica (pestaña "Body"), y la
respuesta completa (código de estado + JSON de la pestaña "Body" de la respuesta).

## 3. Dependencias entre solicitudes y variables dinámicas

- **`sensor_id`**: se captura automáticamente en el paso 3 (sensor de vibración) y se usa
  en los pasos 8 y 9. El paso 9 la vacía (`""`) después de eliminar ese sensor. Luego se
  vuelve a capturar en el paso 13 (sensor conflicto A) porque estaba vacía, y se usa en el
  paso 17 (limpieza) para eliminar ese mismo sensor por su id.
- **`sensor_id_extra`**: se captura solo en el paso 14 (sensor conflicto B) y se usa en el
  paso 18 (limpieza).
- Ambas variables usan en su script la condición `if (!pm.collectionVariables.get(...))`
  para no sobrescribirse por accidente si se repite una solicitud.
- **No saltarse pasos ni cambiar el orden**: por ejemplo, el paso 12 (`404`) depende de que
  el paso 9 ya haya eliminado el sensor de vibración; el paso 15 (`409`) depende de que
  existan *exactamente* los 2 sensores de presión creados en los pasos 13 y 14 (si el
  paso 7 no se ejecutó antes, seguiría habiendo un tercer sensor de presión del paso 2, y
  el escenario ya no sería "2 coincidencias" sino "3").
- Si se necesita repetir la secuencia desde cero, lo más simple es: ejecutar primero la
  carpeta **"04 - Limpieza"** completa (pasos 16-19 de esta tabla) para vaciar la
  colección, y luego volver a empezar desde el paso 1. Si alguna variable quedó con un
  valor inesperado, se puede limpiar a mano en la pestaña "Variables" de la colección
  (dejar `sensor_id` y `sensor_id_extra` en blanco).

## 4. Momento exacto para la captura de MongoDB Compass

La mejor evidencia de persistencia se toma **justo después del paso 3** (cuando ya existen
los 3 sensores creados: temperatura, presión y vibración, y todavía no se ha modificado ni
eliminado ninguno):

1. En MongoDB Compass, abrir la base `monitoreo_industrial` → colección `sensores`.
2. Hacer clic en "Refresh" si ya se tenía la colección abierta.
3. Tomar la captura mostrando los 3 documentos completos (con sus campos `tipo`, `valor`,
   `ubicacion`, `fecha` y `_id` visibles).
4. Guardarla como `evidencias/12_mongodb_compass_persistencia.png`.

Una segunda captura opcional (no obligatoria) se puede tomar después del paso 15 (el
`409`), para mostrar los 2 sensores de presión en conflicto, o después del paso 19, para
mostrar la colección vacía tras la limpieza.

## 5. Limpieza al finalizar

Una vez tomadas todas las capturas necesarias:

1. Ejecutar, en orden, las 4 solicitudes de la carpeta **"04 - Limpieza"** (pasos 16 a 19
   de la tabla de la sección 2).
2. Confirmar que la solicitud `17. GET Verificar coleccion vacia - limpieza` responde
   `200` con un cuerpo `[]` (lista vacía).
3. (Opcional) Refrescar MongoDB Compass y confirmar que la colección `sensores` quedó sin
   documentos, igual que al cierre de la Fase 4.

## 6. Dónde guardar las capturas

Todas las capturas van dentro de la carpeta [evidencias/](.) de este proyecto, con los
nombres exactos indicados en las tablas de arriba (por ejemplo,
`evidencias/01_post_crear_sensor.png`).

---

**Nota:** este archivo es una guía para que tú (o cualquier persona con acceso a Postman y
MongoDB Compass en su propio equipo) completes las capturas manualmente. No se generó, ni
se afirma haber generado, ninguna captura de pantalla real como parte de esta guía.

# Bitácora del proyecto — EA2 MongoDB Sensores

Este archivo registra, fase por fase, los comandos ejecutados, los resultados obtenidos y
las decisiones tomadas durante el desarrollo del proyecto.

---

## FASE 1 — Preparación del entorno

**Fecha:** 13/11/2026

**Objetivo de la fase:** preparar y verificar el entorno de desarrollo, sin implementar
todavía la aplicación Flask ni la conexión a MongoDB.

### 1. Verificación del sistema operativo

- Sistema operativo detectado: **Windows** (NT 10.0.26200.0).

### 2. Verificación de Python, pip y Git

Comandos ejecutados:

```powershell
python --version
pip --version
git --version
```

Resultados:

- Python: `3.10.10`
- pip: `26.1.1` (antes de actualizar dentro del entorno virtual)
- Git: `2.42.0.windows.2`

### 3. Verificación de MongoDB Community Server

Comandos ejecutados:

```powershell
Get-Service -Name "MongoDB*"
mongosh --eval "db.runCommand({ ping: 1 })"
mongosh --eval "db.version()"
```

Resultados:

- Servicio de Windows `MongoDB` (MongoDB Server) encontrado con estado **Running**.
- Instalación ubicada en `C:\Program Files\MongoDB\Server\9.0\`.
- Versión del servidor: **9.0.4**.
- `mongosh` (consola de MongoDB) instalada, versión **2.8.2**.
- Prueba de conexión (`ping`) exitosa: `{ ok: 1 }`.

**Conclusión:** MongoDB local está instalado, corriendo y accesible. No fue necesario
instalar ni configurar nada adicional.

### 4. Verificación de MongoDB Compass

Se encontró la instalación de **MongoDB Compass** en
`C:\Users\Diana.Giraldo\AppData\Local\MongoDBCompass\` (versión de la app `1.53.0`).
Compass es opcional para el desarrollo (sirve para explorar visualmente la base de datos),
pero ya está disponible para usarse cuando se necesite revisar los datos manualmente.

### 5. Creación del entorno virtual

Comando ejecutado:

```powershell
python -m venv .venv
```

Resultado: entorno virtual creado correctamente en `.venv/` (se verificó la existencia de
`.venv\Scripts\python.exe`).

### 6. Archivo `requirements.txt`

Se creó el archivo [requirements.txt](./requirements.txt) con las dependencias solicitadas:

```
Flask==3.0.3
pymongo==4.8.0
python-dotenv==1.0.1
pytest==8.3.2
```

No se agregaron dependencias adicionales a las pedidas.

### 7. Instalación de dependencias

Comandos ejecutados:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Resultado: instalación exitosa de Flask 3.0.3, pymongo 4.8.0, python-dotenv 1.0.1 y
pytest 8.3.2, junto con sus dependencias internas (Werkzeug, Jinja2, click, dnspython,
pluggy, etc.). Ningún error durante la instalación.

### 8. Verificación de importación de las librerías

Comando ejecutado:

```powershell
.\.venv\Scripts\python.exe -c "import flask, pymongo, dotenv, pytest; print(...)"
```

Resultado: las cuatro librerías se importaron sin errores. Se mostró un aviso
(`DeprecationWarning`) de Flask indicando que `flask.__version__` quedará obsoleto en el
futuro; es solo informativo y no afecta el funcionamiento del proyecto.

### 9. Archivo `.gitignore`

Se creó [.gitignore](./.gitignore) excluyendo `.venv/`, `__pycache__/`, `.env`,
`.pytest_cache/` y otros archivos temporales habituales en proyectos Python.

### 10. Carpetas del proyecto

Se crearon las carpetas:

- `tests/` — para las pruebas funcionales de la API (se usará en una fase posterior).
- `evidencias/` — para guardar capturas de pantalla y evidencias de las pruebas realizadas.

Ambas se dejaron con un archivo `.gitkeep` para que Git las registre aunque todavía estén
vacías.

### 11. Documentación inicial

Se crearon [README.md](./README.md) (con el objetivo del proyecto y los pasos reales de
configuración) y este mismo archivo, `BITACORA.md`.

### Problemas encontrados

Ninguno. Python, Git, MongoDB y Compass ya estaban instalados en el equipo, y el entorno
virtual se creó y configuró sin inconvenientes.

### Checklist de cierre de la Fase 1

- [x] Python y pip funcionan correctamente.
- [x] Entorno virtual `.venv` creado.
- [x] Flask y PyMongo instalados y verificados mediante importación.
- [x] Estructura inicial de carpetas preparada (`tests/`, `evidencias/`).
- [x] Estado de MongoDB local verificado (servicio activo, conexión exitosa).
- [x] `README.md` y `BITACORA.md` creados con información real.

**Pendientes para la Fase 2:** crear la conexión desde Python a MongoDB, definir la
estructura del proyecto Flask y comenzar con la implementación de los endpoints.

---

## FASE 2 — Conexión con MongoDB local

**Fecha:** 13/11/2026

**Objetivo de la fase:** configurar la conexión desde Python a MongoDB local, crear la
base de datos `monitoreo_industrial` y la colección `sensores`, y verificar operaciones
básicas de conexión y persistencia. No se implementaron todavía los endpoints REST.

### 1. Archivo `database.py`

Se creó [database.py](./database.py), que centraliza la conexión a MongoDB:

- Lee `MONGO_URI` y `MONGO_DB_NAME` desde variables de entorno (con `python-dotenv`),
  usando como valores por defecto `mongodb://localhost:27017/` y `monitoreo_industrial`.
- Configura un timeout de selección de servidor de 5000 ms (`serverSelectionTimeoutMS`).
- Expone `obtener_cliente()`, `obtener_base_datos()` y `obtener_coleccion_sensores()`.
- Expone `verificar_conexion()`, que ejecuta un `ping` y devuelve `True`/`False` sin
  imprimir la URI completa (para no exponer credenciales si en el futuro la cadena de
  conexión las llegara a tener).
- Importar el archivo **no** ejecuta ninguna conexión; el cliente de MongoDB se crea de
  forma perezosa (solo cuando se llama a `obtener_cliente()`).

### 2. Variables de entorno

Se crearon [.env.example](./.env.example) y `.env` (este último no se sube al repositorio)
con:

```
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=monitoreo_industrial
```

Se confirmó con `git check-ignore -v .env` que el archivo `.env` queda excluido de Git por
la regla definida en `.gitignore` (línea `.env`).

### 3. Script `init_db.py`

Se creó [init_db.py](./init_db.py), que:

- Verifica la conexión antes de hacer cualquier otra cosa.
- Revisa con `list_collection_names()` si la colección `sensores` ya existe.
- Si no existe, la crea con `create_collection()`; si ya existe, no hace nada (para no
  borrar ni sobrescribir información existente).
- Verifica al final que la colección haya quedado disponible.
- Cierra la conexión con `cliente.close()` en un bloque `finally`.
- Devuelve el código de salida `1` si ocurre un error, `0` si todo sale bien.

### 4. Script `verify_db.py`

Se creó [verify_db.py](./verify_db.py), que:

- Verifica la conexión y que la base de datos y la colección existan.
- Inserta el documento de prueba pedido (`tipo: temperatura`, `valor: 25.5`,
  `ubicacion: Planta A`, `fecha` actual en UTC).
- Consulta el documento por su `_id` y compara cada campo contra los valores originales.
- Usa `try/finally` para que el documento de prueba se elimine siempre, incluso si falla
  alguna verificación anterior.
- Verifica, después de eliminar, que el documento ya no exista.
- Devuelve el código de salida `1` si cualquier verificación falla, `0` si todo pasa.

### 5. Pruebas ejecutadas y resultados reales

Todas las pruebas se ejecutaron con el Python del entorno virtual
(`.venv\Scripts\python.exe`).

**Prueba 1 — Verificación de conexión (`database.py`):**

```powershell
.\.venv\Scripts\python.exe database.py
```

Resultado: `Conexion exitosa. Base de datos configurada: monitoreo_industrial` (exit code 0).

**Prueba 2 — Primera ejecución de `init_db.py`:**

```powershell
.\.venv\Scripts\python.exe init_db.py
```

Resultado: `Coleccion 'sensores' creada correctamente.` → base de datos y colección
quedaron listas (exit code 0).

**Prueba 3 — Ejecución de `verify_db.py` (primer intento):**

```powershell
.\.venv\Scripts\python.exe verify_db.py
```

Resultado: **falló** en el paso 5 (comparación de campos). Ver sección de errores abajo.

**Corrección aplicada** (ver detalle en "Errores encontrados y soluciones").

**Prueba 3 (repetida) — Ejecución de `verify_db.py` tras la corrección:**

```powershell
.\.venv\Scripts\python.exe verify_db.py
```

Resultado: los 7 pasos se ejecutaron correctamente — conexión OK, base de datos y
colección encontradas, documento insertado, consultado, campos coincidentes, documento
eliminado y limpieza confirmada. Mensaje final: `Prueba de conexion y persistencia
EXITOSA.` (exit code 0).

**Prueba 4 — Segunda ejecución de `init_db.py` (idempotencia):**

```powershell
.\.venv\Scripts\python.exe init_db.py
```

Resultado: `La coleccion 'sensores' ya existe. No se modifica nada.` (exit code 0). Se
confirma que el script puede ejecutarse varias veces sin error ni duplicar nada.

**Prueba 5 — Verificación visual con `mongosh` (consola, como control adicional):**

```powershell
mongosh --quiet monitoreo_industrial --eval "db.getCollectionNames()"
mongosh --quiet monitoreo_industrial --eval "db.sensores.countDocuments({})"
```

Resultado: `[ 'sensores' ]` y `0` documentos — confirma que la colección quedó creada y
vacía (el documento de prueba se eliminó correctamente y no quedaron residuos).

### Errores encontrados y soluciones

**Error 1: la comparación de fechas fallaba en `verify_db.py`.**

Al ejecutar `verify_db.py` por primera vez, el paso de comparación de campos marcó error
en el campo `fecha`:

- Valor esperado (generado en Python): `datetime(2026, 11, 13, 20, 20, 54, 811654,
  tzinfo=timezone.utc)` (con microsegundos y zona horaria).
- Valor obtenido (leído desde MongoDB): `datetime(2026, 11, 13, 20, 20, 54, 811000)` (sin
  zona horaria y con los microsegundos redondeados a milisegundos).

**Causa:** MongoDB (formato BSON) solo guarda fechas con precisión de milisegundos, y por
defecto PyMongo devuelve las fechas leídas sin información de zona horaria (`naive`). Por
eso, al comparar con `==` contra la fecha original (con microsegundos y con zona horaria),
la comparación siempre fallaba, aunque la fecha fuera "la misma" en la práctica.

**Solución aplicada:**

1. En `database.py`, se agregó la opción `tz_aware=True` al crear el `MongoClient`, para
   que las fechas que devuelve MongoDB vengan con zona horaria UTC (igual que
   `datetime.now(timezone.utc)`).
2. En `verify_db.py`, se redondeó la fecha de prueba a milisegundos antes de insertarla
   (función `_fecha_actual_compatible_con_mongo()`), ya que esa es la precisión real que
   MongoDB puede almacenar.

Con estos dos cambios, la fecha guardada y la fecha leída quedaron exactamente iguales y
la prueba pasó sin problema.

### Verificación visual con MongoDB Compass

No se generaron capturas (no se deben simular), pero los pasos para comprobarlo
manualmente quedaron documentados en el [README.md](./README.md), sección "Verificación
visual con MongoDB Compass": conectar a `mongodb://localhost:27017/`, revisar que aparezca
la base `monitoreo_industrial`, entrar a la colección `sensores` y confirmar que queda
vacía después de ejecutar `verify_db.py`.

### Checklist de cierre de la Fase 2

- [x] La conexión desde Python funciona (`database.py`, `verificar_conexion()`).
- [x] La base de datos `monitoreo_industrial` existe (creada por `init_db.py`).
- [x] La colección `sensores` existe.
- [x] Se pueden insertar y consultar documentos (`verify_db.py`).
- [x] Los documentos temporales de prueba se eliminan correctamente (confirmado con
  `mongosh`: 0 documentos en la colección tras la prueba).
- [x] Los scripts pueden ejecutarse nuevamente sin errores (`init_db.py` ejecutado dos
  veces, `verify_db.py` corregido y verificado).
- [x] `README.md` y `BITACORA.md` actualizados con información real.

**Pendientes para la Fase 3:** implementar los endpoints REST (`POST`, `GET`, `PUT`,
`DELETE`) de la API Flask, usando `database.py` para acceder a la colección `sensores`, y
agregar las validaciones de los campos y rangos permitidos.

---

## FASE 3 — Implementación de API REST CRUD con Flask y MongoDB

**Fecha:** 13/11/2026

**Objetivo de la fase:** implementar la API RESTful con Flask para crear, consultar,
actualizar y eliminar sensores, reutilizando la conexión de `database.py`, con
validaciones de datos y manejo de errores con códigos HTTP apropiados.

### 1. Archivos creados / modificados

- **`errores.py`** (nuevo): define las excepciones controladas que usa la API
  (`ErrorValidacion`, `SensorNoEncontrado`, `ConflictoMultiplesSensores`,
  `TipoContenidoNoSoportado`, `ServicioNoDisponible`), cada una con su código HTTP.
- **`validaciones.py`** (nuevo): funciones reutilizables para validar `tipo`, `valor`
  (rango según tipo), `ubicacion` y `fecha` (ISO 8601 → `datetime` UTC redondeado a
  milisegundos), además de las validaciones completas para `POST` y `PUT`.
- **`API.py`** (nuevo): aplicación Flask con la función fábrica `crear_app(nombre_bd=None)`
  y los 7 endpoints pedidos.
- **`tests/test_api.py`** (nuevo): 22 pruebas automatizadas con pytest y el cliente de
  pruebas de Flask.
- **`database.py`** (modificado): se agregó el parámetro opcional `nombre_bd` a
  `obtener_base_datos()` y `obtener_coleccion_sensores()`, para que las pruebas puedan usar
  una base de datos de pruebas separada. El comportamiento por defecto (sin pasar el
  parámetro) no cambió, así que `init_db.py` y `verify_db.py` siguen funcionando igual.
- **`README.md`** y **`BITACORA.md`**: actualizados con la documentación de esta fase.

### 2. Diseño de la API

- `API.py` usa una función fábrica `crear_app(nombre_bd=None)` en vez de un único objeto
  Flask global. Esto permite crear una instancia de la app apuntando a la base de datos
  real (`monitoreo_industrial`, usada por `app = crear_app()` al final del archivo) o a una
  base de datos de pruebas (`crear_app(nombre_bd="monitoreo_industrial_test")`, usada por
  `tests/test_api.py`), sin duplicar código ni tocar `database.py` más de lo necesario.
- El servidor **no** se inicia al importar `API.py`; `app.run()` solo se ejecuta dentro de
  `if __name__ == "__main__":`.
- Las respuestas se arman con `jsonify`. Los `ObjectId` se convierten a texto (`str`) y las
  fechas se devuelven en formato ISO 8601 UTC terminado en `Z` (ej.
  `2026-11-13T10:30:00Z`).
- El manejo de errores es centralizado con `@app.errorhandler(...)`: en vez de poner
  `try/except` en cada endpoint, los errores (de validación, de MongoDB, o no esperados)
  "suben" hasta un manejador que arma la respuesta JSON con el código HTTP correcto. Esto
  evita usar `except Exception` para ocultar bugs de programación: solo se traducen
  explícitamente los errores de negocio (`ErrorAPI` y sus subclases) y los errores propios
  de PyMongo (`PyMongoError`, `ServerSelectionTimeoutError`); cualquier otro error
  inesperado se registra en la consola del servidor (con `traceback.print_exc()`) y se
  responde con un `500` genérico, sin exponer el detalle interno al cliente.

### 3. Endpoints implementados

| Método | Ruta | Código de éxito |
|---|---|---|
| `POST` | `/sensores/` | 201 |
| `GET` | `/sensores/` (con filtro opcional `?tipo=`) | 200 |
| `PUT` | `/sensores/<tipo>` | 200 (404 si no existe, 409 si hay varios) |
| `DELETE` | `/sensores/<tipo>` | 200 (404 si no existe, 409 si hay varios) |
| `PUT` | `/sensores/id/<sensor_id>` | 200 (400 si el id es inválido, 404 si no existe) |
| `DELETE` | `/sensores/id/<sensor_id>` | 200 (400 si el id es inválido, 404 si no existe) |

Para los endpoints por `<tipo>`, se usa `count_documents({"tipo": tipo})` antes de
modificar o eliminar: si da `0` se responde `404`, si da más de `1` se responde `409` (sin
tocar ningún documento), y solo si da exactamente `1` se hace el `update_one`/`delete_one`
usando el `_id` concreto de ese documento (para no modificar/eliminar varios por error).

### 4. Comandos ejecutados y resultados

**Primera ejecución de las pruebas automatizadas:**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_api.py -v
```

Resultado: **20 pruebas pasaron, 2 fallaron** (`test_put_por_id_inexistente_devuelve_404` y
`test_delete_por_id_inexistente_devuelve_404`). Ver la causa y la corrección en la sección
de errores.

**Segunda ejecución (tras corregir el dato de prueba):**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_api.py -v
```

Resultado: **22 pruebas pasaron, 0 fallaron.**

**Arranque manual del servidor y pruebas con `curl` (verificación de extremo a extremo,
contra la base de datos real `monitoreo_industrial`):**

```powershell
.\.venv\Scripts\python.exe API.py
```

Se probaron, con `curl.exe`, los siguientes casos (todos con resultado correcto):

- `POST /sensores/` → `201`, documento creado con `_id` y `fecha` en formato `...Z`.
- `GET /sensores/` → `200`, lista con los sensores creados.
- `GET /sensores/?tipo=presion` → `200`, solo el sensor filtrado.
- `PUT /sensores/temperatura` → `200`, valor actualizado.
- `PUT /sensores/id/<id>` → `200`, campo actualizado, `tipo` sin cambios.
- `DELETE /sensores/id/<id>` y `DELETE /sensores/temperatura` → `200`, confirmando luego
  con `GET /sensores/` que la colección quedó en `[]`.
- `POST` con `valor` fuera de rango → `400`.
- `POST` con `tipo` inválido (`"humedad"`) → `400`.
- `POST` con `Content-Type: text/plain` → `415`.
- `PUT /sensores/vibracion` sin sensores de ese tipo → `404`.
- `POST /sensores/temperatura` (método no soportado en esa ruta) → `405`.
- `GET /no-existe` (ruta inexistente) → `404`.
- Creando dos sensores de `vibracion` y luego `PUT`/`DELETE /sensores/vibracion` → `409` en
  ambos casos, sin modificar ni eliminar ningún documento (se limpiaron manualmente por
  `id` al final de la prueba).

Al finalizar estas pruebas manuales, se confirmó con `mongosh` que la base de datos
`monitoreo_industrial` quedó con la colección `sensores` vacía (0 documentos), igual que
antes de empezar la Fase 3.

### 5. Errores encontrados y correcciones

**Error 1: dos pruebas automatizadas fallaban por un dato de prueba incorrecto, no por un
bug de la API.**

Las pruebas `test_put_por_id_inexistente_devuelve_404` y
`test_delete_por_id_inexistente_devuelve_404` usaban el identificador
`"64b64b64b64b64b64b64b64"` como ejemplo de un `ObjectId` "válido mas no existente". Al
contarlo, ese texto tiene solo **23 caracteres**, no los 24 que requiere un `ObjectId`
válido. Por eso la API respondía `400` (formato inválido) en vez de `404` (no encontrado):
el comportamiento de la API era correcto, el dato de la prueba estaba mal construido.

**Solución aplicada:** se cambió el identificador de prueba a `"000000000000000000000000"`
(24 caracteres hexadecimales válidos, pero que no corresponde a ningún documento real), lo
que permitió probar específicamente el caso `404`. Tras el cambio, las 22 pruebas pasaron.

### 6. Checklist de cierre de la Fase 3

- [x] `API.py` existe y el servidor inicia correctamente (`python API.py`).
- [x] Los cinco comportamientos CRUD funcionan (crear, listar, listar por tipo, actualizar,
  eliminar).
- [x] Las operaciones por identificador (`/sensores/id/<id>`) funcionan.
- [x] MongoDB almacena y devuelve los datos correctamente (`_id` como texto, `fecha` en
  ISO 8601 UTC).
- [x] Las validaciones básicas están implementadas (campos obligatorios, tipo, rango,
  ubicación, fecha, campos desconocidos, inmutabilidad de `tipo`/`_id`).
- [x] Los errores devuelven respuestas JSON con el código HTTP correspondiente (400, 404,
  405, 409, 415, 500, 503).
- [x] Las pruebas automatizadas pasan (22/22).
- [x] `README.md` y `BITACORA.md` actualizados con información real.

**Pendientes para la Fase 4:** quedará a definir según las siguientes instrucciones del
proyecto (por ejemplo, documentación final, empaquetado u otras mejoras). No se ha avanzado
nada de la Fase 4 todavía.

---

## FASE 4 — Auditoría de validaciones, manejo de errores y pruebas negativas

**Fecha:** 13/11/2026

**Objetivo de la fase:** auditar el cumplimiento de los requisitos académicos, ampliar la
cobertura de pruebas (casos límite, tipos de dato incorrectos, fechas inválidas, errores de
MongoDB) y corregir defectos reales si se encontraban.

### 1. Matriz de cumplimiento académico

| Requisito | Evidencia |
|---|---|
| `POST /sensores/` | [API.py:128](./API.py) (`crear_sensor`); probado en `test_post_crea_sensor` y 20+ pruebas más en `tests/test_api.py`. |
| `GET /sensores/` | [API.py:138](./API.py) (`listar_sensores`); `test_get_general_sin_datos_devuelve_lista_vacia`, `test_get_general_devuelve_todos_los_sensores`. |
| `GET /sensores/` con filtro por tipo | Mismo handler, usa `request.args.get("tipo")`; `test_get_por_tipo_filtra_correctamente`, `test_get_por_tipo_invalido_devuelve_400`. |
| `PUT` según tipo | [API.py:148](./API.py) (`actualizar_sensor_por_tipo`); `test_put_por_tipo_actualiza_el_sensor` y pruebas de límites/conflicto. |
| `DELETE` según tipo | [API.py:161](./API.py) (`eliminar_sensor_por_tipo`); `test_delete_por_tipo_elimina_el_sensor`. |
| Validación de tipo | [validaciones.py](./validaciones.py) función `validar_tipo`; `test_post_tipo_invalido` (9 variantes), `test_get_por_tipo_invalido_en_query_string_tambien_rechaza`. |
| Validación de rangos | `validar_valor` en [validaciones.py](./validaciones.py); `test_post_valor_en_el_limite_es_valido` y `test_post_valor_fuera_del_limite_es_invalido` (6 combinaciones cada una, límites inclusivos exactos). |
| Ubicación obligatoria | `validar_ubicacion`; `test_post_falta_un_campo_devuelve_400`, `test_post_ubicacion_invalida` (6 variantes). |
| Fecha obligatoria y válida | `validar_fecha`; `test_post_fecha_invalida` (7 variantes, incluye fecha imposible 30 de febrero), `test_post_fecha_se_normaliza_a_utc`. |
| Manejo de errores de solicitudes | `errores.py` + manejadores centralizados en [API.py:205-232](./API.py); cubre 400/404/405/409/415. |
| Manejo de errores de conexión a MongoDB | Manejadores `ServerSelectionTimeoutError` (503) y `PyMongoError` (500) en [API.py:217-227](./API.py); probado con mocks en `tests/test_errores_mongo.py` (sin detener el servicio real). |
| Respuestas JSON | Todas las respuestas usan `jsonify(...)`, incluidas las de error (`{"error": "..."}`), verificado en todas las pruebas. |
| Persistencia real | `tests/test_api.py` usa MongoDB real (base de pruebas separada); además se repitió `verify_db.py` con resultado exitoso durante esta fase. |

### 2-4. Auditoría de validaciones, CRUD y errores de MongoDB — metodología y hallazgos

La auditoría se hizo probando cada caso **de verdad** (no solo leyendo el código), con
scripts exploratorios temporales contra la API real (usando bases de datos de auditoría
separadas, luego eliminadas) y, para los fallos de MongoDB, con mocks controlados
(`unittest.mock` + `monkeypatch` de pytest), tal como pide la actividad, sin detener el
servicio real de MongoDB en ningún momento.

**Resultado general: no se encontraron defectos funcionales reales.** La implementación de
la Fase 3 ya cumplía correctamente con:

- Límites inclusivos exactos de `valor` para los tres tipos (se probaron los límites
  exactos y los valores "límite ± 0.01").
- Rechazo de cadenas, booleanos, `null`, listas, objetos, `NaN`, `Infinity` y `-Infinity`
  en `valor` (gracias a `math.isfinite()` ya presente en `validar_valor`).
- Rechazo de `ubicacion` vacía, solo espacios, `null`, números, listas y objetos; recorte
  correcto de espacios exteriores.
- Rechazo de fechas malformadas y de fechas imposibles (ej. `"2026-02-30T00:00:00Z"`,
  `"2026-13-01T00:00:00Z"`): `datetime.fromisoformat()` ya valida rangos de mes/día.
- Normalización correcta a UTC de fechas con `Z`, con desfase horario (`-05:00`) y sin
  zona horaria (se asume UTC, documentado).
- Precisión de milisegundos preservada correctamente (microsegundos `123456` → `123000`
  al guardar y al serializar).
- Rechazo de cuerpos JSON vacíos, malformados, arreglos en lugar de objetos, campos
  desconocidos y `Content-Type` incorrecto (incluyendo que `"application/json; charset=
  utf-8"` sí se acepta, por ser un caso válido).
- Aislamiento correcto de operaciones por `tipo`: con 0 coincidencias → `404`; con 1 → se
  modifica/elimina; con 2+ → `409` **sin tocar ningún documento** (confirmado comparando
  los valores antes y después del intento fallido).
- Aislamiento correcto de operaciones por `_id`: solo afectan el documento indicado, el
  resto de sensores del mismo tipo no se modifican.
- Inmutabilidad de `tipo` y `_id` en `PUT`, con o sin identificador.
- `PUT` con cuerpo vacío (`{}`) se rechaza con `400`.
- Identificadores de Mongo inválidos (muy cortos, muy largos, con caracteres no
  hexadecimales) devuelven `400`; identificadores válidos pero inexistentes devuelven
  `404`.
- Métodos HTTP no soportados en una URL válida devuelven `405` (por ejemplo, `GET` en
  `/sensores/id/<id>`, que solo admite `PUT`/`DELETE`).
- Errores de MongoDB: timeout/no disponible → `503`; error de lectura u escritura
  (`OperationFailure`, `PyMongoError` genérico) → `500`; excepción totalmente inesperada
  (simulada con `RuntimeError`) → `500` genérico. En los tres casos, la respuesta al
  cliente **nunca** incluye el mensaje interno del error ni la URI de conexión (se probó
  deliberadamente con un mensaje de error que contenía `usuario`/`clave-secreta`, y no
  aparece en la respuesta JSON), mientras que el error sí queda impreso en la consola del
  servidor (verificado con `capsys` en las pruebas).

**Observación de diseño (no es un defecto):** en `PUT /sensores/<tipo>` y
`PUT /sensores/id/<sensor_id>`, el código primero busca el sensor (pudiendo responder
`404`/`409`) y **después** valida el `Content-Type`/cuerpo JSON (pudiendo responder
`400`/`415`). Esto significa que, si ambas cosas fallan a la vez, prevalece el error sobre
la existencia del recurso. Se decidió **no** reordenar esto, porque no es un defecto (cada
validación sigue funcionando correctamente por separado) y la actividad pide explícitamente
no reestructurar la aplicación sin una razón justificada.

### 5. Revisión de calidad de código (sección 6 de la actividad)

| Aspecto | Resultado |
|---|---|
| Duplicación de código | Los endpoints por `tipo` y por `id` repiten un patrón similar (buscar → validar → actualizar → responder). Es una duplicación menor y deliberada para mantener cada función simple y fácil de leer; no se refactorizó porque la actividad pide no reestructurar la aplicación sin necesidad. |
| Funciones demasiado extensas | No se encontraron funciones largas; cada handler tiene entre 4 y 10 líneas. |
| Manejo de excepciones | Se usan excepciones específicas (`ErrorAPI` y subclases, `PyMongoError`, `ServerSelectionTimeoutError`); no hay ningún `except Exception` que oculte bugs de programación dentro de la lógica de negocio. El único `@app.errorhandler(Exception)` es el mecanismo estándar de Flask para no exponer trazas al cliente, y registra el error completo en consola. |
| Uso de recursos y cierre de conexiones | `MongoClient` es un singleton reutilizado durante toda la vida del proceso (recomendado por PyMongo); `init_db.py` y `verify_db.py` lo cierran explícitamente en su bloque `finally` al terminar. |
| Configuración de Flask | `app.run(debug=True)` solo se ejecuta en `if __name__ == "__main__"`; se confirmó que el manejador `@app.errorhandler(Exception)` captura cualquier error antes de que el depurador interactivo de Werkzeug pudiera mostrar una traza en el navegador. |
| Ausencia de credenciales en código | No hay credenciales en ningún archivo; `.env`/`.env.example` solo tienen la URI local sin usuario/contraseña (MongoDB local sin autenticación). |
| Compatibilidad con Python 3.10 | Confirmado: todas las 96 pruebas pasan con Python 3.10.10. El manejo manual del sufijo `"Z"` en `validar_fecha` existe precisamente porque `datetime.fromisoformat()` no lo soporta de forma nativa hasta Python 3.11. |
| Consistencia de respuestas JSON | Todas las respuestas (éxito y error) usan `jsonify(...)`; los errores siempre tienen la forma `{"error": "..."}`. |
| Compatibilidad con scripts de fases anteriores | Se volvió a ejecutar `database.py`, `init_db.py` (dos veces) y `verify_db.py` tras los cambios de esta fase: los tres siguen funcionando exactamente igual (ver sección 7). |

**Conclusión de la revisión de calidad:** no se aplicó ningún cambio de código a `API.py`,
`validaciones.py`, `errores.py` ni `database.py`, porque no se encontró ningún defecto que
lo justificara. Los únicos archivos nuevos/modificados fueron de pruebas y documentación.

### 6. Archivos modificados

- **`tests/test_api.py`** (ampliado): se agregaron ~56 pruebas de integración nuevas
  (muchas parametrizadas con `@pytest.mark.parametrize` para evitar duplicación), **sin
  modificar ni eliminar ninguna de las 22 pruebas existentes de la Fase 3**.
- **`tests/test_errores_mongo.py`** (nuevo): 8 pruebas unitarias que simulan fallos de
  MongoDB con `unittest.mock` y `monkeypatch`, sin depender de un servidor real ni
  detener el servicio de MongoDB.
- **`README.md`**: se documentaron en detalle las reglas de validación auditadas, los
  formatos de fecha aceptados, el comportamiento ante múltiples sensores del mismo tipo,
  y la diferencia entre pruebas de integración y unitarias.
- **`BITACORA.md`**: esta sección.

No se modificó `API.py`, `validaciones.py`, `errores.py`, `database.py`, `init_db.py` ni
`verify_db.py`.

### 7. Ejecución y regresión

**Suite completa de pruebas automatizadas:**

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Resultado: **96 pruebas pasaron, 0 fallaron** (22 de la Fase 3 + 66 nuevas de integración
en `tests/test_api.py` + 8 nuevas unitarias en `tests/test_errores_mongo.py`).

**Regresión de los scripts de fases anteriores (ejecutados en este orden, tras los cambios
de la Fase 4):**

```powershell
.\.venv\Scripts\python.exe database.py      # Verificacion de conexion
.\.venv\Scripts\python.exe init_db.py       # Idempotencia (1ra vez en esta sesion)
.\.venv\Scripts\python.exe init_db.py       # Idempotencia (2da vez)
.\.venv\Scripts\python.exe verify_db.py     # Persistencia y limpieza
```

Resultados: los cuatro comandos terminaron con código de salida `0`. `init_db.py` reportó
en ambas ejecuciones `"La coleccion 'sensores' ya existe. No se modifica nada."`, y
`verify_db.py` completó sus 7 pasos (conexión, verificación de BD/colección, inserción,
consulta, comparación de campos, eliminación y confirmación de limpieza) sin errores.

**Confirmación de que la base principal conserva sus datos:** antes, durante y después de
toda la auditoría y de la ejecución de la suite de pruebas, se verificó con `mongosh` que
`monitoreo_industrial.sensores` se mantuvo en **0 documentos** (el mismo estado de cierre
de la Fase 3) y que no quedó ninguna base de datos de auditoría ni de pruebas residual:

```powershell
mongosh --quiet monitoreo_industrial --eval "db.sensores.countDocuments({})"
mongosh --quiet --eval "db.adminCommand('listDatabases').databases.map(d => d.name)"
```

Resultado: `0` documentos; solo las bases de datos del sistema (`admin`, `config`,
`local`), la base `iudigital_proyectos` (preexistente, ajena a este proyecto) y
`monitoreo_industrial`.

### 8. Checklist de cierre de la Fase 4

- [x] Los requisitos académicos están cubiertos (ver matriz de cumplimiento).
- [x] Las validaciones funcionan correctamente (auditadas con casos límite reales).
- [x] Los errores HTTP son consistentes (400/404/405/409/415/500/503, siempre en JSON).
- [x] Los errores de MongoDB están controlados (probados con mocks: 503/500, sin exponer
  detalles internos ni credenciales).
- [x] Todas las pruebas automatizadas pasan (96/96).
- [x] No existen regresiones (scripts de fases anteriores siguen funcionando igual).
- [x] La base principal conserva sus datos (0 documentos, igual que al cierre de la Fase 3).
- [x] `README.md` y `BITACORA.md` actualizados.

**Pendientes:** ninguno dentro del alcance de la Fase 4. La duplicación menor de código
entre los endpoints por tipo/por id (mencionada en la revisión de calidad) queda anotada
como observación, no como defecto, y no se modificó para respetar la restricción de no
reestructurar la aplicación.

---

## FASE 5 — Pruebas funcionales con Postman y evidencias reales

**Fecha:** 13/11/2026

**Objetivo de la fase:** preparar y ejecutar pruebas funcionales de todos los endpoints
mediante Postman, documentando los resultados con capturas de pantalla reales.

**Resultado general: parcialmente completada.** La colección de Postman se preparó y se
verificó que funciona perfectamente de extremo a extremo, pero **no fue posible abrir las
aplicaciones de escritorio Postman ni MongoDB Compass** en este entorno para tomar las
capturas de pantalla reales que pide la actividad. Esta sección documenta exactamente qué
se hizo, qué se intentó, y qué queda pendiente para completarse manualmente.

### 1. Colección Postman creada

Se creó [postman/EA2-MongoDB-Sensores-CRUD.postman_collection.json](./postman/EA2-MongoDB-Sensores-CRUD.postman_collection.json),
en formato Postman Collection **v2.1** (`schema: .../v2.1.0/collection.json`), con el
nombre exacto pedido: **"EA2 - MongoDB Sensores CRUD"**.

Se generó con un script Python temporal (`build_postman_tmp.py`, eliminado después de
usarlo) para evitar errores de sintaxis JSON al escribir un archivo tan grande a mano; el
archivo final se validó recargándolo con `json.load()` antes de continuar.

**Variables de colección:** `base_url` (`http://127.0.0.1:5000`), `sensor_id` y
`sensor_id_extra` (ambas vacías por defecto, se completan solas con scripts al ejecutar la
colección).

**19 solicitudes en 4 carpetas:**

- **01 - CRUD principal** (7): crear temperatura/presión/vibración, consultar todos,
  filtrar por tipo, actualizar por tipo, eliminar por tipo.
- **02 - Operaciones por ID** (2): actualizar y eliminar por `_id` (usa `{{sensor_id}}`,
  capturado automáticamente al crear el sensor de vibración).
- **03 - Validaciones y errores** (6): tipo no permitido (400), valor fuera de rango
  (400), PUT a sensor inexistente (404), dos solicitudes de preparación que crean 2
  sensores de presión, y el DELETE con múltiples coincidencias (409).
- **04 - Limpieza** (4): elimina todo lo creado por la práctica y confirma con un GET
  final que la colección quedó vacía.

Cada solicitud incluye un script de prueba (`pm.test(...)`) que verifica el código HTTP
esperado y, en varios casos, el contenido de la respuesta; los scripts de captura de `_id`
revisan primero si la variable ya tiene un valor (`if (!pm.collectionVariables.get(...))`)
para no sobrescribir un identificador accidentalmente, tal como pide la actividad.

### 2. Intento de ejecución con Postman (aplicación de escritorio)

Se confirmó que Postman **sí está instalado** en este equipo
(`C:\Users\Diana.Giraldo\AppData\Local\Postman\`, versión de la app `12.36.2`), y que
MongoDB Compass también lo está (ya confirmado desde la Fase 1).

Con tu autorización, se activó **Computer Use** para poder observar y controlar la
interfaz gráfica. Se intentó abrir Postman dos veces (usando el ejecutable principal y
también el ejecutable de la versión instalada directamente) y MongoDB Compass una vez.
En los tres intentos:

- La herramienta reportó que el proceso se había "lanzado en segundo plano".
- Sin embargo, al revisar la lista de ventanas (`cua.listWindows()`) y la lista de
  procesos del sistema (`Get-Process`) varias veces, con tiempos de espera de hasta 25
  segundos adicionales, **ninguna de las dos aplicaciones llegó a producir una ventana ni
  un proceso visible** (ni siquiera uno que apareciera y luego fallara).

**Conclusión:** no fue posible interactuar con Postman ni con MongoDB Compass en este
entorno (muy probablemente una limitación del entorno de automatización remoto para
ejecutar aplicaciones de escritorio basadas en Electron, no un problema del proyecto ni de
las aplicaciones en sí). Siguiendo la instrucción de la actividad ("si no puedes
interactuar con Postman... deja la actividad pendiente y explica cómo hacerlo
manualmente"), se dejó esta parte pendiente en vez de inventar o simular capturas.

### 3. Pruebas realmente ejecutadas — Newman (no curl, no simuladas)

En lugar de usar `curl` para "fingir" una ejecución de Postman, se usó **Newman**, que es
el motor oficial de línea de comandos de Postman (ejecuta el mismo archivo
`.postman_collection.json`, con el mismo motor de solicitudes y los mismos scripts de
prueba que usaría la aplicación de escritorio). Esto es una ejecución real de la colección
de Postman, aunque sin interfaz gráfica.

Comandos ejecutados:

```powershell
.venv\Scripts\python.exe API.py          # Se dejo corriendo la API real en otra terminal
npm install newman@6.2.3 --no-fund --no-audit   # Instalacion local (npx tenia una
                                                  # dependencia rota, @faker-js/faker)
.\node_modules\.bin\newman.cmd run "postman\EA2-MongoDB-Sensores-CRUD.postman_collection.json" --color off
```

**Resultado real (dos ejecuciones, ambas con el mismo resultado):**

```
requests: 19 ejecutadas, 0 fallidas
test-scripts: 19 ejecutados, 0 fallidos
assertions: 30 ejecutadas, 0 fallidas
total run duration: ~3 segundos
```

Es decir: las 19 solicitudes (los 13 escenarios pedidos más las 4 de preparación/limpieza
necesarias para que el flujo sea reproducible) respondieron exactamente con los códigos
HTTP esperados, contra la API Flask real y la base de datos MongoDB real. La segunda
ejecución se guardó completa en
[evidencias/resultados_newman_cli.txt](./evidencias/resultados_newman_cli.txt).

Después de cada ejecución se verificó con `mongosh` que `monitoreo_industrial.sensores`
quedó en **0 documentos** (la carpeta "04 - Limpieza" de la colección se encarga de esto),
confirmando que no quedaron residuos de la prueba.

### 4. Distinción explícita: Newman vs. Postman (GUI) vs. curl

- **Newman (SÍ se ejecutó):** usa el mismo archivo de colección y el mismo motor de
  Postman; es una ejecución real y automatizada de la colección, pero sin ventana gráfica
  ni capturas de pantalla posibles.
- **Postman de escritorio (NO se pudo ejecutar):** se intentó mediante Computer Use, pero
  la aplicación no llegó a abrir ninguna ventana en este entorno.
- **curl (NO se usó para "simular" Postman):** en esta fase no se usó `curl` en ningún
  momento como sustituto de Postman; toda la verificación funcional de esta fase se hizo
  con Newman (ejecutando la colección real) y, anteriormente, en fases pasadas, sí se usó
  `curl` para probar la API directamente (eso quedó documentado en las Fases 3 y 4, no se
  confunde aquí con pruebas de Postman).

### 5. Capturas obtenidas

**Ninguna.** No se generaron capturas de pantalla de Postman ni de MongoDB Compass, porque
ninguna de las dos aplicaciones pudo abrirse (ver punto 2). No se simuló ni se inventó
ninguna captura, conforme a las restricciones de la actividad.

### 6. Evidencias pendientes

Quedan pendientes, para que tú las completes manualmente (instrucciones detalladas en el
[README.md](./README.md), sección "Pruebas funcionales con Postman"):

1. `evidencias/01_post_crear_sensor.png`
2. `evidencias/02_get_todos_sensores.png`
3. `evidencias/03_get_filtrar_tipo.png`
4. `evidencias/04_put_actualizar_sensor.png`
5. `evidencias/05_delete_eliminar_sensor.png`
6. `evidencias/06_put_por_id.png`
7. `evidencias/07_delete_por_id.png`
8. `evidencias/08_validacion_tipo.png`
9. `evidencias/09_validacion_rango.png`
10. `evidencias/10_sensor_inexistente.png`
11. `evidencias/11_conflicto_409.png`
12. Una captura adicional de MongoDB Compass mostrando los documentos reales en
    `monitoreo_industrial.sensores`.

### 7. Regresión (sección 8 de la actividad)

Se volvió a ejecutar la suite completa de pruebas automatizadas, antes y después de
trabajar en la colección de Postman:

```powershell
.venv\Scripts\python.exe -m pytest -q
```

Resultado: **96 pruebas pasaron, 0 fallaron** (las mismas 96 de la Fase 4, sin cambios,
porque no se modificó ningún archivo de la API en esta fase). La base de datos principal
`monitoreo_industrial` se mantuvo en 0 documentos antes, durante y después de toda la
fase (verificado varias veces con `mongosh`).

### 8. Archivos creados o modificados

- **`postman/EA2-MongoDB-Sensores-CRUD.postman_collection.json`** (nuevo): la colección
  completa.
- **`evidencias/resultados_newman_cli.txt`** (nuevo): salida real de la ejecución con
  Newman (evidencia textual, no una captura de pantalla, pero real y verificable).
- **`README.md`**: nueva sección "Pruebas funcionales con Postman", con instrucciones de
  importación, variables, orden de ejecución y la lista de evidencias pendientes.
- **`BITACORA.md`**: esta sección.

No se modificó `API.py`, `validaciones.py`, `errores.py`, `database.py`, `init_db.py`,
`verify_db.py`, ni los archivos de `tests/` (no se detectó ningún defecto que lo
justificara; la colección de Postman confirmó que la API responde exactamente como se
espera en los 13 escenarios pedidos, más los de preparación/limpieza).

### 9. Checklist de cierre de la Fase 5

- [x] La colección Postman es válida (formato v2.1, se valida con `json.load` y se
  ejecuta sin errores con Newman).
- [x] Los endpoints se ejecutan correctamente (19/19 solicitudes, 30/30 aserciones, con
  Newman contra la API y MongoDB reales).
- [x] Las variables dinámicas funcionan (`sensor_id`/`sensor_id_extra` se capturan y se
  reutilizan correctamente, confirmado por los resultados de Newman).
- [x] Los códigos HTTP son correctos en los 13 escenarios pedidos.
- [ ] **Pendiente:** capturas de pantalla reales de los endpoints principales (no se
  pudo abrir Postman en este entorno).
- [ ] **Pendiente:** verificación visual en MongoDB Compass (no se pudo abrir Compass en
  este entorno).
- [x] Las pruebas automatizadas siguen pasando (96/96, sin regresiones).
- [x] `README.md` y `BITACORA.md` actualizados, distinguiendo claramente Newman, Postman
  (GUI) y curl.

**Pendientes:** las 11 capturas de pantalla de Postman y la captura de MongoDB Compass
(sección 6 de esta bitácora). Postman y Compass están instalados en el equipo y la
colección ya está lista para importar; solo falta que se ejecuten manualmente desde una
sesión donde esas aplicaciones puedan abrir su interfaz gráfica.

---

## FASE 6 — Documentación, reproducibilidad y preparación de entrega

**Fecha:** 13/11/2026

**Objetivo de la fase:** auditar y completar la documentación técnica, verificar (de forma
estática, sin ejecutar nada) que el proyecto sea reproducible desde cero, y preparar la
lista de archivos para el ZIP de entrega, sin generarlo todavía.

**Restricción especial de esta fase:** la estudiante estaba ejecutando Postman y tomando
capturas de pantalla en paralelo. Por eso, en esta fase **no se ejecutó la API, ni Newman,
ni las pruebas automatizadas, ni se escribió en MongoDB, ni se tocó la colección Postman ni
la carpeta `evidencias/`**. Todo el trabajo de esta fase fue auditoría estática (lectura de
archivos) y edición de documentación (`README.md` y `BITACORA.md`).

### 1. Auditoría documental de README.md

Se revisó el `README.md` existente (heredado de las Fases 1-5) contra la estructura pedida
para esta fase, y se encontraron las siguientes brechas, ya corregidas:

- **Faltaba una sección "Descripción" explícita** con nombre del proyecto, tecnologías
  utilizadas y arquitectura. Se agregó, incluyendo un diagrama simple en texto de las
  capas (`API.py` → `validaciones.py`/`errores.py` → `database.py` → MongoDB).
- **"Requisitos previos" no mencionaba Postman ni Git** como opcionales. Se agregaron.
- **No existía una sección "Instalación" consolidada y numerada.** Antes, los pasos de
  configuración estaban repartidos en varias secciones distintas (de cuando se escribieron
  en fases separadas). Se creó una sección única "Instalación" con los 7 pasos pedidos
  (abrir carpeta, crear venv, instalar dependencias, configurar `.env`, verificar MongoDB,
  inicializar BD, ejecutar la API), verificando que cada comando coincide exactamente con
  los archivos reales del proyecto (`requirements.txt`, `.env.example`, `init_db.py`,
  `API.py`). Se recortó la duplicación que esto generaba en la sección de "Configuración
  de MongoDB", dejando ahí solo el detalle adicional (tabla de variables, explicación de
  cada script) sin repetir los mismos comandos dos veces.
- **La documentación de los endpoints era incompleta.** Antes solo había una tabla resumen
  y ejemplos completos para 3 de las 7 operaciones (crear, actualizar por tipo, actualizar/
  eliminar por id). Se agregó una sección "Uso de la API — detalle de cada operación" con
  las 7 operaciones pedidas (POST, GET, GET con filtro, PUT por tipo, DELETE por tipo, PUT
  por id, DELETE por id), cada una con objetivo, método, URL, cuerpo JSON (cuando aplica),
  respuesta esperada y código HTTP.
- **No existía una sección dedicada a "Manejo de errores".** Antes los códigos de error
  estaban mezclados en una sola tabla con los códigos de éxito. Se creó la sección
  "Manejo de errores" con los 7 códigos de error (400, 404, 405, 409, 415, 500, 503),
  cuándo ocurre cada uno, y la aclaración de que los detalles técnicos nunca se exponen al
  cliente.
- **La sección de pruebas no indicaba resultados numéricos previos.** Se agregó la
  mención explícita de "96 pruebas, 96 exitosas, 0 fallidas (Fase 4)" y "19 solicitudes,
  30 aserciones, 0 fallidas (Fase 5, con Newman)", dejando explícito que son resultados
  **ya documentados en fases anteriores**, no una ejecución nueva de esta fase.
- **Faltaba mencionar Newman como alternativa opcional** a la interfaz gráfica de Postman
  para ejecutar la colección. Se agregó, aclarando que Newman no reemplaza las capturas de
  pantalla porque no tiene interfaz gráfica.
- **La sección de evidencias no referenciaba la guía de capturas** creada en la fase
  anterior. Se agregó un enlace a `evidencias/GUIA_CAPTURAS.md`, y se reforzó la redacción
  para dejar explícito que la captura de evidencias está "en proceso" (la estudiante
  ejecutándolo en paralelo) y que esta documentación no afirma que ya estén completas ni
  intenta listar el contenido actual de la carpeta `evidencias/` (para no quedar
  desactualizada ni interferir con ese trabajo).
- Se agregó la nueva sección **"Preparación de entrega (Fase 6)"** (ver punto 5 de esta
  bitácora).

**Archivos modificados en este punto:** `README.md` únicamente. No se tocó ningún archivo
de código.

### 2. Revisión de requirements.txt

Se revisó `requirements.txt` contra los `import` reales de todos los archivos `.py` del
proyecto (`API.py`, `database.py`, `validaciones.py`, `errores.py`, `init_db.py`,
`verify_db.py`, `tests/test_api.py`, `tests/test_errores_mongo.py`), usando únicamente
lectura de código (sin ejecutar `pip` ni tocar el entorno virtual):

```
Flask==3.0.3
pymongo==4.8.0
python-dotenv==1.0.1
pytest==8.3.2
```

**Resultado: no se encontró ningún problema que justifique modificar el archivo.**

- Todas las dependencias externas que se importan en el código (`flask`, `pymongo`/`bson`,
  `dotenv`) están cubiertas por estos 4 paquetes; `bson` viene incluido con `pymongo`, no
  es un paquete aparte.
- `pytest` se usa únicamente en `tests/`, pero se mantiene en el mismo archivo porque así
  se definió desde la Fase 1 (mantener el proyecto simple con un solo archivo de
  dependencias, en vez de separar "requirements-dev.txt").
- Las cuatro versiones fijadas son compatibles con Python 3.10 (Flask 3.0.3 requiere
  Python ≥3.8; pymongo 4.8.0 requiere ≥3.7; python-dotenv 1.0.1 requiere ≥3.8; pytest
  8.3.2 requiere ≥3.8).
- No se encontraron dependencias innecesarias ni paquetes sin usar.

**No se modificó `requirements.txt`** ni se ejecutó `pip install` durante esta fase.

### 3. Auditoría de reproducibilidad (estática, sin ejecutar nada)

| Aspecto revisado | Resultado |
|---|---|
| Rutas relativas | No se encontraron rutas absolutas en ningún archivo `.py` (verificado con búsqueda de patrones tipo `C:\` o `X:\`). `tests/test_api.py` y `tests/test_errores_mongo.py` resuelven la raíz del proyecto de forma dinámica con `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`, por lo que funcionan sin importar en qué carpeta se clone el proyecto. |
| Variables de entorno | `MONGO_URI` y `MONGO_DB_NAME` tienen valores por defecto sensatos en `database.py` y se pueden sobreescribir con `.env`; `.env.example` existe y no contiene credenciales reales. |
| Configuración de MongoDB | Local, sin autenticación, puerto por defecto `27017`; coherente en todos los archivos (`database.py`, `init_db.py`, `verify_db.py`, `tests/`). |
| Comandos de inicialización | `python init_db.py` coincide con el comportamiento real del script (idempotente, no borra datos). |
| Comandos para iniciar Flask | `python API.py` coincide con el bloque `if __name__ == "__main__": app.run(debug=True)` de `API.py`. |
| Ejecución de pruebas | `python -m pytest` es coherente con la estructura de `tests/` (sin `conftest.py` ni configuración especial de pytest que pudiera romperse en otro equipo). |
| Archivos ignorados por Git | `.gitignore` ya excluye `.venv/`, `__pycache__/`, `.env`, `.pytest_cache/`, `*.zip` y archivos temporales de SO/editor; coincide con la lista de "qué no incluir en el ZIP". |
| Dependencias de archivos locales | No se detectaron referencias a archivos fuera del proyecto (por ejemplo, ninguna ruta a `C:\Users\...` dentro del código fuente). |

**Conclusión: no se encontraron problemas de reproducibilidad.** El proyecto debería
funcionar igual en cualquier equipo con Python 3.10+ y MongoDB local, siguiendo los pasos
de la sección "Instalación" del README actualizado.

### 4. Verificación de nomenclatura y preparación de entrega

Se revisó la nomenclatura pedida por el profesor (`Apellido_Nombre_EA2.zip`) contra los
datos disponibles del repositorio (usuario de GitHub `LauGarciaAgudelo`). Se propuso el
nombre `GarciaAgudelo_Laura_EA2.zip`, dejando explícito en el README que es una inferencia
a partir del nombre de usuario (no una confirmación formal) y pidiendo que se verifique el
nombre y apellido(s) exactos antes de usarlo.

Se preparó (en el README, sección "Preparación de entrega") la lista completa de archivos
a incluir y a excluir del ZIP. **No se generó ningún archivo ZIP en esta fase.**

### 5. Estado de las evidencias pendientes

No se tocó la carpeta `evidencias/` en ningún momento de esta fase (ni para leer su
contenido detalladamente, ni para modificarlo). Se sabe, por el contexto de la actividad,
que la estudiante está completando las capturas de pantalla manualmente en paralelo a
esta fase, siguiendo `evidencias/GUIA_CAPTURAS.md`. El estado exacto (qué capturas ya
existen) no se registra aquí para no quedar desactualizado ni interferir con ese trabajo.

### 6. Checklist de cierre de la Fase 6

- [x] `README.md` completo: descripción, tecnologías, arquitectura, estructura,
  requisitos previos, instalación en 7 pasos, uso detallado de los 7 endpoints,
  validaciones, manejo de errores (7 códigos), pruebas (pytest + Postman + Newman) y
  preparación de entrega.
- [x] `requirements.txt` revisado: coherente con los imports del proyecto, versiones
  compatibles con Python 3.10, sin dependencias innecesarias. No se modificó (no había
  ningún problema que corregir).
- [x] Configuración documentada (variables de entorno, `.env.example`, MongoDB local).
- [x] Los 7 endpoints están correctamente explicados (objetivo, método, URL, cuerpo,
  respuesta, código HTTP).
- [x] Validaciones y errores documentados (incluye los 7 códigos de error).
- [x] La colección Postman está referenciada (README y `evidencias/GUIA_CAPTURAS.md`).
- [x] Lista de archivos de entrega preparada (incluir / excluir), ZIP **no generado**.
- [x] No se interfirió con las pruebas manuales de Postman (no se ejecutó la API, Newman,
  pytest, ni se escribió en MongoDB ni en `evidencias/` durante esta fase).
- [x] `BITACORA.md` actualizado con esta sección.

**Pendientes para la Fase 7 (o para el cierre de la actividad):** completar las capturas
de pantalla reales en `evidencias/`, confirmar el nombre exacto del archivo ZIP, y generar
el ZIP de entrega (con autorización explícita, todavía no otorgada).


# EA2 — API de sensores industriales

## Descripción

Este proyecto corresponde a la actividad **Bases de datos NoSQL y operaciones CRUD** de la asignatura Tecnologías Web. Se desarrolló una API con Python y Flask para registrar, consultar, actualizar y eliminar información de sensores industriales almacenada en MongoDB local.

Cada sensor tiene cuatro campos: `tipo`, `valor`, `ubicacion` y `fecha`. Los tipos permitidos y sus rangos son:

| Tipo | Valor permitido |
|---|---|
| Temperatura (`temperatura`) | -10 a 100 °C |
| Presión (`presion`) | 0 a 500 kPa |
| Vibración (`vibracion`) | 0 a 5 mm/s |

## Herramientas utilizadas

- **Python 3.10 y Flask:** desarrollo de la API.
- **MongoDB local:** almacenamiento de los sensores.
- **PyMongo:** conexión entre Python y MongoDB.
- **Postman:** pruebas de las solicitudes HTTP.
- **MongoDB Compass:** consulta visual de los datos.
- **pytest:** pruebas automatizadas.

## Instalación y ejecución

Se necesita tener instalado Python y MongoDB Community Server. Los siguientes comandos se ejecutan desde PowerShell, dentro de la carpeta del proyecto.

**1. Crear el entorno virtual:**

```powershell
python -m venv .venv
```

**2. Instalar las dependencias:**

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**3. Crear el archivo de configuración:**

```powershell
Copy-Item .env.example .env
```

La configuración predeterminada utiliza MongoDB local en `mongodb://localhost:27017/`.

**4. Verificar que MongoDB esté funcionando:**

```powershell
.venv\Scripts\python.exe database.py
```

**5. Crear la base de datos y la colección:**

```powershell
.venv\Scripts\python.exe init_db.py
```

Este paso prepara la base de datos `monitoreo_industrial` y la colección `sensores`, sin borrar datos existentes.

**6. Iniciar la API:**

```powershell
.venv\Scripts\python.exe API.py
```

La API queda disponible en `http://127.0.0.1:5000` mientras el servidor esté en ejecución.

## Operaciones de la API

| Método | Dirección | Función |
|---|---|---|
| POST | `/sensores/` | Crear un sensor |
| GET | `/sensores/` | Consultar todos los sensores |
| GET | `/sensores/?tipo=temperatura` | Consultar sensores por tipo |
| PUT | `/sensores/<tipo>` | Actualizar un sensor según su tipo |
| DELETE | `/sensores/<tipo>` | Eliminar un sensor según su tipo |
| PUT | `/sensores/id/<sensor_id>` | Actualizar un sensor por su identificador |
| DELETE | `/sensores/id/<sensor_id>` | Eliminar un sensor por su identificador |

Para **crear** un sensor, se envía una solicitud `POST` a `http://127.0.0.1:5000/sensores/` con el encabezado `Content-Type: application/json` y el siguiente cuerpo:

```json
{
  "tipo": "temperatura",
  "valor": 25.5,
  "ubicacion": "Planta A",
  "fecha": "2026-11-13T10:30:00Z"
}
```

Si los datos son correctos, la API devuelve el sensor creado, incluyendo el identificador `_id`, con código **201**.

Para **consultar**, se utiliza `GET /sensores/`. También se puede agregar `?tipo=temperatura` para filtrar los resultados. Las consultas correctas devuelven código **200**.

Para **actualizar**, se utiliza `PUT /sensores/temperatura`, enviando únicamente los campos que se desean cambiar. Por ejemplo:

```json
{
  "valor": 40
}
```

Para **eliminar**, se utiliza `DELETE /sensores/presion`. Las operaciones correctas de actualización y eliminación devuelven código **200**.

Cuando existen varios sensores del mismo tipo, es necesario utilizar las rutas por identificador (`/sensores/id/<sensor_id>`) para elegir el registro exacto.

## Validaciones y manejo de errores

La API comprueba que:

- El tipo sea `temperatura`, `presion` o `vibracion`.
- El valor sea numérico y esté dentro del rango correspondiente.
- La ubicación sea un texto que no esté vacío.
- La fecha tenga un formato válido, por ejemplo `2026-11-13T10:30:00Z`.
- Al crear un sensor se incluyan los cuatro campos obligatorios.
- Al actualizar un sensor no se cambien su tipo ni su identificador.

Si una solicitud presenta un problema, la API devuelve un mensaje de error en formato JSON:

| Código | Significado |
|---|---|
| 400 | Datos incorrectos o incompletos |
| 404 | Sensor no encontrado |
| 405 | Método HTTP no permitido |
| 409 | Hay varios sensores del mismo tipo y se requiere identificarlos |
| 415 | La solicitud no se envió como JSON |
| 500 | Error interno del servidor |
| 503 | No se puede establecer conexión con MongoDB |

Se realizaron pruebas en Postman a través de la colección creada, las capturas de pantalla de las operaciones y validaciones están en la carpeta `evidencias/`. También se incluyen evidencias de los datos almacenados en MongoDB Compass.

## Archivos principales

| Archivo o carpeta | Contenido |
|---|---|
| `API.py` | Rutas y operaciones de la API |
| `database.py` | Conexión con MongoDB |
| `validaciones.py` | Comprobación de los datos de los sensores |
| `errores.py` | Manejo de errores |
| `init_db.py` | Preparación de la base de datos |
| `requirements.txt` | Dependencias necesarias |
| `.env.example` | Ejemplo de configuración local |
| `postman/` | Colección de solicitudes para las pruebas |
| `evidencias/` | Capturas de las pruebas realizadas |

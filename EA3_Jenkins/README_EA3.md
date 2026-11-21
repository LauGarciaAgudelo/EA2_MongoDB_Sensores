# EA3 – Automatización de pruebas y despliegue con Jenkins

## Descripción

En esta actividad se utiliza Jenkins para automatizar las pruebas y el despliegue de la API REST desarrollada en la actividad EA2, encargada de gestionar registros de sensores mediante Flask y MongoDB.

El proceso permite obtener el código desde GitHub, preparar el entorno de Python, instalar las dependencias y ejecutar las pruebas. También incluye una opción para desplegar la aplicación localmente y verificar su funcionamiento.

## Herramientas utilizadas

- **Jenkins:** automatización del proceso.
- **Git y GitHub:** almacenamiento y descarga del código.
- **Python 3.12 y Flask:** desarrollo de la API.
- **MongoDB:** almacenamiento de los datos.
- **Pytest:** ejecución de pruebas.
- **Waitress:** ejecución de la API durante el despliegue.
- **PowerShell:** ejecución de los scripts de apoyo.

## Configuración del entorno

Para ejecutar el proyecto se utiliza la siguiente configuración:

| Elemento | Configuración |
|---|---|
| Repositorio | `LauGarciaAgudelo/EA2_MongoDB_Sensores` |
| Rama | `main` |
| Job de Jenkins | `EA3-CD-Sensores-Flask` |
| Agente | `ea3-deploy-limited` |
| Jenkins | `http://localhost:8080` |
| MongoDB | `localhost:27017` |
| API | `http://127.0.0.1:5000` |

El despliegue se realiza únicamente en el equipo local. No requiere crear nuevos usuarios ni instalar servicios adicionales de Windows.

## Configuración del agente de Jenkins

Para ejecutar el Pipeline se configuró un agente local conectado al servidor de Jenkins.

1. Crear una carpeta `JenkinsEA3\agent` dentro del perfil de Windows.
2. Ingresar a **Manage Jenkins → Nodes → New Node**.
3. Crear un agente permanente con el nombre `ea3-deploy-limited`.
4. Asignar un ejecutor y utilizar la misma etiqueta `ea3-deploy-limited`.
5. Configurar como directorio de trabajo la ruta completa de la carpeta creada.
6. Seleccionar la conexión del agente con el controlador y habilitar WebSocket.
7. En las propiedades del nodo, agregar la variable `PYTHON312` con la ruta de Python 3.12.
8. Descargar `agent.jar` desde Jenkins y ejecutar el comando de conexión proporcionado en la página del agente.

Una vez conectado, el agente debe aparecer con estado **Online**.

La consola utilizada para iniciar el agente debe permanecer abierta durante las ejecuciones. El comando de conexión contiene un secreto que no debe publicarse ni incluirse en las evidencias.

## Etapas del Pipeline

El archivo `Jenkinsfile` define las siguientes etapas:

1. **Descarga del código:** obtiene la versión del proyecto desde GitHub.
2. **Verificación de Python:** comprueba que Python 3.12 esté disponible.
3. **Preparación del entorno:** crea un entorno virtual para ejecutar el proyecto.
4. **Instalación de dependencias:** instala las librerías definidas en `requirements.txt`.
5. **Ejecución de pruebas:** utiliza Pytest para comprobar el funcionamiento de la aplicación.
6. **Preparación del despliegue:** organiza los archivos necesarios para ejecutar la API.
7. **Despliegue y verificación:** cuando está habilitado, inicia la API y comprueba que responda correctamente.

Si alguna etapa de validación o pruebas falla, el Pipeline se detiene y no continúa con el despliegue.

## Creación del Job en Jenkins

1. Ingresar a Jenkins y seleccionar **New Item**.
2. Escribir el nombre `EA3-CD-Sensores-Flask`.
3. Seleccionar el tipo **Pipeline**.
4. En la configuración del Pipeline, elegir **Pipeline script from SCM**.
5. Seleccionar **Git** e ingresar el repositorio:

   `https://github.com/LauGarciaAgudelo/EA2_MongoDB_Sensores.git`

6. Configurar la rama `*/main`.
7. En **Script Path**, escribir `Jenkinsfile`.
8. Guardar la configuración.

Para la primera ejecución, el parámetro `DEPLOY_API` debe permanecer en `false`. De esta manera se comprueba primero que el código se descarga correctamente y que las pruebas se ejecutan sin errores.

## Despliegue local

Para realizar el despliegue se utiliza un script de PowerShell que administra la ejecución de la API con Waitress.

Desde una segunda consola PowerShell, ubicada en la carpeta del proyecto, ejecutar:

```powershell
.\EA3_Jenkins\Local-Api-Supervisor.ps1
```

Después, ejecutar nuevamente el Job con `DEPLOY_API=true`.

Si el proceso finaliza correctamente, la API debe quedar disponible en:

`http://127.0.0.1:5000/sensores/`

Para comprobar su funcionamiento se puede ejecutar:

```powershell
Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:5000/sensores/"
```

La respuesta esperada es **HTTP 200**, que indica que la API está disponible.

El supervisor debe permanecer activo durante la demostración. Como se trata de un despliegue local para la práctica, la aplicación no está configurada para iniciarse automáticamente al reiniciar Windows.

## Archivos principales

| Archivo | Descripción |
|---|---|
| `Jenkinsfile` | Define las etapas del Pipeline. |
| `requirements.txt` | Contiene las dependencias de Python. |
| `EA3_Jenkins/Prepare-Release.ps1` | Prepara los archivos para el despliegue. |
| `EA3_Jenkins/Promote-Release.ps1` | Solicita la actualización de la aplicación. |
| `EA3_Jenkins/Local-Api-Supervisor.ps1` | Administra la ejecución local de la API. |

## Resultado esperado

Al finalizar la práctica se espera contar con un Job de Jenkins capaz de obtener el proyecto desde GitHub, instalar sus dependencias, ejecutar las pruebas automatizadas y desplegar la API localmente cuando se habilite esta opción.

Esto permite reducir las tareas manuales y comprobar el funcionamiento de la aplicación antes de realizar su despliegue.
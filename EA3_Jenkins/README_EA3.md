# EA3 — Pipeline local de Jenkins para sensores

## Objetivo y alcance

El pipeline obtiene el proyecto desde GitHub, instala dependencias dentro de entornos virtuales y ejecuta las pruebas existentes. Con `DEPLOY_API=true`, prepara una release independiente y solicita al supervisor local que publique la API Flask con Waitress.

Esta estrategia no crea usuarios de Windows, servicios, tareas programadas ni permisos del sistema. El agente inbound y el supervisor se ejecutan como procesos de la sesión normal del usuario. No se modifican los endpoints ni las pruebas de EA2.

## Herramientas, Job y puertos

- Job previsto: `EA3-CD-Sensores-Flask`, tipo Pipeline from SCM.
- Repositorio: `https://github.com/LauGarciaAgudelo/EA2_MongoDB_Sensores.git`, rama `*/main`, script `Jenkinsfile`.
- Jenkins: `http://localhost:8080`.
- Agente: nodo `ea3-deploy-limited`, conectado mediante WebSocket.
- Python: 3.12, obtenido desde `PYTHON312` configurado en el nodo.
- Git: instalación existente en el equipo, visible desde la sesión que ejecuta el agente.
- MongoDB: `localhost:27017`.
- API: `127.0.0.1:5000`; no se abre el puerto a la red.
- Waitress: `3.0.2`, dependencia fijada en `requirements.txt`.

Waitress carga `API:app` desde cada directorio de release. No se usa `debug=True` ni se inicia Flask con el servidor de desarrollo.

## Agente inbound local

1. En una consola PowerShell normal, crea el directorio dentro del perfil:

   ```powershell
   $agentRoot = Join-Path $env:USERPROFILE 'JenkinsEA3\agent'
   New-Item -ItemType Directory -Path $agentRoot -Force
   ```

2. En **Manage Jenkins → Nodes → New Node**, crea un nodo:
   - Nombre: `ea3-deploy-limited`.
   - Tipo: Permanent Agent.
   - Ejecutores: `1`.
   - Remote root directory: la ruta absoluta expandida del directorio anterior.
   - Labels: `ea3-deploy-limited`.
   - Usage: solo jobs que coincidan con esta etiqueta.
   - Launch method: Launch agent by connecting it to the controller.
   - Habilita WebSocket.
   - En Node Properties → Environment variables, define `PYTHON312` con la ruta del `python.exe` 3.12 existente en este equipo, sin comillas.

3. Descarga el cliente desde la instancia local de Jenkins:

   ```powershell
   Invoke-WebRequest -Uri 'http://localhost:8080/jnlpJars/agent.jar' `
       -OutFile (Join-Path $agentRoot 'agent.jar')
   ```

4. Antes de pegar el comando generado, desactiva el historial persistente de PSReadLine para esa consola, si está disponible:

   ```powershell
   if (Get-Command Set-PSReadLineOption -ErrorAction SilentlyContinue) {
       Set-PSReadLineOption -HistorySaveStyle SaveNothing
   }
   ```

   Luego copia el comando de conexión que muestra la página del nodo y ejecútalo en esa consola. Debe usar `java -jar`, `http://localhost:8080/`, el nombre `ea3-deploy-limited`, `-webSocket` y `-workDir $agentRoot`. No compartas ni guardes el secreto del nodo en archivos, historial o repositorio. El secreto permanece temporalmente en los argumentos del proceso del agente, por lo que herramientas de inspección/seguridad del equipo podrían verlo. Mantén abierta la consola para que el agente permanezca online.

El pipeline siempre solicita la etiqueta dedicada, por lo que no debe ejecutarse en el nodo integrado/controlador que funciona como `LocalSystem`. El agente conectado desde la sesión del usuario ejecuta los pasos con el token normal de esa sesión.

Esta modalidad no aísla el pipeline de tus archivos personales: los comandos descargados desde SCM se ejecutan como tu usuario y pueden acceder a los archivos y recursos que ese usuario tenga disponibles. Revisa el repositorio y limita quién puede configurar o ejecutar el Job antes de habilitar el despliegue.

## Etapas del Jenkinsfile

1. **Checkout:** limpia solo el workspace del agente y obtiene el código SCM.
2. **Verificar Python 3.12:** comprueba que `PYTHON312` existe y apunta a Python 3.12.
3. **Preparar entorno de pruebas:** crea `.venv` dentro del workspace.
4. **Instalar dependencias:** instala `requirements.txt` y ejecuta `pip check`.
5. **Pruebas:** ejecuta `pytest -q`. Un error detiene el pipeline y no permite las etapas posteriores.
6. **Preparar archivos de despliegue:** copia solo `API.py`, `database.py`, `validaciones.py`, `errores.py` y `requirements.txt` a un paquete temporal del workspace. No copia `.env`, entornos virtuales antiguos, pruebas, evidencias ni el workspace completo.
7. **Desplegar y verificar API local:** solo se ejecuta con `DEPLOY_API=true`. Prepara una release y su propio `.venv` bajo `%USERPROFILE%\JenkinsEA3\deploy\releases`, entrega una solicitud al supervisor y comprueba `GET http://127.0.0.1:5000/sensores/` con HTTP 200.

`DEPLOY_API` es `false` por defecto. El primer build de validación no necesita el supervisor, WinSW, el servicio de API ni acceso para reiniciar servicios. `disableConcurrentBuilds()` evita builds simultáneos de este Job.

## Supervisor local y ciclo de despliegue

Inicia el supervisor desde una **segunda consola PowerShell**, abierta por el usuario y fuera del agente y de cualquier build:

```powershell
Set-Location '<ruta-del-clon-local-del-repositorio>'
.\EA3_Jenkins\Local-Api-Supervisor.ps1
```

La raíz por defecto será `%USERPROFILE%\JenkinsEA3\deploy`. El supervisor crea allí releases, estado de control y logs; no escribe dentro del checkout. Mantén la consola abierta mientras la API deba estar disponible. El supervisor es la única instancia permitida y procesa una solicitud de despliegue cada vez.

Para una release, el supervisor:

- Verifica que el PID activo corresponde al `python.exe` de la release administrada y a Waitress en `127.0.0.1:5000`; no termina un proceso desconocido que use el puerto.
- Detiene la instancia anterior de forma controlada, inicia la nueva mediante `python.exe -m waitress --listen=127.0.0.1:5000 API:app` y comprueba HTTP 200.
- Si la candidata falla, intenta recuperar la release previa. No elimina releases ni logs automáticamente.
- Escribe solicitudes y estado bajo `control`, y logs bajo `logs`, siempre fuera del repositorio.

La verificación del pipeline sucede antes de que el build termine. Para comprobar persistencia después del build, espera a que Jenkins muestre el resultado final y, desde otra consola, ejecuta:

```powershell
Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5000/sensores/' -TimeoutSec 10
Get-NetTCPConnection -State Listen -LocalPort 5000
```

Waitress no es hijo del proceso del build: lo inicia el supervisor independiente, cuyo entorno no contiene `JENKINS_NODE_COOKIE`. Esta separación evita depender de que Jenkins preserve un proceso hijo del build. La API permanece mientras la sesión de Windows y el supervisor continúen activos. No se garantiza persistencia al cerrar sesión, cerrar abruptamente el supervisor o reiniciar el equipo; no se instala un servicio para lograrlo.

Si el supervisor se cierra con `Ctrl+C`, intenta detener de forma controlada el Waitress que administra. Para otro despliegue, vuelve a iniciarlo en la consola separada. Si el puerto 5000 ya está ocupado por un proceso que el supervisor no reconoce, el despliegue falla de forma cerrada y no termina ese proceso.

## Crear manualmente el Job

Después de publicar y revisar el Jenkinsfile en GitHub:

1. En Jenkins selecciona **New Item**, nombre `EA3-CD-Sensores-Flask`, tipo **Pipeline**.
2. En **Pipeline**, selecciona **Pipeline script from SCM**.
3. SCM: **Git**.
4. Repository URL: `https://github.com/LauGarciaAgudelo/EA2_MongoDB_Sensores.git`.
5. Branch specifier: `*/main`.
6. Script Path: `Jenkinsfile`.
7. Guarda. El primer build debe conservar `DEPLOY_API=false`; así ejecuta checkout, Python, dependencias, pruebas y preparación temporal, sin iniciar despliegue.

Antes de una ejecución con `DEPLOY_API=true`, confirma que el nodo está online, Python y Git funcionan bajo la sesión del agente, MongoDB responde localmente, el supervisor está activo y el puerto 5000 está disponible o pertenece a la versión que administra el supervisor. Habilitar el despliegue implica una interrupción breve al reiniciar Waitress.

## Archivos de esta propuesta

- `Jenkinsfile`: pipeline de pruebas y despliegue local opcional.
- `EA3_Jenkins/Prepare-Release.ps1`: copia los archivos permitidos y prepara un entorno propio cuando se solicita.
- `EA3_Jenkins/Promote-Release.ps1`: entrega la solicitud local y espera el resultado del supervisor.
- `EA3_Jenkins/Local-Api-Supervisor.ps1`: administra Waitress y la recuperación local.
- `EA3_Jenkins/EA3SensoresAPI.xml`: configuración WinSW anterior, conservada pero no utilizada por esta arquitectura.
- `requirements.txt`: incluye `waitress==3.0.2`.

No se deben guardar secretos de Jenkins, archivos `.env`, credenciales ni datos de conexión privados en el repositorio. La configuración de MongoDB local usa `mongodb://localhost:27017/` y la base por defecto de la aplicación.

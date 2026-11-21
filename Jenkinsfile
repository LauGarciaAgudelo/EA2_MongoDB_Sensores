pipeline {
    agent {
        label 'ea3-deploy-limited'
    }

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timestamps()
    }

    parameters {
        booleanParam(
            name: 'DEPLOY_API',
            defaultValue: false,
            description: 'Habilitar solo cuando el agente y el supervisor local estén preparados.'
        )
    }

    environment {
        MONGO_URI = 'mongodb://localhost:27017/'
    }

    stages {
        stage('Checkout') {
            steps {
                deleteDir()
                checkout scm
                script {
                    def commit = bat(
                        returnStdout: true,
                        script: '@git rev-parse --short=8 HEAD'
                    ).trim()
                    env.RELEASE_ID = "${env.BUILD_NUMBER}-${commit}"
                }
            }
        }

        stage('Verificar Python 3.12') {
            steps {
                bat '''
                    @echo off
                    if not defined PYTHON312 (
                        echo ERROR: Configure PYTHON312 en el agente Jenkins dedicado.
                        exit /b 2
                    )
                    if not exist "%PYTHON312%" (
                        echo ERROR: No existe el ejecutable configurado en PYTHON312.
                        exit /b 2
                    )
                    "%PYTHON312%" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)"
                    if errorlevel 1 (
                        echo ERROR: PYTHON312 no apunta a Python 3.12.
                        exit /b 3
                    )
                    "%PYTHON312%" --version
                '''
            }
        }

        stage('Preparar entorno de pruebas') {
            steps {
                bat '''
                    @echo off
                    "%PYTHON312%" -m venv .venv
                    if errorlevel 1 exit /b 1
                    call ".venv\\Scripts\\python.exe" -m pip --version
                    if errorlevel 1 exit /b 1
                '''
            }
        }

        stage('Instalar dependencias') {
            steps {
                bat '''
                    @echo off
                    call ".venv\\Scripts\\python.exe" -m pip install -r requirements.txt
                    if errorlevel 1 exit /b 1
                    call ".venv\\Scripts\\python.exe" -m pip check
                    if errorlevel 1 exit /b 1
                '''
            }
        }

        stage('Pruebas') {
            steps {
                bat '''
                    @echo off
                    call ".venv\\Scripts\\python.exe" -m pytest -q
                    if errorlevel 1 exit /b 1
                '''
            }
        }

        stage('Preparar archivos de despliegue') {
            steps {
                bat '''
                    @echo off
                    powershell.exe -NoProfile -NonInteractive -File "EA3_Jenkins\\Prepare-Release.ps1" -SourceRoot "%WORKSPACE%" -DestinationRoot "%WORKSPACE%\\.ea3-package" -ReleaseId "%RELEASE_ID%" -PythonExecutable "%PYTHON312%"
                    if errorlevel 1 exit /b 1
                '''
            }
        }

        stage('Desplegar y verificar API local') {
            when {
                expression {
                    return params.DEPLOY_API
                }
            }
            steps {
                bat '''
                    @echo off
                    if not defined USERPROFILE (
                        echo ERROR: El agente no expone USERPROFILE.
                        exit /b 2
                    )
                    set "EA3_DEPLOY_ROOT=%USERPROFILE%\\JenkinsEA3\\deploy"
                    powershell.exe -NoProfile -NonInteractive -File "EA3_Jenkins\\Prepare-Release.ps1" -SourceRoot "%WORKSPACE%" -DestinationRoot "%EA3_DEPLOY_ROOT%\\releases" -ReleaseId "%RELEASE_ID%" -PythonExecutable "%PYTHON312%" -InstallDependencies
                    if errorlevel 1 exit /b 1
                    powershell.exe -NoProfile -NonInteractive -File "EA3_Jenkins\\Promote-Release.ps1" -DeployRoot "%EA3_DEPLOY_ROOT%" -ReleaseId "%RELEASE_ID%"
                    if errorlevel 1 exit /b 1
                    powershell.exe -NoProfile -NonInteractive -Command "$ErrorActionPreference = 'Stop'; $response = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5000/sensores/' -TimeoutSec 10; if ($response.StatusCode -ne 200) { throw 'GET /sensores/ no devolvió HTTP 200.' }"
                    if errorlevel 1 exit /b 1
                '''
            }
        }
    }

    post {
        success {
            echo 'Pipeline terminado correctamente.'
        }
        failure {
            echo 'Pipeline fallido; revisar la etapa que reportó el error.'
        }
    }
}

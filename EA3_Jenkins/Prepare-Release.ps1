param(
    [Parameter(Mandatory = $true)]
    [string] $SourceRoot,

    [Parameter(Mandatory = $true)]
    [string] $DestinationRoot,

    [Parameter(Mandatory = $true)]
    [string] $ReleaseId,

    [Parameter(Mandatory = $true)]
    [string] $PythonExecutable,

    [switch] $InstallDependencies
)

$ErrorActionPreference = 'Stop'

if ($ReleaseId -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$') {
    throw 'ReleaseId solo puede contener letras, números, punto, guion y guion bajo.'
}

$sourcePath = (Resolve-Path -LiteralPath $SourceRoot).Path
$destinationBase = [System.IO.Path]::GetFullPath($DestinationRoot)
$releasePath = Join-Path $destinationBase $ReleaseId

New-Item -ItemType Directory -Path $destinationBase -Force | Out-Null

if (Test-Path -LiteralPath $releasePath) {
    throw "La versión destino ya existe; no se sobrescribirá: $releasePath"
}

$requiredFiles = @(
    'API.py',
    'database.py',
    'validaciones.py',
    'errores.py',
    'requirements.txt'
)

foreach ($file in $requiredFiles) {
    $sourceFile = Join-Path $sourcePath $file
    if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) {
        throw "Falta el archivo requerido para el despliegue: $file"
    }
}

if ($InstallDependencies) {
    if (-not (Test-Path -LiteralPath $PythonExecutable -PathType Leaf)) {
        throw 'No se encontró el ejecutable de Python configurado.'
    }

    $pythonVersion = & $PythonExecutable -c 'import sys; print(sys.version_info.major, sys.version_info.minor, sep=chr(46))'
    if ($LASTEXITCODE -ne 0 -or $pythonVersion.Trim() -ne '3.12') {
        throw 'El ejecutable configurado debe ser Python 3.12.'
    }
}

New-Item -ItemType Directory -Path $releasePath | Out-Null

foreach ($file in $requiredFiles) {
    Copy-Item -LiteralPath (Join-Path $sourcePath $file) -Destination $releasePath
}

if ($InstallDependencies) {
    $venvPython = Join-Path $releasePath '.venv\Scripts\python.exe'
    & $PythonExecutable -m venv (Join-Path $releasePath '.venv')
    if ($LASTEXITCODE -ne 0) {
        throw 'No se pudo crear el entorno virtual de la versión candidata.'
    }

    & $venvPython -m pip install --disable-pip-version-check -r (Join-Path $releasePath 'requirements.txt')
    if ($LASTEXITCODE -ne 0) {
        throw 'No se pudieron instalar las dependencias de la versión candidata.'
    }

    & $venvPython -m pip check
    if ($LASTEXITCODE -ne 0) {
        throw 'La verificación de dependencias de la versión candidata falló.'
    }
}

Write-Output "Archivos permitidos preparados en: $releasePath"

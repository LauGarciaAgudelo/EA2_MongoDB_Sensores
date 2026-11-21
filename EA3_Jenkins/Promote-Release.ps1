param(
    [Parameter(Mandatory = $true)]
    [string] $DeployRoot,

    [Parameter(Mandatory = $true)]
    [string] $ReleaseId,

    [ValidateRange(15, 600)]
    [int] $RequestTimeoutSeconds = 180
)

$ErrorActionPreference = 'Stop'

if ($ReleaseId -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$') {
    throw 'ReleaseId solo puede contener letras, números, punto, guion y guion bajo.'
}

$root = [System.IO.Path]::GetFullPath($DeployRoot).TrimEnd('\')
$releasePath = Join-Path $root "releases\$ReleaseId"
$controlPath = Join-Path $root 'control'
$requestsPath = Join-Path $controlPath 'requests'
$statusPath = Join-Path $controlPath 'status'
$heartbeatPath = Join-Path $controlPath 'supervisor.json'
$requestPath = Join-Path $requestsPath "$ReleaseId.json"
$requestTempPath = "$requestPath.$([Guid]::NewGuid().ToString('N')).tmp"
$statusFile = Join-Path $statusPath "$ReleaseId.json"

if (-not (Test-Path -LiteralPath (Join-Path $releasePath 'API.py') -PathType Leaf) -or
    -not (Test-Path -LiteralPath (Join-Path $releasePath '.venv\Scripts\python.exe') -PathType Leaf)) {
    throw "No existe una release preparada con entorno propio: $releasePath"
}

if (Test-Path -LiteralPath $requestPath) {
    throw "Ya existe una solicitud para esta release: $requestPath"
}
if (Test-Path -LiteralPath $statusFile) {
    throw "Ya existe un estado para esta release; no se sobrescribirá: $statusFile"
}

if (-not (Test-Path -LiteralPath $heartbeatPath -PathType Leaf)) {
    throw 'No está activo Local-Api-Supervisor.ps1. Inícialo desde una consola separada del agente.'
}

$heartbeat = Get-Content -LiteralPath $heartbeatPath -Raw | ConvertFrom-Json
$lastHeartbeat = [DateTimeOffset]::Parse([string]$heartbeat.updatedAtUtc).UtcDateTime
if (((Get-Date).ToUniversalTime() - $lastHeartbeat).TotalSeconds -gt 15) {
    throw 'El supervisor no ha actualizado su estado recientemente; no se enviará el despliegue.'
}

New-Item -ItemType Directory -Path $requestsPath -Force | Out-Null
New-Item -ItemType Directory -Path $statusPath -Force | Out-Null

$request = [ordered]@{
    releaseId = $ReleaseId
    requestedAtUtc = [DateTime]::UtcNow.ToString('o')
}
$encoding = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText(
    $requestTempPath,
    (ConvertTo-Json -InputObject $request -Depth 4),
    $encoding
)
Move-Item -LiteralPath $requestTempPath -Destination $requestPath

$deadline = (Get-Date).AddSeconds($RequestTimeoutSeconds)
do {
    if (Test-Path -LiteralPath $statusFile -PathType Leaf) {
        $status = Get-Content -LiteralPath $statusFile -Raw | ConvertFrom-Json
        if ($status.status -eq 'succeeded') {
            Write-Output $status.message
            return
        }
        if ($status.status -eq 'failed') {
            throw "El supervisor rechazó el despliegue: $($status.message)"
        }
    }

    if (Test-Path -LiteralPath $heartbeatPath -PathType Leaf) {
        $heartbeat = Get-Content -LiteralPath $heartbeatPath -Raw | ConvertFrom-Json
        $lastHeartbeat = [DateTimeOffset]::Parse([string]$heartbeat.updatedAtUtc).UtcDateTime
        if (((Get-Date).ToUniversalTime() - $lastHeartbeat).TotalSeconds -gt 15) {
            throw 'El supervisor dejó de responder mientras procesaba el despliegue.'
        }
    }
    Start-Sleep -Seconds 2
} while ((Get-Date) -lt $deadline)

throw "El supervisor no confirmó la release $ReleaseId dentro de $RequestTimeoutSeconds segundos. Revisa su consola y los archivos de estado."

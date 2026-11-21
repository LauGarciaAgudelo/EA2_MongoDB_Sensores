param(
    [string] $DeployRoot = "$env:USERPROFILE\JenkinsEA3\deploy",

    [ValidateRange(1, 60)]
    [int] $PollIntervalSeconds = 2,

    [ValidateRange(10, 300)]
    [int] $StartupTimeoutSeconds = 60
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
    throw 'No está definida la variable USERPROFILE para esta sesión.'
}

$root = [System.IO.Path]::GetFullPath($DeployRoot).TrimEnd('\')
$releasesPath = Join-Path $root 'releases'
$controlPath = Join-Path $root 'control'
$requestsPath = Join-Path $controlPath 'requests'
$processingPath = Join-Path $controlPath 'processing'
$processedPath = Join-Path $controlPath 'processed'
$statusPath = Join-Path $controlPath 'status'
$statePath = Join-Path $root 'state'
$logsPath = Join-Path $root 'logs'
$activeStateFile = Join-Path $statePath 'active.json'
$heartbeatFile = Join-Path $controlPath 'supervisor.json'
$lockFile = Join-Path $controlPath 'supervisor.lock'
$healthUrl = 'http://127.0.0.1:5000/sensores/'
$script:activeState = $null
$script:lockStream = $null
$script:lastHttpError = 'La API todavía no respondió HTTP 200.'

foreach ($directory in @(
    $releasesPath,
    $requestsPath,
    $processingPath,
    $processedPath,
    $statusPath,
    $statePath,
    $logsPath
)) {
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
}

function Write-AtomicJson {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path,

        [Parameter(Mandatory = $true)]
        [object] $Value
    )

    $tempPath = "$Path.$([Guid]::NewGuid().ToString('N')).tmp"
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText(
        $tempPath,
        (ConvertTo-Json -InputObject $Value -Depth 8),
        $encoding
    )
    Move-Item -LiteralPath $tempPath -Destination $Path -Force
}

function Read-JsonFile {
    param([Parameter(Mandatory = $true)][string] $Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $null
    }
    return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json)
}

function Write-DeploymentStatus {
    param(
        [string] $ReleaseId,
        [string] $Status,
        [string] $Message,
        [string] $Rollback = 'not-needed'
    )

    Write-AtomicJson -Path (Join-Path $statusPath "$ReleaseId.json") -Value ([ordered]@{
        releaseId = $ReleaseId
        status = $Status
        message = $Message
        rollback = $Rollback
        updatedAtUtc = [DateTime]::UtcNow.ToString('o')
    })
}

function Get-ManagedProcess {
    param([Parameter(Mandatory = $true)][object] $State)

    $processId = [int]$State.processId
    $process = Get-CimInstance -ClassName Win32_Process -Filter "ProcessId = $processId" -ErrorAction Stop
    if ($null -eq $process) {
        return $null
    }

    $expectedPython = [System.IO.Path]::GetFullPath([string]$State.pythonPath)
    $commandLine = [string]$process.CommandLine
    if ([string]::IsNullOrWhiteSpace([string]$process.ExecutablePath) -or
        -not [string]::Equals(
            [System.IO.Path]::GetFullPath([string]$process.ExecutablePath),
            $expectedPython,
            [System.StringComparison]::OrdinalIgnoreCase
        ) -or
        $commandLine -notmatch '(?i)(?:^|\s)-m\s+waitress(?:\s|$)' -or
        $commandLine -notmatch '--listen=127\.0\.0\.1:5000' -or
        $commandLine -notmatch 'API:app') {
        throw "El PID $processId no coincide con la identidad esperada de Waitress; no se modificará."
    }

    return $process
}

function Get-ListenerProcessIds {
    try {
        $connections = @(
            Get-NetTCPConnection -State Listen -LocalPort 5000 -ErrorAction Stop
        )
    }
    catch {
        if ($_.FullyQualifiedErrorId -eq 'CmdletizationQuery_NotFound,Get-NetTCPConnection') {
            return @()
        }
        throw
    }

    return @($connections | Select-Object -ExpandProperty OwningProcess -Unique)
}

function Wait-PortFree {
    param([int] $TimeoutSeconds = 20)

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        if (@(Get-ListenerProcessIds).Count -eq 0) {
            return
        }
        Start-Sleep -Milliseconds 250
    } while ((Get-Date) -lt $deadline)

    $pids = @(Get-ListenerProcessIds) -join ', '
    throw "El puerto 5000 sigue ocupado por PID(s) $pids; no se terminarán procesos ajenos."
}

function Test-ApiHttp200 {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 3 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            return $true
        }
        $script:lastHttpError = "HTTP $($response.StatusCode)"
        return $false
    }
    catch {
        $script:lastHttpError = $_.Exception.Message
        return $false
    }
}

function Wait-ForApi {
    param(
        [Parameter(Mandatory = $true)][object] $State,
        [int] $TimeoutSeconds = $StartupTimeoutSeconds
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $script:lastHttpError = 'La API todavía no respondió HTTP 200.'
    do {
        $process = Get-ManagedProcess -State $State
        if ($null -eq $process) {
            throw "Waitress terminó antes de responder. Revisa los logs de la release $($State.releaseId)."
        }
        if (Test-ApiHttp200) {
            return
        }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)

    throw "GET $healthUrl no devolvió HTTP 200. Último error: $script:lastHttpError"
}

function Stop-ManagedProcess {
    param([Parameter(Mandatory = $true)][object] $State)

    $process = Get-ManagedProcess -State $State
    if ($null -eq $process) {
        return
    }

    Stop-Process -Id ([int]$State.processId) -ErrorAction Stop
    $deadline = (Get-Date).AddSeconds(15)
    do {
        $process = Get-CimInstance -ClassName Win32_Process -Filter "ProcessId = $([int]$State.processId)" -ErrorAction Stop
        if ($null -eq $process) {
            return
        }
        $null = Get-ManagedProcess -State $State
        Start-Sleep -Milliseconds 250
    } while ((Get-Date) -lt $deadline)

    throw "Waitress PID $($State.processId) no terminó dentro del tiempo esperado."
}

function Start-Release {
    param([Parameter(Mandatory = $true)][string] $ReleaseId)

    $releasePath = Join-Path $releasesPath $ReleaseId
    $pythonPath = Join-Path $releasePath '.venv\Scripts\python.exe'
    foreach ($requiredPath in @(
        (Join-Path $releasePath 'API.py'),
        (Join-Path $releasePath 'database.py'),
        $pythonPath
    )) {
        if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
            throw "Falta un archivo de la release: $requiredPath"
        }
    }

    & $pythonPath -c 'import waitress'
    if ($LASTEXITCODE -ne 0) {
        throw "Waitress no está disponible en el entorno de la release $ReleaseId."
    }

    $stdoutPath = Join-Path $logsPath "waitress-$ReleaseId.stdout.log"
    $stderrPath = Join-Path $logsPath "waitress-$ReleaseId.stderr.log"
    if ((Test-Path -LiteralPath $stdoutPath) -or (Test-Path -LiteralPath $stderrPath)) {
        throw "Ya existen logs para la release $ReleaseId; no se sobrescribirán."
    }

    [Environment]::SetEnvironmentVariable('MONGO_URI', 'mongodb://localhost:27017/', 'Process')
    [Environment]::SetEnvironmentVariable('MONGO_DB_NAME', 'monitoreo_industrial', 'Process')
    [Environment]::SetEnvironmentVariable('JENKINS_NODE_COOKIE', $null, 'Process')

    $process = Start-Process `
        -FilePath $pythonPath `
        -ArgumentList '-m waitress --listen=127.0.0.1:5000 API:app' `
        -WorkingDirectory $releasePath `
        -RedirectStandardOutput $stdoutPath `
        -RedirectStandardError $stderrPath `
        -PassThru

    $state = [pscustomobject]@{
        releaseId = $ReleaseId
        processId = $process.Id
        pythonPath = $pythonPath
        stdoutPath = $stdoutPath
        stderrPath = $stderrPath
        startedAtUtc = [DateTime]::UtcNow.ToString('o')
    }

    try {
        Wait-ForApi -State $state
        return $state
    }
    catch {
        Stop-ManagedProcess -State $state
        throw
    }
}

function Restore-PreviousRelease {
    param([Parameter(Mandatory = $true)][object] $PreviousState)

    $process = Get-ManagedProcess -State $PreviousState
    if ($null -ne $process) {
        if (Test-ApiHttp200) {
            return $PreviousState
        }
        Stop-ManagedProcess -State $PreviousState
    }

    Wait-PortFree
    return (Start-Release -ReleaseId ([string]$PreviousState.releaseId))
}

function Process-DeploymentRequest {
    param([Parameter(Mandatory = $true)][System.IO.FileInfo] $RequestFile)

    $releaseId = [System.IO.Path]::GetFileNameWithoutExtension($RequestFile.Name)
    if ($releaseId -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$') {
        Write-Warning "Se ignora una solicitud con nombre de release inválido: $($RequestFile.Name)"
        return
    }

    $processingFile = Join-Path $processingPath "$releaseId.json"
    Move-Item -LiteralPath $RequestFile.FullName -Destination $processingFile
    $previousState = $script:activeState
    $candidateState = $null
    $rollbackResult = 'not-needed'

    try {
        $request = Read-JsonFile -Path $processingFile
        if ([string]$request.releaseId -ne $releaseId) {
            throw 'El ID de la solicitud no coincide con el nombre del archivo.'
        }

        Write-DeploymentStatus -ReleaseId $releaseId -Status 'deploying' -Message 'La release está en preparación para promoción.'

        if ($previousState) {
            Stop-ManagedProcess -State $previousState
        }
        Wait-PortFree

        $candidateState = Start-Release -ReleaseId $releaseId
        Write-AtomicJson -Path $activeStateFile -Value $candidateState
        $script:activeState = $candidateState
        Write-DeploymentStatus -ReleaseId $releaseId -Status 'succeeded' -Message "Release $releaseId activa y GET $healthUrl devolvió HTTP 200."
        Write-Host "Release activa: $releaseId (PID $($candidateState.processId))."
    }
    catch {
        $deploymentError = $_.Exception.Message
        $rollbackResult = 'no-previous-release'

        if ($candidateState) {
            try {
                Stop-ManagedProcess -State $candidateState
            }
            catch {
                $rollbackResult = "failed:could-not-stop-candidate:$($_.Exception.Message)"
                Write-Warning "No se pudo detener la release candidata: $($_.Exception.Message)"
            }
        }

        if ($previousState) {
            try {
                $restoredState = Restore-PreviousRelease -PreviousState $previousState
                Write-AtomicJson -Path $activeStateFile -Value $restoredState
                $script:activeState = $restoredState
                $rollbackResult = "restored:$($restoredState.releaseId)"
            }
            catch {
                $rollbackResult = "failed:$($_.Exception.Message)"
                Write-Warning "No se pudo verificar/restaurar la release anterior: $($_.Exception.Message)"
            }
        }

        $message = "Falló el despliegue de ${releaseId}: $deploymentError. Recuperación: $rollbackResult"
        Write-DeploymentStatus -ReleaseId $releaseId -Status 'failed' -Message $message -Rollback $rollbackResult
        Write-Warning $message
    }
    finally {
        if (Test-Path -LiteralPath $processingFile -PathType Leaf) {
            Move-Item -LiteralPath $processingFile -Destination (Join-Path $processedPath "$releaseId.json")
        }
    }
}

try {
    $script:lockStream = [System.IO.File]::Open(
        $lockFile,
        [System.IO.FileMode]::OpenOrCreate,
        [System.IO.FileAccess]::ReadWrite,
        [System.IO.FileShare]::None
    )
}
catch {
    throw "Ya hay un supervisor activo o no se pudo adquirir el bloqueo: $($_.Exception.Message)"
}

try {
    $script:activeState = Read-JsonFile -Path $activeStateFile
    if ($script:activeState) {
        $null = Get-ManagedProcess -State $script:activeState
        Write-Host "Estado previo encontrado para la release $($script:activeState.releaseId)."
    }

    Write-Host "Supervisor local listo para $healthUrl. Mantén esta consola abierta."
    while ($true) {
        Write-AtomicJson -Path $heartbeatFile -Value ([ordered]@{
            processId = $PID
            updatedAtUtc = [DateTime]::UtcNow.ToString('o')
        })

        $pendingRequests = @(
            Get-ChildItem -LiteralPath $requestsPath -Filter '*.json' -File |
                Sort-Object LastWriteTimeUtc
        )
        foreach ($requestFile in $pendingRequests) {
            Process-DeploymentRequest -RequestFile $requestFile
        }

        Start-Sleep -Seconds $PollIntervalSeconds
    }
}
finally {
    if ($script:activeState) {
        try {
            Stop-ManagedProcess -State $script:activeState
            Write-Host 'Waitress detenido de forma controlada al cerrar el supervisor.'
        }
        catch {
            Write-Warning "No se pudo detener el proceso administrado: $($_.Exception.Message)"
        }
    }
    if ($script:lockStream) {
        $script:lockStream.Dispose()
    }
}

# Inicia os serviços Compose do Sinalyx, com espera pelo Docker e compilação opcionais.
[CmdletBinding()]
param(
    [switch]$Build,
    [switch]$WaitDocker,
    [string]$LogFile
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

if (-not $LogFile) {
    $LogFile = Join-Path $ProjectRoot "logs\sinalyx_start.log"
}

$logDir = Split-Path -Parent $LogFile
if ($logDir) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Registra a etapa no terminal e no arquivo de acompanhamento da inicialização.
function Write-SinalyxLog {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}

# Confere se o motor do Docker está respondendo antes de iniciar os serviços.
function Test-DockerReady {
    docker info *> $null
    return ($LASTEXITCODE -eq 0)
}

Write-SinalyxLog "Iniciando Sinalyx em $ProjectRoot"

if ($WaitDocker) {
    Write-SinalyxLog "Aguardando Docker ficar disponivel..."
    $ready = $false
    for ($attempt = 1; $attempt -le 60; $attempt++) {
        if (Test-DockerReady) {
            $ready = $true
            break
        }
        Start-Sleep -Seconds 5
    }
    if (-not $ready) {
        throw "Docker nao ficou disponivel dentro do tempo esperado."
    }
}

Set-Location $ProjectRoot

$composeArgs = @("compose", "up", "-d")
if ($Build) {
    $composeArgs += "--build"
}

Write-SinalyxLog "Executando: docker $($composeArgs -join ' ')"
& docker @composeArgs 2>&1 | Tee-Object -FilePath $LogFile -Append
if ($LASTEXITCODE -ne 0) {
    throw "docker compose up falhou com codigo $LASTEXITCODE."
}

Write-SinalyxLog "Sinalyx iniciado."
Write-Host ""
Write-Host "Frontend local: http://localhost/"
Write-Host "API via frontend: http://localhost/api/health"
Write-Host "API direta local: http://127.0.0.1:8000/health"

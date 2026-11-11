# Encerra e remove os containers do projeto Compose do Sinalyx, preservando seus volumes.
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

Set-Location $ProjectRoot
Write-Host "Parando Sinalyx sem apagar volumes..."
docker compose down

if ($LASTEXITCODE -ne 0) {
    throw "docker compose down falhou com codigo $LASTEXITCODE."
}

Write-Host "Sinalyx parado. Volumes e dados persistentes foram preservados."

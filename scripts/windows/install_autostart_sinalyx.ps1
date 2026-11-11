# Cadastra o início do Sinalyx no login desta conta do Windows, sem privilégio elevado.
[CmdletBinding()]
param(
    [string]$TaskName = "Sinalyx Local Autostart"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$StartScript = Join-Path $PSScriptRoot "start_sinalyx.ps1"
$LogFile = Join-Path $ProjectRoot "logs\autostart_sinalyx.log"

if (-not (Test-Path $StartScript)) {
    throw "Script de inicializacao nao encontrado: $StartScript"
}

New-Item -ItemType Directory -Path (Split-Path -Parent $LogFile) -Force | Out-Null

$arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$StartScript`" -WaitDocker -LogFile `"$LogFile`""
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arguments -WorkingDirectory $ProjectRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principalUser = "$env:USERDOMAIN\$env:USERNAME"
$principal = New-ScheduledTaskPrincipal -UserId $principalUser -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description "Inicia o Sinalyx com docker compose up -d ao fazer login no Windows." `
    -Force | Out-Null

Write-Host "Tarefa agendada criada: $TaskName"
Write-Host "Log de inicializacao: $LogFile"
Write-Host "A tarefa aguarda o Docker ficar disponivel e nao apaga volumes."

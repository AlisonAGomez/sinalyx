# Remove somente a tarefa agendada indicada; não desinstala a aplicação nem apaga dados.
[CmdletBinding()]
param(
    [string]$TaskName = "Sinalyx Local Autostart"
)

$ErrorActionPreference = "Stop"

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $task) {
    Write-Host "Tarefa agendada nao encontrada: $TaskName"
    return
}

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
Write-Host "Tarefa agendada removida: $TaskName"

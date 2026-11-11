# Gera uma cópia SQL pelo container do Sinalyx; só substitui a saída após concluir a cópia.
param(
    [string]$ContainerName = "sinalyx-banco",
    [string]$Database = "sinalyx",
    [string]$User = "sinalyx",
    [string]$OutputPath = "sinalyx_backup.sql"
)

$ErrorActionPreference = "Stop"

$destino = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputPath)
$identificador = [guid]::NewGuid().ToString('N')
$temporario = Join-Path ([IO.Path]::GetDirectoryName($destino)) ".sinalyx-$identificador.tmp"
$remoto = "/tmp/sinalyx-$identificador.sql"

try {
    # O arquivo no container evita que o PowerShell mude a codificação do SQL.
    docker exec $ContainerName pg_dump -U $User -d $Database --clean --if-exists --file $remoto 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Falha ao gerar backup no PostgreSQL." }

    docker cp "${ContainerName}:$remoto" $temporario 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Falha ao copiar backup; arquivo anterior preservado." }
    if (-not (Test-Path -LiteralPath $temporario -PathType Leaf) -or
        (Get-Item -LiteralPath $temporario).Length -eq 0) {
        throw "Backup vazio ou ausente; arquivo anterior preservado."
    }

    # O temporário fica no mesmo volume; a saída anterior só é substituída após a cópia completa.
    if (Test-Path -LiteralPath $destino) {
        [IO.File]::Replace($temporario, $destino, [System.Management.Automation.Language.NullString]::Value)
    } else {
        [IO.File]::Move($temporario, $destino)
    }
} finally {
    if (Test-Path -LiteralPath $temporario) { Remove-Item -LiteralPath $temporario -Force }
    try {
        docker exec $ContainerName rm -f -- $remoto 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) { Write-Warning "Nao foi possivel remover o arquivo temporario do container." }
    } catch { Write-Warning "Nao foi possivel limpar o arquivo temporario do container." }
}

Write-Host "Backup salvo com sucesso."

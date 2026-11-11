# Aplica a cópia SQL indicada ao banco do Sinalyx. Executar somente no destino confirmado.
param(
    [Parameter(Mandatory = $true)]
    [string]$BackupPath,
    [string]$ContainerName = "sinalyx-banco",
    [string]$Database = "sinalyx",
    [string]$User = "sinalyx"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $BackupPath -PathType Leaf) -or
    (Get-Item -LiteralPath $BackupPath).Length -eq 0) {
    throw "Backup ausente, vazio ou invalido."
}

# Operação destrutiva: restaura o SQL fornecido sobre o banco escolhido.
# Aceita somente dumps SQL confiáveis do pg_dump, não scripts arbitrários.
$origem = (Resolve-Path -LiteralPath $BackupPath).Path
$remoto = "/tmp/sinalyx-restore-$([guid]::NewGuid().ToString('N')).sql"
try {
    docker cp $origem "${ContainerName}:$remoto" 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Falha ao copiar backup; restore nao iniciado." }

    docker exec $ContainerName psql -X -U $User -d $Database --set ON_ERROR_STOP=1 --single-transaction --file $remoto 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Restore falhou; PostgreSQL ou Docker reportou erro." }
} finally {
    try {
        docker exec $ContainerName rm -f -- $remoto 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) { Write-Warning "Nao foi possivel remover o arquivo temporario do container." }
    } catch { Write-Warning "Nao foi possivel limpar o arquivo temporario do container." }
}

Write-Host "Restore concluido com sucesso."

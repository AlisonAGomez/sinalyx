# Consulta os serviços e endereços locais; não inicia nem para containers.
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

# Procura um endereço da rede física para informar o acesso, evitando interfaces virtuais.
function Get-FirstLocalIPv4 {
    try {
        $primaryIp = Get-NetIPConfiguration |
            Where-Object {
                $_.IPv4DefaultGateway -and
                $_.IPv4Address -and
                $_.NetAdapter.Status -eq "Up" -and
                $_.InterfaceAlias -notmatch "vEthernet|WSL|Docker|Loopback|VirtualBox|VMware"
            } |
            Sort-Object { $_.NetAdapter.InterfaceMetric } |
            Select-Object -First 1

        if ($primaryIp) {
            return $primaryIp.IPv4Address.IPAddress
        }

        $fallbackIp = Get-NetIPAddress -AddressFamily IPv4 |
            Where-Object {
                $_.IPAddress -notlike "127.*" -and
                $_.IPAddress -notlike "169.254.*" -and
                $_.PrefixOrigin -ne "WellKnown" -and
                $_.InterfaceAlias -notmatch "vEthernet|WSL|Docker|Loopback|VirtualBox|VMware"
            } |
            Sort-Object InterfaceMetric |
            Select-Object -First 1 -ExpandProperty IPAddress
        return $fallbackIp
    } catch {
        return $null
    }
}

Set-Location $ProjectRoot

Write-Host "Status dos containers Sinalyx:"
docker compose ps

$localIp = Get-FirstLocalIPv4
Write-Host ""
Write-Host "URLs principais:"
Write-Host "  Frontend local: http://localhost/"
if ($localIp) {
    Write-Host "  Frontend na rede local: http://$localIp/"
    Write-Host "  API via frontend: http://$localIp/api/health"
}
Write-Host "  API direta local: http://127.0.0.1:8000/health"
Write-Host "  Nome local opcional: http://sinalyx.local/"

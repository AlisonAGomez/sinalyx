"""Executa PowerShell real com docker simulado, sem acessar daemon ou banco."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize("shell", ["powershell", "pwsh"])
@pytest.mark.parametrize("operacao,cenario", [
    ("backup", "sucesso"), ("backup", "dump_falha"), ("backup", "copia_parcial"),
    ("backup", "vazio"), ("backup", "novo"), ("backup", "relativo"), ("restore", "sucesso"), ("restore", "sql_falha"),
    ("restore", "copia_parcial"), ("restore", "vazio"), ("restore", "ausente"),
])
def test_comandos_nativos_abortam_e_preservam_backup(tmp_path, shell, operacao, cenario):
    executavel = shutil.which(shell)
    if not executavel:
        pytest.skip(f"{shell} indisponivel")
    original = tmp_path / "backup existente.sql"
    original.write_bytes(b"BACKUP ANTERIOR")
    if cenario in {"novo", "ausente"}:
        original.unlink()
    elif operacao == "restore" and cenario == "vazio":
        original.write_bytes(b"")
    roteiro = Path(__file__).resolve().parents[1] / "scripts" / f"{operacao}_postgres.ps1"
    harness = tmp_path / "mock.ps1"
    harness.write_text(r'''
param($Roteiro, $Arquivo, $Operacao, $Cenario)
$global:chamadas = @()
function global:docker {
    $global:LASTEXITCODE = 0
    $global:chamadas += ,@($args)
    if ($args -contains 'pg_dump') {
        if ($Cenario -eq 'dump_falha') { $global:LASTEXITCODE = 7; return }
        'DUMP NOVO'
    }
    if ($args[0] -eq 'cp') {
        if ($Operacao -eq 'backup') {
            $conteudo = if ($Cenario -eq 'vazio') { '' } else { 'DUMP NOVO' }
            [IO.File]::WriteAllText($args[-1], $conteudo)
        }
        if ($Cenario -eq 'copia_parcial') { $global:LASTEXITCODE = 8 }
    }
    if ($args -contains 'psql' -and $Cenario -eq 'sql_falha') { $global:LASTEXITCODE = 9 }
}
$falhou = $false
$erro = ''
try {
    if ($Cenario -eq 'relativo') {
        Set-Location -LiteralPath (Split-Path -Parent $Arquivo)
        $Arquivo = Split-Path -Leaf $Arquivo
    }
    if ($Operacao -eq 'backup') { & $Roteiro -OutputPath $Arquivo }
    else { & $Roteiro -BackupPath $Arquivo }
} catch { $falhou = $true; $erro = $_.Exception.Message }
@{falhou=$falhou; chamadas=$global:chamadas; erro=$erro} | ConvertTo-Json -Depth 5 -Compress
''', encoding="utf-8-sig")
    resultado = subprocess.run([executavel, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(harness),
                               str(roteiro), str(original), operacao, cenario],
                              capture_output=True, text=True, timeout=30)
    assert resultado.returncode == 0, resultado.stderr
    dados = json.loads(resultado.stdout.strip().splitlines()[-1])
    sucesso = cenario in {"sucesso", "novo", "relativo"}
    assert dados["falhou"] == (not sucesso), dados["erro"]
    comandos = dados["chamadas"]
    if operacao == "backup" and sucesso:
        assert original.read_bytes() == b"DUMP NOVO"
    elif cenario == "ausente":
        assert not original.exists()
    elif operacao == "restore" and cenario == "vazio":
        assert original.read_bytes() == b""
    else:
        assert original.read_bytes() == b"BACKUP ANTERIOR"
    assert not list(tmp_path.glob("*.tmp"))
    if not sucesso:
        assert "Backup salvo" not in resultado.stdout
        assert "Restore concluido" not in resultado.stdout
    if operacao == "restore":
        sql = [cmd for cmd in comandos if "psql" in cmd]
        if cenario in {"copia_parcial", "ausente", "vazio"}:
            assert not sql
        else:
            assert len(sql) == 1
            assert "ON_ERROR_STOP=1" in sql[0] and "--single-transaction" in sql[0]

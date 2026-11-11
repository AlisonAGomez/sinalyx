"""Identidade interna de uma amostra inicial, sem armazenar conteúdo do log."""

import hashlib
import re
from pathlib import Path


LIMITE_AMOSTRA = 4096


def tamanho_assinatura(assinatura: str | None) -> int:
    """Lê quantos bytes foram usados na assinatura, limitando a amostra a 4096 bytes."""
    correspondencia = re.fullmatch(r"sha256:(\d+):[0-9a-f]{64}", assinatura or "")
    if not correspondencia:
        return 0
    return min(int(correspondencia[1]), LIMITE_AMOSTRA)


def identificar_geracao(caminho: Path) -> str:
    """Assina o prefixo atual completo até 4096 bytes, sem salvar conteúdo."""
    with caminho.open("rb") as arquivo:
        amostra = arquivo.read(LIMITE_AMOSTRA)
    return f"sha256:{len(amostra)}:{hashlib.sha256(amostra).hexdigest()}"


def corresponde_assinatura(caminho: Path, anterior: str) -> bool:
    """Compara somente os N bytes já assinados, independentemente de append.

    N=0 não fornece evidência de substituição. Prefixos idênticos continuam
    indistinguíveis; assinaturas inválidas não confirmam correspondência.
    """
    partes = re.fullmatch(r"sha256:(\d+):([0-9a-f]{64})", anterior)
    if not partes or int(partes[1]) > LIMITE_AMOSTRA:
        return False
    tamanho = int(partes[1])
    if tamanho == 0:
        return True
    with caminho.open("rb") as arquivo:
        amostra = arquivo.read(tamanho)
    return len(amostra) == tamanho and hashlib.sha256(amostra).hexdigest() == partes[2]

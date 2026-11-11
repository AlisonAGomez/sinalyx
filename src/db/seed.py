"""Criação inicial de contas controlado do PostgreSQL do Sinalyx.

O criação inicial de contas oficial cria somente o administrador inicial configurado por variaveis
de ambiente e evita duplicacao quando o email já existe.
"""

from __future__ import annotations

from typing import Any

from src.db.init_db import create_tables
from src.db.repository import seed_initial_admin


def run_seed() -> dict[str, Any]:
    """Prepara tabelas e executa o criação inicial de contas do administrador inicial.

    Retorno:
        Dicionário com o resultado da criação ou o motivo de não criar.
    """
    create_tables()
    return seed_initial_admin()


def main() -> None:
    """Executa o criação inicial de contas pela linha de comando."""
    result = run_seed()
    if result.get("created"):
        print("Administrador inicial criado com sucesso.")
    else:
        reason = result.get("reason", "nenhuma acao necessaria")
        print(f"Seed concluido: {reason}.")


if __name__ == "__main__":
    main()

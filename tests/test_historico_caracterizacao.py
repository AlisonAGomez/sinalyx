"""Paginação de histórico com registros sintéticos, sem dados operacionais."""

import json
import tracemalloc
from datetime import datetime, timedelta

import pytest
from sqlalchemy import event
from sqlalchemy.dialects import postgresql



@pytest.fixture
def historico(banco):
    repo, models, fabrica, _ = banco
    inicio = datetime(2026, 1, 1)
    with fabrica.begin() as sessao:
        sessao.add_all([
            models.LivePfSenseWindow(
                window_uid=f"sintetica-{i}", execution_id="execucao-sintetica",
                created_at=inicio + timedelta(seconds=i), local_log_path="sintetico.log",
                final_label="anomaly" if i % 2 else "normal", risk_level="low",
                features_json={}, model_outputs_json={"ai_support": {"enabled": bool(i % 3)}},
                metadata_json={}, raw_json={"sintetico": "x" * 256},
            ) for i in range(1000)
        ])
    return repo, models, fabrica


@pytest.mark.parametrize("offset", [0, 450, 1000, 1200])
def test_pagina_ordenacao_total_e_vazia(historico, offset):
    repo, _, _ = historico
    resultado = repo.list_history_windows(limit=50, offset=offset)
    assert resultado["total"] == 1000
    assert (resultado["offset"], resultado["limit"]) == (offset, 50)
    assert [item["id"] for item in resultado["windows"]] == list(range(1000, 0, -1))[offset:offset + 50]


@pytest.mark.parametrize("apoio", [True, False])
def test_filtro_ai_antes_da_paginacao(historico, apoio):
    repo, _, _ = historico
    resultado = repo.list_history_windows(limit=50, offset=10,
                                         filters={"final_label": "anomaly", "ai_support": apoio})
    esperado = [i + 1 for i in reversed(range(1000)) if i % 2 and bool(i % 3) == apoio]
    assert resultado["total"] == len(esperado)
    assert [item["id"] for item in resultado["windows"]] == esperado[10:60]


@pytest.mark.parametrize("funcao,chave", [
    ("list_history_windows", "windows"),
    ("list_history_alerts", "alerts"),
])
def test_filtros_ausencia_offset_e_pagina_vazia(historico, funcao, chave):
    repo, models, fabrica = historico
    with fabrica.begin() as sessao:
        sessao.get(models.LivePfSenseWindow, 998).model_outputs_json = {}
        sessao.get(models.LivePfSenseWindow, 996).model_outputs_json = {"ai_support": {}}
        sessao.get(models.LivePfSenseWindow, 994).model_outputs_json = {
            "ai_support": {"enabled": "sim"}
        }

    listar = getattr(repo, funcao)
    resultado = listar(limit=5, offset=2, filters={"ai_support": False})
    ids = [item["id"] for item in resultado[chave]]
    esperado = [i + 1 for i in reversed(range(1000))
               if (funcao == "list_history_windows" or i % 2)
               and (i + 1 in {998, 996} or (i + 1 != 994 and not bool(i % 3)))]
    assert resultado["total"] == len(esperado)
    assert ids == esperado[2:7]
    assert 998 in esperado and 996 in esperado
    assert 994 not in esperado

    vazio = listar(limit=5, offset=len(esperado), filters={"ai_support": False})
    assert vazio["total"] == len(esperado)
    assert vazio[chave] == []


def test_alertas_filtros_e_ordenacao(historico):
    repo, _, _ = historico
    resultado = repo.list_history_alerts(limit=8, offset=3)
    assert resultado["total"] == 500
    assert [item["id"] for item in resultado["alerts"]] == [
        i + 1 for i in reversed(range(1000)) if i % 2
    ][3:11]
    assert all(item["final_label"] == "anomaly" for item in resultado["alerts"])


def test_expressao_ai_compila_para_postgresql(historico):
    repo, models, _ = historico
    sql = str(repo._live_window_ai_support_expression(
        models.LivePfSenseWindow
    ).compile(dialect=postgresql.dialect()))
    assert "model_outputs_json" in sql
    assert "->>" in sql


@pytest.mark.parametrize("funcao,chave,filtros,total_esperado", [
    ("list_history_windows", "windows", {}, 1000),
    ("list_history_windows", "windows", {"ai_support": True}, 666),
    ("list_history_alerts", "alerts", {}, 500),
    ("list_history_alerts", "alerts", {"ai_support": True}, 333),
])
def test_medicao_carregamento_sintetico(
    historico, funcao, chave, filtros, total_esperado
):
    repo, _, fabrica = historico
    carregados = []
    sqls = []
    event.listen(fabrica, "loaded_as_persistent", lambda sessao, objeto: carregados.append(objeto.id))
    motor = fabrica.kw["bind"]

    def registrar_sql(conn, cursor, statement, parameters, context, executemany):
        sqls.append(statement)

    event.listen(motor, "before_cursor_execute", registrar_sql)
    tracemalloc.start()
    try:
        resultado = getattr(repo, funcao)(limit=50, filters=filtros)
        _, pico = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
        event.remove(motor, "before_cursor_execute", registrar_sql)
    assert resultado["total"] == total_esperado
    assert len(carregados) <= 50
    assert len(resultado[chave]) == 50
    assert any("COUNT(" in sql.upper() for sql in sqls)
    assert any("LIMIT" in sql.upper() and "OFFSET" in sql.upper()
               for sql in sqls if "COUNT(" not in sql.upper())
    print(json.dumps({"registros_sinteticos": 1000, "objetos_carregados": len(carregados),
                      "itens_devolvidos": 50, "pico_python_bytes": pico, "consultas": len(sqls)}))


@pytest.fixture
def execucoes_pequenas(banco):
    repo, models, fabrica, _ = banco
    inicio = datetime(2026, 1, 1)
    dados = [
        ("A", 0, 10, "anomaly", "scan", "high", "primeiro", {"enabled": "sim", "conservative": "yes"}),
        ("A", 5, None, "normal", None, "", "segundo", {}),
        ("B", 3, 30, "anomaly", "flood", "low", "terceiro", {"enabled": True}),
        ("", 1, None, None, "", None, "quarto", {}),
        ("unknown", 2, None, "normal", None, None, "quinto", {}),
    ]
    with fabrica.begin() as sessao:
        for indice, (execucao, segundo, janela, rotulo, ataque, risco, caminho, apoio) in enumerate(dados):
            sessao.add(models.LivePfSenseWindow(
                window_uid=f"contrato-{indice}", execution_id=execucao,
                created_at=inicio + timedelta(seconds=segundo),
                window_timestamp=inicio + timedelta(seconds=janela) if janela is not None else None,
                local_log_path=caminho, final_label=rotulo,
                attack_type=ataque, risk_level=risco, status="success",
                features_json={}, model_outputs_json={"ai_support": apoio},
                metadata_json={}, raw_json={},
            ))
    return repo, models, fabrica


def test_contrato_execucoes_antes_e_depois_da_agregacao(execucoes_pequenas):
    repo, _, _ = execucoes_pequenas
    pagina = repo.list_history_executions(limit=2, offset=0)
    assert (pagina["total"], pagina["limit"], pagina["offset"]) == (3, 2, 0)
    assert [item["execution_id"] for item in pagina["executions"]] == ["A", "B"]
    primeira = pagina["executions"][0]
    assert primeira["total_windows"] == 2
    assert primeira["total_anomalies"] == 1
    assert primeira["ai_support_count"] == 1
    assert primeira["ai_support_conservative_count"] == 1
    assert primeira["local_log_path"] == "primeiro"
    assert primeira["final_label_distribution"] == {"normal": 1, "anomaly": 1}
    assert primeira["attack_type_distribution"] == {"unknown": 1, "scan": 1}
    assert primeira["risk_level_distribution"] == {"unknown": 1, "high": 1}
    assert primeira["first_seen_at"] == "2026-01-01T00:00:00"
    assert primeira["last_seen_at"] == "2026-01-01T00:00:05"
    ultima = repo.list_history_executions(limit=2, offset=2)
    assert ultima["total"] == 3
    assert ultima["executions"][0]["execution_id"] == "unknown"
    assert ultima["executions"][0]["total_windows"] == 2
    assert ultima["executions"][0]["local_log_path"] == "quinto"
    assert repo.list_history_executions(limit=2, offset=3)["executions"] == []
    filtrada = repo.list_history_executions(filters={"final_label": "anomaly", "ai_support": True})
    assert filtrada["total"] == 2
    assert [item["execution_id"] for item in filtrada["executions"]] == ["B", "A"]


def test_contrato_resumo_vazio_e_historico(execucoes_pequenas, banco):
    repo, models, fabrica = execucoes_pequenas
    resumo = repo.summarize_history()["live"]
    assert resumo["total_windows"] == 5
    assert resumo["total_alerts"] == 2
    assert resumo["total_executions"] == 3
    assert resumo["final_label_distribution"] == {"normal": 2, "anomaly": 2, "unknown": 1}
    assert resumo["attack_type_distribution"] == {"unknown": 3, "scan": 1, "flood": 1}
    assert resumo["risk_level_distribution"] == {"unknown": 3, "high": 1, "low": 1}
    assert (resumo["ai_support_count"], resumo["ai_support_conservative_count"]) == (2, 1)
    assert resumo["latest_window"]["local_log_path"] == "terceiro"
    assert resumo["latest_alert"]["local_log_path"] == "terceiro"
    filtrado = repo.summarize_history({"ai_support": False})["live"]
    assert filtrado["total_windows"] == 3
    assert filtrado["ai_support_count"] == 0

    with fabrica.begin() as sessao:
        sessao.query(models.LivePfSenseWindow).delete()
    vazio = repo.summarize_history()["live"]
    assert vazio["total_windows"] == vazio["total_executions"] == 0
    assert vazio["final_label_distribution"] == {}
    assert vazio["latest_window"] is vazio["latest_alert"] is None


@pytest.fixture
def historico_distribuido(banco):
    repo, models, fabrica, _ = banco
    inicio = datetime(2026, 1, 1)
    with fabrica.begin() as sessao:
        sessao.add_all([
            models.LivePfSenseWindow(
                window_uid=f"distribuida-{i}", execution_id=f"exec-{i % 20:02d}",
                created_at=inicio + timedelta(seconds=i),
                local_log_path="sintetico.log",
                final_label="anomaly" if i % 2 else "normal",
                attack_type="scan" if i % 2 else None,
                risk_level="high" if i % 2 else None,
                features_json={},
                model_outputs_json={"ai_support": {
                    "enabled": bool(i % 3), "conservative": "yes" if i % 4 == 0 else False,
                }},
                metadata_json={}, raw_json={},
            ) for i in range(1000)
        ])
    return repo, fabrica


def test_agregacoes_distribuidas_nao_materializam_historico(historico_distribuido):
    repo, fabrica = historico_distribuido
    objetos = []
    sqls = []
    motor = fabrica.kw["bind"]

    def registrar_sql(conn, cursor, statement, parameters, context, executemany):
        sqls.append(statement.upper())

    event.listen(fabrica, "loaded_as_persistent", lambda sessao, objeto: objetos.append(objeto))
    event.listen(motor, "before_cursor_execute", registrar_sql)
    try:
        pagina = repo.list_history_executions(limit=5, offset=3)
        assert pagina["total"] == 20
        assert [item["execution_id"] for item in pagina["executions"]] == [
            "exec-16", "exec-15", "exec-14", "exec-13", "exec-12"
        ]
        assert all(item["total_windows"] == 50 for item in pagina["executions"])
        assert len(objetos) == 0
        objetos_execucoes = len(objetos)
        assert any("GROUP BY" in sql and "LIMIT" in sql and "OFFSET" in sql for sql in sqls)

        sqls.clear()
        resumo = repo.summarize_history()["live"]
        assert resumo["total_windows"] == 1000
        assert resumo["total_alerts"] == 500
        assert resumo["total_executions"] == 20
        assert resumo["final_label_distribution"] == {"normal": 500, "anomaly": 500}
        assert resumo["attack_type_distribution"] == {"unknown": 500, "scan": 500}
        assert resumo["risk_level_distribution"] == {"unknown": 500, "high": 500}
        assert resumo["ai_support_count"] == 666
        assert resumo["ai_support_conservative_count"] == 250
        assert resumo["latest_window"]["id"] == 1000
        assert resumo["latest_alert"]["id"] == 1000
        assert len(objetos) <= 2
        print(json.dumps({
            "janelas": 1000, "execucoes_na_pagina": 5,
            "objetos_execucoes": objetos_execucoes,
            "objetos_resumo": len(objetos),
        }))
        assert sum("GROUP BY" in sql for sql in sqls) >= 3
        assert all("LIMIT" in sql for sql in sqls if "SELECT LIVE_PFSENSE_WINDOWS.ID" in sql)
    finally:
        event.remove(motor, "before_cursor_execute", registrar_sql)


def test_execucoes_empatadas_preservam_ordem_e_paths(banco):
    repo, models, fabrica, _ = banco
    instante = datetime(2026, 1, 1)
    dados = [
        ("A", 10, "A-primeiro"),
        ("B", 10, "B-primeiro"),
        ("B", 0, "B-outro"),
        ("A", 0, "A-outro"),
    ]
    with fabrica.begin() as sessao:
        for indice, (execucao, segundo, caminho) in enumerate(dados):
            sessao.add(models.LivePfSenseWindow(
                window_uid=f"empate-{indice}", execution_id=execucao,
                created_at=instante,
                window_timestamp=instante + timedelta(seconds=segundo),
                local_log_path=caminho, features_json={},
                model_outputs_json={}, metadata_json={}, raw_json={},
            ))
    pagina = repo.list_history_executions(limit=1)
    assert pagina["total"] == 2
    assert pagina["executions"][0]["execution_id"] == "B"
    assert pagina["executions"][0]["local_log_path"] == "B-primeiro"
    seguinte = repo.list_history_executions(limit=1, offset=1)
    assert seguinte["executions"][0]["execution_id"] == "A"
    assert seguinte["executions"][0]["local_log_path"] == "A-primeiro"

"""Verificação real de host keys do Paramiko com transporte/SFTP simulados."""

import json
from dataclasses import replace
from types import SimpleNamespace

import pytest


@pytest.fixture(scope="module")
def chaves():
    import paramiko
    return paramiko.RSAKey.generate(2048), paramiko.RSAKey.generate(2048)


@pytest.mark.parametrize("cenario", ["conhecido", "desconhecido", "divergente", "porta_alternativa"])
def test_verificacao_ssh_sem_rede(coletor, chaves, monkeypatch, caplog, cenario):
    import paramiko
    modulo, config = coletor
    esperada, recebida = chaves
    if cenario == "porta_alternativa":
        config = replace(config, port=2222)
    nome = "[ssh.example.test]:2222" if config.port != 22 else config.host
    if cenario == "desconhecido":
        nome = "outro.example.test"
    config.known_hosts_path.write_text(
        f"{nome} {esperada.get_name()} {esperada.get_base64()}\n",
        encoding="utf-8",
    )
    config.local_path.write_bytes(b"anterior")
    autenticacoes = []

    class Transporte:
        fechado = False
        def use_compression(self, **kwargs): pass
        def get_security_options(self): return SimpleNamespace(key_types=["rsa-sha2-512"])
        def start_client(self, **kwargs): pass
        def get_remote_server_key(self): return recebida if cenario == "divergente" else esperada
        def _log(self, *args): pass
        def close(self): self.fechado = True

    transporte = Transporte()
    conectar = paramiko.SSHClient.connect

    def conectar_sem_rede(cliente, **kwargs):
        assert isinstance(cliente._policy, paramiko.RejectPolicy)
        return conectar(cliente, **kwargs, sock=object(), transport_factory=lambda *a, **k: transporte)

    class Sftp:
        fechado = False
        def stat(self, caminho): return SimpleNamespace(st_size=9)
        def get(self, remoto, local):
            from pathlib import Path
            Path(local).write_bytes(b"sintetico")
        def close(self): self.fechado = True

    sftp = Sftp()
    monkeypatch.setattr(paramiko.SSHClient, "connect", conectar_sem_rede)
    monkeypatch.setattr(paramiko.SSHClient, "_auth", lambda *a, **k: autenticacoes.append(True))
    monkeypatch.setattr(paramiko.SSHClient, "open_sftp", lambda self: sftp)
    resposta = modulo.collect_filter_log(config)
    if cenario in {"conhecido", "porta_alternativa"}:
        assert resposta["last_fetch_status"] == "success"
        assert autenticacoes == [True]
        assert config.local_path.read_bytes() == b"sintetico"
        assert sftp.fechado
    else:
        assert resposta["last_fetch_status"] == "error"
        assert resposta["error_type"] == ("BadHostKeyException" if cenario == "divergente" else "SSHException")
        assert not autenticacoes
        assert config.local_path.read_bytes() == b"anterior"
        assert config.host not in resposta["error"] + caplog.text
    assert transporte.fechado
    assert not config.local_path.with_name("filter.log.tmp").exists()
    assert config.password not in json.dumps(resposta) + caplog.text


@pytest.mark.parametrize("cenario", ["arquivo_ausente", "host_ausente", "modo_inseguro", "arquivo_invalido"])
def test_configuracao_ssh_falha_antes_de_conectar(coletor, monkeypatch, cenario, caplog):
    import paramiko
    modulo, config = coletor
    if cenario != "arquivo_ausente":
        config.known_hosts_path.write_text("ssh.example.test ssh-rsa !!!\n", encoding="utf-8")
    if cenario == "host_ausente":
        config = replace(config, host=None)
    if cenario == "modo_inseguro":
        config = replace(config, allow_unknown_host=True)
    monkeypatch.setattr(paramiko.SSHClient, "connect", lambda *a, **k: pytest.fail("Não deve conectar"))
    resposta = modulo.collect_filter_log(config)
    assert resposta["last_fetch_status"] == "error"
    assert config.password not in json.dumps(resposta) + caplog.text
    assert "!!!" not in resposta["error"]


def test_padrao_ssh_e_rejeicao_e_known_hosts_do_usuario(coletor, monkeypatch):
    import paramiko
    modulo, config = coletor
    chamadas = []
    monkeypatch.setattr(paramiko.SSHClient, "load_system_host_keys", lambda self: chamadas.append("known_hosts"))

    def conectar(cliente, **kwargs):
        assert isinstance(cliente._policy, paramiko.RejectPolicy)
        raise paramiko.SSHException("ERRO_SINTETICO_NAO_PUBLICAR")

    monkeypatch.setattr(paramiko.SSHClient, "connect", conectar)
    resposta = modulo.collect_filter_log(replace(config, known_hosts_path=None))
    assert config.allow_unknown_host is False
    assert chamadas == ["known_hosts"]
    assert "ERRO_SINTETICO_NAO_PUBLICAR" not in resposta["error"]


def test_configuracao_central_ssh(coletor, monkeypatch):
    from src.core.config import get_settings
    modulo, config = coletor
    settings = replace(get_settings(), pfsense_known_hosts_path=str(config.known_hosts_path),
                       pfsense_allow_unknown_host=False)
    monkeypatch.setattr(modulo, "get_settings", lambda: settings)
    efetiva = modulo.PfSenseCollectorConfig.from_env()
    assert efetiva.known_hosts_path == config.known_hosts_path
    assert efetiva.allow_unknown_host is False

# Implantação local

O Docker Compose é o fluxo oficial de implantação local. Os relatos de deploy
registram as condições das respectivas fases. Confira os requisitos do recorte
no [README principal](../README.md) antes de executar este procedimento.

## Preparação

Leia [ambiente](environment.md), [segurança](security.md) e [banco](database.md).
Configure `.env` privado sem sobrescrever arquivos existentes e disponibilize
modelos confiáveis no volume `./data:/app/data`. Não embuta dados nas imagens.
Defina credenciais do banco, administrador e segredo JWT conforme o perfil.

Na raiz:

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

Serviços Compose: `frontend`, `api`, `postgres`. Os nomes de containers
configurados são `sinalyx-painel`, `sinalyx-servidor`, `sinalyx-banco`.
Esses nomes identificam os containers no Docker Desktop. Os serviços internos
continuam sendo `frontend`, `api` e `postgres`, preservando a comunicação entre
eles. Imagens, portas e volumes não dependem do nome apresentado.
O volume PostgreSQL é `sinalyx_pgdata`.

## Acesso padrão e rede

Frontend: `http://localhost/`; API direta: `http://127.0.0.1:8000`;
PostgreSQL: `127.0.0.1:5432`. Todos os binds padrão são loopback.
`VITE_API_BASE_URL=/api` direciona chamadas pelo Nginx. Não presumir que
`http://IP_LOCAL/` já esteja acessível na rede.

Acesso compartilhado exige decisão de implantação: configurar
`SINALYX_FRONTEND_BIND` para a interface pretendida, firewall, perfil
demo/production, segredo forte e TLS no proxy apropriado.
`SINALYX_FRONTEND_HOST_PORT` altera a porta publicada. Revisar valores reais
já existentes: eles prevalecem sobre defaults.
Nomes locais/DNS não abrem portas nem garantem TLS.

## Verificação e parada

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/live
Invoke-RestMethod http://127.0.0.1:8000/ready
Invoke-RestMethod http://localhost/api/health
docker compose logs --tail 80 api
docker compose down
```

Revise logs antes de compartilhar. `down` preserva volumes; não acrescente
`-v` como rotina. Health não substitui validação de login, upload, inferência
e gravação/consulta no PostgreSQL. Swagger por `/api/docs` usa URLs relativas
para preservar o prefixo OpenAPI; carregamento e execução foram validados na
[Fase 3](fase3_qa_integrado.md). Veja também [testes](testing.md).

Desde a Fase 2E:

- `/live`: liveness, HTTP 200 com `{"status":"ok"}`, sem consultar dependências.
- `/health`: contrato anterior preservado, incluindo indicação de banco; HTTP
  200 não significa que análise/autenticação estão disponíveis.
- `/ready`: HTTP 200 com `{"status":"ready"}` ou 503 com
  `{"status":"not_ready"}`. Verifica PostgreSQL/tabelas mínimas e artefatos
  carregados em memória após preload completo. Não carrega modelos nem infere.

A sonda de banco usa conexão separada, timeout de conexão de 2 segundos e
statement timeout de 2 segundos. DNS, múltiplos hosts e falhas do sistema podem
exceder esses tempos; não é deadline global garantido. Não retorna causas,
paths ou dados internos. Banco desabilitado mantém readiness negativa, mesmo
com fallback JSON. Falha no preload exige corrigir a causa e reiniciar a API;
carregamento parcial/sob demanda não confirma readiness.

Compose permanece usando `/health` por compatibilidade, pois não foi possível
validar integração Docker. Trocar o healthcheck para `/ready` pode impedir o
frontend de subir quando banco/modelos faltarem; validar em ambiente isolado
antes dessa mudança. `/ready` não prova qualidade dos modelos, integridade de
todos os campos do schema ou sucesso de uma análise completa.

## Scripts Windows, backup e restore

[Scripts Windows](../scripts/README.md) iniciam/param a stack e podem instalar
autostart no login. Autostart da stack não significa coletor pfSense contínuo.
Instalação de tarefa agendada e restore não foram executados nesta fase.

Backup/restore devem usar destino privado e banco de teste antes de aplicação
no banco existente. O dump gerado inclui comandos de limpeza; restore pode
substituir dados. Não copiar uma pasta antiga inteira sobre o projeto atual.
Veja [backup e restauração](../scripts/README.md#backup-e-restore) para os cuidados e o alcance da validação.

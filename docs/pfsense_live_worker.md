# Worker live pfSense

O serviço Compose `live-worker` (`sinalyx-coleta-experimental`) executa
`python -m src.workers.pfsense_live_worker` com o mesmo Dockerfile da API e
usuário não-root `sinalyx`. Não publica portas nem acessa Docker socket.
Cada rodada chama diretamente `process_live_pfsense(collect=True, persist=True,
finite_file=False, window="5s")`. Não há chamadas HTTP ao pipeline.

`SINALYX_PFSENSE_WORKER_INTERVAL_SECONDS` tem default 5 e mínimo 1.
`SINALYX_PFSENSE_WORKER_AUTOSTART` tem default false e só determina o primeiro
controle. Depois, `worker_control.json` prevalece, inclusive após restart.
Controle inválido ou removido durante execução interrompe novos ciclos.

Os arquivos ficam em `data/runtime/pfsense/live/`, compartilhados entre API e
worker pelo volume `/app/data`. A API escreve apenas `worker_control.json`;
o worker escreve apenas `worker_status.json`, exceto pela criação exclusiva
do controle no bootstrap. Escritas usam temporário, flush/fsync e publicação
atômica; o bootstrap não sobrescreve um comando administrativo concorrente.
O diretório do host precisa ser gravável pelo usuário `sinalyx` no container.

Endpoints autenticados:

- `GET /live/pfsense/worker/status`: estado observado e desejado, horário da
  última atualização e último ciclo. Um status antigo não prova que o processo
  está vivo; confira `updated_at` e o estado do container.
- `POST /live/pfsense/worker/start`: somente admin; solicita processamento lógico.
- `POST /live/pfsense/worker/stop`: somente admin; bloqueia novos ciclos. A rodada
  em andamento pode concluir. Não inicia, mata ou remove containers.

O worker relê controle em esperas de até 0,5 s. Erros de ciclo recebem backoff
exponencial, limitado a 60 s, e sucesso restaura o intervalo configurado.
SIGTERM/SIGINT interrompem esperas; uma rodada já iniciada termina antes da saída.
O Compose concede 120 s antes de forçar término; ajuste `stop_grace_period`
conforme a duração real observada de SSH/inferência/banco no ambiente.

Toda chamada persistente, incluindo API manual e CLI, usa o mesmo advisory lock
PostgreSQL: bigint assinado derivado dos primeiros oito bytes do SHA-256 de
`sinalyx:pfsense:live-execution`. Uma conexão permanece aberta durante toda a
rodada e é liberada em `finally`. Falha ao liberar invalida a conexão antes de
devolvê-la ao pool. Lock ocupado retorna `busy` sem coleta nem alteração de
offset; PostgreSQL indisponível impede início. Replay `persist=False` dispensa
o lock: use somente arquivo/estado isolado, nunca junto ao worker operacional.
Não há migrations nem tabelas novas. Use uma única instância do worker para
manter um único escritor de status; o lock protege também chamadas manuais.

As configurações SSH existentes vêm do `.env`. `RejectPolicy` e known_hosts
permanecem obrigatórios. `SINALYX_PFSENSE_KEY_PATH` e
`SINALYX_PFSENSE_KNOWN_HOSTS_PATH` devem apontar para arquivos acessíveis **dentro
do container**; configure bind mounts somente leitura em override privado se
necessário. Nunca copie chave privada para a imagem nem versione chaves,
known_hosts reais ou credenciais. O `.env` real não deve ser versionado.

Status e mensagens do worker não incluem conteúdo do log, assinatura de geração,
credenciais, endereço do pfSense ou caminhos internos. Falhas são descritas por
mensagem operacional genérica. Parser, features, modelos e decisão permanecem
no pipeline existente. Testes automatizados usam dados sintéticos e PostgreSQL
descartável, sem conexão real ao pfSense.

A coleta contínua só pode ser considerada operacionalmente validada após teste
real contra pfSense. Boot Docker parado valida infraestrutura e controle, não
valida conectividade SSH nem coleta contínua real.

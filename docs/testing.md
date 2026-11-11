# Testes e validação

Status: **ATUAL** como procedimento. Resultados datados ficam nos relatórios de
fase; comandos abaixo não significam que uma integração já foi executada.

## Testes neste recorte

**Executáveis com os arquivos públicos.** Os testes do parser e os casos de contratos que usam fixtures sintéticas podem rodar sem pesos oficiais. A instalação pelo lockfile e os dois typechecks do frontend também podem ser executados neste recorte.

**Frontend e avaliador.** A logo original está incluída. O GITHUB-REORG-07 aprovou os typechecks, 106 testes em 14 suítes e o build do frontend. O avaliador em scripts/evaluate_component_contribution_tcc.py está incluído para os dois testes sintéticos. Os requisitos dos testes históricos estão abaixo. Consulte o [README principal](../README.md#instalação-e-execução-local).

**Dependentes de ambiente de QA ou acervo privado.** Os testes opt-in de integração precisam de PostgreSQL descartável. O replay de 355 janelas em `tests/test_component_contributions_backend.py` exige o avaliador, os CSVs históricos e a configuração oficial de `current`. A verificação de evidência offline em `tests/test_component_contribution.py` exige a saída histórica já gerada. Esses insumos históricos ficam fora do candidato. Falhas por import ausente e skips por insumo indisponível devem ser registrados separadamente.

**API sem modelos.** Com o banco desabilitado e sem os artefatos, a API pode iniciar em modo degradado. `/live` e `/health` podem responder HTTP 200, enquanto `/ready` retorna 503. Validar a prontidão e executar análises reais exige o store autorizado de `current` e, no fluxo da API, PostgreSQL configurado.

## Backend local

Na raiz, com a venv Python 3.10.11 preparada, use terminal separado para não
alterar o ambiente de uma API em execução:

```powershell
$env:PYTHON_DOTENV_DISABLED = '1'
$env:SINALYX_TEST_ADMIN_EMAIL = ''
$env:SINALYX_TEST_ADMIN_PASSWORD = ''
$env:SINALYX_TEST_API_BASE_URL = 'http://127.0.0.1:8000'
.\.venv\Scripts\python.exe -m compileall -q -x 'bruteforce_recent_history_prototype\.py$' src scripts tests migrations
.\.venv\Scripts\python.exe -m pytest -q -ra --tb=short
# Opcional: executar somente as regressões do parser.
.\.venv\Scripts\python.exe -m pytest -q tests/test_pfsense_parser.py
```

O compileall da base compatível exclui apenas o protótipo congelado
`scripts/experiments/bruteforce_recent_history_prototype.py`, cuja sintaxe
preexistente não compila em Python 3.10. O compileall irrestrito continua com
essa limitação. Os testes experimentais usam a cópia `_py310_compat.py` por
roteamento existente em `tests/experiments/conftest.py`.

`tests/test_pfsense_parser.py` é descoberto automaticamente pela suíte geral;
a chamada específica acima é apenas opcional. Os testes de upload/erros, login e SSH exercitam controles
locais; mocks de sessão e transporte não comprovam integração PostgreSQL/pfSense.
`tests/test_api_smoke.py` depende de API em execução e credenciais de teste.
Um **skip** indica teste não executado, nunca aprovação dessa integração.

## Distribuição Windows experimental: referência do checkout privado (AUD-11)

Os comandos desta seção documentam o checkout privado completo. O builder, as fixtures e os testes de distribuição Windows estão fora do candidato público. Para validar o recorte público, use as seções de backend e frontend deste guia.

Os testes abaixo executam o builder oficial com uma raiz temporária. Copiam
somente código Python, configuração Alembic e template de migration; não copiam
o `frontend/dist` nem os modelos canônicos. A fixture compartilhada fica em
`tests/support/distribution.py`.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q -ra -p no:cacheprovider tests/test_distribution_launcher.py tests/test_distribution_package.py
```

O frontend sintético contém `index.html`, um asset JavaScript e o contrato
same-origin `/api`. Os arquivos de modelos são marcadores não executáveis,
acompanhados de manifest com as 13 features e registry current-only sintéticos.
Isso valida cópia/integridade, allowlist, sanitização, determinismo, imports e
preflight por presença de recursos. **Não valida desserialização ou inferência**,
nem equivale ao build Vue real, ao bundle ONEDIR ou ao Setup instalado.

As rejeições de URL de desenvolvimento, ausência de `/api`, source maps,
dotfiles, recursos obrigatórios ausentes, registry/manifest incompatíveis e
conteúdo sensível continuam exercitando as validações reais. Apenas falha de
cópia é injetada para verificar limpeza do staging. Os subprocessos isolam
variáveis Sinalyx/banco herdadas e usam dados/ProgramData temporários. Nos testes
de primeira execução, o cofre é falso; nenhum Credential Manager real é usado.
A saída do launcher é capturada explicitamente em UTF-8.

O gate adicional `test_pacote_com_artefatos_reais_opt_in` mantém os requisitos
reais do builder: current completo em `data/models`, manifest/registry válidos
e frontend compilado com `VITE_API_BASE_URL=/api`. Sem opt-in ele aparece como
**skipped**, não como aprovação. Com opt-in, pré-requisito ausente/inválido é
falha, nunca fallback para fixtures. Ele verifica integridade e hashes das
entradas, sem carregar modelos ou iniciar a API.

Após preparar esses recursos em um checkout de QA isolado (para não substituir
um `dist` local de desenvolvimento), execute nesse checkout:

```powershell
$env:SINALYX_TEST_REAL_DISTRIBUTION = '1'
try {
    .\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider tests/test_distribution_package.py::test_pacote_com_artefatos_reais_opt_in
} finally {
    Remove-Item Env:SINALYX_TEST_REAL_DISTRIBUTION -ErrorAction SilentlyContinue
}
```

Carregamento/inferência com modelos oficiais, PostgreSQL real, instalação Windows,
ACLs, Credential Manager, reboot e uninstall exigem seus QAs de integração
separados; sucesso dos contratos sintéticos não os aprova. Os demais testes de
registry/manifest que leem artefatos canônicos conservam seus pré-requisitos.
Não há alteração da classificação experimental da distribuição Windows.

Para executar a suíte sem chamar uma API externa já em execução, use um terminal
de QA separado, desabilite dotenv/banco e remova somente os opt-ins desse terminal:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DATABASE_ENABLED = 'false'
'SINALYX_TEST_POSTGRES_URL', 'SINALYX_TEST_ADMIN_EMAIL', 'SINALYX_TEST_ADMIN_PASSWORD', 'SINALYX_TEST_REAL_DISTRIBUTION' |
    ForEach-Object { Remove-Item "Env:$_" -ErrorAction SilentlyContinue }
.\.venv\Scripts\python.exe -B -m pytest -q -ra -p no:cacheprovider --ignore=tests/test_api_smoke.py
```

A exclusão explícita de `test_api_smoke.py` separa o smoke HTTP externo; não o
aprova. Os skips PostgreSQL, plataforma e gate real devem ser registrados
individualmente, sem convertê-los em passed.

## Frontend

Em `frontend/`:

```powershell
npm ci
npm audit
npm run typecheck
npm run build
```

`npm ci` reproduz o lockfile; `npm audit` consulta advisories no momento da
execução e seu resultado pode mudar. Não usar `audit fix --force` como validação.
Na Fase 2D não houve alteração frontend/dependências e esses comandos não foram
repetidos. A Fase 2A registrou instalação/audit; a Fase 2C registrou typecheck/build.
Esses resultados são históricos, não uma nova auditoria de dependências.

## Docker e integração pendente

Em ambiente isolado com Docker disponível:

```powershell
docker compose config --quiet
docker compose build
docker compose up -d
docker compose ps
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://localhost/api/health
```

Não imprimir `compose config` expandido: pode revelar secrets.
Verifique separadamente: saúde PostgreSQL, login de teste, upload permitido e
negado, gravação/consulta de análise, proxy `/api/`, headers de HTML/assets e
endereços confiáveis do proxy. Confira também OpenAPI/Swagger pelo prefixo:
o caminho via proxy não foi comprovado. Use apenas logs sintéticos/revisados.
Health HTTP sozinho não prova inferência nem persistência.

Docker segue indisponível neste ambiente. Build, containers, migração, seed,
integração banco e conexão SSH real não foram executados na Fase 2D.

## Como registrar

| Situação | Significado |
| --- | --- |
| Executado/aprovado | Comando rodou e há resultado desta fase |
| Executado/falhou | Registrar comando, causa e alcance |
| Skip | Teste coletado, mas corpo não executado |
| Não executado | Fora do escopo ou sem ambiente |
| Pendência | Validação necessária ainda sem evidência |

O relatório da Fase 2D registra os resultados daquela etapa e fica no acervo histórico.
Consulte o [índice da documentação](README.md#resultados-históricos) para os registros incluídos nesta cópia.

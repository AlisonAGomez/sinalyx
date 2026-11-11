# Ambiente do Sinalyx

## Versões e alcance da baseline

O Python oficial é **3.10.11, 64 bits**, também registrado em `.python-version`.
A Fase 2A foi validada no Windows com essa versão, Node **24.19.0** e npm
**11.17.0**. Python 3.12 foi usado apenas na validação auxiliar da Fase 1 e não
substitui a versão oficial.

O conjunto numérico preservado é TensorFlow 2.21.0, Keras 3.12.4, NumPy 2.2.6,
pandas 2.3.3, scikit-learn 1.7.2, SciPy 1.15.3 e h5py 3.14.0. A validação de
imports e testes não significa que modelos foram retreinados, promovidos ou
reavaliados com dados reais.

`requirements.txt` fixa as dependências declaradas e as bibliotecas numéricas
transitivas relevantes a partir dos metadados do ambiente anterior. O arquivo
`requirements-windows-py310.lock` registra a resolução da instalação limpa, com
versões e hashes dos pacotes para Windows x64/Python 3.10. Não foi produzido por
um `pip freeze` indiscriminado. Não usar esse lock Windows como lock Linux.

Uma segunda venv limpa validou a instalação com hashes, `pip check`, as 76
versões do lock e o carregamento somente de leitura dos artefatos de `current`
pelo loader oficial. Os resultados e limites estão no relatório da Fase 2A.

## Criar o ambiente Python

Instale o [Python 3.10.11 oficial](https://www.python.org/downloads/release/python-31011/)
para seu usuário e confira a versão antes de criar a venv. Não sobrescreva uma
venv existente sem antes preservá-la. Na recuperação da Fase 2A, uma cópia
histórica foi movida para `backups/ambiente-fase2a/venv-anterior/`; esse caminho
não faz parte da instalação atual e os ambientes legados foram posteriormente
arquivados fora da árvore do repositório.

Na raiz do projeto, usando PowerShell:

```powershell
py -3.10 --version
# A saída deve ser Python 3.10.11.
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-windows-py310.lock
.\.venv\Scripts\python.exe -m pip check
```

Não é necessário ativar a venv quando o executável é chamado pelo caminho
completo. Se o launcher `py` não localizar a instalação, use o caminho completo
do `python.exe` 3.10.11 instalado. A instalação de referência usou o pip 23.0.1
e o setuptools 65.5.0 fornecidos por essa versão do Python.

Para resolver dependências em outra plataforma:

```bash
python -m pip install -r requirements.txt
python -m pip check
```

Esse segundo comando de instalação preserva versões diretas, mas pode resolver
transitivas diferentes. Requer validação própria e não equivale à reprodução
exata do ambiente Windows.

## Testes Python sem carregar ambiente real

Na raiz do projeto, para executar a baseline sem ler `.env` ou autenticar com
credenciais reais:

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

`tests/test_pfsense_parser.py` segue a descoberta padrão `test_*.py` do pytest.
Seus dois testes já integram a suíte geral; a execução específica é opcional.

O compileall completo encontra uma incompatibilidade preexistente com Python
3.10 no protótipo congelado `scripts/experiments/bruteforce_recent_history_prototype.py`.
Não houve alteração desse arquivo. Os testes experimentais já usam o roteamento
de `tests/experiments/conftest.py` para a cópia `_py310_compat.py`. O comando
acima valida a base compatível, excluindo somente esse protótipo. Não transforma
a falha conhecida do compileall irrestrito em aprovação. Veja [testes](testing.md)
para a distinção entre procedimento, execução e pendência.

Os testes HTTP fazem skip quando a API não está disponível. Para QA integrado,
prepare posteriormente uma instância isolada e usuários de teste; forneça
`SINALYX_TEST_API_BASE_URL`, `SINALYX_TEST_ADMIN_EMAIL` e
`SINALYX_TEST_ADMIN_PASSWORD` fora do Git. Os testes desta baseline não promovem
experimentos nem utilizam holdout real para ajuste.

As variáveis acima valem para o terminal atual. Abra outro terminal para iniciar
a aplicação com seu ambiente local, ou remova `PYTHON_DOTENV_DISABLED` quando
quiser permitir o carregamento normal do `.env`.

## Upload e erros da API (Fase 2B)

`POST /analyze/pfsense` aceita `.log` com corpo HTTP de até **52.428.800 bytes
(50 MiB)**, incluindo o envelope multipart. Portanto, o arquivo precisa deixar
espaço para esse envelope. O padrão acompanha `client_max_body_size 50m` do
Nginx existente; o proxy não foi alterado.

`SINALYX_LIMITE_UPLOAD_BYTES` configura esse limite em bytes no backend. Reinicie
a API após alterar a configuração. Valor ausente/inválido usa o padrão; zero ou
negativo é limitado a um byte, conforme o leitor central de inteiros. O exemplo
está em `.env.example`; no Compose, a API já recebe esse arquivo por `env_file`.
Não aumente o limite sem avaliar memória, disco e tempo do pipeline.

A API conta os bytes efetivamente recebidos, inclusive sem `Content-Length`, e
retorna **413 / `upload_too_large`** antes do pipeline ao exceder o limite.
O serviço também limita a cópia do arquivo em blocos de até 64 KiB. Upload vazio
retorna 400 e extensão não suportada retorna 415. O processamento continua sendo
aguardado na mesma requisição, executado no thread pool da stack atual.

O upload temporário é removido ao terminar. Resultados concluídos e fallback
JSON permanecem disponíveis; saídas incompletas da própria requisição são
removidas em falha. Nenhum arquivo preexistente é alvo dessa limpeza.

Respostas de erro usam mensagens estáveis, sem exceção técnica bruta. O logger
`sinalyx.api` registra operação, identificador de erro, tipo e localização no
código, sem mensagem da exceção, SQL, payload ou variáveis locais. Veja
[upload e erros](security.md#upload-e-erros). O relatório A02/A03 fica no acervo histórico.

## Frontend

A baseline local usa Node 24.19.0. O Vite 6.4.3 também declara suporte às linhas
18, 20 e >=22; isso é compatibilidade declarada, não validação de todas essas
versões. O Dockerfile existente continua usando Node 20 e precisa de validação
Docker separada.

```powershell
node --version
npm --version
cd frontend
npm ci
npm audit
npm run typecheck
npm run build
npm run dev
```

Use `npm ci` para reproduzir o lockfile; `npm install` é reservado a alterações
intencionais de dependências. Não execute `npm audit fix --force`. `dev` e
`preview` ficam vinculados a `127.0.0.1`. Para um teste de rede autorizado, informe
explicitamente o endereço necessário, por exemplo `npm run dev -- --host IP_DE_TESTE`.

O npm 11.17.0 informou que o postinstall do esbuild não tinha autorização na
política local. O build passou com o binário fornecido pelo pacote opcional da
plataforma, sem liberar scripts indiscriminadamente. `lucide-vue-next` gerou
aviso de depreciação; migração de biblioteca visual não faz parte desta fase.

## Arquivos e variáveis de ambiente

- `.env` e `frontend/.env`: configurações reais privadas.
- `.env.example` e `frontend/.env.example`: exemplos versionáveis.
- `DATABASE_ENABLED`: habilita persistência PostgreSQL.
- `DATABASE_URL`: conexão da API com o banco.
- `SINALYX_AUTH_SECRET_KEY`: segredo de assinatura dos tokens.
- `SINALYX_ADMIN_EMAIL` e `SINALYX_ADMIN_PASSWORD`: administrador inicial.
- `SINALYX_CORS_ORIGINS`: origens permitidas para o frontend.
- `SINALYX_PFSENSE_*`: configurações opcionais do coletor.

Nunca sobrescreva um `.env` já configurado ao copiar exemplos. Mantenha valores
reais fora de comandos compartilhados, relatórios, imagens e commits. A política
Git e os dois contextos Docker excluem ambientes reais e variantes; apenas os
exemplos são permitidos.

Troque segredos de desenvolvimento antes de uso compartilhado. Autenticação,
CORS e hardening funcional não foram modificados na Fase 2A.

## Docker

Na Fase 2C, frontend, API e PostgreSQL passaram a ter publicação padrão somente
em loopback. Configurações existentes no `.env` prevalecem sobre os defaults e
precisam de revisão pelo operador; esta fase não altera o arquivo real.

Antes de compartilhar o ambiente, configure `SINALYX_ENV=demo` ou `production`,
um segredo JWT aleatório forte e TLS em um reverse proxy apropriado. A API
recusa inicialização com segredo ausente, padrão ou trivial nesses perfis.
O fallback local não é adequado à rede. Consulte o [guia de segurança](security.md)
para SSH, limites de login e configuração de proxy. O relatório da Fase 2C fica no acervo histórico.

Na raiz, com Docker e Compose disponíveis e ambiente privado já preparado:

```powershell
docker compose config --quiet
docker compose build
```

Não imprima a configuração expandida: ela pode conter credenciais. Docker
permaneceu indisponível na Fase 2A; os comandos acima **não foram validados**.
O Dockerfile Python mantém `python:3.10-slim`, cuja versão de patch pode diferir
de 3.10.11; não se afirma reprodução exata da imagem nesta fase.

A imagem API não embute `data/`; modelos privados são fornecidos pelo volume
existente. Consulte [dados e modelos](dados_modelos.md) para a classificação dos
perfis e artefatos. Os resultados da Fase 2A ficam no acervo histórico.

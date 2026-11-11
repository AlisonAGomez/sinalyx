# Sinalyx

O Sinalyx é um projeto de Trabalho de Conclusão de Curso (TCC) para análise de logs de firewall pfSense. O painel organiza os resultados por janela de tráfego e ajuda a investigar comportamentos que merecem atenção.

## O que o sistema faz

- Importa arquivos de log do pfSense para análise.
- Apresenta a classificação de cada janela, o nível de risco e os sinais que ajudam a interpretar o resultado.
- Permite consultar alertas, análises anteriores e resultados no painel. O acesso depende da autenticação e das permissões do usuário.

## Como funciona

O parser lê os registros do firewall. O pipeline agrupa os eventos em janelas e calcula as 13 características usadas pelo perfil oficial, `current`. Autoencoder e Isolation Forest avaliam cada janela. O Ensemble combina os sinais desses modelos, e o Decision Engine aplica os critérios de decisão junto com os sinais das regras de segurança.

## Arquitetura e tecnologias

| Camada | Responsabilidade | Tecnologia |
| --- | --- | --- |
| Processamento | Leitura dos logs, janelas, modelos e decisão | Python 3.10, TensorFlow/Keras e scikit-learn |
| API e dados | Recebimento de arquivos, autenticação, gravação e consulta | FastAPI e PostgreSQL 16 |
| Painel | Consulta de resultados, histórico e investigação | Vue 3 e TypeScript |
| Ambiente local | Execução do painel, da API e do banco | Docker Compose |

O [guia de arquitetura](docs/architecture.md) detalha as responsabilidades e o fluxo entre as camadas.

## Instalação e execução local

O código-fonte e os arquivos de dependências estão nesta cópia. A logo original está incluída e o frontend passou nos typechecks, no Vitest e no build no GITHUB-REORG-07. A execução completa exige os artefatos oficiais de `current`, que ficam fora do repositório. A clonagem por si só é insuficiente para executar uma análise completa.

Quando esses arquivos estiverem disponíveis por meio autorizado:

1. Tenha Docker e Docker Compose disponíveis. Os Dockerfiles instalam as dependências declaradas para o painel e a API.
2. Use `.env.example` como referência para criar um `.env` local e privado. Configure as credenciais do PostgreSQL, o administrador inicial e o segredo de autenticação conforme o [guia de ambiente](docs/environment.md).
3. Disponibilize os artefatos confiáveis de `current` em `data/models/`, conforme o [guia de dados e modelos](docs/dados_modelos.md). O Compose disponibiliza essa pasta à API pelo volume local.
4. Na raiz do projeto, confira a configuração e suba os serviços.

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

Com as portas padrão, o painel fica em `http://localhost/`. Use `/api/ready` para conferir a prontidão da API, que depende do PostgreSQL e dos modelos. Consulte o [guia de implantação](docs/deploy_local_sinalyx.md) para verificar os serviços.

## Testes

Com o ambiente Python preparado, execute `python -m pytest` na raiz. No frontend, após instalar as dependências com `npm ci`, execute `npm run test:run`, `npm run test:typecheck` e `npm run typecheck`. Use `npm run build` para verificar a compilação. A suíte completa tem pré-requisitos adicionais, como PostgreSQL descartável e arquivos de avaliação. Consulte [testes e dependências deste recorte](docs/testing.md#testes-neste-recorte).

## Limitações conhecidas

- O Sinalyx apoia investigação e não bloqueia ataques automaticamente.
- Logs de firewall permitem observar padrões de rede. Por si só, eles não comprovam tentativas de senha incorreta.
- A avaliação de 355 janelas documenta um recorte histórico. Ela não mede generalização de forma independente. Veja o [estudo de ablação](docs/evidencias/ablation_tcc_reproducible_v1.md).
- A coleta direta contínua do pfSense e a distribuição Windows são experimentais. A distribuição Windows fica fora desta cópia. A inclusão de PostgreSQL gerenciado pelo instalador continua bloqueada.

## Documentação

- [Índice da documentação](docs/README.md)
- [Mapa do código](docs/source_code_walkthrough.md)
- [Contribuição](CONTRIBUTING.md) e [relatos de segurança](SECURITY.md)

## Informações acadêmicas

O Sinalyx começou como Trabalho de Conclusão de Curso desenvolvido em equipe. Conforme informado pelo proprietário do repositório, os direitos sobre o código da etapa acadêmica são compartilhados entre os integrantes.

O proprietário conduzirá individualmente a evolução pós-TCC, respeitando os direitos sobre os componentes reutilizados da etapa acadêmica. O objetivo dessa evolução é transformar o Sinalyx em um produto de segurança para ambientes empresariais. Esse objetivo faz parte do trabalho futuro.

A referência histórica da versão está em [VERSION](VERSION).

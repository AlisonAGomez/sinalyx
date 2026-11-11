# Documentação do Sinalyx

## Comece aqui

- [Arquitetura](architecture.md) descreve o caminho dos logs até o painel.
- [Mapa do código](source_code_walkthrough.md) indica os arquivos de entrada e as responsabilidades de cada parte.
- [Ambiente](environment.md) e [implantação local](deploy_local_sinalyx.md) descrevem as dependências e o fluxo Docker Compose.
- [Banco de dados](database.md), [segurança](security.md) e [testes](testing.md) orientam a manutenção.

## Processamento e interface

- [Dados e modelos](dados_modelos.md) e [versionamento dos perfis](model_versioning_and_fallback.md) registram o papel de `current` e a diferença entre perfis oficiais, experimentais e históricos.
- [Contribuição dos componentes](component_contributions_backend.md) explica o contrato e as evidências da integração.
- [Consulta de ameaças](consulta_ameacas.md) e [mapeamento ATT&CK](mitre_mapping.md) descrevem as referências exibidas na interface.
- [Frontend](../frontend/README.md), [testes do frontend](../frontend/tests/README.md) e [scripts](../scripts/README.md) orientam quem trabalha nesses módulos.

## Experimental

- [Coleta incremental](pfsense_live_worker.md) documenta o worker experimental.
## Resultados históricos

- [Validação consolidada](consolidated_validation_report.md), [ablação](evidencias/ablation_tcc_reproducible_v1.md) e [metodologia de contribuição](evidencias/component_contribution_methodology_v1.md) registram experimentos e resultados de seus recortes.
- [QA integrado da Fase 3](fase3_qa_integrado.md) registra a execução daquela fase.
## Compatibilidade legada

- [Pipelines históricos](../scripts/historical/pipelines/README.md) descreve as implementações preservadas para compatibilidade.

## Pendências desta cópia

O [README principal](../README.md) identifica os pré-requisitos externos para execução. Documentos históricos podem mencionar arquivos preservados na origem e ausentes desta cópia.

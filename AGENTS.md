# Orientações de manutenção

- Leia o [mapa do código](docs/source_code_walkthrough.md), o [guia de testes](docs/testing.md) e as instruções locais antes de editar.
- Confira o estado do Git e preserve alterações existentes.
- Use `current` como referência do comportamento oficial. Mudanças no parser, na ordem das 13 características, nos modelos, nos thresholds ou na decisão exigem escopo explícito e evidência de paridade ou de validação.
- Preserve os contratos da API, as permissões e a persistência quando a mudança estiver em outra camada. Aplique autorização no backend.
- Use dados sintéticos nos testes. Mantenha logs operacionais, artefatos locais, credenciais e evidências privadas fora do Git.
- Execute as verificações da área alterada e registre comandos, resultados e limitações. Veja [Contribuição](CONTRIBUTING.md).

## Fluxo Git

Siga o [guia de contribuição](CONTRIBUTING.md) e trate cada etapa como uma ação distinta.

- Prepare alterações locais dentro do escopo autorizado.
- Crie commits quando a tarefa autorizar essa etapa. Confira o conteúdo preparado antes de registrar o commit.
- Execute push somente com autorização explícita.
- Promova mudanças ao produto somente com autorização para essa etapa e após as validações aplicáveis.

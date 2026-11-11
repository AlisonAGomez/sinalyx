# Orientações de manutenção

- Leia o [mapa do código](docs/source_code_walkthrough.md), o [guia de testes](docs/testing.md) e as instruções locais antes de editar.
- Confira o estado do Git e preserve alterações existentes.
- Use `current` como referência do comportamento oficial. Mudanças no parser, na ordem das 13 características, nos modelos, nos thresholds ou na decisão exigem escopo explícito e evidência de paridade ou de validação.
- Preserve os contratos da API, as permissões e a persistência quando a mudança estiver em outra camada. Aplique autorização no backend.
- Use dados sintéticos nos testes. Mantenha logs operacionais, artefatos locais, credenciais e evidências privadas fora do Git.
- Execute as verificações da área alterada e registre comandos, resultados e limitações. Veja [Contribuição](CONTRIBUTING.md).

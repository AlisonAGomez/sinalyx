# Contribuição

Descreva o problema, o comportamento esperado e a menor alteração que resolve o caso. Quando o trabalho envolver ciência de dados, identifique o perfil, os artefatos e o recorte de avaliação.

## Fluxo de contribuição

- Crie uma branch por assunto e use um nome descritivo, como docs/guia-de-instalacao.
- Registre commits em português. Separe documentação, correções e funcionalidades em commits que descrevam cada mudança.
- Execute as verificações adequadas ao escopo. Registre resultados e pendências no pull request e solicite revisão antes do merge.
- Mudanças em componentes científicos oficiais exigem autorização explícita e validação conforme o guia de testes.
- Execute push somente com autorização explícita.

## Verificações locais

Use o [guia de ambiente](docs/environment.md) e o [guia de testes](docs/testing.md). Confira o estado do Git antes de editar.

- Python: execute os testes da área alterada com `python -m pytest`.
- Frontend: na pasta `frontend/`, execute `npm run test:run`, `npm run test:typecheck`, `npm run typecheck` e `npm run build`.
- Docker ou banco: valide a configuração e o fluxo alterado com dados sintéticos em ambiente isolado.
- Informe quais verificações foram executadas, quais dependiam de recursos externos e quais ficaram pendentes.

Use exemplos sintéticos ao relatar bugs. Encaminhe vulnerabilidades pelo [canal privado de segurança](SECURITY.md).

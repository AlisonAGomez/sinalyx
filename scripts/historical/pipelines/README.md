# Pipelines históricos do Sinalyx

Estes módulos são **HISTÓRICOS/LEGADOS**. Permanecem disponíveis para
reprodutibilidade e registro do TCC, mas não compõem o runtime oficial nem são
o fluxo recomendado de treinamento ou validação. Os caminhos antigos em
`src/pipelines/` são apenas wrappers de compatibilidade.

O `train.py` pode alterar artefatos do modelo `current`; por isso, seu uso
exige autorização explícita pela opção `--allow-legacy-current-overwrite`.
Novos experimentos e candidatos devem seguir a metodologia experimental atual.
O runtime oficial continua sendo `current`; Candidate v1 não foi promovido e
Candidate v2 não deve ser criado sem evidência experimental positiva.

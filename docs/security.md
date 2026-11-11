# Segurança

Status: **ATUAL**, controles do código após a Fase 2C. Este guia descreve o
comportamento implementado; não certifica um ambiente de produção.

## Acesso e credenciais

JWT HS256 assina tokens com expiração. Senhas usam PBKDF2-HMAC-SHA256, salt
aleatório e comparação em tempo constante. A API consulta a conta no PostgreSQL
e verifica estado ativo; operações administrativas exigem papel `admin`.
Proteções do frontend não substituem as dependências de autorização do backend.
Não há ownership entre usuário e análise; veja [banco](database.md).

Perfis compartilhados exigem segredo JWT não trivial; o fallback de
desenvolvimento é restrito aos perfis locais. Configure segredo aleatório forte
fora do Git. Não há refresh/revogação central de tokens implementados como
novos controles nesta fase. O seed pode reativar o administrador configurado.

## Upload e erros

`POST /analyze/pfsense` aceita `.log`. O limite padrão de corpo HTTP é
52.428.800 bytes (50 MiB), incluindo multipart, configurável por
`SINALYX_LIMITE_UPLOAD_BYTES`. A contagem independe de confiar em
`Content-Length`; a cópia também é limitada, em blocos de 64 KiB.
Vazio retorna 400, extensão não aceita 415 e excesso 413.

Arquivos temporários usam nomes gerados; a limpeza atinge os arquivos da própria
requisição. Resultados concluídos são preservados. Respostas e logs tratados
não publicam exceções brutas, SQL, senha ou payload.
O logger registra operação, identificador de erro, classe e localização.
A extensão aceita não equivale a antivírus ou garantia de conteúdo válido.

## Login e administração

O limitador de login conta tentativas por endereço do cliente observado pela
API: padrão de 10 tentativas por janela fixa de 60 s e até 4.096 clientes
ativos. Retorna 429 e `Retry-After`; não armazena email ou senha.
O limite de corpo é de 32 KiB por padrão nos métodos POST/PATCH de login e
administração cobertos pelo middleware; não é um limite global de toda a API.
Schemas limitam comprimento dos campos e erros de validação removem
`input`/`ctx` que poderiam repetir credenciais.

O estado é **por processo**, desaparece no restart e não é distribuído entre
workers. Atrás de proxy sem encaminhamento confiável, clientes podem compartilhar
a quota do proxy. Isso não equivale a proteção global contra ataques distribuídos.

## SSH/SFTP

O coletor usa `RejectPolicy`. Host desconhecido ou chave divergente é rejeitado.
Um arquivo explícito em `SINALYX_PFSENSE_KNOWN_HOSTS_PATH` é a fonte exclusiva
de confiança; sem ele, são carregadas as chaves conhecidas do usuário.
Verifique a fingerprint por canal confiável antes de preparar esse arquivo.
O modo antigo de aceitar host desconhecido é recusado; não há `AutoAddPolicy`.

Credenciais e caminhos de chave são configuração privada do servidor.
Uma execução manual do coletor realmente acessa o equipamento e escreve
estado local; não é teste somente de leitura.

## Ambiente e Docker

Use `.env.example` como referência, sem sobrescrever ambiente real.
Valores `VITE_*` entram no frontend e não podem conter secrets.
CORS deve listar as origens necessárias; CORS não é autorização.

Compose publica frontend/API/PostgreSQL em loopback por padrão. Overrides
locais podem ampliar essa exposição. A imagem API usa usuário sem privilégios
e recebe `data/` por volume; os contextos de build excluem ambientes reais,
dados, credenciais e caches. O frontend usa cópias explícitas de fontes.
Essas exclusões não removem secrets já rastreados pelo Git.

Nginx oculta a versão e aplica `nosniff`, `SAMEORIGIN` e
`strict-origin-when-cross-origin`, inclusive em assets.
Ele substitui `X-Forwarded-For` pelo cliente observado. A API Compose tem
`FORWARDED_ALLOW_IPS` vazio por padrão. Habilitar confiança exige proxy/endereço
controlado e validado; não usar confiança indiscriminada em qualquer remetente.

## Limitações e publicação

A [auditoria 2D.1](fase2d1_github_public_audit.md)
abrange conteúdo já exposto e histórico local; exclusões no Git não removem
material publicado anteriormente.

TLS depende do ambiente; não há TLS/HSTS configurados nesta stack.
CSP continua pendente. Docker integrado, proxy, headers HTTP reais, health e
PostgreSQL não foram validados neste ambiente. Não extrapolar testes unitários
de SSH ou login para conexão real com pfSense/banco.

Não publicar `.env`, senhas, tokens, chaves, known_hosts privados, dumps ou
backups. Logs, PCAPs, modelos, dados e screenshots exigem decisão individual.
Veja o [guia de testes](testing.md) e o [índice da documentação](README.md).
Os relatos das Fases 2B e 2C e o guia de publicação ficam no acervo histórico.

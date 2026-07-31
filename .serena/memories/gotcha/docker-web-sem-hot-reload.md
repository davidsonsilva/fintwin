# Gotcha: container `web` do docker-compose não reflete mudanças no código

O serviço `web` em `docker-compose.yml` usa `build: context: ./apps/web` **sem volume montado**
para o código-fonte. Isso significa que editar arquivos em `apps/web/src/**` no host **não**
atualiza o que o Next.js serve em `http://localhost:3000` — o container continua rodando o
build congelado de quando a imagem foi criada pela última vez.

**Sintoma**: usuário reporta "não mudou nada" mesmo após uma edição correta e visualmente
confirmada no código; `curl localhost:3000` responde 200 normalmente, mascarando o problema
(a página carrega, só que é a versão antiga).

**Como diagnosticar**: `netstat -ano | grep :3000` mostra o processo dono da porta; se for
`com.docker.backend.exe`/`wslrelay.exe` (não um `node`/`next` local), o app está rodando dentro
de um container Docker, não em `next dev` no host. Confirmar com `docker ps` — nome típico
`gemeo-financeiro-web-1`.

**Fix**: depois de qualquer mudança em `apps/web/`, rodar:
```
docker compose build web && docker compose up -d web
```
antes de qualquer verificação visual (browser automation ou pedir pro usuário olhar). Sem isso,
qualquer comparação visual é inútil e pode gerar rodadas de frustração do tipo "não mudou nada"
que na real são apenas cache de build, não erro de CSS/markup.

**Nota relacionada**: a automação de browser (`mcp__claude-in-chrome__computer` screenshot) tem
se mostrado instável neste ambiente (timeout "Script injection timed out" persistente mesmo após
esperas de 5s+). Quando isso acontece, não insistir mais que 3-4 tentativas — usar `Read` direto
no arquivo de imagem de referência (`imagens/screenshots/*.png`) para comparação visual em vez de
depender do browser ao vivo, e validar via lint/tsc/testes + inspeção de CSS existente.

Ver também `mem:planning/design-system-css-para-cva-e-meta-harness_20260727` (sessão de migração
CVA anterior, onde a mesma confusão sobre "o que está rodando de fato" já quase aconteceu).
# Skill visual-rebuild — construída e validada em caso real (2026-07-30)

Status: **implementada e validada de ponta a ponta**, incluindo um ciclo real de correção
(card "Distribuição das despesas") que convergiu para `approved`.

## O que é

Skill de projeto em `.claude/skills/visual-rebuild/` para reconstruir/validar componentes
contra uma imagem de referência. Substitui o ciclo de "olhar screenshot e adivinhar".

## Quando NÃO usar a skill (correção do Davidson, 2026-07-30)

Em ajustes visuais que ele mesmo pediu a partir do que está vendo na tela
("as porcentagens não estão alinhadas", "as cores estão sem vida"), ele **valida olhando
o resultado** — não quer o loop capture/compare. Nesses casos: aplicar a mudança, rebuildar
o container `web` e devolver a tela. A skill é para reconstrução contra mockup e para
regressão, não para toda mexida de CSS.

## Objetivo da comparação (correção do Davidson, 2026-07-30)

**Não é igualar tamanhos.** É **layout, cores e tipografia**. A referência quase nunca tem
a mesma largura do render, e isso não é defeito.

Por padrão: omitir `canvas` e omitir `bounds` no `reference-spec.json`. Registrar
dimensões de mockup em escala diferente gera findings `high` falsos que afogam o que
importa. `bounds` só como exceção, quando as escalas forem comprovadamente iguais.

## Decisão de design central: a comparação é assimétrica

Não usar visão para avaliar o render — o DOM já tem a verdade exata (`getBoundingClientRect`
+ `getComputedStyle`). Visão só serve para ler a imagem de referência. A proposta original
(`imagens/proposta-skill.md`) tratava os dois lados simetricamente; está errado.

## Decisões de infra

1. **Loop de dev**: `next dev` no host na porta 3001 (HMR ~2s); API no Docker.
   O container `web` não tem bind mount, então cada correção exigiria rebuild de 40-90s.
   **Mas o Davidson olha a porta 3000 (Docker)** — sempre `docker compose build web &&
   up -d web` antes de dizer que está pronto.
2. **Pré-requisito descoberto**: a API só liberava CORS para `localhost:3000`. Foi
   necessário tornar as origens configuráveis em `apps/api/src/interfaces/http/main.py`
   (`CORS_ALLOW_ORIGINS`, default inclui 3000 e 3001) e rebuildar o container `api`.
3. **Comparação**: DOM estrutural + pixelmatch só entre renders próprios (regressão).
   Instalados `pixelmatch` + `pngjs` como devDependency em `apps/web`.

## Validações feitas

**Teste sintético** (6 deviações plantadas): todas detectadas com delta exato, **zero
falsos positivos** nos 2 elementos deixados corretos. Referência perfeita → `matchRate 1`,
0 findings. Determinismo: 2 capturas independentes = **0 pixels diferentes** em 147.771.

**Caso real** (card de despesas vs mockup): 7 findings → 0 em 2 iterações, `approved` em
1920 e 1440.

## Limitação encontrada NO USO (importante)

A comparação estrutural **aprovou um render visualmente quebrado**: nomes truncados em
"Mo...", "Ali...". O diff numérico não vê ellipsis nem overflow.

Corrigido: `capture.js` agora detecta `scrollWidth > clientWidth` e `compare.js` emite
finding `layout/high` de truncamento, **independente da referência**.

Lição maior (Davidson: "essa skill não ficou boa não"): um `reference-spec.json` pobre faz
`approved` significar "não havia quase nada para checar". A raiz foi **estimar a referência
a olho** em vez de medir — exatamente o que a skill existe para evitar. Existe
`scripts/measure-reference.js` para extrair números do PNG; use-o.

## Viewport importa

A largura do card muda com a grade: **1920 → 530px; 1440 → 368px**. Um layout que cabe num
não cabe no outro. Validar em mais de um viewport. Preferir **container queries**
(`container: ft-card / inline-size` em `.ft-analytics-card`) a media queries — o que manda
é a largura do card, não a da tela.

## Gotchas

- `.ft-card` NÃO existe: o `Card` foi migrado para CVA (Tailwind puro). Âncoras utilizáveis
  são as classes de `design-system.css` (`.ft-analytics-card`, `.ft-expense-layout`...).
  Não há `data-testid` no projeto.
- **Git Bash exige `MSYS_NO_PATHCONV=1`**, senão `--route "/dashboard/x"` vira
  `C:/Program Files/Git/dashboard/x`.
- Rodar os scripts **a partir de `apps/web`**. `pixelmatch` v7 é ESM sem campo `exports`,
  então `import()` ignora `NODE_PATH`; ambos os scripts resolvem deps por `createRequire`
  sobre roots conhecidos.
- `.visual/` está no `.gitignore`.
- profileId determinístico: `/onboarding` → "Carregar dados de demonstração".
- profileId de demo em uso: `d5b17141-43c8-4758-91c7-d516532d475a`.

## Estado final do card "Distribuição das despesas" (aprovado pelo Davidson)

- **Legenda em 3 colunas**: o grid vive em `.ft-chart-legend`
  (`8px minmax(0,1fr) 48px auto`) e `.ft-legend-item` é `display: contents`.
  Motivo: com um grid por linha, a coluna `auto` do valor é dimensionada isoladamente e
  "950,00" desalinha de "2.200,00" — as colunas só *parecem* alinhadas quando os números
  têm o mesmo comprimento. Nome à esquerda com **peso 400** (600 comia largura demais),
  % centralizada, valor à direita.
- **Donut com degradê**: um `linearGradient` por fatia com o eixo correndo **ao longo do
  arco** (tangente ao raio médio, `(sin θ, cos θ)`), não ao longo do raio — cor cheia no
  meio da fatia, escurecida 42% (`color-mix`) nas duas pontas. O ângulo médio é calculado
  descontando o `paddingAngle` (constante `PADDING_ANGLE` compartilhada com o `<Pie>`),
  senão o degradê fica torto em relação ao setor real.
- `useId()` devolve delimitadores (`:r0:` / `«r0»`) que **não sobrevivem a `url(#...)`** —
  precisa sanitizar antes de virar id de gradiente.
- Raio do donut é limitado pela **menor** dimensão do container: altura manda mais que
  largura. Aumentar só a coluna não faz o donut crescer.
- **Divergência aceita**: a referência não tem divisória sob o header; a nossa tem. Veio do
  item 9 do pente fino (global, `.ft-card-header { border-bottom }`). Davidson: "foi um
  ajuste de layout que o agente fez errado mas eu acabei deixando" — fica como está.

## Estado dos testes

`npx vitest run`: 32 passam, 2 falham em `AutonomyPanel.test.tsx`. **Falha pré-existente**,
verificada: o HEAD do `AutonomyPanel.tsx` contém o texto "aplicável", a cópia de trabalho
não — removido numa sessão anterior sem atualizar o teste. Não relacionado à skill.

`npx tsc --noEmit`: 3 erros pré-existentes em `ProfileStep.tsx` e `ResourceStepForm.tsx`
(resolver react-hook-form/zod). Não relacionados.

Contexto anterior: `mem:planning/polish-dashboard-11-itens_20260729`

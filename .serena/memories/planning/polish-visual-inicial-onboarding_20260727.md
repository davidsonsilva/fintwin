# Plano: Aplicar o design system --ft-* na Tela Inicial e no Onboarding

## 📅 Criado em: 2026-07-27

## 🎯 Status: ⚠️ EM REVISÃO — 2ª rodada de correções aplicada, aguardando avaliação visual do usuário

---

## 📋 Resumo Executivo

Rodada 1 (implementação inicial + fix de overlap no stepper) foi avaliada pelo usuário como "simples demais, não bate com a imagem de referência". Usuário forneceu 2 fontes de extração mais precisas: `imagens/Design.md` (extração textual detalhada) e `imagens/desing.md.json` (JSON estruturado com valores hex exatos, spacing, radius, efeitos, e o mapeamento exato ícone↔item de navegação). Rodada 2 usa o JSON como fonte de verdade (mais preciso que o Design.md textual) para corrigir cores, efeitos e a lacuna estrutural mais visível: falta de chip de ícone por etapa no onboarding.

## ❌ Correções do Usuário

### Correção 1: Overlap no stepper (rodada 1, resolvida)
Ver detalhes na versão anterior desta memória — `white-space: nowrap` causava sobreposição de labels longos em colunas estreitas.

### Correção 2: Visual "simples demais", não bate com a imagem de referência
- **O que o usuário ensinou**: eu presumi que "já existe um design-system.css, então está tudo coberto" — mas o arquivo era uma extração inicial menos precisa. O usuário extraiu de novo com mais detalhe (`Design.md` + `desing.md.json`), fornecendo valores hex exatos, efeitos (glow, backdrop-blur/glassmorphism), e principalmente o **mapeamento explícito ícone→cada etapa do onboarding** que eu não tinha usado.
- **Causa raiz identificada por comparação estruturada**: (a) paleta de acentos incompleta (faltavam azul/rosa/laranja como tokens distintos), (b) nenhum efeito de glassmorphism/glow aplicado (`backdrop-filter` ausente), (c) **o maior gap**: o stepper do onboarding não tinha chip de ícone por etapa, só barra de progresso + texto — mesmo o design system já tendo o padrão de "ícone sempre em chip" usado no Dashboard, nunca foi trazido para o onboarding.
- **Achado extra na 2ª leitura do CSS**: já existia uma classe `.ft-onboarding` (max-width 1180px) definida em `design-system.css` desde a extração original, mas **nunca foi usada** — `OnboardingWizard.tsx` usava `max-w-2xl` (672px) do Tailwind, quase metade da largura pretendida. Isso por si só já fazia o layout parecer mais "encolhido"/simples do que o design pretendia.
- **Como aplicar no futuro**: ao herdar um design-system.css já existente de sessão anterior, não presumir que todas as classes definidas nele já foram aplicadas nos componentes — grepar por cada classe candidata (`.ft-onboarding`, `.ft-step-icon` etc.) e confirmar uso real antes de assumir cobertura completa.

## ✅ Decisões Tomadas (rodada 2)
1. Usar `imagens/desing.md.json` como fonte primária de valores exatos (hex, radius, spacing, efeitos) — mais preciso que o `Design.md` textual, que tinha aproximações ("~#9AA3B2").
2. Atualizar os tokens `--ft-*` existentes com os valores exatos do JSON, mantendo os MESMOS nomes de variável (não renomear) — minimiza risco, já que todo o CSS/componentes existentes referenciam essas variáveis.
3. Adicionar 3 tokens de acento novos (`--ft-blue`, `--ft-pink`, `--ft-orange` + soft variants) para cobrir a paleta completa do JSON, mesmo sem uso imediato fora do onboarding — forward-compatible para quando o Dashboard for revisitado.
4. Adicionar glassmorphism sutil (`backdrop-filter: blur(14px)`) em `.ft-card`.
5. Criar `.ft-step-icon` (chip 32px, estado padrão/muted e is-active/is-complete/primary) e usá-lo no `OnboardingWizard.tsx`, com ícones exatos do JSON (`UserCircle`, `Wallet`, `Banknote`, `ClipboardList`, `Calculator`, `Target`, `Calendar`, `ClipboardCheck` — na mesma ordem que `STEP_LABELS`, confirmado batendo 1:1 com os títulos reais de `resourceConfigs.ts`).
6. Trocar o wrapper do `OnboardingWizard` de `max-w-2xl` (672px, Tailwind) para a classe `.ft-onboarding` (1180px) já definida mas nunca usada.

## 🔧 Implementação Real (rodada 2)

### Tokens (`design-system.css :root`)
- Backgrounds/texto/bordas atualizados com os hex exatos do JSON (`--ft-bg-page: #03111f`, `--ft-bg-surface: #0c1a29`, `--ft-text-primary: #f7f9fc`, etc.).
- `--ft-primary` (verde-menta) `#22e6b1`→`#31e6ae`, `--ft-purple` `#9a5cff`→`#a76af7`, `--ft-warning` `#ffb020`→`#ffb815`, `--ft-danger` `#ff525d`→`#f24c5f`, `--ft-secondary` (ciano) `#44d8f3`→`#2dddeb`.
- Novos: `--ft-blue`/`--ft-pink`/`--ft-orange` (+soft), `--ft-divider`, `--ft-backdrop-blur`.
- `--ft-radius-sm/md/lg`: 10/14/18px → 8/12/16px (valores exatos do JSON).
- `--ft-shadow-primary`/`--ft-shadow-purple`: ajustados para bater com `glowGreen`/`glowPurple` do JSON.

### `.ft-card`
- `backdrop-filter: blur(14px)` (+ prefixo `-webkit-`) adicionado — efeito de glassmorphism sutil que o JSON pede (`visualStyle: ["glassmorphism sutil", ...]`) e que não existia antes.

### `.ft-stepper` / novo `.ft-step-icon`
- Chip 32px por etapa, cor/fundo mudam com o estado (`is-active`/`is-complete` → cor primária + fundo translúcido + glow; padrão → cinza neutro).

### `OnboardingWizard.tsx`
- Wrapper trocado de `max-w-2xl` (Tailwind) para `.ft-onboarding` (1180px, já definido no CSS mas nunca usado).
- `STEP_ICONS` array com os 8 ícones do lucide-react, na ordem exata do JSON (`sidebar.navigation`), confirmada batendo com os títulos reais de `resourceConfigs.ts`.
- Cada `<li>` do stepper agora renderiza `<span className="ft-step-icon"><Icon size={16} /></span>` antes da barra de progresso.

### Validação
- `npm test`: 34/34 passando.
- `npx tsc --noEmit`: 5 erros, mesmos pré-existentes.
- Container `web` rebuildado.

## 🚦 Próximo Passo
**Aguardando avaliação visual do usuário** via `http://localhost:3000` e `http://localhost:3000/onboarding` — 2ª rodada, com paleta/efeitos/ícones mais fiéis ao JSON de referência.

# Arquitetura — FinTwin AI

Este documento descreve como o sistema é organizado e por quê. Para regras de
domínio e critérios de aceitação, ver [`Spec.md`](Spec.md); este documento é
sobre estrutura de código e fluxo de dados, não sobre requisitos de produto.

## Princípio central

O motor financeiro é **determinístico e auditável**: toda saída numérica
(saldo, autonomia, fragilidade, resultado de simulação) vem de um caso de uso
do domínio, nunca de um modelo de linguagem. O agente conversacional é uma
camada de leitura/proposta sobre esse motor — ele nunca calcula números por
conta própria e nunca persiste uma mudança sem confirmação explícita do
usuário.

## Camadas (back-end, Clean Architecture)

```
apps/api/src/
├── domain/           regras financeiras puras — sem FastAPI, sem SQLAlchemy
├── application/       casos de uso: orquestram domínio + repositórios
├── infrastructure/    persistência (SQLAlchemy), repositórios, cliente LLM
└── interfaces/http/   routers FastAPI, schemas Pydantic (borda HTTP)
```

A dependência aponta sempre para dentro: `interfaces` → `application` →
`domain`; `domain` não importa nada das camadas externas. Isso permite testar
regra financeira sem banco e sem HTTP.

### `domain/` — um módulo por conceito financeiro

| Módulo | Responsabilidade |
|---|---|
| `financial_profile/` | Perfil, contas, rendas, obrigações, dívidas, metas |
| `cashflow/` | Fluxo de caixa mensal a partir dos dados do perfil |
| `projection/` | Projeção de saldo/fluxo para os próximos meses |
| `autonomy/` | Autonomia financeira básica e ajustada (ativos vs. despesas essenciais) |
| `fragility/` | Detecção de fragilidades com evidência associada (não só rótulo) |
| `decisions/` | Simulador de decisões — comparação antes/depois de um cenário |
| `preventive_plans/` | Geração de planos preventivos a partir de fragilidades |
| `opportunity/` | Motor de oportunidades levantadas pelo agente, com regras de suporte |
| `recommendations/` | Registro de recomendações e seu ciclo de vida |
| `balance_history/` | Histórico de saldos (snapshots) |
| `obligations/` | Regras específicas de obrigações recorrentes |
| `agent/` | Contratos de domínio usados pelo agente (não o cliente LLM em si) |

Todo valor monetário usa `Decimal` — nunca `float` — para evitar erro de
arredondamento em cálculo financeiro.

### `application/use_cases/`

Um arquivo por área (`dashboard_use_cases.py`, `simulation_use_cases.py`,
`fragility_use_cases.py`, etc.). Cada caso de uso recebe repositórios via
injeção de dependência, chama o domínio, e devolve DTOs — nunca modelos do
SQLAlchemy nem `Decimal` bruto; a formatação final para exibição acontece na
borda (router/serializer), não dentro do caso de uso.

`agent_use_cases.py` é o maior arquivo do backend: monta as ferramentas
expostas ao LLM, valida o `tool_input` recebido e decide quais tools podem
gravar dado (nenhuma grava direto — ver seção "Agente conversacional").

### `infrastructure/`

- `persistence/`: engine SQLAlchemy, sessão, modelos ORM, Alembic
  (`apps/api/alembic/versions/` tem uma migração por Vertical Slice).
- `repositories/`: implementação concreta dos repositórios que o domínio e
  os casos de uso consomem por interface.
- `llm/anthropic_client.py`: wrapper fino sobre a API de mensagens da
  Anthropic (chamada única, não-streaming, com tool calling nativo). Lê
  `ANTHROPIC_API_KEY` de variável de ambiente — nunca hardcoded.
- `ai/`: utilidades de suporte ao agente (fora do cliente HTTP em si).

### `interfaces/http/`

Um router por recurso (`profile`, `account`, `income`, `obligation`, `debt`,
`goal`, `event`, `dashboard`, `fragility`, `simulation`, `preventive_plan`,
`recommendation`, `agent`, `demo`). `main.py` monta a `FastAPI app`, CORS e
inclui todos os routers. `rate_limit.py` é um limitador em memória, por IP,
usado apenas no endpoint de mensagem do agente (mitigação simples de abuso
do endpoint pago da Anthropic — ver seção de segurança no README).

## Agente conversacional

O agente não é um chatbot financeiro genérico: ele é uma interface de
linguagem natural para o mesmo motor determinístico que alimenta o
dashboard. Fluxo:

1. Usuário manda mensagem → `POST /{profile_id}/agent/messages`.
2. `AnthropicAgentClient` chama a API da Anthropic com tool calling.
3. Tools disponíveis (`agent_use_cases.py`):
   - `get_dashboard_summary`, `get_autonomy`, `list_fragilities` — **leitura**,
     delegam para os mesmos casos de uso que o dashboard usa (garante que a
     resposta do agente bate com o que a UI mostra).
   - `propose_simulation` — monta uma proposta de simulação, mas **não
     persiste nada**.
   - `raise_opportunity` — registra uma oportunidade levantada na conversa
     para revisão posterior, sujeita a regras de suporte (não deixa o modelo
     afirmar juízo de valor sem evidência).
4. Qualquer ação que grave dado passa por confirmação humana explícita:
   `POST /{profile_id}/agent/actions/{action_id}/confirm`. O agente propõe,
   o usuário confirma — nunca o inverso.

Essa separação leitura/proposta vs. confirmação humana é a principal defesa
contra prompt injection: mesmo que a conversa seja manipulada, não há tool
capaz de gravar dado financeiro sem uma ação humana fora do LLM.

## Front-end

```
apps/web/src/
├── app/                 rotas do Next.js (App Router) + design-system.css
└── features/
    ├── onboarding/
    ├── dashboard/
    ├── fragility/
    ├── simulation/
    ├── preventive-plans/
    ├── recommendations/
    └── agent/
```

Next.js 16 (App Router), TypeScript, Tailwind v4, shadcn/ui (Base UI),
Recharts, TanStack Query. O front-end **não contém regra financeira** — cada
feature busca dado já calculado da API e só exibe. O design system é próprio
do projeto (tokens `--ft-*`, dark-only), não segue Material Design 3 — decisão
registrada para este produto especificamente.

## Banco de dados

PostgreSQL, uma migração Alembic por Vertical Slice
(`apps/api/alembic/versions/`), nunca alteração retroativa de migração já
aplicada. Sessão isolada por request via dependência do FastAPI.

## O que este documento não cobre

Regras de negócio (o que conta como fragilidade, como autonomia é calculada,
critérios de aceitação por Vertical Slice) estão em
[`Spec.md`](Spec.md) — este documento é só sobre organização de código.

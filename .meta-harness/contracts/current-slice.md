# Slice atual: VS-09 — Agente conversacional

> Gerado a partir do plano aprovado em `planning/vs09-agente-conversacional_20260725` (Serena, sessão de 2026-07-26).

## Contexto

VS-01–08 entregaram persistência, onboarding, dashboard, projeção (VS-04), autonomia (VS-05), radar de fragilidade (VS-06), simulador de decisões (VS-07) e planos preventivos (VS-08). A VS-09 (Spec seções 6.8, 7, 18.11, 25) entrega o agente conversacional: interpreta linguagem natural via API da Anthropic (tool calling nativo, sem LangChain/LangGraph), mapeia intenções para os casos de uso já existentes e explica resultados — nunca calculando valores por conta própria.

Escopo desta primeira entrega, deliberadamente reduzido: explicar indicadores/fragilidades, criar simulação estruturada (com confirmação explícita), pedir dados ausentes, histórico básico. Comparar cenários, gerar plano preventivo via agente e navegação ficam para uma iteração seguinte.

Nenhuma mudança foi necessária no motor de decisões (VS-07) — o agente reaproveita `DECISION_TYPES` e `validate_decision_parameters` sem duplicar regra de validação.

## Escopo entregue

### Domínio (`apps/api/src/domain/agent/`)
- `entities.py::Conversation`, `AgentMessage` — novo módulo.
- `repository.py::ConversationRepository`, `AgentMessageRepository` (Protocol).
- `shared/enums.py::MessageRole` (USER/ASSISTANT) — novo enum.

### Persistência (5ª e 6ª tabelas desde a VS-02)
- `ConversationModel` (`conversations`), `AgentMessageModel` (`agent_messages`), migração Alembic `e4a1f7c9d3b2`.
- `SqlAlchemyConversationRepository`, `SqlAlchemyAgentMessageRepository`.

### Infraestrutura LLM (`apps/api/src/infrastructure/llm/`)
- `anthropic_client.py::AnthropicAgentClient` — wrapper fino sobre a API da Anthropic; `system` e mensagens do usuário sempre separados (Spec seção 25); modelo via env var `AGENT_MODEL`, default `claude-haiku-4-5-20251001`.

### Aplicação (`apps/api/src/application/use_cases/agent_use_cases.py`)
- `SendAgentMessageUseCase` — orquestra histórico → tools allowlisted (`get_dashboard_summary`, `get_autonomy`, `list_fragilities`, `propose_simulation`) → Anthropic → persiste mensagens. A tool `propose_simulation` NUNCA persiste — apenas valida via `validate_decision_parameters` (reuso VS-07) e empacota os parâmetros como `pending_action`.
- `ConfirmPendingActionUseCase` — revalida os parâmetros e SÓ ENTÃO chama `SimulateDecisionUseCase` (já existente, persiste). Este caminho NUNCA volta a chamar o LLM (garante o critério de aceite #18 do MVP também na escrita). Idempotente: confirmar a mesma ação duas vezes levanta `PendingActionAlreadyConfirmedError`.

### Interface HTTP (Spec seção 18.11, literal + 1 adição mínima documentada)
- `POST /api/v1/profiles/{profile_id}/agent/messages` — contrato seção 19 completo (`data`/`evidence`/`assumptions`/`limitations`/`generated_at`/`version`).
- `POST /api/v1/profiles/{profile_id}/agent/actions/{action_id}/confirm` — retorna `SimulationResponse` (schema já existente da VS-07).
- `GET /api/v1/profiles/{profile_id}/agent/conversations/{conversation_id}/messages` — adição além do literal da Spec, necessária para "histórico básico" (entrega explícita da VS-09).

### Front-end (`apps/web`)
- `src/features/agent/`: `types.ts`, `api.ts`, `AgentPanel.tsx`, `PendingActionCard.tsx`.
- Terceiro trilho no AppShell (`dashboard/[profileId]/layout.tsx`): sidebar | conteúdo | painel do agente, painel lateral persistente usando tokens `--ft-*` já existentes.
- Removido o teaser desativado "IA FinTwin (em breve)" do `Sidebar.tsx` — substituído pelo painel real.
- Invalidação de queries (`dashboard-summary`, `autonomy`, `fragilities`, `simulations`) conforme `components_to_update` retornado pela API.

## Fora de escopo (não implementado nesta slice)

- Comparar cenários via agente, gerar plano preventivo via agente, navegação guiada pelo agente (adiados para iteração seguinte, decisão registrada no plano).
- RAG, banco vetorial, embeddings, LangGraph, LangChain (fora de escopo explícito da Spec seção 26).
- Execução autônoma de qualquer ação sem confirmação explícita do usuário.

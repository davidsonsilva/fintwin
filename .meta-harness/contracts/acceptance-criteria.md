# Critérios de aceitação: VS-09 — Agente conversacional

> Extraído da seção "Critérios de Aceite" do plano aprovado em `planning/vs09-agente-conversacional_20260725`.

1. **Testes automatizados**: `pytest` cobre `agent_use_cases.py` (tools de leitura, `propose_simulation` nunca persiste, `ConfirmPendingActionUseCase` persiste e é idempotente, allowlist rejeita tool desconhecida) e os endpoints HTTP do agente — suíte completa sem regressões (179 testes, 168 preexistentes + 11 novos).
2. **Migração aplicada**: `alembic upgrade head` cria as tabelas `conversations` e `agent_messages`; `downgrade()` remove o enum `messagerole` do Postgres (`drop(checkfirst=True)`, lição da VS-08).
3. **Testes de frontend**: `npx vitest run` cobre `AgentPanel` com API mockada (envio de mensagem, pergunta por dado ausente, proposta pendente e confirmação) — requisito explícito da Spec seção 27.2.
4. **Nenhum número inventado**: toda resposta do agente com valor numérico vem de uma tool call real (`evidence` rastreável); a tool `propose_simulation` nunca persiste nada; a confirmação (`ConfirmPendingActionUseCase`) nunca volta a chamar o LLM.
5. **Allowlist de ferramentas**: qualquer tool fora de `{get_dashboard_summary, get_autonomy, list_fragilities, propose_simulation}` é rejeitada antes de qualquer execução (Spec seção 25).
6. **Separação sistema/usuário**: `system` prompt e mensagem do usuário são sempre parâmetros separados na chamada à API da Anthropic, nunca concatenados.
7. **Pureza de domínio**: `src/domain/agent/` sem imports de framework (`fastapi`, `sqlalchemy`, `anthropic`, `next`).
8. **Sem scope creep**: nenhuma capacidade de "comparar cenários", "gerar plano preventivo via agente" ou "navegar o usuário" implementada nesta slice (adiadas por decisão registrada no plano); nenhuma mudança no motor de decisões da VS-07.
9. **Endpoints da Spec seção 18.11 + 1 adição documentada**: `POST /profiles/{profile_id}/agent/messages` (contrato seção 19 completo), `POST /profiles/{profile_id}/agent/actions/{action_id}/confirm`, e `GET /profiles/{profile_id}/agent/conversations/{conversation_id}/messages` (adição mínima para histórico básico, documentada em `current-slice.md`).
10. **Fluxo manual real**: via `docker compose`, com o perfil de demonstração, enviar uma mensagem ao agente pedindo o saldo (tool de leitura), propor uma simulação estruturada, confirmar e verificar que a simulação foi persistida em `/simulations`.

# Plano: VS-09 — Agente Conversacional

## 📅 Criado em: 2026-07-25

## 🎯 Status: PLANEJADO (aguardando aprovação)

---

## 📋 Resumo Executivo

A VS-09 entrega a última slice de feature do FinTwin AI antes da consolidação do MVP (VS-10): um agente conversacional que interpreta linguagem natural, mapeia para os casos de uso já existentes (motor determinístico das VS-01 a VS-08) e explica resultados — nunca calculando valores por conta própria. O agente usa a API da Anthropic diretamente (tool calling nativo, sem LangChain/LangGraph, que estão banidos pela Spec), roda em Claude Haiku 4.5 em produção, e vive num painel lateral persistente no AppShell.

O ponto mais delicado da slice é a regra de segurança da Spec (seção 25): "aprovação explícita para alterar dados persistidos". Como `SimulateDecisionUseCase` (VS-07) já persiste ao executar, sem passo de preview, resolvemos isso com um fluxo de duas chamadas — o agente propõe (não persiste) e uma segunda chamada, determinística e sem LLM, confirma e persiste.

Escopo da primeira entrega deliberadamente reduzido: explicar indicadores/fragilidades, criar simulação estruturada (com confirmação), pedir dados ausentes, histórico básico. Comparar cenários, gerar plano preventivo via agente e navegação ficam para uma iteração seguinte.

---

## 🎯 Objetivo

Entregar a camada de interação inteligente da Spec (seção 6.8): o agente "explica resultados produzidos por um motor matemático confiável", sem nunca inventar números, sem substituir o dashboard, e sem persistir nada sem confirmação explícita do usuário.

---

## 🏗️ Arquitetura / Abordagem Escolhida

### Solução Final

Fluxo obrigatório da Spec (seção 7): Usuário → interface conversacional → interpretador de intenção (Claude + tool calling) → schema estruturado validado → caso de uso → motor financeiro determinístico → resultado estruturado → agente explica → dashboard atualiza.

```
POST /profiles/{id}/agent/messages
  → Claude Haiku 4.5 interpreta intenção, chama tools allowlisted
  → tools de leitura (get_dashboard_summary, get_autonomy, list_fragilities) executam de verdade via casos de uso existentes
  → tool propose_simulation NÃO persiste: valida via validate_decision_parameters (reuso VS-07) e empacota os parâmetros como pending_action
  → se faltar campo obrigatório: vira pending_questions na resposta (nunca um valor inventado)
  → resposta segue contrato da seção 19 (data/evidence/assumptions/limitations/generated_at/version)

[usuário revisa o pending_action na UI e confirma explicitamente]

POST /profiles/{id}/agent/actions/{action_id}/confirm
  → revalida os parâmetros (defesa em profundidade) e SÓ ENTÃO chama SimulateDecisionUseCase (persiste)
  → este endpoint NUNCA chama o LLM de novo — é 100% determinístico
```

### Camadas (seguindo a arquitetura em vigor: domain/application/infrastructure/interfaces)

- **domain/agent/entities.py**: `Conversation`, `AgentMessage` (role: `MessageRole` novo enum em `shared/enums.py`, seguindo o padrão de `PlanStatus`/`Severity`).
- **domain/agent/repository.py**: `ConversationRepository`, `AgentMessageRepository` (Protocol, mesmo padrão dos demais repos).
- **application/use_cases/agent_use_cases.py**: `SendAgentMessageUseCase` (orquestra histórico → tools → Anthropic → persiste mensagens), `ConfirmPendingActionUseCase`.
- **infrastructure/llm/anthropic_client.py**: wrapper fino sobre a API da Anthropic; `system` param sempre separado do texto do usuário (seção 25 — "separação entre mensagem do usuário e instruções de sistema"); modelo via env var `AGENT_MODEL`, default `claude-haiku-4-5-20251001`.
- **interfaces/http/routers/agent.py** + **schemas/agent.py**: os 3 endpoints (ver abaixo).
- **Persistência**: 2 tabelas novas (`conversations`, `agent_messages`), migração Alembic (padrão já repetido em toda slice desde a VS-02).

### Tools (allowlist explícita, seção 25 — nenhuma tool fora desta lista pode ser chamada)

| Tool | Efeito | Caso de uso reaproveitado |
|---|---|---|
| `get_dashboard_summary` | leitura | `GetDashboardSummaryUseCase` |
| `get_autonomy` | leitura | `GetAutonomyUseCase` |
| `list_fragilities` | leitura | `ListFragilitiesUseCase` |
| `propose_simulation` | NÃO persiste — valida e empacota | `validate_decision_parameters` (VS-07), nunca chama `SimulateDecisionUseCase` diretamente |

Nenhum schema de intenção novo: `criar simulação estruturada` mapeia direto para os `DECISION_TYPES` já existentes em `decisions/engine.py` (CASH_PURCHASE, FINANCING, LOAN, etc.) — zero regra de validação reinventada.

### Frontend

- `AgentPanel.tsx` novo: terceiro trilho no `dashboard/[profileId]/layout.tsx` (sidebar de navegação | conteúdo | painel do agente), usando os tokens `--ft-*` já existentes (design system da sessão de redesign de 2026-07-24).
- `features/agent/` (types.ts, api.ts, AgentPanel.tsx, PendingActionCard.tsx com botões Confirmar/Cancelar).
- Após confirmação: invalidar queries do TanStack Query conforme `components_to_update` retornado pela API (`dashboard_summary`, `autonomy`, `fragilities`).

---

## ✅ Decisões Tomadas

### Decisão 1: LLM do agente = Anthropic API direto (Claude)
- **O quê**: chamada direta à API da Anthropic, tool calling nativo, sem LangChain/LangGraph.
- **Por quê**: já é o ecossistema do projeto (CascadeFlow usa Claude); LangChain/LangGraph estão explicitamente banidos na Spec (seção 26).
- **Alternativas rejeitadas**: OpenAI API direto; adiar a escolha do provedor.

### Decisão 2: Escopo da primeira entrega = subconjunto essencial
- **O quê**: explicar indicadores/fragilidades + criar simulação estruturada (com confirmação) + pedir dados ausentes + histórico básico.
- **Adiado**: comparar cenários, gerar plano preventivo via agente, navegar o usuário.
- **Por quê**: reduz risco, valida o padrão de tool-calling antes de expandir para mais ferramentas.

### Decisão 3: UI do agente = painel lateral persistente
- **O quê**: painel de chat sempre visível ao lado do conteúdo principal.
- **Por quê**: Spec permite painel lateral OU drawer; usuário priorizou visibilidade constante sobre economia de espaço horizontal.
- **Alternativa rejeitada**: drawer acessível globalmente.

### Decisão 4: Aprovação explícita antes de persistir = fluxo de 2 chamadas (propor → confirmar)
- **O quê**: o agente propõe (tool `propose_simulation`, não persiste); uma segunda chamada HTTP separada, sem LLM, confirma e chama o caso de uso real que persiste.
- **Por quê**: satisfaz a regra de segurança da seção 25 sem precisar modificar `SimulateDecisionUseCase` (usado também pelo formulário manual da VS-07, que continua funcionando como está).
- **Alternativa rejeitada**: criar um caminho de "preview" não-persistente separado no motor — mais engenharia, desnecessário para o escopo desta slice.
- **Implicação crítica de segurança**: o endpoint de confirmação NUNCA deve voltar a chamar o LLM — é a garantia central de que "o agente não calcula valores por conta própria" (critério de aceite #18 do MVP) também vale no caminho de persistência, não só na explicação.

### Decisão 5: Modelo Claude em produção = Claude Haiku 4.5
- **O quê**: o agente conversacional do FinTwin AI (produto) roda em Claude Haiku 4.5, configurável via env var `AGENT_MODEL`.
- **Por quê**: o agente só interpreta intenção/schema e explica resultados já calculados pelo motor — não faz raciocínio financeiro complexo por conta própria.
- **Nota crítica**: esta decisão é INDEPENDENTE da política do CascadeFlow (`cascade-policy.json`), que rege apenas o Claude Code como assistente de desenvolvimento deste projeto — não confundir os dois contextos durante a implementação.
- **Alternativas rejeitadas**: Claude Sonnet 5; adiar a escolha via env var sem default definido.

---

## ❌ Lições das Correções

Nenhuma correção do usuário durante esta discussão — todas as propostas técnicas foram aprovadas sem ajuste. As "lições" relevantes para esta slice vêm de slices anteriores e já estão em `project_overview`:
- Cálculos financeiros parcelados usam `ROUND_UP`, nunca `ROUND_HALF_UP` (lição da VS-08, não deve ser relevante aqui mas vale revisar se o agente expuser algum cálculo parcelado).
- Contratos do Meta Harness (`.meta-harness/contracts/*.md`) precisam ser regenerados ANTES de rodar `validate-step.sh` para esta slice — esquecer isso gerou uma rejeição falsa de "scope creep" na VS-08.
- Migração Alembic com enum novo precisa de `drop(checkfirst=True)` manual no `downgrade()` (lição da VS-08) — `MessageRole` é um enum novo, então a migração desta slice deve aplicar essa lição desde o início.
- Pydantic serializa `Decimal` como string — DTOs do agente que expuserem valores monetários devem seguir o padrão `MoneyDto`/`_money_dict`, nunca string crua.

---

## 🔧 Especificações Técnicas

### Requisitos Funcionais

1. Endpoint `POST /profiles/{profile_id}/agent/messages` — interpreta mensagem, retorna contrato seção 19 completo.
2. Endpoint `POST /profiles/{profile_id}/agent/actions/{action_id}/confirm` — confirma e persiste, sem LLM.
3. Endpoint `GET /profiles/{profile_id}/agent/conversations/{conversation_id}/messages` — histórico básico (adição mínima além do literal da Spec).
4. Tools allowlisted: `get_dashboard_summary`, `get_autonomy`, `list_fragilities`, `propose_simulation`.
5. Persistência de `conversations` e `agent_messages`.
6. Painel lateral persistente no frontend, com fluxo de confirmação de ação pendente.

### Requisitos Não-Funcionais

- Segurança: allowlist de tools rígida (rejeitar qualquer tool não cadastrada antes de chegar a um caso de uso); `system` prompt sempre separado da mensagem do usuário; nenhuma chamada externa não documentada; `ANTHROPIC_API_KEY` via variável de ambiente.
- Auditabilidade: toda resposta com número vem de um caso de uso real (nunca gerado pelo LLM) — critério de aceite #18 do MVP.
- Observabilidade (seção 28): logar falhas do agente e qual ferramenta foi chamada, sem registrar conteúdo financeiro sensível integral.

### Critérios de Aceite

- [ ] Agente explica indicadores e fragilidades usando dados reais (via tools de leitura).
- [ ] Agente propõe uma simulação estruturada sem persistir nada.
- [ ] Confirmação do usuário persiste a simulação via `SimulateDecisionUseCase` existente, sem chamar o LLM de novo.
- [ ] Campos obrigatórios ausentes viram perguntas ao usuário, nunca valores inventados.
- [ ] Histórico básico de conversa é recuperável.
- [ ] Nenhuma tool fora da allowlist pode ser executada.
- [ ] Testes de frontend cobrem o fluxo do agente com API mockada (requisito explícito da seção 27.2).

---

## 🗺️ Plano de Implementação

### Fase 1: Domínio e persistência
- [ ] `MessageRole` enum em `shared/enums.py`.
- [ ] `domain/agent/entities.py` (Conversation, AgentMessage).
- [ ] `domain/agent/repository.py` (Protocols).
- [ ] `infrastructure/persistence/models.py` — `ConversationModel`, `AgentMessageModel`.
- [ ] `infrastructure/repositories/conversation_repository.py`, `agent_message_repository.py`.
- [ ] Migração Alembic (com `drop(checkfirst=True)` no downgrade do enum, lição da VS-08).
- **Arquivos afetados**: `apps/api/src/domain/shared/enums.py`, `apps/api/src/domain/agent/*`, `apps/api/src/infrastructure/persistence/models.py`, `apps/api/src/infrastructure/repositories/*`, `apps/api/alembic/versions/*`.

### Fase 2: Cliente Anthropic e orquestração
- [ ] `infrastructure/llm/anthropic_client.py` (wrapper, system/user separado, model via env var).
- [ ] Registro de tools allowlisted + despacho para os casos de uso reais (leitura) ou `propose_simulation` (não-persistente).
- [ ] `application/use_cases/agent_use_cases.py`: `SendAgentMessageUseCase`, `ConfirmPendingActionUseCase`.
- **Arquivos afetados**: `apps/api/src/infrastructure/llm/*`, `apps/api/src/application/use_cases/agent_use_cases.py`.
- **Dependências**: Fase 1.

### Fase 3: HTTP
- [ ] `schemas/agent.py` (contrato seção 19: data/evidence/assumptions/limitations/generated_at/version).
- [ ] `routers/agent.py` com os 3 endpoints.
- **Arquivos afetados**: `apps/api/src/interfaces/http/schemas/agent.py`, `apps/api/src/interfaces/http/routers/agent.py`.
- **Dependências**: Fase 2.

### Fase 4: Frontend
- [ ] `features/agent/` (types, api, AgentPanel, PendingActionCard).
- [ ] Terceiro trilho no `dashboard/[profileId]/layout.tsx`.
- [ ] Invalidação de queries conforme `components_to_update`.
- **Arquivos afetados**: `apps/web/src/features/agent/*`, `apps/web/src/app/dashboard/[profileId]/layout.tsx`.
- **Dependências**: Fase 3.

### Fase 5: Testes e Meta Harness gate
- [ ] Testes de backend (allowlist, propose vs confirm, roundtrip de persistência).
- [ ] Testes de frontend com API mockada (painel + pending action + invalidação).
- [ ] **Regenerar contratos do Meta Harness (`.meta-harness/contracts/*.md`) para a VS-09 ANTES de rodar `validate-step.sh`** — lição da VS-08, prevenir rejeição falsa por "scope creep".
- [ ] `capture-baseline.sh` → implementar → commit checkpoint → `validate-step.sh` → corrigir se REJECTED → revalidar até limpo.
- **Dependências**: Fases 1-4.

### Ordem de Execução

1. Fase 1 (domínio/persistência) → 2 (LLM/orquestração) → 3 (HTTP) → 4 (frontend) → 5 (testes/gate).

---

## ⚠️ Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Agente "vaza" e calcula um valor por conta própria em texto livre | Média | Alto (viola critério #18 do MVP) | Todo número na resposta deve ter `evidence` rastreável a uma tool call real; revisar prompt do sistema para instruir explicitamente a nunca declarar números sem tool call associada |
| Confirmação acidental persiste simulação indesejada | Baixa | Médio | `PendingActionCard` exige clique explícito, mostra resumo legível dos parâmetros antes de confirmar |
| Prompt injection via mensagem do usuário tenta extrair system prompt ou chamar tool fora da allowlist | Baixa | Médio | Separação nativa `system`/`user` da API Anthropic; allowlist validada no backend, não confia em texto do LLM |
| Custo/latência da API Anthropic em produção | Média | Baixo (Haiku é barato) | Modelo Haiku 4.5 já escolhido por esse motivo; configurável via env var se precisar trocar |

---

## 🧪 Estratégia de Testes

- **Testes unitários (backend)**: `propose_simulation` nunca chama `SimulateDecisionUseCase`; `validate_decision_parameters` reaproveitado sem duplicação; allowlist rejeita tool desconhecida; `MessageRole`/entities.
- **Testes de integração (backend)**: fluxo completo propose → confirm via API real (Anthropic mockado); histórico de conversa recuperável.
- **Testes de frontend**: `AgentPanel` com API mockada (seção 27.2, requisito explícito da Spec) — renderização de mensagens, `PendingActionCard`, confirmação dispara invalidação de queries.
- **Testes manuais**: demo real via Docker Compose, seguindo o padrão de verificação funcional das slices anteriores.

---

## 📚 Contexto e Referências

- Memória original: `planning/temp_20260725_000000` (deletada após consolidação)
- Spec: seções 6.8, 7, 18.11, 19, 24, 25, 26, 27.2, 31 (`docs/Spec.md`)
- Meta Harness: `planning/meta-harness_20260724` (fluxo de gate por slice)
- Redesign de layout: `planning/redesign-layout-fintwin_20260724` (AppShell e tokens `--ft-*` que o painel do agente vai herdar)
- Estado geral do projeto: `project_overview`

---

## 🚦 Próximo Passo

**Aguardando aprovação do usuário para iniciar implementação.**

Quando aprovado:
1. Seguir o plano fase por fase (Fase 1 → 5).
2. Consultar as lições da VS-08 (enum no downgrade, `ROUND_UP`, contratos do Meta Harness) antes de cada passo relevante.
3. Atualizar `project_overview` e criar `planning/vs09-agente-conversacional_20260725` com progresso ao final de cada fase — não esperar o fim da sessão.

# Plano: VS-09 — Agente Conversacional

## 📅 Criado em: 2026-07-25 | Implementado em: 2026-07-26 | Verificado manualmente em: 2026-07-26

## 🎯 Status: ✅ CONCLUÍDO E VERIFICADO (Meta Harness APPROVED, 0 findings; testes automatizados 185 backend + 34 frontend; verificação manual real via Docker Compose confirmada pelo usuário, incluindo 1 fix pós-aprovação)

---

## 📋 Resumo Executivo

Entregue o subconjunto essencial da VS-09: agente conversacional via API da Anthropic (Claude Haiku 4.5, tool calling nativo, sem LangChain/LangGraph), painel lateral persistente no AppShell. Capacidades: explicar indicadores/fragilidades (tools de leitura reais), criar simulação estruturada com confirmação explícita (fluxo de 2 chamadas: propor sem persistir → confirmar sem LLM), pedir dados ausentes, histórico básico de conversa.

Passou por **3 rodadas de correção via Meta Harness** (Codex `gpt-5.6-terra`) antes de fechar `APPROVED, 0 findings`, e mais **1 correção pós-aprovação** encontrada na verificação manual real (guard anti-número-sem-evidência bloqueava respostas legítimas) — ver seções abaixo.

---

## 🏗️ Arquitetura implementada (como ficou de fato)

Ver `.meta-harness/contracts/current-slice.md` (versão final, pós-correções) para o detalhamento completo de arquivos/camadas. Resumo:

- `domain/agent/` (entities: `Conversation`, `AgentMessage` com campo `confirmed: bool`; repository Protocol).
- `infrastructure/llm/anthropic_client.py` — wrapper, `system`/mensagem sempre separados, model via env `AGENT_MODEL` (default `claude-haiku-4-5-20251001`).
- `application/use_cases/agent_use_cases.py` — `SendAgentMessageUseCase` (tools allowlisted: `get_dashboard_summary`, `get_autonomy`, `list_fragilities`, `propose_simulation`), `ConfirmPendingActionUseCase` (claim atômico via `try_claim`, nunca chama o LLM).
- Persistência: `conversations` + `agent_messages` (migração `e4a1f7c9d3b2`) + coluna `confirmed` (migração separada e idempotente `f1b2c3d4e5a6` — checa existência via inspector antes de adicionar/remover).
- HTTP: `POST /profiles/{id}/agent/messages`, `POST /profiles/{id}/agent/actions/{action_id}/confirm`, `GET /profiles/{id}/agent/conversations/{id}/messages`.
- Frontend: `features/agent/` (AgentPanel, PendingActionCard), terceiro trilho no `dashboard/[profileId]/layout.tsx`, teaser "IA FinTwin (em breve)" removido do Sidebar.
- `docker-compose.yml`: `api` recebe `ANTHROPIC_API_KEY`/`AGENT_MODEL` do host (ou de um `.env` na raiz do projeto, que o `docker compose` lê automaticamente).

## ✅ Decisões Tomadas (originais, mantidas)

Ver histórico completo na versão anterior desta memória (git blame) — resumo: Anthropic API direto; escopo essencial primeiro; painel lateral persistente; fluxo de 2 chamadas propor/confirmar; Claude Haiku 4.5 em produção (independente do CascadeFlow).

---

## ❌ Achados do Meta Harness e correções (OURO — ler antes de mexer neste código)

### Rodada 1 — REJECTED (4 HIGH + 1 MEDIUM)
1. **`docker-compose.yml` não repassava `ANTHROPIC_API_KEY`/`AGENT_MODEL`** ao serviço `api` → adicionado.
2. **`SendAgentMessageUseCase` não validava que a conversa pertence ao perfil** da rota (vazamento de histórico entre perfis) → `conversation.profile_id != profile_id` agora rejeita.
3. **`ConfirmPendingActionUseCase` não validava o perfil dono da ação pendente** (permitia confirmar simulação de outro perfil com um `action_id` válido) → busca a conversa da mensagem e compara `profile_id`.
4. **Confirmação não era atômica**: marcar `confirmed=True` só depois de simular permitia duas confirmações concorrentes duplicarem a simulação → **lição arquitetural importante**: `confirmed` virou coluna dedicada (não mais campo dentro do JSON `pending_action`), com claim atômico via `UPDATE ... WHERE confirmed=false` (`try_claim`).
5. **Texto final do LLM podia conter números sem nenhuma tool call** → guard: se a resposta tem dígito e nenhuma tool foi chamada, substitui por fallback.
6. **`AgentPanel` sem tratamento de erro ao confirmar** (rede, 409, 422) → `onError` adicionado, com tratamento especial pro 409 (reflete estado real em vez de insistir).

### Rodada 2 — REJECTED (4 HIGH, sobre a própria correção da rodada 1)
1. **Editar uma migração já commitada é proibido pelo harness** (trata cada commit como possível ponto de deploy) — a coluna `confirmed` tinha sido adicionada in-place em `e4a1f7c9d3b2` (já commitada na rodada 1) → revertido; nova migração separada `f1b2c3d4e5a6`.
2. **Histórico legado quebrava**: mensagens antigas já tinham `"confirmed"` dentro do JSON `pending_action` (formato da rodada 1) → `TypeError` de argumento duplicado ao montar o schema → normalizado (remove a chave antiga do dict antes de espalhar, usa a coluna como fonte da verdade).
3. **Guard anti-número usava `tool_calls` (inclui `propose_simulation`) em vez de `evidence`** (só populada por tools de leitura) → um número inventado após só uma `propose_simulation` passava ileso → trocado para checar `evidence`.
4. **Claim commitava isoladamente antes de simular**: uma falha entre o claim e a simulação deixava a ação presa como "confirmada" sem simulação correspondente, sem chance de retry → `try_claim` não comita mais sozinho; fica na mesma transação que `simulation_repo.add()` (que comita os dois juntos). Se falhar no meio, `get_session()` fecha a sessão sem commit → rollback implícito → ação volta a ficar disponível.

### Rodada 3 — REJECTED (1 HIGH, sobre a correção da rodada 2)
1. **A migração nova (`f1b2c3d4e5a6`) não era compatível com bancos que já tinham rodado a versão da rodada 1 de `e4a1f7c9d3b2`** (que ainda criava `confirmed` inline) — esse estado intermediário já está no histórico do git e o harness trata como um possível estado real de deploy → migração tornada **idempotente**: checa via `sa.inspect(...).get_columns(...)` se a coluna já existe antes de adicionar/remover.

### Rodada 4 — **APPROVED, 0 findings**

### Pós-aprovação (achado na verificação manual, 2026-07-26) — corrigido
**O guard anti-número-sem-evidência (rodada 1/2) era bom demais em bloquear**: usava "tem QUALQUER dígito" como gatilho, então perguntas legítimas de esclarecimento com contagens/percentuais ("por quantos meses? por exemplo, 3 meses", "qual percentual, 50%?") caíam no fallback genérico — quebrando exatamente a capacidade "pedir dados ausentes" que é requisito explícito da slice. Corrigido: o guard agora só aciona em **padrões de valor monetário** (`R$\d`, `\breais\b`, número com 2 casas decimais tipo `1000,00`), preservando a garantia original (nunca expor um valor financeiro fabricado) sem bloquear explicações conceituais. Commit `f6ef006`.

## 🎓 Lições gerais para próximas slices

- **Nunca editar uma migração já commitada, mesmo dentro da mesma sessão/PR** — o Meta Harness (e a prática correta) trata cada commit como um possível ponto de deploy real. Sempre criar uma migração nova em cima, e se a mudança precisar ser resiliente a estados históricos incertos, tornar a migração idempotente (checar existência via `sa.inspect` antes de `add_column`/`drop_column`).
- **Campos que precisam de garantia atômica (idempotência, exclusão mútua) não devem viver dentro de um blob JSON** — usar uma coluna dedicada permite `UPDATE ... WHERE coluna=valor` condicional, que é a única forma real de atomicidade sem lock explícito.
- **Guards de segurança devem checar o sinal mais específico disponível** (`evidence` real, não "alguma tool foi chamada") — `propose_simulation` conta como tool_call mas não é evidência de leitura; confundir os dois deixa uma brecha.
- **Claims atômicos (`try_claim`) não devem commitar isoladamente** quando o efeito colateral real (persistir a simulação) depende do sucesso de passos posteriores na mesma operação — deixar tudo na mesma transação do `Session` por request garante que uma falha no meio é recuperável via rollback implícito do `get_session()`.
- **Guards de "não invente números" precisam mirar o padrão específico do risco (valor monetário), não um proxy genérico demais (qualquer dígito)** — um proxy largo demais quebra funcionalidade legítima (pedir dados ausentes com exemplos numéricos). Válido tanto para este guard quanto para futuros filtros de conteúdo: sempre testar manualmente com perguntas exploratórias/conceituais, não só com perguntas que pedem um valor direto do dashboard.
- **Container Docker rodando não significa código atualizado** — se uma sessão implementa mudanças de código enquanto os containers já estavam de pé (de uma sessão anterior), é preciso `docker compose up -d --build` para reconstruir as imagens antes de testar. "Cliquei e não aconteceu nada" foi sintoma disso + da `ANTHROPIC_API_KEY` ainda não estar no ambiente do `docker compose`.
- **`docker compose` lê um `.env` na raiz do projeto automaticamente** — não é preciso `export` manual no shell se a chave já estiver lá; útil para segredos como `ANTHROPIC_API_KEY` persistirem entre sessões sem precisar redefinir toda vez.

## ✅ Verificação Manual Realizada (2026-07-26, confirmada pelo usuário)

- `docker compose up -d --build` (rebuild após as mudanças da VS-09) + `docker compose exec api python -m alembic upgrade head` (migração aplicada em Postgres real, `e4a1f7c9d3b2` + `f1b2c3d4e5a6`).
- `ANTHROPIC_API_KEY` confirmada presente no container `api` via `.env` do projeto.
- Teste 1: pediu resumo do dashboard e autonomia ao agente → resposta usou os valores reais do perfil demo (saldo R$12.500,00, obrigações R$4.950,00 — mesmos valores fixos desde a VS-03/VS-08), confirmando que o agente chama `get_dashboard_summary`/`get_autonomy` de verdade, sem inventar números.
- Teste 2 (encontrou o bug pós-aprovação): pediu para "explorar cenários de perda de renda" e "simular provisão de IPTU/IPVA" → ambas caíram no fallback genérico de "não tenho essa informação". Diagnosticado e corrigido (ver seção acima). Reteste confirmou: agora o agente pergunta os dados faltantes normalmente (percentual, valor anual) sem cair no fallback.
- Fluxo de propor+confirmar simulação **não foi testado manualmente** (usuário optou por não testar, já coberto por testes automatizados incluindo o caminho de confirmação/idempotência/isolamento entre perfis).

## 📚 Pendências conhecidas

- Comparar cenários via agente, gerar plano preventivo via agente, navegação guiada pelo agente — adiados para iteração futura (decisão original do plano).
- Tools de leitura atuais (`get_dashboard_summary`, `get_autonomy`, `list_fragilities`) não cobrem listagem de fontes de renda/obrigações — por isso "perda de renda" e "nova despesa recorrente (IPTU/IPVA)" exigem que o USUÁRIO informe os valores, o agente não consegue buscá-los sozinho. Se isso incomodar na prática, considerar uma tool `list_income_sources`/`list_obligations` numa iteração futura.

## 📚 Contexto e Referências

- Spec: seções 6.8, 7, 18.11, 19, 24, 25, 26, 27.2, 31 (`docs/Spec.md`)
- Contratos finais do Meta Harness: `.meta-harness/contracts/current-slice.md`, `acceptance-criteria.md`
- Relatórios das 4 rodadas: `.meta-harness/reports/codex-review-20260726-{081742,083710,094231,094741}.md`
- Commits (ordem): `c73c92c` (implementação inicial) → `e49cd5c` (fix rodada 1) → `b2d01bd` (fix rodada 2) → `6047cd4` (fix rodada 3) → `22525ab` (docs: aprovação final) → `f6ef006` (fix pós-aprovação: guard de dinheiro)

## 🚦 Próximo Passo

VS-09 concluída e verificada. Próxima slice: **VS-10 — Consolidação do MVP** (testes E2E, melhorias de UX, acessibilidade, documentação, segurança, seed, demonstração ponta a ponta, relatório de limitações).

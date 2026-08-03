# Oportunidades acionáveis na resposta do agente — contrato do backend

## 📅 2026-08-01 | branch `feat/recomendacao-proativa` | commit `ed789c2`

## 🎯 Status: backend CONCLUÍDO e testado (263 backend passing). Frontend NÃO tocado (parada pedida pelo usuário).

## Problema

Uma resposta da IA pode conter várias oportunidades. Elas viviam no texto, e o
cliente teria que procurar trechos como "O que fazer" no Markdown.

## Como ficou

- Tool nova `raise_opportunity` (uma chamada por oportunidade), na allowlist.
  Nada é extraído do Markdown depois da resposta.
- `AgentReply.opportunities: list[ActionableOpportunity]` + campo `opportunities`
  em `AgentMessageData` e `AgentMessageHistoryItem`.
- **Divisão rígida**: a IA descreve (title/diagnosis/suggested_actions) e aponta
  `evidence_refs`; o backend classifica (`assessment`) e decide
  `available_actions`, `requires_simulation`, `simulation_status`,
  `related_plan_id`, `related_recommendation_id`.
- `id` = `f"{message_id}-op{n}"` (estável dentro da mensagem).
- `_READ_TOOLS` separa o que conta como evidência — `propose_simulation` e
  `raise_opportunity` não contam (mantém fechada a brecha do guard
  anti-valor-inventado da VS-09).
- Evidências ganharam id (`ev1`, `ev2`, ...), devolvido ao modelo como
  `evidence_id` dentro do tool_result. Ref inválida é descartada.

## Arquivos-chave novos

- `domain/agent/topics.py` — catálogo de assuntos (7). Cada assunto diz se é
  simulável (`decision_type`), que planos o endereçam (`plan_risk_codes`), que
  fragilidades o classificam e de onde vem o assessment.
  **Assunto fora do catálogo não vira bloco** — vira conversa.
- `domain/agent/opportunities.py` — entidades + `available_actions()` puro +
  `to_dict`/`from_dict`.

## Decisões tomadas (registrar antes de mudar)

1. **Assessment só de fonte oficial**: `classify_income_commitment` (tier/value,
   policy `income_commitment_bands` v1) ou severidade do Radar de Fragilidade
   (policy = código da regra, `RULES_VERSION`). Sem fonte na mesma mensagem →
   `assessment: null`. Nunca fabricado.
2. **Plano vence recomendação** em `available_actions` (estado mais avançado).
   `save` só aparece quando não há nem plano ativo nem pendente do assunto.
3. **Dedupe por assunto**: dois `raise_opportunity` do mesmo topic viram um bloco.
4. **`simulated` nunca é emitido nesta etapa** — não há vínculo simulação↔bloco.
5. **Bloco persistido é snapshot**: `available_actions` do histórico reflete o
   momento da resposta, não o estado atual. Nada é reescrito para trás.
6. `get_dashboard_summary` passou a devolver `income_commitment_status` — o
   prompt já mandava usar esse campo desde `a38e690`, mas a tool não o servia.
7. `ACTIVE_PLAN_STATUSES` migrou de `recommendation_use_cases` para
   `domain/preventive_plans/entities.py` (é conhecimento de domínio).
8. `SendAgentMessageUseCase` agora exige `recommendation_repo` e `plan_repo`.

## 🔁 Ajustes aprovados pelo usuário (2026-08-01, segunda rodada)

O contrato foi **aprovado com seis ajustes**, todos implementados (276 testes
passando). O que mudou em relação às decisões acima:

1. **Salvar não aceita conteúdo do cliente.** `POST .../from-conversation` agora
   recebe só `conversation_id`, `message_id`, `opportunity_id`. O backend carrega
   o bloco persistido e tira dele topic/diagnóstico/ações/evidências. O campo
   livre `payload` **saiu da rota** — dado do cliente não substitui o snapshot.
   *Isso quebra o `SaveFromConversation.tsx` atual (salvava o texto da mensagem
   inteira). Corrigir na etapa do AgentPanel, antes da validação no navegador.*
2. **`due_date_concentration` entrou no catálogo** (8 assuntos). Fragilidade
   `CONCENTRATED_DUE_DATES`, não simulável (não há decisão que reorganize datas).
   Catálogo **não deve crescer além disso** por enquanto.
3. **`available_actions` continua snapshot, mas não é autorização.** Toda ação é
   revalidada no clique: plano ativo → 409 `{current_action: "view_plan"}`;
   recomendação equivalente → 409 `{current_action: "view_recommendation"}`.
   Regra de equivalência centralizada em
   `application/use_cases/opportunity_links.py` — usada tanto na montagem do
   bloco quanto na revalidação, para as duas nunca divergirem.
   (Revoga o "dedupe por assunto" da decisão 3 acima e refina a decisão 5.)
4. **Identidade = `topic + subject_key`.** `subject_key` no formato
   `goal:<id>` / `debt:<id>` / `source:<id>`, validado contra as entidades reais
   do perfil — id inexistente **recusa o bloco** (identidade que não aponta para
   nada separaria dois blocos sem diferença real). `AgentTopic.subject_kind` diz
   que tipo cada assunto aceita. `get_dashboard_summary` passou a devolver
   `main_goal_id` para o agente poder apontar a meta sem inventar id.
5. **Título e diagnóstico também não julgam.** `domain/agent/language.py`: léxico
   de julgamento com nível (0 tranquiliza, 1–3 alarmam) + nível que a
   classificação oficial sustenta (tier healthy→0…critical→3; severity low/medium→1,
   high→2, critical→3). Sem assessment, nenhum julgamento; com assessment, nada
   acima do nível dele, e palavra tranquilizadora só em nível 0. Chamada com
   julgamento sem lastro é **recusada** (o backend não reescreve o texto da IA),
   e o erro devolvido ao modelo pede a versão neutra.
   Caso do usuário: "Sua renda está bastante comprometida" com `tier: attention`
   é barrado — "bastante" é nível 2.
6. **Migração não aplicada no Docker** (mantido). `subject_key` mora dentro do
   JSON do bloco, então **não houve nova migração**.

## 🔬 Meta Harness — rodada de 2026-08-02

Rodado pela primeira vez nesta slice (o usuário cobrou: "toda vez tenho que
lembrar de fazer isso" → virou memória de feedback permanente).

Contratos `.meta-harness/contracts/*` ainda descreviam a slice CSS→CVA;
reescritos para esta slice (commit `d95cd1d`). **Ressalva de método**: escritos
pelo mesmo agente que implementou, depois da implementação, cobrindo os dois
commits — por isso a revisão de `ed789c2` acusou requisitos que só nasceram em
`2167564`. Se repetir, versionar contrato por commit.

Vereditos: `ed789c2` REJECTED (4), `2167564` REJECTED (3), `389d33d` REJECTED
(1), `HEAD` **APPROVED** (0).

Findings reais corrigidos (commits `389d33d` e o seguinte):

1. **Guard anti-valor-inventado não alcançava o texto do bloco.** `_LOOKS_LIKE_MONEY`
   só inspecionava a resposta conversacional. Correção: número no bloco exige
   `evidence_refs` naquele bloco — e a régua ali é **qualquer dígito**
   (`_HAS_DIGIT`), não formato de moeda: "2000", "80%" e "2 meses" são os
   formatos em que o inventado mais parece cálculo. Era a brecha da VS-09
   reaberta num canal novo.
2. **Corrida no salvar.** Revalidar em memória não decide corrida: duas
   requisições passam as duas antes de qualquer INSERT confirmar. Coluna
   `opportunity_id` **única** em `recommendations` (migração `c1e4a7b90d52`,
   não aplicada no Docker) + `add_for_opportunity` no repositório, seguindo o
   tratamento de `IntegrityError` que `balance_snapshot_repository` já usava.
   Corrida perdida vira 409 com o registro que venceu.
3. **"aceitável" faltava no léxico** de julgamento, embora o prompt do agente já
   a listasse entre as classificações que a IA não declara sozinha.

**Gotcha do harness**: o Codex nunca conseguiu rodar a suíte —
`apps/api/.venv/Scripts/python.exe` não inicia no ambiente dele (aponta para um
Python 3.12 que ele não enxerga), e os comandos de frontend dão EPERM no sandbox
read-only. Todos os vereditos são por inspeção de diff; os 284 verdes são
medição local. Vale resolver isso antes da próxima rodada, senão o critério de
testes fica sempre NOT_VERIFIED.

## Etapa 3 (2026-08-02): entidades reais + AgentPanel

Commits: `4952512` (backend complementar), `900ad81` (AgentPanel),
`91b4ae4` (contratos do harness), + relatórios.

- `get_dashboard_summary` passou a devolver `debts` e `income_sources` com
  `entity_type` no vocabulário de `SubjectKind` — sem tool nova. Antes disso
  `subject_key` só era produzível para `goal:`; o resto exigiria o modelo
  inventar um id, que a validação recusa.
- 4 testes novos no backend (2 fontes → 2 blocos, mesma fonte → 1, entidade de
  outro perfil recusada, resumo expõe os ids). Suíte: **288 passando**.
- Front: `OpportunityCard.tsx` novo; `SaveFromConversation.tsx` **deletado**.
  Salvar envia só os três ids; 409 troca a ação exibida. 5 testes novos.
- Falhas em `AutonomyPanel.test.tsx` (2) são **anteriores** — confirmado por
  `git stash`. Não mexer nelas nesta linha de trabalho.
- Contrato do harness agora declara quais commits cobre (correção do erro de
  método da rodada anterior). Backend: APPROVED, 0 findings. Front:
  APPROVED_WITH_WARNINGS, 1 MEDIUM.

## Etapa 4 (2026-08-02): migração aplicada + validação integrada

Migrações aplicadas no Postgres do Docker: `e7d3b5a91c40` → `a9c2e5f70b31` →
`c1e4a7b90d52`. Índice `ix_recommendations_opportunity_id` UNIQUE conferido no
schema real, não só no Alembic.

**Bug achado só na integração** (commit `44fc674`): `main_goal_id` supunha que
`summary.main_goal` fosse a entidade da meta — é um `MainGoalSummary`, que só
tem descrição e progresso. `AttributeError` derrubava `get_dashboard_summary`
inteiro: **toda conversa do agente respondia 500** para qualquer perfil com
meta. Nenhum teste pegou porque todos rodavam com perfil sem metas — a
expressão ficava no ramo `else`. Quatro rodadas de harness APPROVED passaram
por cima disso. Lição: teste que só exercita o ramo vazio não cobre o campo.

Validação por DOM (`javascript_tool`) no perfil real
`057943a0-6187-475c-9411-7dc78ef50cf0`, com screenshot indisponível:
tudo verde. Detalhe importante: o card de `emergency_reserve` (assunto
simulável) veio **sem** botão de simular, confirmando a decisão da etapa 3 no
caminho real.

**Gotcha do ambiente**: `screenshot` e `read_page` da extensão Chrome falham com
"Script injection timed out" nesta máquina, mas `javascript_tool` funciona na
mesma aba. Validação por DOM é o caminho viável; capturas visuais dependem do
usuário.

## Pendências / o que ainda precisa de decisão do usuário

- **Chamada `raise_opportunity` truncada** (limitação observada, não corrigida
  nesta etapa): em uma resposta o modelo emitiu um terceiro bloco com apenas
  `topic` e `title`, sem `diagnosis` nem `suggested_actions`. O guard recusou
  corretamente, mas o usuário perde uma oportunidade sem saber. Provável
  truncamento de saída do modelo. Decidido não abrir implementação agora.
- **Duas dívidas / duas fontes**: o perfil real tem uma de cada. A separação por
  entidade fica coberta pelos testes automatizados; não criar dado artificial no
  perfil real (instrução explícita do usuário, 2026-08-02).

- ~~Botão `simulate` sem caminho real~~ — RESOLVIDO em `68c6fea`: o backend
  parou de oferecer `simulate` (decisão do usuário, 2026-08-02). A regra passou
  a ser "`available_actions` é o que dá para fazer agora, não o que o produto
  pretende oferecer". `requires_simulation` continua no bloco como informação e
  volta a governar a ação quando existir caminho de oportunidade → simulação.
  Revalidado no harness: APPROVED, 0 findings.
- **Badge de classificação não é exibido.** `assessment` traz `tier`/`severity`
  em representação interna e o domínio não tem rótulo pt-BR para eles; traduzir
  no cliente seria o cliente classificando.
- ~~Casamento por `payload["topic"]` vindo do front~~ — RESOLVIDO no ajuste 1:
  `topic` e `subject_key` são gravados pelo backend a partir do bloco.
- **`SaveFromConversation.tsx` está quebrado** até a etapa do AgentPanel (envia
  `payload`, a rota agora exige `opportunity_id`). Não validar no navegador antes
  de corrigir.
- `subject_key` só é produzível hoje para `goal:` (`main_goal_id` no
  `get_dashboard_summary`). Dívidas e fontes de renda ainda não têm id em
  nenhuma tool de leitura — o agente vai omitir `subject_key` nesses assuntos.
- Migração `a9c2e5f70b31` validada só em sqlite descartável; o Postgres do
  Docker ainda está em `e7d3b5a91c40` (imagem da API não tem bind mount →
  precisa `docker compose up -d --build` + `alembic upgrade head`).
- `AgentPanel` intocado: hoje ignora `opportunities` (campo aditivo, não quebra).
- Sem `context_snapshot_id` (nada no domínio a apontar) e sem status `draft`.

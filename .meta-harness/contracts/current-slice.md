# Slice atual: Oportunidades acionáveis na resposta do agente (contrato do backend)

> Plano registrado em `planning/oportunidades-estruturadas-na-conversa_20260801` (Serena).
>
> **Aviso de procedência**: este contrato foi redigido pelo mesmo agente que implementou a
> slice, a partir dos pedidos verbatim do usuário (2026-08-01 e 2026-08-02). Não é um contrato
> escrito antes da implementação por um terceiro. Divergência entre este texto e o pedido
> original é falha do contrato, não do revisor.

## Contexto

Slice **puramente backend**. Nenhuma mudança em `apps/web` — pedido explícito do usuário:
"Pare após concluir o contrato do backend. Não altere o AgentPanel ainda."

O problema: uma resposta da IA pode conter várias oportunidades financeiras, e elas viviam
soltas no texto. O frontend teria que interpretar Markdown e procurar trechos como "O que
fazer" para saber o que era acionável. Cada oportunidade precisa sair como bloco estruturado
independente.

A slice tem **dois commits**, revisados separadamente:

- `ed789c2` — o contrato do backend.
- `2167564` — seis ajustes pedidos pelo usuário ao aprovar o contrato.

## Escopo entregue — commit `ed789c2` (contrato)

### Como as oportunidades nascem

Tool nova `raise_opportunity` no loop de tool calling, uma chamada por oportunidade. **Nada é
extraído do Markdown depois da resposta** — regra 2 do pedido.

Divisão rígida de responsabilidade: a IA descreve (`title`, `diagnosis`, `suggested_actions`) e
aponta `evidence_refs`; o **backend** classifica (`assessment`) e decide `available_actions`,
`requires_simulation`, `simulation_status`, `related_plan_id`, `related_recommendation_id`.

### Domínio novo

- `domain/agent/topics.py` — catálogo de assuntos. Por assunto: é simulável
  (`decision_type`)? que planos o endereçam (`plan_risk_codes`)? que fragilidades o classificam
  (`fragility_codes`)? de onde vem o assessment? **Assunto fora do catálogo não vira bloco** —
  continua sendo conversa, porque um bloco com botão promete uma capacidade que o domínio
  precisa sustentar.
- `domain/agent/opportunities.py` — entidades, `available_actions()` puro, `to_dict`/`from_dict`.

### Persistência e compatibilidade

Coluna `opportunities` (JSON, **nullable**) em `agent_messages`, migração `a9c2e5f70b31`,
idempotente via `sa.inspect`. **Sem backfill**: mensagem gravada antes da coluna é lida como
resposta sem blocos (`None → []`). Nada é migrado nem reescrito.

### Guard de evidência

`_READ_TOOLS` separa o que conta como evidência. `propose_simulation` e `raise_opportunity` não
leem nada do perfil e **não contam** — manter isso fechado é o que preserva a correção do guard
anti-valor-inventado achada na VS-09. Evidências ganharam id (`ev1`, `ev2`…), devolvido ao
modelo dentro do `tool_result`; referência a evidência inexistente é descartada.

## Escopo entregue — commit `2167564` (seis ajustes)

1. **Salvar não aceita conteúdo do cliente.** `POST /profiles/{id}/recommendations/from-conversation`
   passa a receber só `conversation_id`, `message_id`, `opportunity_id`. O campo livre `payload`
   **saiu da rota**. O backend carrega o bloco persistido e tira dele topic, diagnóstico, ações,
   evidências e assessment.
2. **`due_date_concentration` entrou no catálogo** (8 assuntos). Fragilidade
   `CONCENTRATED_DUE_DATES`, não simulável. Catálogo **não cresce além disso**.
3. **`available_actions` continua snapshot, mas não é autorização.** Nada no histórico é
   reescrito; a ação é revalidada no clique e devolve **409** com o estado atual
   (`view_plan` / `view_recommendation`) em vez de criar um segundo registro.
4. **Identidade = `topic` + `subject_key`** (`goal:<id>`, `debt:<id>`, `source:<id>`), validada
   contra as entidades reais do perfil. Id inexistente **recusa o bloco**.
5. **Título e diagnóstico também não julgam.** Léxico de julgamento com nível
   (`domain/agent/language.py`) contra o nível que a classificação oficial sustenta. Chamada com
   julgamento sem lastro é **recusada**, não corrigida.
6. **Migração não aplicada no Docker** — pedido explícito. `subject_key` mora dentro do JSON do
   bloco, então **não houve migração nova** neste commit.

## Fora de escopo (não implementado nesta slice)

- **Qualquer mudança em `apps/web`** — parada pedida pelo usuário.
- **Status `draft`** na recomendação — proibido pelo pedido (regra 11). O ciclo segue
  `pending/approved/rejected/expired/superseded`, e o estado do cálculo mora separado em
  `simulation_status`.
- **`simulation_status: "simulated"`** nunca é emitido: não existe vínculo simulação↔bloco
  nesta etapa.
- **`context_snapshot_id` e `follow_up_question`** do contrato TypeScript original — o projeto
  já tem `pending_questions`, e não há nada no domínio para apontar um snapshot id.
- **Aplicar a migração no Postgres do Docker** — o container segue em `e7d3b5a91c40`.
- **`subject_key` para dívidas e fontes de renda** — nenhuma tool de leitura expõe esses ids
  ainda; só `goal:` é produzível (via `main_goal_id`, novo em `get_dashboard_summary`).

## Débito conhecido e assumido

`apps/web/src/features/recommendations/SaveFromConversation.tsx` **está quebrado** desde o
commit `2167564`: ele salva o texto da mensagem inteira e envia `payload`, que a rota não aceita
mais. Não há conserto de uma linha — a granularidade mudou de mensagem para oportunidade, que é
a etapa seguinte (AgentPanel). Reportado ao usuário; validação no navegador adiada até lá.

## Verificação executada

- `apps/api/.venv/Scripts/python.exe -m pytest`: **276 passed** ao fim de `2167564`
  (263 ao fim de `ed789c2`; baseline antes da slice era 254).
- Cadeia de migrações validada do zero num sqlite descartável em `ed789c2`
  (`alembic upgrade head` → coluna `opportunities` presente; head único `a9c2e5f70b31`).
- **Nenhuma verificação no navegador** — o frontend não foi tocado e o débito acima impede
  validação end-to-end antes da próxima etapa.

**Sem baseline**: os commits desta slice não têm arquivo em `.meta-harness/baselines/`. Os
baselines existentes (`statuscard-before.json` etc.) são de slices de frontend e não servem
aqui. O intérprete Python do projeto é `apps/api/.venv` (3.12); o Python do sistema não tem
`psycopg` e faz a suíte quebrar com 60 erros de import.

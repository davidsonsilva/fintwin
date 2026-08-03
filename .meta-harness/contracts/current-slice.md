# Slice atual: entidades reais no `subject_key` + AgentPanel consome os blocos

> Plano registrado em `planning/oportunidades-estruturadas-na-conversa_20260801` (Serena).
>
> **Aviso de procedência**: este contrato foi redigido pelo mesmo agente que implementou a
> etapa, a partir do pedido verbatim do usuário (2026-08-02). Não é um contrato escrito antes
> da implementação por um terceiro. Divergência entre este texto e o pedido original é falha
> do contrato, não do revisor.
>
> **Etapa anterior encerrada.** O contrato do backend (blocos estruturados, guards de número e
> de julgamento, revalidação no clique, unicidade por `opportunity_id`) foi revisado e aprovado
> em `b9a41f1`. O texto daquele contrato está no histórico do git; este arquivo cobre **apenas**
> os dois commits desta etapa. Não reavalie o que já foi aprovado, exceto para apontar regressão.

## Commits sob revisão

- `4952512` — backend complementar: as leituras devolvem os identificadores das dívidas e das
  fontes de renda.
- `900ad81` — frontend: o AgentPanel renderiza um bloco por oportunidade e para de salvar a
  mensagem inteira.
- `44fc674` — correção do `MainGoalSummary`, encontrada na validação integrada (ver abaixo).
- `37b75f5` — fim da oscilação da fileira de indicadores no dashboard (ver seção própria em
  `acceptance-criteria.md`, critérios 17-23). Bug reportado pelo usuário em vídeo: os seis cards
  compactos alternando entre linhas e colunas sozinhos, sem redimensionar, interagir ou mudar
  dados.

## Commit `44fc674`: o resumo carrega a identidade da meta

`main_goal_id` foi exposto em `4952512` supondo que `summary.main_goal` fosse a entidade da
meta. É um `MainGoalSummary`, que só tem `description` e `progress_pct`. O acesso a `.id`
estourava `AttributeError` e derrubava `get_dashboard_summary` inteiro — **toda conversa com o
agente respondia 500** para qualquer perfil que tivesse uma meta. Descoberto só ao aplicar a
migração e conversar com o perfil real; nenhuma das quatro rodadas anteriores de revisão pegou.

A causa da lacuna importa mais que o conserto: todos os testes rodavam com perfil **sem metas**,
então a expressão ficava no ramo `else` e nunca era avaliada. Cobertura que só exercita o ramo
vazio de um `if` não cobre o campo.

Critérios para este commit:

17. **A correção é mínima e no lugar certo.** `MainGoalSummary` passa a carregar `id`, preenchido
    a partir da meta escolhida. Não pode haver `getattr` defensivo, `try/except` em volta do
    acesso, nem `id` opcional com default — isso esconderia a próxima ocorrência do mesmo erro.

18. **O teste de regressão exercita o caminho real.** Cria um perfil **com meta**, chama
    `get_dashboard_summary` de verdade (não um fake do resumo) e afirma `main_goal_id`.
    Verificado que falha sem a correção.

19. **Nada além do bug.** Nenhuma mudança de comportamento em outro campo do resumo, nenhum
    arquivo não relacionado, e o commit não carrega estado do harness nem untracked.

## O problema desta etapa

`subject_key` já aceitava `debt:<id>` e `source:<id>` e já era validado contra as entidades
reais do perfil. Mas nenhuma tool de leitura devolvia esses identificadores — só a meta
principal tinha `id` exposto. Na prática o agente só conseguia produzir `goal:<id>`: para
apontar uma dívida ou uma fonte de renda, teria que inventar um identificador, e a validação
(corretamente) recusa. O suporte existia no papel e não no uso.

Do lado do cliente, o painel salvava a **mensagem inteira** como recomendação, com o texto
corrido no `payload`. Uma resposta com três assuntos virava um registro só. Esse caminho foi
deliberadamente quebrado no commit anterior (o campo livre `payload` deixou de existir na
rota) e é aqui que ele é substituído.

## O que o usuário pediu (verbatim, 2026-08-02)

Backend complementar:

1. "Exponha os identificadores estáveis das dívidas e fontes de renda nas tools de leitura já
   existentes. Evite criar uma tool nova se for possível estender com segurança."
2. "A IA precisa receber apenas os campos necessários: id; nome ou descrição; valor/contexto
   relevante; tipo da entidade."
3. "Permita gerar e validar: `debt:<debtId>`; `source:<incomeSourceId>`. Mantenha a validação no
   backend contra as entidades reais do profileId. Não aceite IDs livres produzidos pelo modelo
   sem validação."
4. Testes garantindo: duas dívidas diferentes geram dois blocos; duas fontes diferentes geram
   dois blocos; a mesma entidade não gera duplicata; entidade de outro perfil ou inexistente é
   recusada.

AgentPanel:

5. "Preserve o texto natural em `reply`."
6. "Renderize um bloco para cada item de `opportunities`."
7. "Use apenas `available_actions` para mostrar os botões."
8. "Remova o `SaveFromConversation` antigo que salvava a mensagem inteira."
9. "Ao salvar, envie somente `conversation_id`, `message_id` e `opportunity_id`."
10. "Trate 409 atualizando a ação para `view_plan` ou `view_recommendation`."
11. "Não inferir classificação, simulação ou ações no frontend."
12. "Mensagens antigas sem `opportunities` continuam apenas com o texto normal."
13. "Não aplique ainda a migração no Postgres em execução."

## Decisões de implementação que o revisor deve julgar

- **Onde os identificadores foram expostos**: em `get_dashboard_summary`, junto do
  `main_goal_id` que já existia. Não foi criada tool nova. O revisor deve julgar se estender o
  "resumo" com duas listas de entidades é seguro (não vaza dado de outro perfil, não infla a
  resposta a ponto de atrapalhar) ou se seria mais correto uma leitura separada.
- **`entity_type` usa o mesmo vocabulário de `SubjectKind`** (`debt`, `source`, `goal`), para o
  agente montar a chave sem traduzir nada.
- **Badge de classificação não é renderizado.** `assessment` traz `tier`/`severity` em
  representação interna (`attention`, `medium`) e o domínio não expõe rótulo em pt-BR para eles.
  Traduzir no cliente seria o cliente classificando. Optou-se por não exibir.
- **`simulate` é renderizado desabilitado.** O backend oferece a ação, mas não existe caminho de
  uma oportunidade até uma simulação: os parâmetros nascem da proposta do agente
  (`propose_simulation` → `pending_action`) e o bloco não os carrega. Botão morto é ruim;
  inventar os parâmetros no cliente seria pior. O revisor deve dizer se concorda.
- **`view_plan` leva à lista de planos** (`/dashboard/{profileId}/plans`), porque não existe
  rota por plano individual.
- **O corpo do 409 é lido de `ApiError.message`**, que carrega o texto bruto da resposta. O
  parse é defensivo (`try/catch`, checa `error === "action_outdated"`); se falhar, o card cai no
  erro genérico em vez de quebrar.

## Fora de escopo desta etapa

- Aplicar as migrações no Postgres em execução (duas pendentes: `a9c2e5f70b31`,
  `c1e4a7b90d52`). Proibido pelo usuário.
- Ampliar o catálogo de assuntos.
- Ligar `simulate` a um caminho real.
- Corrigir as duas falhas pré-existentes em `AutonomyPanel.test.tsx` (verificadas como
  anteriores a estes commits, por `git stash`).

---

# Etapa adicional: Registro de recomendações refeito contra o Design System

> **Escopo desta rodada.** Revise **somente** os dois commits abaixo. Tudo o que veio antes
> (blocos estruturados, AgentPanel, oscilação da fileira de indicadores) já foi revisado e
> aprovado — não reavalie, exceto para apontar regressão introduzida por estes dois.

## Commits sob revisão

- `ef30e78` — a tela `Registro de recomendações` deixa de ser uma pilha de cards e passa a ser
  uma lista dentro de uma moldura única, refeita contra `imagens/FinTwin AI — Design System.md`.
- `716ff9f` — correção de 1px no alinhamento vertical do texto dentro do badge de status,
  aplicada no ponto de chamada.

## Origem

Pedido verbatim do usuário (2026-08-02): usar `imagens/FinTwin AI — Design System.md` como
referência, preservar toda a funcionalidade, remover o padding duplicado, usar altura natural,
não usar `Card.Root interactive` se o item não for integralmente clicável, não usar hover com
deslocamento em linhas de registro, usar tokens, remover `#b49cff` hardcoded, trocar classes
tipográficas arbitrárias por padrões do Design System quando existirem, diferenciar os cinco
status sem criar novas regras de domínio, e **não alterar outras telas**.

## Decisões que o revisor deve julgar

- **Registro virou `<li>` dentro de um `Card.Root` único**, com `p-0` na moldura e o padding
  só na linha. É a leitura do §11.2 (card é Header/Content/Footer em torno de um valor
  principal e uma visualização — um registro não tem nenhum dos dois) combinada com o §7
  (separar superfícies próximas com borda discreta, não acumular sombra). O revisor deve
  dizer se concorda com a leitura ou se o documento comportava manter cards.
- **Trilho colorido de 3px por status.** O badge sozinho não distinguia `rejected` de
  `superseded`, que compartilham o tom neutro. O mapa `STATUS_RAIL` é local ao arquivo;
  `STATUS_TONES` em `types.ts` não foi tocado. O revisor deve confirmar que isso não é uma
  regra de domínio nova disfarçada de apresentação.
- **Correção do badge feita no chamador, não em `badgeVariants`.** A causa está no primitivo
  (`min-h-[22px]` fecha a altura exata, `items-center` fica sem folga, e o padding simétrico
  não compensa a descendente não usada). Corrigir lá mudaria toda tela que usa Badge, o que o
  usuário proibiu. O revisor deve julgar se a duplicação no chamador é aceitável dado o veto.
- **`assignToColumns`/oscilação não têm relação com esta etapa.** Arquivo diferente.

## Fora de escopo desta etapa (registrado como tarefa separada, não corrigir)

- `.ft-header` tem `height: 98px` fixo com `.ft-header-left` em `position: absolute`; em 390px
  um título de duas linhas transborda e colide com o conteúdo abaixo. **Pré-existente**,
  atinge qualquer página com título longo. Apontar como regressão desta etapa é falso positivo.
- Correção global do primitivo `Badge` e revisão dos seus consumidores.
- As duas falhas pré-existentes em `AutonomyPanel.test.tsx`.
- Os 3 erros de `tsc` pré-existentes em `ProfileStep.tsx` e `ResourceStepForm.tsx`.

## Resultado da revisão desta etapa

Rodada em duas execuções, uma por commit (o harness usa `TARGET^` como base, então não há
como cobrir dois commits numa chamada só).

| Commit | Relatório | Veredito | Findings |
|---|---|---|---|
| `ef30e78` | `codex-review-20260802-212910.md` | APPROVED_WITH_WARNINGS | 1 MEDIUM |
| `716ff9f` | `codex-review-20260802-213304.md` | APPROVED | 0 |

**O finding MEDIUM de `ef30e78` é falso positivo, causado por este contrato — não por defeito
no código.** A primeira versão da lista de critérios era cumulativa: os critérios 25–34 foram
escritos cobrindo os dois commits, e cada commit foi revisado contra a lista inteira. O
critério 33 descreve o offset do Badge, que só existe em `716ff9f`; cobrado contra `ef30e78`,
ele aponta uma ausência que é a definição do commit seguinte, não uma falha.

A confirmação está na segunda execução, que avaliou o mesmo critério no commit a que ele
pertence e o aprovou: *"O diff é restrito ao ajuste de padding dos dois badges e atende ao
critério 33 sem alterar a caixa"*. Somados, os dois commits satisfazem os critérios 25 a 34.

Nenhuma correção de código foi feita em resposta a este finding. O contrato foi ajustado para
atribuir cada critério ao seu commit — ver o cabeçalho "Atribuição por commit" em
`acceptance-criteria.md`.

**Limitação da revisão**: `vitest` e `next build` ficaram NOT_VERIFIED nas duas execuções, por
EPERM do sandbox do Codex ao criar diretório temporário. `tsc` alcançou apenas os três
diagnósticos pré-existentes fora do diff. O veredito APPROVED vale por inspeção de diff, não
por suíte executada pelo revisor.

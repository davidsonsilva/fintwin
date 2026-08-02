# Critérios de aceitação: entidades reais no `subject_key` + AgentPanel

> Derivados do pedido verbatim do usuário em 2026-08-02. Registro em
> `planning/oportunidades-estruturadas-na-conversa_20260801` (Serena).
>
> **Aviso de procedência**: escritos pelo agente que implementou a etapa. Ver o aviso em
> `current-slice.md`. Cobrem apenas os commits `4952512` e `900ad81`.

## Backend complementar (`4952512`)

1. **Os identificadores saem de uma leitura já existente.** Nenhuma tool nova foi criada, e a
   tool estendida continua sendo de leitura pura (nada é escrito, nenhum efeito colateral).

2. **Só o necessário para identificar e situar.** Cada entidade devolve id, descrição, o valor
   relevante e o tipo. Nada além disso — em particular, nenhum campo que permita ao agente
   derivar uma classificação por conta própria.

3. **Escopo por perfil.** As entidades são listadas pelo `profile_id` da conversa. Não pode
   existir caminho que devolva dívida ou fonte de renda de outro perfil.

4. **A validação de `subject_key` não afrouxou.** Continua verificando formato **e** existência
   contra as entidades reais do perfil. Um id produzido livremente pelo modelo — inclusive um id
   que exista, mas em outro perfil — recusa o bloco.

5. **O guard anti-valor-inventado não regride.** A tool agora devolve números (parcela, valor da
   renda). Isso não pode abrir caminho para um bloco citar número sem apontar `evidence_refs`: a
   régua continua sendo "qualquer dígito no texto do bloco exige evidência apontada".

6. **Testes cobrindo as quatro garantias pedidas**: duas dívidas → dois blocos; duas fontes →
   dois blocos; mesma entidade → um bloco; entidade inexistente **ou de outro perfil** →
   recusada.

## AgentPanel (`900ad81`)

7. **O texto natural é preservado.** `reply` continua sendo renderizado inteiro na bolha. Os
   blocos são adicionais, não substitutos, e nada do texto é consumido ou reescrito.

8. **Um bloco por item de `opportunities`.** Sem agrupamento, sem filtro, sem reordenação
   inventada pelo cliente.

9. **Os botões saem apenas de `available_actions`.** Não pode existir botão condicionado a outro
   campo (`related_plan_id`, `requires_simulation`, `simulation_status`) sem que a ação
   correspondente esteja na lista. Os demais campos podem ser usados para *montar o destino* de
   uma ação já oferecida — não para decidir que ela existe.

10. **O caminho antigo foi removido.** `SaveFromConversation.tsx` não existe mais e não há
    referência remanescente a ele. Nenhuma outra rota do app salva a mensagem inteira.

11. **O cliente envia só referências.** A chamada de salvar carrega exatamente
    `conversation_id`, `message_id`, `opportunity_id`. Nenhum texto, título ou diagnóstico do
    cliente pode chegar ao registro.

12. **409 é obedecido, não contornado.** Ao receber `action_outdated`, o card passa a oferecer a
    ação que o backend indicou (`view_plan` / `view_recommendation`) e deixa de oferecer salvar.
    Não pode haver retry automático nem criação de um segundo registro.

13. **Nada é inferido no cliente.** Nenhuma classificação, severidade ou rótulo de tier é
    calculado, traduzido ou exibido a partir de `assessment`; nenhuma decisão sobre simulação é
    tomada localmente.

14. **Mensagem sem oportunidades continua só texto.** Ausência do campo (mensagens antigas) e
    lista vazia se comportam igual: nenhum bloco, nenhum botão.

## Ambos

15. **Sem regressão de testes.** Nenhum teste pré-existente removido ou marcado `skip`. As duas
    falhas de `AutonomyPanel.test.tsx` são anteriores a estes commits — apontá-las como
    regressão é falso positivo.

16. **Escopo respeitado**: nenhuma migração aplicada no Postgres em execução, catálogo de
    assuntos não ampliado, ciclo de vida da recomendação intocado.

## Oscilação da fileira de indicadores (`37b75f5`)

Pedido do usuário (verbatim, 2026-08-02): "Para a mesma largura do container e o mesmo conjunto
de cards, o resultado do layout deve ser sempre idêntico. Prefira determinar a composição apenas
pela largura do container e por breakpoints determinísticos. Não use a altura resultante dos
próprios cards como entrada de um algoritmo que depois altera a largura deles." E: "Não faça uma
correção cosmética removendo animações ou transitions."

17. **O laço foi cortado, não amortecido.** Nenhuma altura renderizada alimenta a decisão de
    composição. Não vale resolver com debounce, epsilon maior, `requestAnimationFrame`, flag de
    "já decidiu" ou guarda de igualdade sobre o mesmo algoritmo realimentado — a dependência
    saída→entrada tem que ter deixado de existir.

18. **A composição é função pura da largura da seção.** `composeLayout(w)` não lê estado, ref,
    data, relógio nem aleatoriedade. Mesma largura ⇒ mesmo resultado, sempre, independente do
    caminho percorrido até aquela largura.

19. **A distribuição em colunas também é determinística.** Qual card entra em qual coluna não
    pode depender de medição. O revisor deve julgar se trocar o balanceamento por altura pelo
    rodízio é perda aceitável — a justificativa alegada é que as colunas são `flex-1` de mesma
    largura e que, para 6 cards em 3 colunas, o rodízio reproduz a distribuição antiga.

20. **Nada foi corrigido por cosmética.** Nenhuma animação, `transition` ou `will-change` foi
    removida para esconder o sintoma.

21. **Keys por identidade.** Os cards continuam keyados por `card.key`; trocar de coluna não
    remonta o card.

22. **As restrições de legibilidade sobreviveram.** `MIN_COMPACT_WIDTH` e `MIN_EVENTS_WIDTH`
    continuam filtrando composições inviáveis; a simplificação não pode ter passado a permitir
    card compacto abaixo do mínimo.

23. **Teste de regressão no navegador existe e mede o que promete.** Carrega o dashboard, espera
    estabilizar, captura os bounding boxes dos seis cards, espera ≥5s sem interação e confirma
    que nada mudou; e verifica que a mesma largura, alcançada descendo e subindo, produz a mesma
    composição.

### Reprodução do sintoma (`39fa802`)

A primeira versão deste contrato registrava que a oscilação não tinha sido reproduzida. Isso foi
corrigido: ela **foi** reproduzida no perfil real, com o código anterior restaurado no container.

A banda estava fora de todas as larguras varridas antes. Ela existe porque o card de eventos
precisa estar **ao lado** e ser **mais alto que a grade**: aí `max(gridHeight, eventsHeight)`
vale `eventsHeight` para todos os candidatos, o termo dominante do score se anula, e a escolha
entre 2 e 3 colunas passa a ser decidida só pelo desequilíbrio entre colunas — o termo mais
sensível a variação de altura. Isso exige seção entre ~1148px e ~1209px, ou seja viewport
~1480-1600px.

Medição, viewport parado, sem interação, 50 amostras em 5,5s por largura:

| viewport | antes (`37b75f5^`) | depois (`37b75f5`) |
|---|---|---|
| 1480 | 4 layouts distintos | 1 |
| 1490 | 4 | 1 |
| 1500 | 4 | 1 |
| 1510 | 4 | 1 |
| 1520 | 4 | 1 |
| 1530 | 3 | 1 |
| 1540 | 3 | 1 |
| 1550 | 4 | 1 |
| 1560 | 3 | 1 |
| 1570 | 4 | 1 |
| 1580 | 4 | 1 |
| 1590 | 3 | 1 |
| 1600 | 3 | 1 |

Antes, a contagem de colunas na banda também era errática (2 em 1480, 3 em 1490-1510, 2 em 1520,
3 em 1530...). Depois, 3 colunas em toda a banda, com a largura do card crescendo monotonicamente
de 262px a 296px.

24. **O teste de regressão cobre a banda que reproduz o bug.** O terceiro caso de
    `dashboard-layout-stability.spec.ts` afirma um único layout distinto com o viewport parado em
    1490/1520/1550/1580px — larguras em que o código anterior media 4 layouts distintos.

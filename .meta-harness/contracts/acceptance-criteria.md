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

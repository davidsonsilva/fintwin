# Critérios de aceitação: Oportunidades acionáveis na resposta do agente

> Derivados dos pedidos verbatim do usuário em 2026-08-01 (11 regras + testes mínimos) e
> 2026-08-02 (6 ajustes na aprovação). Registro em
> `planning/oportunidades-estruturadas-na-conversa_20260801` (Serena).
>
> **Aviso de procedência**: escritos pelo agente que implementou a slice. Ver o aviso em
> `current-slice.md`.

1. **O texto conversacional é preservado e não é fonte de dado estruturado.** A resposta em
   linguagem natural continua no campo de texto da mensagem. Nenhum bloco é obtido analisando
   Markdown depois da resposta — nem por regex, nem procurando seções como "O que fazer".
   Verificação: o caminho que popula `opportunities` parte exclusivamente de chamadas de tool.

2. **Identificador estável dentro da mensagem.** Cada bloco tem `id` próprio, derivado do
   `message_id`, distinto entre blocos da mesma resposta e estável entre a resposta e a leitura
   do histórico.

3. **Valores, classificações e severidades vêm das tools e do domínio.** `assessment` só existe
   quando uma tool de leitura produziu a classificação **na mesma mensagem**: faixa de
   comprometimento da renda (`income_commitment_bands`) ou severidade do Radar de Fragilidade
   (policy = código da regra). Não pode existir caminho de código que fabrique tier, severity,
   value, policy_id ou policy_version a partir do que a IA escreveu.

4. **Sem classificação oficial, `assessment` é `null`.** Nunca um objeto vazio, nunca um valor
   inventado, nunca um default "neutro" que a interface possa exibir como veredito.

5. **A IA não julga em nenhum campo.** Além de não informar números, o texto de `title`,
   `diagnosis` e `suggested_actions` não pode carregar adjetivo de veredito nem intensificador
   que a classificação oficial não sustente. Critério concreto do usuário: *"Sua renda está
   bastante comprometida"* com `tier: attention` deve ser **barrado**. Sem assessment, nenhum
   julgamento; com assessment, nada acima do nível dele; palavra tranquilizadora
   (saudável, seguro) só quando a régua de fato tranquiliza. A chamada barrada é **recusada**,
   não silenciosamente reescrita pelo backend.

6. **`available_actions` é definido pelo backend.** Nenhum campo vindo da IA influencia a lista.
   Regras: `simulate` só quando existe motor capaz de simular o assunto; plano ativo para o
   assunto oferece `view_plan` e **não** `save`; recomendação equivalente pendente oferece
   `view_recommendation`; `save` só quando não há nem plano nem recomendação.

7. **`available_actions` não é autorização.** O bloco persistido é snapshot do que foi exibido e
   **não é reescrito** quando surge um plano ou recomendação depois. Mas toda ação é revalidada
   no clique, contra o estado atual do perfil, e uma ação defasada retorna o estado atual
   (`view_plan` ou `view_recommendation`) em vez de criar um registro duplicado. A regra de
   equivalência usada na revalidação deve ser a **mesma** usada na montagem do bloco — duas
   implementações separadas divergiriam, e é a segunda que autoriza.

8. **O cliente não substitui o snapshot.** Ao salvar, o cliente envia apenas referências
   (`conversation_id`, `message_id`, `opportunity_id`). Assunto, diagnóstico, ações e evidências
   são lidos do bloco persistido. Não pode haver campo de conteúdo livre na rota que acabe no
   registro.

9. **Identidade é `topic` + `subject_key`.** Duas oportunidades do mesmo assunto sobre entidades
   diferentes (duas dívidas) são dois blocos; sobre a mesma entidade, um só. `subject_key` é
   validado contra as entidades reais do perfil — chave que não aponta para nada recusa o bloco.
   Sem entidade específica, a identidade é só o `topic`.

10. **Ciclo de vida da recomendação intocado.** Nenhum status `draft`. O ciclo segue
    `pending/approved/rejected/expired/superseded`, e o estado do cálculo mora separado em
    `simulation_status` (`not_simulated` / `simulated` / `not_required`). Nesta etapa
    `simulated` nunca é emitido.

11. **Compatibilidade com o que já está gravado.** Mensagem antiga sem `opportunities` continua
    sendo lida e renderizada. A coluna é nullable, **sem backfill**, e nenhuma mensagem
    persistida é migrada ou reescrita. Bloco gravado antes de `subject_key` existir continua
    válido.

12. **O guard anti-valor-inventado não regride.** Só tools de leitura contam como evidência para
    a checagem que substitui a resposta quando ela cita dinheiro sem lastro.
    `raise_opportunity` e `propose_simulation` não podem contar — foi exatamente essa brecha que
    o Meta Harness achou na VS-09.

13. **Sem regressão de testes.** Nenhum teste pré-existente removido ou marcado `skip`. Testes
    alterados só onde o contrato da rota mudou por pedido do usuário (critério 8), e a intenção
    original de cada um deve continuar coberta.

14. **Escopo respeitado**: nenhum arquivo de `apps/web` alterado, nenhuma migração aplicada no
    Docker em execução, catálogo de assuntos não ampliado além de `due_date_concentration`.

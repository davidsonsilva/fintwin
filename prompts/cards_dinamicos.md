# Refatoração definitiva dos cards responsivos do FinTwin

> **Instrução de execução:** leia este arquivo integralmente antes de alterar o código. Depois, implemente a refatoração no projeto atual. Não entregue apenas análise, plano ou pseudocódigo.

Atue como um Senior Front-end Engineer especializado em React, TypeScript, Tailwind CSS, componentização, CSS Grid, Flexbox e Container Queries.

# Estratégia incremental obrigatória

Não migre todos os cards de uma vez.

Esta refatoração deve ser executada incrementalmente, resolvendo e validando um problema por vez.

## Etapa 1 — Infraestrutura estrutural

Primeiro, crie somente a infraestrutura reutilizável:

- `Card.Root`;
- `Card.Header`;
- `Card.Content`;
- `Card.Footer`.

Nesse momento, não migre todos os cards do dashboard.

A infraestrutura deve controlar apenas a moldura e não deve conter regras específicas de métricas, valores, eventos, gráficos ou outros tipos de conteúdo.

## Etapa 2 — Card piloto

Após criar a infraestrutura, aplique-a somente no card:

`Próximos eventos financeiros`

Esse será o card piloto da refatoração.

Não altere os demais cards antes de concluir a validação do piloto.

O objetivo desta etapa é comprovar que a arquitetura funciona corretamente antes de propagá-la pelo projeto.

O card piloto deve preservar integralmente:

- conteúdo atual;
- textos;
- valores;
- cores;
- ícones;
- tipografia;
- tooltips;
- ações;
- identidade visual;
- comportamento funcional.

Não redesenhe o card.

## Etapa 3 — Validação do piloto

Valide o card piloto isoladamente em containers com aproximadamente:

- 180 px;
- 220 px;
- 260 px;
- 320 px;
- 400 px;
- 520 px.

Teste também:

- títulos longos;
- descrições longas;
- valores financeiros grandes;
- vários eventos;
- ausência e presença de footer;
- quebra de linha;
- crescimento vertical;
- alinhamento dos elementos.

Critérios obrigatórios:

- nenhum conteúdo pode ser cortado;
- não pode existir sobreposição;
- não pode existir scroll horizontal acidental;
- valores financeiros não podem usar `truncate`;
- o card deve crescer verticalmente quando necessário;
- o layout deve mudar de horizontal para vertical quando faltar espaço;
- a responsividade deve considerar a largura do próprio card;
- o Design System existente deve permanecer inalterado.

Execute também:

- TypeScript;
- lint;
- testes;
- build;
- validações visuais disponíveis no projeto.

## Etapa 4 — Correção da infraestrutura

Caso o card piloto apresente qualquer problema, corrija primeiro a infraestrutura ou a composição específica do piloto.

Não avance para os demais cards enquanto o card piloto não atender a todos os critérios de aceite.

Não crie exceções improvisadas dentro do componente estrutural apenas para fazer o piloto funcionar.

Regras específicas do conteúdo devem permanecer no componente concreto do card.

## Etapa 5 — Ponto de controle

Depois que o card piloto estiver implementado e validado:

1. apresente os arquivos alterados;
2. mostre a arquitetura criada;
3. informe os breakpoints de container utilizados;
4. apresente os resultados dos testes;
5. mostre o resultado de `git diff`;
6. mostre o resultado de `git status`;
7. aguarde minha avaliação antes de realizar uma migração ampla.

Não faça merge na `master`.

## Etapa 6 — Cards complexos

Somente após a validação do card piloto, aplique a infraestrutura aos cards mais complexos.

Considere complexos os cards que possuam:

- listas;
- gráficos;
- timelines;
- gauges;
- vários valores;
- ações;
- conteúdo que muda de orientação;
- dados que possam crescer dinamicamente.

Migre um tipo de card por vez.

Após cada tipo migrado:

- valide a responsividade;
- execute as verificações técnicas;
- corrija regressões antes de continuar.

## Etapa 7 — Cards simples

Somente depois da validação dos cards complexos, migre os cards simples, como:

- título e valor;
- título e descrição;
- métricas pequenas;
- indicadores com poucas informações.

Não altere todos os arquivos em massa sem validar cada grupo.

## Regra definitiva

A ordem obrigatória é:

`infraestrutura → card piloto → validação → cards complexos → cards simples`

Não execute:

`infraestrutura → migração de todos os cards → validação no final`

Resolver e validar um problema por vez é um requisito desta tarefa.

## Objetivo

Refatore o sistema de cards do dashboard para criar uma arquitetura reutilizável, responsiva e orientada por composição.

O problema atual é que os cards estão sendo tratados como se todos possuíssem a mesma estrutura interna. Isso está errado.

O componente genérico deve controlar somente a estrutura externa do card:

Card
├── Header
│   ├── Ícone opcional
│   ├── Título
│   └── Ajuda/tooltip opcional
├── Content
│   └── Conteúdo completamente livre
└── Footer opcional
    └── Botão, link ou qualquer ação

O conteúdo interno pode ser:

- um valor financeiro;
- uma métrica;
- uma lista;
- um gráfico;
- um gauge;
- uma timeline;
- uma tabela;
- uma lista de eventos;
- um radar de fragilidade;
- qualquer outra composição.

O componente base não deve tentar prever ou controlar esses formatos.

---

# Regra arquitetural principal

Não crie uma API como esta:

```tsx
<GenericCard
  title=""
  icon=""
  value=""
  subtitle=""
  description=""
  button=""
  layout="horizontal"
  variant="metric"
/>
```

Esse formato cria um componente cheio de condicionais, propriedades opcionais e regras específicas para cada conteúdo.

Use composição:

```tsx
<Card.Root>
  <Card.Header
    icon={...}
    title="..."
    help={...}
  />

  <Card.Content>
    {/* Estrutura específica deste card */}
  </Card.Content>

  <Card.Footer>
    {/* Ação opcional */}
  </Card.Footer>
</Card.Root>
```

Cada parte deve possuir uma responsabilidade única.

---

# Responsabilidades dos componentes

## `Card.Root`

Deve controlar somente:

* superfície;
* borda;
* border-radius;
* overflow;
* estrutura vertical;
* preenchimento da célula do grid;
* container query;
* comportamento geral de altura.

Estrutura recomendada:

```tsx
<article className="@container/card flex h-full min-h-0 min-w-0 flex-col overflow-hidden">
```

O `Card.Root` não deve conhecer valores, gráficos, métricas, datas ou tipos de conteúdo.

## `Card.Header`

Deve controlar:

* ícone opcional;
* título;
* tooltip opcional;
* alinhamento;
* quebra segura do título.

O título precisa aceitar uma ou várias linhas sem quebrar o card.

Utilize obrigatoriamente:

```css
min-width: 0;
overflow-wrap: anywhere;
```

Não aplique `truncate` ou `line-clamp` por padrão. O texto só deve ser cortado quando isso for uma decisão explícita daquele card.

## `Card.Content`

Deve ser completamente livre.

Ele deve apenas fornecer a área estrutural do conteúdo:

```tsx
<div className="min-h-0 min-w-0 flex-1">
  {children}
</div>
```

O layout interno deve ser definido pelo componente específico:

* `grid`;
* `flex`;
* `auto-fit`;
* `minmax`;
* container queries;
* quebra para coluna;
* reorganização de dados;
* gráfico responsivo.

## `Card.Footer`

Deve ser opcional.

Quando existir, deve permanecer na parte inferior do card usando:

```css
margin-top: auto;
```

O footer pode receber:

* botão;
* link;
* grupo de ações;
* conteúdo customizado.

Não presuma que todo footer será um botão.

---

# Responsividade obrigatória

A responsividade dos cards deve ser baseada principalmente na largura real do card, não apenas na largura da viewport.

Utilize Container Queries:

```tsx
<Card.Root className="@container/card">
```

Exemplos:

```tsx
<div className="
  grid
  grid-cols-[minmax(0,1fr)_auto]
  gap-3
  @max-[260px]/card:grid-cols-1
">
```

```tsx
<div className="
  grid
  grid-cols-[52px_minmax(0,1fr)_auto]
  gap-4
  @max-[340px]/card:grid-cols-[52px_minmax(0,1fr)]
  @max-[240px]/card:grid-cols-1
">
```

A reorganização deve acontecer de acordo com o espaço disponível.

Não basta reduzir fontes ou esconder conteúdo.

---

# Regras obrigatórias contra quebra de layout

Aplique corretamente:

```css
min-width: 0;
min-height: 0;
overflow-wrap: anywhere;
word-break: normal;
```

Em layouts Grid, utilize:

```css
minmax(0, 1fr);
```

Evite:

```css
grid-template-columns: 1fr auto;
```

quando o primeiro conteúdo puder crescer sem limite.

Prefira:

```css
grid-template-columns: minmax(0, 1fr) auto;
```

Valores financeiros como:

```text
R$ 33.070,35
R$ 2.950.000,00
R$ 850.000.000,00
```

não podem:

* escapar do card;
* ficar escondidos atrás de outro elemento;
* provocar scroll horizontal;
* sobrepor textos;
* ser cortados silenciosamente.

Quando não houver espaço horizontal, a composição deve mudar para coluna.

---

# Alturas

Não defina uma altura fixa global para todos os cards.

A altura deve ser determinada por:

1. conteúdo;
2. célula do grid;
3. necessidade específica do card;
4. variante explícita de layout.

É permitido que o `Card.Root` use `h-full` para preencher a célula onde está inserido.

Não é permitido usar alturas fixas para mascarar problemas de layout.

Cards de gráficos podem receber `min-height` na composição externa ou no componente específico:

```tsx
<Card.Root className="min-h-[420px]">
```

Essa regra não deve ser colocada em todos os cards.

---

# Implementação esperada

Crie uma estrutura semelhante a:

```text
components/
└── card/
    ├── Card.tsx
    ├── CardHeader.tsx
    ├── CardContent.tsx
    ├── CardFooter.tsx
    ├── card.types.ts
    └── index.ts
```

Ou implemente como Compound Components:

```tsx
export const Card = {
  Root: CardRoot,
  Header: CardHeader,
  Content: CardContent,
  Footer: CardFooter,
};
```

Prefira Compound Components, desde que a implementação permaneça simples, tipada e legível.

---

# API mínima esperada

```tsx
type CardRootProps = {
  children: React.ReactNode;
  className?: string;
};

type CardHeaderProps = {
  icon?: React.ReactNode;
  title: React.ReactNode;
  help?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
};

type CardContentProps = {
  children: React.ReactNode;
  className?: string;
};

type CardFooterProps = {
  children: React.ReactNode;
  className?: string;
};
```

Não adicione propriedades específicas como:

```tsx
value
amount
month
percentage
chart
events
status
metric
```

Essas informações pertencem aos componentes concretos, não ao card estrutural.

---

# Preserve o Design System existente

Não redesenhe o dashboard.

Preserve:

* cores;
* tokens CSS;
* tipografia;
* bordas;
* ícones;
* sombras;
* espaçamentos visuais;
* textos;
* comportamento dos tooltips;
* identidade visual atual do FinTwin.

A tarefa é corrigir arquitetura e responsividade, não criar outro design.

Não invente novas cores ou componentes visuais sem necessidade técnica.

---

# Componentes concretos

Após criar a infraestrutura base, migre inicialmente estes três tipos de card.

## 1. Card de autonomia

Exemplo:

```text
[ícone] Autonomia adversa [?]         3,6 meses
```

Comportamento:

* em cards largos, título e valor podem ficar na mesma linha;
* em cards estreitos, o valor deve ir para baixo;
* o título pode quebrar em duas linhas;
* tooltip nunca deve ser espremido ou sobreposto;
* nenhuma informação pode ser perdida.

## 2. Card de fragilidade

Exemplo:

```text
[ícone] Fragilidade detectada [?]
        3 encontradas

        Ver radar de fragilidade →
```

Comportamento:

* conteúdo pode ficar abaixo do título;
* ação pode estar no conteúdo ou footer conforme a semântica atual;
* em larguras estreitas, o botão deve ocupar a largura disponível;
* o texto da ação pode quebrar sem escapar da borda.

## 3. Card de próximos eventos financeiros

Cada evento possui:

* dia;
* mês;
* título;
* descrição;
* valor.

Em largura ampla:

```text
[data] [título e descrição] [valor]
```

Em largura intermediária:

```text
[data] [título e descrição]
       [valor]
```

Em largura muito estreita:

```text
[data]
[título]
[descrição]
[valor]
```

O valor não pode ficar cortado como ocorre atualmente.

O card pode crescer verticalmente quando necessário.

---

# Cards com gráficos

Cards como:

* Distribuição das despesas;
* Evolução do saldo líquido;
* Comprometimento da renda;

devem usar o mesmo `Card.Root`, `Card.Header`, `Card.Content` e `Card.Footer`.

Entretanto, cada gráfico mantém sua implementação interna própria.

Exemplo:

```tsx
<Card.Root>
  <Card.Header
    title="Evolução do saldo líquido"
    help={<HelpTooltip />}
  />

  <Card.Content>
    <BalanceChart />
  </Card.Content>

  <Card.Footer>
    <CardAction href="/historico">
      Ver histórico completo
    </CardAction>
  </Card.Footer>
</Card.Root>
```

O componente `Card` não deve saber que existe um gráfico.

O gráfico deve receber dimensões responsivas do container e não depender de largura fixa.

---

# Layout externo do dashboard

Separe claramente duas responsabilidades:

## Dashboard Grid

Responsável por:

* quantidade de colunas;
* largura das células;
* `col-span`;
* `row-span`;
* ordenação;
* distribuição geral dos cards.

## Card

Responsável por:

* estrutura interna;
* superfície;
* header;
* content;
* footer.

Não coloque regras específicas do dashboard dentro de `Card.Root`.

Exemplo:

```tsx
<div className="
  grid
  grid-cols-1
  gap-4
  md:grid-cols-2
  xl:grid-cols-4
">
  <MetricCard />
  <MetricCard />
  <AutonomyCard />
  <EventsCard className="xl:row-span-2" />
</div>
```

---

# Proibições

Não faça nenhuma destas soluções:

1. Não crie um único componente com dezenas de props opcionais.
2. Não use `overflow-hidden` para esconder valores que não cabem.
3. Não resolva responsividade apenas reduzindo fonte.
4. Não use largura fixa nos conteúdos.
5. Não use altura fixa para mascarar desalinhamento.
6. Não aplique `truncate` em valores financeiros.
7. Não mantenha layouts horizontais quando o espaço não comportar.
8. Não coloque todos os cards em um único componente cheio de variantes.
9. Não altere o Design System.
10. Não invente conteúdo, títulos ou valores.
11. Não force todos os cards a terem footer.
12. Não force todos os cards a terem ícone.
13. Não force todos os conteúdos a terem a mesma estrutura.

---

# Processo de execução

Antes de modificar arquivos:

1. Inspecione os componentes atuais de card.
2. Localize duplicações.
3. Identifique propriedades específicas misturadas à estrutura genérica.
4. Identifique alturas e larguras fixas.
5. Identifique usos incorretos de `overflow-hidden`, `truncate` e `line-clamp`.
6. Identifique quais grids externos controlam os cards.
7. Apresente um resumo curto do diagnóstico.

Depois:

1. Crie os componentes estruturais.
2. Migre os três cards de referência.
3. Preserve o comportamento e estilo visual.
4. Execute lint, TypeScript e testes existentes.
5. Corrija regressões.
6. Mostre os arquivos alterados.
7. Explique brevemente como novos cards devem ser criados.

Não pare apenas na análise. Faça a implementação.

---

# Cenários de validação

Valide os cards em containers com aproximadamente:

```text
180 px
220 px
260 px
320 px
400 px
520 px
```

Não valide somente mudando a largura total da janela.

Cada card deve ser testado dentro de um container individual.

Verifique:

* títulos curtos;
* títulos longos;
* valores pequenos;
* valores financeiros muito longos;
* presença e ausência de tooltip;
* presença e ausência de ícone;
* presença e ausência de footer;
* conteúdo com uma linha;
* conteúdo com múltiplas linhas;
* cards com gráficos;
* listas com vários itens.

---

# Critérios de aceite

A tarefa só estará concluída quando:

* existir um componente estrutural reutilizável;
* o conteúdo de cada card continuar livre;
* não houver scroll horizontal acidental;
* valores não forem cortados;
* textos não se sobrepuserem;
* títulos puderem quebrar;
* o footer continuar no final quando existir;
* cards sem footer funcionarem normalmente;
* cards estreitos se reorganizarem verticalmente;
* cards largos aproveitarem o espaço horizontal;
* a responsividade depender da largura do card;
* o Design System atual for preservado;
* TypeScript passar sem erros;
* lint e testes existentes passarem;
* não houver uma API genérica cheia de props específicas.

---

# Entrega final

Ao terminar, retorne:

1. diagnóstico encontrado;
2. arquitetura implementada;
3. arquivos criados e alterados;
4. cards migrados;
5. regras responsivas aplicadas;
6. comandos de validação executados;
7. resultado dos testes;
8. limitações restantes, caso existam;
9. exemplo de como criar um novo card usando a infraestrutura.

Implemente a solução de forma incremental e mantenha o código simples. Não crie abstrações além das necessárias.


## Regra de interpretação obrigatória

Importante: não interprete “reutilizável” como “todos os cards devem usar o mesmo layout interno”.

Reutilizável significa compartilhar apenas:

- superfície;
- header;
- área de conteúdo;
- footer opcional;
- regras estruturais básicas.

Cada card concreto continua responsável por sua própria composição interna.

Não redesenhe os cards. Não simplifique os conteúdos. Não esconda informações. Não tente corrigir tudo com alturas fixas, truncamento ou redução de fonte.

Primeiro entenda a arquitetura atual, depois implemente e valide visualmente em diferentes larguras de container.

O ponto que deve ficar inequívoco para o agente é:

> **O card genérico define a moldura. O componente concreto define o conteúdo e sua reorganização responsiva.**

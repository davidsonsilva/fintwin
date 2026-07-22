# FinTwin AI — Especificação Definitiva do MVP Web

> **Status:** Aprovada para implementação  
> **Abordagem:** Spec-Driven Development + Domain-Driven Design pragmático  
> **Produto:** Plataforma Web visual de simulação e prevenção financeira com agente de IA integrado  
> **Versão:** MVP v1  
> **Idioma da aplicação:** Português do Brasil  
> **Moeda inicial:** BRL

---

## 1. Visão do Produto

O **FinTwin AI** é uma plataforma Web de prevenção financeira pessoal.

Diferentemente de aplicativos que apenas categorizam despesas passadas, o FinTwin deverá projetar o futuro financeiro do usuário, identificar fragilidades, simular decisões antes que sejam tomadas e apresentar planos preventivos explicáveis.

O sistema será composto por:

1. um **motor financeiro determinístico**;
2. uma **API de aplicação**;
3. um **dashboard visual e interativo**;
4. um **simulador de decisões**;
5. um **radar de fragilidade financeira**;
6. um **agente conversacional integrado à interface**.

O usuário não deverá apenas conversar com o sistema. Ele deverá conseguir **visualizar o seu futuro financeiro** por meio de gráficos, comparações, cenários e evidências.

---

## 2. Proposta de Valor

O FinTwin deverá responder, de forma matemática, auditável e explicável, perguntas como:

- Por quanto tempo consigo manter minhas despesas se minha renda diminuir?
- Em qual mês meu saldo poderá ficar negativo?
- Quais são atualmente as minhas maiores fragilidades financeiras?
- Posso assumir um financiamento sem comprometer minha reserva?
- Qual será o impacto de uma compra sobre minhas metas?
- O que causa o déficit previsto em determinado mês?
- O que posso fazer hoje para evitar uma possível crise financeira?
- Qual é a diferença entre o meu cenário atual e uma decisão simulada?
- Como minha autonomia muda em um cenário adverso?

O diferencial central do produto é:

> **Prever riscos financeiros pessoais, simular decisões e demonstrar como evitar crises antes que elas ocorram.**

---

## 3. Princípios Obrigatórios

### 3.1 Motor financeiro determinístico

A LLM não poderá calcular valores financeiros diretamente.

Responsabilidades:

- **Domínio financeiro:** executa cálculos.
- **Aplicação:** coordena casos de uso.
- **Infraestrutura:** persiste e recupera dados.
- **API:** expõe operações de forma segura.
- **Front-end:** apresenta os resultados.
- **Agente de IA:** interpreta intenções e explica resultados.

A LLM poderá transformar uma pergunta em uma solicitação estruturada, mas deverá obrigatoriamente chamar um caso de uso do sistema para obter qualquer valor financeiro.

### 3.2 Rastreabilidade

Todo resultado relevante deverá informar:

- dados utilizados;
- premissas;
- fórmulas;
- período analisado;
- cenário aplicado;
- evidências;
- limitações;
- data de geração.

### 3.3 Sem números inventados

O sistema não poderá:

- inventar taxas;
- completar valores ausentes silenciosamente;
- estimar custos sem informar a premissa;
- produzir recomendações com dados insuficientes;
- tratar uma previsão como garantia.

Quando faltarem dados, o sistema deverá:

1. solicitar a informação ao usuário; ou
2. utilizar uma premissa explicitamente identificada e aprovada; ou
3. declarar que não possui dados suficientes.

### 3.4 Supervisão humana

Nenhuma ação financeira será executada no MVP.

A aprovação de um plano preventivo significará apenas:

- registrar a aprovação;
- atualizar o estado interno do plano;
- permitir acompanhamento visual.

Não haverá movimentação bancária, contratação, portabilidade, transferência ou pagamento automático.

---

## 4. Escopo Funcional do MVP

O MVP deverá possuir oito capacidades principais:

1. cadastro e importação de dados financeiros;
2. dashboard financeiro;
3. projeção de fluxo de caixa;
4. cálculo de autonomia financeira;
5. radar de fragilidade;
6. simulador de decisões;
7. planos preventivos;
8. agente conversacional visual.

---

# 5. Experiência Web

## 5.1 Diretriz de produto

O FinTwin será uma aplicação Web visual, não uma ferramenta CLI voltada ao usuário final.

Uma CLI técnica poderá existir apenas para:

- desenvolvimento;
- execução de migrações;
- carga de fixtures;
- diagnóstico;
- automação de testes.

A experiência principal deverá ocorrer no navegador.

## 5.2 Estrutura visual

A aplicação deverá utilizar:

- dashboard responsivo;
- cards de indicadores;
- gráficos interativos;
- tabelas;
- formulários;
- drawers ou modais de detalhes;
- comparação visual antes/depois;
- painel de chat persistente;
- estados de carregamento;
- estados vazios;
- mensagens de erro compreensíveis;
- tooltips para fórmulas e conceitos.

## 5.3 Requisitos de UX

A interface deverá:

- priorizar clareza sobre densidade;
- evitar “score mágico” sem explicação;
- permitir abrir as evidências de qualquer alerta;
- mostrar premissas de qualquer cenário;
- diferenciar dado real, dado informado e premissa;
- deixar explícito quando o agente está explicando um cálculo já realizado;
- permitir desfazer ou excluir simulações;
- manter histórico de simulações;
- permitir alternância entre cenários;
- destacar visualmente pontos de déficit;
- ser utilizável em desktop e tablet;
- possuir acessibilidade básica de teclado, contraste e labels.

---

# 6. Telas do MVP

## 6.1 Onboarding financeiro

Objetivo: coletar os dados mínimos para gerar o primeiro diagnóstico.

Etapas:

1. perfil;
2. contas e saldos;
3. fontes de renda;
4. despesas e obrigações;
5. dívidas;
6. metas;
7. eventos futuros;
8. revisão dos dados.

Dados:

- moeda;
- número de dependentes;
- capacidade declarada de redução de despesas;
- saldo das contas;
- reserva;
- rendas recorrentes;
- rendas pontuais;
- despesas essenciais;
- despesas não essenciais;
- parcelas;
- dívidas;
- assinaturas;
- impostos;
- seguros;
- metas;
- eventos futuros.

O onboarding deverá permitir:

- inserção manual;
- carga de dados fictícios de demonstração;
- importação posterior por CSV ou JSON.

## 6.2 Dashboard principal

A tela deverá responder:

> “Como está minha situação financeira e o que pode acontecer nos próximos meses?”

### Cards obrigatórios

- saldo líquido disponível;
- autonomia básica;
- autonomia provável;
- autonomia adversa;
- comprometimento da renda;
- próximo déficit previsto;
- quantidade de fragilidades;
- valor mensal de obrigações;
- progresso da principal meta.

### Seções obrigatórias

- gráfico de projeção;
- resumo dos cenários;
- fragilidades prioritárias;
- próximos eventos financeiros;
- plano preventivo ativo;
- atalhos para simulação;
- painel do agente.

## 6.3 Projeção financeira

Exibir gráfico de 12 meses com:

- entradas mensais;
- saídas mensais;
- saldo líquido mensal;
- saldo acumulado;
- linha de saldo zero;
- pontos de déficit;
- eventos futuros;
- marcações de decisões simuladas.

Filtros:

- cenário provável;
- cenário adverso;
- perda de renda;
- cenário personalizado;
- período de 3, 6 ou 12 meses.

Interações:

- tooltip por mês;
- clique em evento;
- visualização dos itens que compõem entradas e saídas;
- comparação entre cenários.

## 6.4 Autonomia financeira

Exibir:

- autonomia básica;
- autonomia ajustada;
- comparação entre cenários;
- faixa estimada;
- composição da queima mensal;
- ativos considerados elegíveis;
- despesas consideradas essenciais;
- premissas.

Evitar medidor isolado sem explicação.

## 6.5 Fragilidades

Exibir lista filtrável por:

- severidade;
- categoria;
- status;
- período.

Cada fragilidade deverá abrir um detalhe com:

- título;
- descrição;
- severidade;
- regra aplicada;
- fórmula;
- entradas;
- resultado;
- limite;
- evidência;
- impacto;
- plano recomendado;
- data da detecção.

## 6.6 Simulações

A página deverá possuir modelos iniciais para:

- compra à vista;
- compra parcelada;
- financiamento de veículo;
- empréstimo;
- nova despesa recorrente;
- redução de renda;
- perda de renda;
- criação de meta;
- aumento de reserva mensal.

A saída deverá mostrar:

- cenário antes;
- cenário depois;
- impacto no saldo;
- impacto na autonomia;
- impacto nas dívidas;
- impacto nas metas;
- primeiro déficit;
- custo total;
- premissas;
- gráfico comparativo;
- recomendação de prosseguir, revisar ou adiar, sem caráter de consultoria.

## 6.7 Planos preventivos

Exibir cards contendo:

- risco relacionado;
- ações propostas;
- impacto esperado;
- prazo;
- status;
- evidências;
- botão de aprovar;
- botão de rejeitar;
- acompanhamento.

Estados permitidos:

- `proposed`;
- `approved`;
- `rejected`;
- `in_progress`;
- `completed`;
- `cancelled`.

## 6.8 Agente visual

O agente deverá estar disponível:

- em painel lateral persistente; ou
- em drawer acessível globalmente.

Capacidades:

- explicar indicadores;
- explicar fragilidades;
- criar uma simulação estruturada;
- solicitar dados ausentes;
- comparar cenários;
- explicar o impacto de uma decisão;
- gerar um plano preventivo por meio dos casos de uso;
- navegar o usuário para a seção relevante;
- atualizar o dashboard após uma operação confirmada.

O agente não deverá substituir o dashboard.

---

# 7. Fluxo do Agente

Fluxo obrigatório:

```text
Usuário
  ↓
Interface conversacional
  ↓
Interpretador de intenção
  ↓
Schema estruturado e validado
  ↓
Caso de uso da aplicação
  ↓
Motor financeiro determinístico
  ↓
Resultado estruturado
  ↓
Agente explica
  ↓
Dashboard atualiza
```

Exemplo de intenção estruturada:

```json
{
  "intent": "simulate_vehicle_purchase",
  "parameters": {
    "price": "50000.00",
    "down_payment": "10000.00",
    "installments": 48,
    "installment_amount": "1350.00",
    "monthly_additional_costs": "900.00"
  }
}
```

O agente deverá validar o schema antes de chamar a API.

---

# 8. Projeção de Fluxo de Caixa

## 8.1 Horizonte

O motor deverá suportar:

- 3 meses;
- 6 meses;
- 12 meses.

O padrão do MVP será 12 meses.

## 8.2 Dados considerados

- saldo inicial;
- rendas recorrentes;
- rendas pontuais;
- despesas recorrentes;
- despesas pontuais;
- parcelas futuras;
- dívidas;
- assinaturas;
- impostos;
- seguros;
- metas;
- eventos futuros.

## 8.3 Saída por período

Para cada mês:

```json
{
  "period": "2026-08",
  "opening_balance": "15500.00",
  "income_total": "8000.00",
  "expense_total": "6900.00",
  "net_cashflow": "1100.00",
  "closing_balance": "16600.00",
  "income_commitment_percentage": "0.8625",
  "deficit": false
}
```

## 8.4 Saída consolidada

- primeiro mês com déficit;
- menor saldo projetado;
- saldo final;
- total de entradas;
- total de saídas;
- principais pressões;
- eventos relevantes;
- premissas;
- cenário.

---

# 9. Índice de Autonomia Financeira

## 9.1 Autonomia básica

```text
Autonomia Básica =
Ativos Líquidos Elegíveis /
Despesas Essenciais Mensais
```

## 9.2 Autonomia ajustada

```text
Autonomia Ajustada =
Ativos Líquidos Elegíveis /
Queima Mensal Ajustada ao Cenário
```

A queima ajustada poderá considerar:

- despesas essenciais;
- serviço da dívida;
- despesas sazonais provisionadas;
- variação de renda;
- concentração de renda;
- dependentes;
- eventos futuros;
- capacidade declarada de redução de despesas.

## 9.3 Apresentação

Exemplo:

```text
Autonomia básica: 5,2 meses
Cenário provável: 4,8 meses
Cenário adverso: 3,1 meses
Perda de renda: 2,6 meses
```

A aplicação deverá informar que os valores representam simulações baseadas nas premissas disponíveis.

---

# 10. Cenários Financeiros

## 10.1 Cenário provável

```yaml
income_multiplier: 1.00
essential_expense_multiplier: 1.00
nonessential_expense_multiplier: 1.00
unexpected_expense: 0
income_loss_months: 0
```

## 10.2 Cenário adverso

```yaml
income_multiplier: 0.75
essential_expense_multiplier: 1.05
nonessential_expense_multiplier: 0.90
unexpected_expense: configurable
income_loss_months: 0
```

## 10.3 Cenário de perda de renda

```yaml
income_multiplier: 0.00
essential_expense_multiplier: 1.00
nonessential_expense_multiplier: 0.70
unexpected_expense: configurable
income_loss_months: configurable
```

## 10.4 Cenário personalizado

O usuário poderá alterar:

- variação da renda;
- variação das despesas essenciais;
- variação das despesas não essenciais;
- despesa inesperada;
- duração da perda de renda;
- redução possível de gastos.

Todos os parâmetros deverão ser visíveis e persistidos junto à simulação.

---

# 11. Radar de Fragilidade

## 11.1 Regras iniciais

1. renda concentrada em uma única fonte acima de 80%;
2. despesas essenciais superiores a 60% da renda;
3. serviço da dívida superior a 30% da renda;
4. uso recorrente de crédito para despesas essenciais;
5. redução da reserva por três períodos consecutivos;
6. aumento de despesas recorrentes por três períodos consecutivos;
7. múltiplas obrigações relevantes vencendo na mesma semana;
8. saldo negativo projetado nos próximos 90 dias;
9. reserva inferior a três meses de despesas essenciais;
10. despesa anual sem provisionamento;
11. parcelas futuras não cobertas pela renda;
12. meta incompatível com o fluxo atual.

## 11.2 Estrutura obrigatória

```json
{
  "code": "INCOME_CONCENTRATION",
  "severity": "high",
  "title": "Renda concentrada",
  "description": "Mais de 80% da renda depende de uma única fonte.",
  "evidence": {
    "main_source_percentage": "0.92"
  },
  "formula": "main_source_income / total_income",
  "threshold": "0.80",
  "detected_at": "2026-07-22"
}
```

Severidades:

- `low`;
- `medium`;
- `high`;
- `critical`.

Nenhuma fragilidade poderá existir sem evidência.

---

# 12. Simulador de Decisões

## 12.1 Casos de uso

- compra à vista;
- compra parcelada;
- financiamento;
- empréstimo;
- perda de renda;
- redução salarial;
- nova despesa recorrente;
- nova meta;
- aumento de reserva.

## 12.2 Comparação obrigatória

```json
{
  "baseline": {},
  "simulated": {},
  "impact": {
    "autonomy_delta_months": "-2.3",
    "closing_balance_delta": "-14500.00",
    "goal_delay_months": 12,
    "new_first_deficit_period": "2026-11"
  }
}
```

## 12.3 Custo total

Para financiamento:

```text
Custo Total =
Entrada +
Soma das Parcelas +
Custos Recorrentes Informados +
Custos Pontuais Informados
```

O custo de oportunidade somente poderá ser calculado quando existir uma taxa explicitamente informada e identificada.

Nenhuma taxa externa será buscada no MVP.

---

# 13. Planos Preventivos

Os planos deverão ser gerados apenas a partir de:

- fragilidades detectadas;
- simulações;
- metas;
- fluxo projetado.

Estrutura:

```json
{
  "id": "plan-001",
  "risk_code": "NEGATIVE_BALANCE_90_DAYS",
  "status": "proposed",
  "actions": [
    {
      "description": "Reservar R$ 500 por mês durante três meses.",
      "expected_monthly_impact": "500.00",
      "due_date": "2026-10-31"
    }
  ],
  "expected_result": {
    "deficit_avoided": true,
    "autonomy_change_months": "1.5"
  },
  "requires_approval": true
}
```

Ações possíveis:

- provisionar despesa anual;
- reduzir categoria recorrente;
- adiar compra;
- aumentar reserva;
- reorganizar vencimentos;
- revisar assinaturas;
- priorizar quitação de dívida;
- ajustar meta;
- aumentar margem de segurança.

---

# 14. Linguagem Ubíqua

- **FinTwin:** projeção derivada do estado financeiro.
- **Autonomia Financeira:** tempo estimado de sustentação das obrigações.
- **Fragilidade:** risco identificado por regra verificável.
- **Evidência:** dado que sustenta uma conclusão.
- **Cenário:** conjunto explícito de premissas.
- **Simulação:** comparação entre estado-base e estado alterado.
- **Decisão Financeira:** evento hipotético avaliado.
- **Plano Preventivo:** conjunto de ações propostas.
- **Obrigação Financeira:** compromisso presente ou futuro.
- **Evento Financeiro:** entrada ou saída pontual ou recorrente.
- **Ativo Elegível:** recurso líquido considerado na autonomia.
- **Queima Mensal:** consumo financeiro mensal usado na autonomia.
- **Déficit:** saldo acumulado inferior a zero.

---

# 15. Modelo de Domínio

## 15.1 Agregados e entidades

### FinancialProfile

```text
id
currency
dependents
monthly_expense_reduction_capacity
created_at
updated_at
```

### FinancialAccount

```text
id
profile_id
description
balance
liquidity_type
eligible_for_autonomy
```

### IncomeSource

```text
id
profile_id
description
amount
frequency
start_date
end_date
stability
```

### FinancialObligation

```text
id
profile_id
description
amount
category
frequency
due_day
start_date
end_date
essential
debt_related
```

### Debt

```text
id
profile_id
description
outstanding_balance
installment_amount
remaining_installments
interest_rate_optional
due_day
```

### FinancialGoal

```text
id
profile_id
description
target_amount
current_amount
deadline
priority
monthly_contribution
```

### FinancialEvent

```text
id
profile_id
description
event_type
amount
date
recurrence
direction
```

### Simulation

```text
id
profile_id
type
parameters
baseline_result
simulated_result
created_at
```

### FragilityFinding

```text
id
profile_id
code
severity
evidence
detected_at
status
```

### PreventivePlan

```text
id
profile_id
risk_code
status
actions
expected_result
created_at
approved_at
```

## 15.2 Value Objects

- `Money`;
- `Percentage`;
- `AutonomyMonths`;
- `ProjectionPeriod`;
- `Severity`;
- `Recurrence`;
- `ScenarioType`;
- `LiquidityType`;
- `PlanStatus`;
- `Currency`;
- `DateRange`.

### Money

Requisitos:

- usar `Decimal`;
- proibir `float`;
- armazenar moeda;
- impedir operações entre moedas diferentes;
- aplicar arredondamento definido;
- rejeitar valor inválido;
- serializar como string em JSON.

---

# 16. Arquitetura Técnica

## 16.1 Estilo arquitetural

- monólito modular;
- API separada do front-end;
- domínio independente;
- sem microsserviços no MVP;
- sem event sourcing no MVP;
- sem CQRS complexo;
- sem abstrações prematuras.

## 16.2 Front-end

Stack recomendada:

- Next.js;
- TypeScript;
- React;
- Tailwind CSS;
- shadcn/ui;
- Recharts;
- React Hook Form;
- Zod;
- TanStack Query.

Responsabilidades:

- dashboard;
- gráficos;
- formulários;
- onboarding;
- chat;
- comparação de cenários;
- visualização de evidências;
- planos preventivos;
- estados de carregamento e erro.

## 16.3 Back-end

Stack recomendada:

- Python 3.12;
- FastAPI;
- Pydantic;
- SQLAlchemy;
- Alembic;
- PostgreSQL;
- pytest.

Responsabilidades:

- domínio;
- casos de uso;
- projeções;
- autonomia;
- fragilidades;
- simulações;
- planos;
- persistência;
- autenticação futura;
- API.

## 16.4 Agente de IA

O agente será implementado somente após o motor e o dashboard estarem estáveis.

No MVP, a primeira versão poderá usar:

- tool calling nativo do provedor escolhido;
- schemas Pydantic;
- camada de autorização;
- histórico curto de conversa;
- chamadas exclusivas aos casos de uso permitidos.

Não usar LangChain ou LangGraph automaticamente. Adotar apenas se existir necessidade concreta comprovada.

---

# 17. Estrutura de Repositório

```text
fintwin/
├── apps/
│   ├── web/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── lib/
│   │   ├── hooks/
│   │   ├── tests/
│   │   └── package.json
│   └── api/
│       ├── src/
│       │   ├── domain/
│       │   │   ├── shared/
│       │   │   ├── financial_profile/
│       │   │   ├── cashflow/
│       │   │   ├── autonomy/
│       │   │   ├── fragility/
│       │   │   ├── decisions/
│       │   │   ├── obligations/
│       │   │   └── preventive_plans/
│       │   ├── application/
│       │   │   ├── use_cases/
│       │   │   └── dto/
│       │   ├── infrastructure/
│       │   │   ├── persistence/
│       │   │   ├── repositories/
│       │   │   └── ai/
│       │   └── interfaces/
│       │       └── http/
│       ├── tests/
│       │   ├── unit/
│       │   ├── integration/
│       │   └── fixtures/
│       └── pyproject.toml
├── packages/
│   └── contracts/
├── data/
│   └── demo/
├── docs/
│   ├── Spec.md
│   ├── architecture/
│   └── decisions/
├── docker-compose.yml
├── .env.example
├── README.md
└── Makefile
```

---

# 18. API do MVP

## 18.1 Perfil

```text
POST   /api/v1/profiles
GET    /api/v1/profiles/{profile_id}
PUT    /api/v1/profiles/{profile_id}
```

## 18.2 Contas

```text
POST   /api/v1/profiles/{profile_id}/accounts
GET    /api/v1/profiles/{profile_id}/accounts
PUT    /api/v1/accounts/{account_id}
DELETE /api/v1/accounts/{account_id}
```

## 18.3 Rendas

```text
POST   /api/v1/profiles/{profile_id}/incomes
GET    /api/v1/profiles/{profile_id}/incomes
PUT    /api/v1/incomes/{income_id}
DELETE /api/v1/incomes/{income_id}
```

## 18.4 Obrigações, dívidas, metas e eventos

Implementar CRUD mínimo seguindo o mesmo padrão.

## 18.5 Dashboard

```text
GET /api/v1/profiles/{profile_id}/dashboard
```

## 18.6 Projeções

```text
POST /api/v1/profiles/{profile_id}/projections
```

Payload:

```json
{
  "months": 12,
  "scenario": "probable",
  "parameters": {}
}
```

## 18.7 Autonomia

```text
POST /api/v1/profiles/{profile_id}/autonomy
```

## 18.8 Fragilidades

```text
POST /api/v1/profiles/{profile_id}/fragilities/detect
GET  /api/v1/profiles/{profile_id}/fragilities
```

## 18.9 Simulações

```text
POST /api/v1/profiles/{profile_id}/simulations
GET  /api/v1/profiles/{profile_id}/simulations
GET  /api/v1/simulations/{simulation_id}
DELETE /api/v1/simulations/{simulation_id}
```

## 18.10 Planos

```text
POST /api/v1/profiles/{profile_id}/plans/generate
GET  /api/v1/profiles/{profile_id}/plans
PATCH /api/v1/plans/{plan_id}/status
```

## 18.11 Agente

```text
POST /api/v1/profiles/{profile_id}/agent/messages
```

O endpoint deverá retornar:

- resposta textual;
- ferramentas acionadas;
- referências aos cálculos;
- componentes que devem ser atualizados;
- perguntas pendentes;
- limitações.

---

# 19. Contratos de Resposta

Toda resposta analítica deverá possuir:

```json
{
  "data": {},
  "evidence": [],
  "assumptions": [],
  "limitations": [],
  "generated_at": "2026-07-22T12:00:00Z",
  "version": "v1"
}
```

Erros:

```json
{
  "error": {
    "code": "INSUFFICIENT_DATA",
    "message": "Não há dados suficientes para calcular a autonomia.",
    "details": {
      "missing_fields": ["essential_monthly_expenses"]
    }
  }
}
```

---

# 20. Dados de Demonstração

Criar um perfil fictício completo.

```text
data/demo/
├── profile.json
├── accounts.json
├── incomes.json
├── obligations.json
├── debts.json
├── goals.json
├── future_events.json
└── simulations/
    └── vehicle_purchase.json
```

Os dados devem gerar propositalmente:

- renda concentrada;
- reserva moderada;
- despesa anual sem provisionamento;
- possível déficit;
- meta impactada por financiamento.

O dashboard deverá possuir ação:

> **Carregar demonstração**

---

# 21. Visualizações Obrigatórias

## 21.1 Gráfico de fluxo de caixa

Tipo:

- linha para saldo acumulado;
- barras para entradas e saídas;
- linha horizontal no zero;
- marcadores para eventos.

## 21.2 Comparação de cenários

Tipo:

- linhas múltiplas;
- provável;
- adverso;
- perda de renda.

## 21.3 Composição das despesas

Tipo:

- barras horizontais ou donut;
- essencial;
- não essencial;
- dívida;
- metas;
- outros.

## 21.4 Autonomia

Tipo:

- barras comparativas;
- evitar gauge isolado.

## 21.5 Simulação antes/depois

Tipo:

- cards comparativos;
- gráfico de linhas;
- tabela de diferenças.

## 21.6 Fragilidades

Tipo:

- lista priorizada;
- badges de severidade;
- timeline opcional.

---

# 22. Requisitos de Front-end

- TypeScript estrito;
- componentes reutilizáveis;
- separação por feature;
- schemas Zod compartilhados;
- sem lógica financeira no front-end;
- tratamento de loading, empty, success e error;
- responsividade;
- acessibilidade;
- testes de componentes críticos;
- formatação brasileira de moeda e datas;
- tema claro e escuro, se não comprometer a entrega;
- design profissional, tecnológico e confiável;
- evitar estética excessivamente bancária ou genérica;
- não usar botões ou elementos falsamente clicáveis.

---

# 23. Requisitos de Back-end

- domínio sem dependência de FastAPI;
- casos de uso explícitos;
- repositórios por interface;
- transações de banco;
- validações Pydantic na borda;
- `Decimal` no domínio;
- migrações Alembic;
- relógio injetável;
- respostas versionadas;
- logs estruturados;
- nenhum dado sensível completo em logs;
- tratamento centralizado de erros;
- documentação OpenAPI.

---

# 24. Persistência

PostgreSQL no ambiente principal do MVP.

SQLite poderá ser usado apenas em testes locais, caso a compatibilidade seja garantida.

Entidades mínimas:

- profiles;
- accounts;
- income_sources;
- obligations;
- debts;
- financial_goals;
- financial_events;
- simulations;
- simulation_results;
- fragility_findings;
- preventive_plans;
- preventive_plan_actions;
- conversations;
- agent_messages.

---

# 25. Segurança e Privacidade

Implementar:

- dados de demonstração fictícios;
- nenhuma telemetria por padrão;
- nenhuma chamada externa não documentada;
- variáveis sensíveis em ambiente;
- validação de upload;
- limite de tamanho de arquivos;
- sanitização de nomes;
- logs sem saldos completos;
- proteção contra prompt injection em conteúdo importado;
- allowlist de ferramentas do agente;
- aprovação explícita para alterar dados persistidos;
- separação entre mensagem do usuário e instruções de sistema.

Aviso obrigatório:

> O FinTwin AI MVP é uma ferramenta educacional e de simulação. Ele não oferece consultoria financeira, recomendação de investimento ou garantia sobre resultados futuros.

---

# 26. Fora do Escopo do MVP

Não implementar:

- Open Finance real;
- integração bancária;
- recomendação de investimentos;
- compra ou venda de ativos;
- suitability;
- comparação de fundos;
- ações, ETFs ou criptomoedas;
- Yahoo Finance;
- InfoMoney;
- coleta de notícias;
- RAG;
- banco vetorial;
- embeddings;
- LangGraph;
- LangChain;
- pagamentos;
- transferências;
- portabilidade automática;
- contratação de produtos;
- autenticação bancária;
- aplicativo mobile;
- microsserviços;
- alertas por WhatsApp;
- dados financeiros oficiais externos;
- execução autônoma de ações.

---

# 27. Estratégia de Testes

## 27.1 Back-end

Usar `pytest`.

Cobrir:

- Money;
- Percentage;
- recorrências;
- projeção mensal;
- saldo acumulado;
- primeiro déficit;
- autonomia básica;
- autonomia ajustada;
- cenários;
- concentração de renda;
- comprometimento com dívida;
- ausência de reserva;
- despesa anual sem provisionamento;
- simulação antes/depois;
- plano preventivo;
- serialização;
- validação;
- endpoints principais;
- persistência.

Metas:

```text
Domínio: mínimo 90%
Projeto back-end: mínimo 80%
```

## 27.2 Front-end

Cobrir:

- cards do dashboard;
- gráfico de projeção;
- formulário de simulação;
- estados vazios;
- detalhes da fragilidade;
- aprovação de plano;
- fluxo do agente com API mockada.

## 27.3 End-to-end

Fluxo mínimo:

1. carregar demonstração;
2. visualizar dashboard;
3. abrir fragilidade;
4. executar simulação;
5. comparar antes/depois;
6. gerar plano;
7. aprovar plano;
8. perguntar ao agente sobre a simulação.

---

# 28. Observabilidade

Implementar:

- logs estruturados;
- correlation id por requisição;
- duração de casos de uso;
- erros de validação;
- falhas do agente;
- ferramenta chamada pelo agente;
- sem registrar conteúdo financeiro sensível integral.

Não implementar stack externa complexa de observabilidade no MVP.

---

# 29. Ambiente e Execução

Fornecer:

- `docker-compose.yml`;
- PostgreSQL;
- API;
- Web;
- `.env.example`;
- migrações;
- seed de demonstração;
- comandos de desenvolvimento;
- comandos de testes.

Comandos esperados:

```bash
docker compose up --build
```

```bash
make test
```

```bash
make seed-demo
```

O README deverá explicar execução em Windows PowerShell.

---

# 30. Vertical Slices

## VS-01 — Fundação do repositório e domínio

Entregar:

- monorepo;
- configuração Web e API;
- Docker Compose;
- PostgreSQL;
- estrutura modular;
- `Money`;
- `Percentage`;
- enums;
- entidades principais;
- testes;
- README inicial.

Não entregar dashboard funcional.

## VS-02 — Persistência e onboarding

Entregar:

- migrações;
- repositórios;
- CRUD mínimo;
- onboarding visual;
- perfil de demonstração;
- validações;
- testes.

## VS-03 — Dashboard básico

Entregar:

- layout;
- navegação;
- cards;
- resumo financeiro;
- integração Web/API;
- loading;
- empty;
- error;
- dados demo.

## VS-04 — Projeção e gráficos

Entregar:

- motor de projeção;
- API;
- gráfico de 12 meses;
- eventos;
- déficit;
- detalhes mensais;
- cenários provável e adverso.

## VS-05 — Autonomia financeira

Entregar:

- autonomia básica;
- autonomia ajustada;
- cenário de perda de renda;
- visualização comparativa;
- evidências;
- premissas.

## VS-06 — Radar de fragilidade

Entregar:

- regras;
- detector;
- severidades;
- evidências;
- lista;
- filtros;
- detalhe visual.

## VS-07 — Simulador visual

Entregar:

- modelos de decisão;
- formulários;
- cenário-base;
- cenário simulado;
- comparação;
- gráfico;
- histórico.

## VS-08 — Planos preventivos

Entregar:

- gerador por regras;
- cards;
- aprovação;
- rejeição;
- acompanhamento;
- impacto esperado.

## VS-09 — Agente conversacional

Entregar:

- painel lateral;
- schemas de intenção;
- tool calling;
- explicações fundamentadas;
- atualização do dashboard;
- tratamento de dados insuficientes;
- histórico básico.

## VS-10 — Consolidação do MVP

Entregar:

- testes E2E;
- melhorias de UX;
- acessibilidade;
- documentação;
- segurança;
- seed;
- demonstração ponta a ponta;
- relatório de limitações.

Não iniciar uma slice enquanto a anterior estiver com testes quebrados.

---

# 31. Critérios de Aceitação do MVP

O MVP será considerado concluído quando:

1. executar via Docker Compose;
2. possuir aplicação Web funcional;
3. permitir cadastrar ou carregar dados de demonstração;
4. persistir os dados;
5. apresentar dashboard;
6. projetar 12 meses;
7. exibir gráficos;
8. identificar primeiro déficit;
9. calcular autonomia básica;
10. calcular autonomia ajustada;
11. detectar ao menos oito fragilidades;
12. exibir evidências;
13. simular ao menos cinco tipos de decisão;
14. comparar antes e depois;
15. gerar plano preventivo;
16. permitir aprovar ou rejeitar o plano;
17. possuir agente visual;
18. impedir que o agente calcule valores por conta própria;
19. funcionar sem fontes financeiras externas;
20. não recomendar investimentos;
21. não utilizar `float` para dinheiro;
22. possuir testes automatizados;
23. explicar premissas e limitações;
24. possuir demonstração ponta a ponta;
25. possuir README para Windows e Docker.

---

# 32. Decisões Arquiteturais Obrigatórias

1. O produto é Web.
2. O dashboard é a experiência principal.
3. O agente é uma camada sobre o motor, não o núcleo.
4. O domínio financeiro é determinístico.
5. O front-end não executa regras financeiras.
6. O MVP será um monólito modular.
7. Não haverá Open Finance real.
8. Não haverá investimentos.
9. Não haverá RAG.
10. Não haverá integrações de mercado.
11. Não haverá execução financeira.
12. Dados monetários usam `Decimal`.
13. Resultados possuem evidências.
14. Cenários possuem premissas explícitas.
15. Simulações sempre comparam antes e depois.

---

# 33. Prompt Master para o Claude Code

Você é o Principal Software Engineer responsável pela implementação do MVP Web do FinTwin AI.

Leia integralmente `docs/Spec.md` antes de modificar qualquer arquivo.

O FinTwin AI é uma plataforma Web visual de simulação e prevenção financeira. A aplicação deverá possuir dashboard, gráficos, projeção, autonomia, radar de fragilidade, simulador de decisões, planos preventivos e um agente conversacional integrado.

## Regras obrigatórias

1. Use exatamente a especificação como fonte de verdade.
2. Não implemente funcionalidades fora da Vertical Slice atual.
3. Não invente requisitos.
4. Não adicione tecnologias sem necessidade comprovada.
5. Use Python 3.12 no back-end.
6. Use FastAPI, Pydantic, SQLAlchemy, Alembic e PostgreSQL.
7. Use Next.js, TypeScript, Tailwind, shadcn/ui, Recharts, Zod e TanStack Query.
8. Use `Decimal` para dinheiro.
9. Não use `float` em cálculos monetários.
10. Mantenha o domínio independente de FastAPI, banco e front-end.
11. Não coloque regras financeiras no front-end.
12. Implemente como monólito modular.
13. Não implemente Open Finance, RAG, LangChain, LangGraph, notícias ou investimentos.
14. Nenhuma ação financeira será executada.
15. Todo cálculo deverá ser determinístico.
16. Toda fragilidade deverá possuir evidência.
17. Toda simulação deverá comparar cenário-base e cenário simulado.
18. Toda resposta do agente que contenha números deverá vir de um caso de uso.
19. Não faça overengineering.
20. Prefira código simples, explícito e testável.

## Processo obrigatório para cada Vertical Slice

Antes de implementar:

1. leia a especificação;
2. inspecione o repositório;
3. identifique arquivos relevantes;
4. apresente um plano curto;
5. liste decisões técnicas;
6. liste critérios de aceitação;
7. implemente somente a slice;
8. execute testes;
9. execute demonstração;
10. revise o diff;
11. informe limitações;
12. indique a próxima slice.

## Ordem obrigatória

```text
VS-01 Fundação do repositório e domínio
VS-02 Persistência e onboarding
VS-03 Dashboard básico
VS-04 Projeção e gráficos
VS-05 Autonomia financeira
VS-06 Radar de fragilidade
VS-07 Simulador visual
VS-08 Planos preventivos
VS-09 Agente conversacional
VS-10 Consolidação do MVP
```

## Execução atual

Execute apenas a **VS-01**.

## Entrega da VS-01

Criar:

- monorepo;
- aplicação Next.js;
- aplicação FastAPI;
- Docker Compose;
- PostgreSQL;
- estrutura modular;
- Value Object `Money`;
- Value Object `Percentage`;
- tipos e enums;
- entidades principais;
- testes unitários;
- README inicial;
- `.env.example`;
- comandos para executar e testar.

## Critérios de aceite da VS-01

- Web e API inicializam;
- PostgreSQL inicializa;
- Docker Compose funciona;
- Python 3.12 configurado;
- TypeScript estrito;
- `pytest` passa;
- testes do front-end passam;
- dinheiro usa `Decimal`;
- moedas incompatíveis são rejeitadas;
- entidades inválidas são rejeitadas;
- domínio não depende da infraestrutura;
- nenhuma capacidade das slices seguintes foi implementada;
- árvore de arquivos está documentada.

## Formato da resposta ao concluir

```text
1. Resumo da implementação
2. Arquivos criados ou modificados
3. Decisões técnicas
4. Testes executados
5. Resultado dos testes
6. Como executar
7. Demonstração realizada
8. Limitações intencionais
9. Riscos encontrados
10. Próxima Vertical Slice
```

---

# 34. Resultado Esperado

Ao final do MVP, o FinTwin deverá ser demonstrável como:

> **Uma plataforma Web visual que projeta o futuro financeiro do usuário, detecta fragilidades, simula decisões, apresenta planos preventivos e permite conversar com um agente de IA que explica resultados produzidos por um motor matemático confiável.**

O produto não deverá ser apresentado como um chatbot financeiro genérico.

O dashboard e o motor de simulação constituem o produto principal. O agente será a camada de interação inteligente sobre essas capacidades.

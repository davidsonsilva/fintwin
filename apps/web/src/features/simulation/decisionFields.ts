import type { DecisionType } from "./types";

export interface DecisionFieldConfig {
  name: string;
  label: string;
  type: "text" | "number" | "checkbox" | "date" | "income-select";
  optional?: boolean;
}

export const DECISION_LABELS: Record<DecisionType, string> = {
  CASH_PURCHASE: "Compra à vista",
  INSTALLMENT_PURCHASE: "Compra parcelada",
  FINANCING: "Financiamento",
  LOAN: "Empréstimo",
  INCOME_LOSS: "Perda de renda",
  SALARY_REDUCTION: "Redução salarial",
  NEW_RECURRING_EXPENSE: "Nova despesa recorrente",
  NEW_GOAL: "Nova meta",
  RESERVE_INCREASE: "Aumento de reserva",
};

export const DECISION_FIELDS: Record<DecisionType, DecisionFieldConfig[]> = {
  CASH_PURCHASE: [
    { name: "description", label: "Descrição", type: "text" },
    { name: "amount", label: "Valor", type: "number" },
    { name: "category", label: "Categoria", type: "text", optional: true },
  ],
  INSTALLMENT_PURCHASE: [
    { name: "description", label: "Descrição", type: "text" },
    { name: "amount", label: "Valor total", type: "number" },
    { name: "down_payment", label: "Entrada", type: "number", optional: true },
    { name: "installments", label: "Número de parcelas", type: "number" },
  ],
  FINANCING: [
    { name: "description", label: "Descrição", type: "text" },
    { name: "total_amount", label: "Valor total", type: "number" },
    { name: "down_payment", label: "Entrada", type: "number", optional: true },
    { name: "installments", label: "Número de parcelas", type: "number" },
    { name: "interest_rate_optional", label: "Taxa de juros (opcional)", type: "text", optional: true },
    { name: "recurring_cost_description", label: "Custo recorrente — descrição", type: "text", optional: true },
    { name: "recurring_cost_amount", label: "Custo recorrente — valor mensal", type: "number", optional: true },
    { name: "one_off_cost_description", label: "Custo pontual — descrição", type: "text", optional: true },
    { name: "one_off_cost_amount", label: "Custo pontual — valor", type: "number", optional: true },
  ],
  LOAN: [
    { name: "description", label: "Descrição", type: "text" },
    { name: "amount", label: "Valor do empréstimo", type: "number" },
    { name: "installments", label: "Número de parcelas", type: "number" },
  ],
  INCOME_LOSS: [
    { name: "income_source_id", label: "Fonte de renda afetada", type: "income-select" },
    { name: "months", label: "Duração (meses)", type: "number" },
    { name: "reduction_pct", label: "Percentual de perda (0 a 1)", type: "number", optional: true },
  ],
  SALARY_REDUCTION: [
    { name: "income_source_id", label: "Fonte de renda afetada", type: "income-select" },
    { name: "reduction_pct", label: "Percentual de redução (0 a 1)", type: "number" },
    { name: "months", label: "Duração em meses (vazio = permanente)", type: "number", optional: true },
  ],
  NEW_RECURRING_EXPENSE: [
    { name: "description", label: "Descrição", type: "text" },
    { name: "amount", label: "Valor mensal", type: "number" },
    { name: "category", label: "Categoria", type: "text" },
    { name: "essential", label: "Despesa essencial", type: "checkbox" },
  ],
  NEW_GOAL: [
    { name: "description", label: "Descrição", type: "text" },
    { name: "target_amount", label: "Valor alvo", type: "number" },
    { name: "current_amount", label: "Valor já acumulado", type: "number", optional: true },
    { name: "monthly_contribution", label: "Contribuição mensal", type: "number" },
    { name: "priority", label: "Prioridade", type: "number", optional: true },
    { name: "deadline", label: "Prazo", type: "date", optional: true },
  ],
  RESERVE_INCREASE: [
    { name: "monthly_amount", label: "Valor mensal reservado", type: "number" },
    { name: "description", label: "Descrição", type: "text", optional: true },
  ],
};

export function buildParameters(decisionType: DecisionType, values: Record<string, string | boolean>): Record<string, unknown> {
  const parameters: Record<string, unknown> = {};
  for (const field of DECISION_FIELDS[decisionType]) {
    const value = values[field.name];
    if (value === undefined || value === "") continue;
    parameters[field.name] = field.type === "checkbox" ? !!value : value;
  }

  if (decisionType === "FINANCING") {
    const costDescription = values["recurring_cost_description"];
    const costAmount = values["recurring_cost_amount"];
    if (costDescription && costAmount) {
      parameters.recurring_costs = [{ description: costDescription, amount: costAmount }];
    }
    delete parameters.recurring_cost_description;
    delete parameters.recurring_cost_amount;

    const oneOffDescription = values["one_off_cost_description"];
    const oneOffAmount = values["one_off_cost_amount"];
    if (oneOffDescription && oneOffAmount) {
      parameters.one_off_costs = [{ description: oneOffDescription, amount: oneOffAmount }];
    }
    delete parameters.one_off_cost_description;
    delete parameters.one_off_cost_amount;
  }

  return parameters;
}

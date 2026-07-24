import { ZodType } from "zod";

import { onboardingApi } from "./api";
import {
  accountSchema,
  debtSchema,
  directionOptions,
  eventSchema,
  goalSchema,
  incomeSchema,
  incomeStabilityOptions,
  liquidityTypeOptions,
  obligationSchema,
  recurrenceOptions,
} from "./schemas";

export type FieldConfig =
  | { name: string; label: string; type: "text" }
  | { name: string; label: string; type: "number" }
  | { name: string; label: string; type: "date" }
  | { name: string; label: string; type: "checkbox" }
  | { name: string; label: string; type: "select"; options: readonly string[] }
  | { name: string; label: string; type: "money" };

export interface ResourceStepConfig<T extends Record<string, unknown>> {
  key: string;
  title: string;
  emptyLabel: string;
  fields: FieldConfig[];
  schema: ZodType<T>;
  defaultValues: T;
  create: (profileId: string, payload: T) => Promise<unknown>;
  list: (profileId: string) => Promise<unknown[]>;
  renderSummary: (item: Record<string, unknown>) => string;
}

export const accountStepConfig: ResourceStepConfig<any> = {
  key: "accounts",
  title: "Contas e saldos",
  emptyLabel: "Nenhuma conta adicionada ainda.",
  fields: [
    { name: "description", label: "Descrição", type: "text" },
    { name: "balance", label: "Saldo", type: "money" },
    { name: "liquidity_type", label: "Tipo de liquidez", type: "select", options: liquidityTypeOptions },
    { name: "eligible_for_autonomy", label: "Elegível para autonomia financeira", type: "checkbox" },
  ],
  schema: accountSchema,
  defaultValues: {
    description: "",
    balance: { amount: "", currency: "BRL" },
    liquidity_type: "checking_account",
    eligible_for_autonomy: false,
  },
  create: (profileId, payload) => onboardingApi.createAccount(profileId, payload),
  list: (profileId) => onboardingApi.listAccounts(profileId),
  renderSummary: (item) => `${item.description} — ${(item.balance as any).amount} ${(item.balance as any).currency}`,
};

export const incomeStepConfig: ResourceStepConfig<any> = {
  key: "incomes",
  title: "Rendas",
  emptyLabel: "Nenhuma renda adicionada ainda.",
  fields: [
    { name: "description", label: "Descrição", type: "text" },
    { name: "amount", label: "Valor", type: "money" },
    { name: "frequency", label: "Frequência", type: "select", options: recurrenceOptions },
    { name: "start_date", label: "Início", type: "date" },
    { name: "end_date", label: "Fim (opcional)", type: "date" },
    { name: "stability", label: "Estabilidade", type: "select", options: incomeStabilityOptions },
  ],
  schema: incomeSchema,
  defaultValues: {
    description: "",
    amount: { amount: "", currency: "BRL" },
    frequency: "monthly",
    start_date: "",
    end_date: "",
    stability: "stable",
  },
  create: (profileId, payload) => onboardingApi.createIncome(profileId, payload),
  list: (profileId) => onboardingApi.listIncomes(profileId),
  renderSummary: (item) => `${item.description} — ${(item.amount as any).amount} ${(item.amount as any).currency}`,
};

export const obligationStepConfig: ResourceStepConfig<any> = {
  key: "obligations",
  title: "Obrigações e despesas",
  emptyLabel: "Nenhuma obrigação adicionada ainda.",
  fields: [
    { name: "description", label: "Descrição", type: "text" },
    { name: "amount", label: "Valor", type: "money" },
    { name: "category", label: "Categoria", type: "text" },
    { name: "frequency", label: "Frequência", type: "select", options: recurrenceOptions },
    { name: "due_day", label: "Dia de vencimento", type: "number" },
    { name: "start_date", label: "Início", type: "date" },
    { name: "end_date", label: "Fim (opcional)", type: "date" },
    { name: "essential", label: "Essencial", type: "checkbox" },
    { name: "debt_related", label: "Relacionada a dívida", type: "checkbox" },
  ],
  schema: obligationSchema,
  defaultValues: {
    description: "",
    amount: { amount: "", currency: "BRL" },
    category: "",
    frequency: "monthly",
    due_day: 1,
    start_date: "",
    end_date: "",
    essential: true,
    debt_related: false,
  },
  create: (profileId, payload) => onboardingApi.createObligation(profileId, payload),
  list: (profileId) => onboardingApi.listObligations(profileId),
  renderSummary: (item) => `${item.description} — ${(item.amount as any).amount} ${(item.amount as any).currency}`,
};

export const debtStepConfig: ResourceStepConfig<any> = {
  key: "debts",
  title: "Dívidas",
  emptyLabel: "Nenhuma dívida adicionada ainda.",
  fields: [
    { name: "description", label: "Descrição", type: "text" },
    { name: "outstanding_balance", label: "Saldo devedor", type: "money" },
    { name: "installment_amount", label: "Valor da parcela", type: "money" },
    { name: "remaining_installments", label: "Parcelas restantes", type: "number" },
    { name: "interest_rate_optional", label: "Taxa de juros (opcional)", type: "text" },
    { name: "due_day", label: "Dia de vencimento", type: "number" },
  ],
  schema: debtSchema,
  defaultValues: {
    description: "",
    outstanding_balance: { amount: "", currency: "BRL" },
    installment_amount: { amount: "", currency: "BRL" },
    remaining_installments: 1,
    interest_rate_optional: "",
    due_day: 1,
  },
  create: (profileId, payload) => onboardingApi.createDebt(profileId, payload),
  list: (profileId) => onboardingApi.listDebts(profileId),
  renderSummary: (item) =>
    `${item.description} — saldo ${(item.outstanding_balance as any).amount} ${(item.outstanding_balance as any).currency}`,
};

export const goalStepConfig: ResourceStepConfig<any> = {
  key: "goals",
  title: "Metas",
  emptyLabel: "Nenhuma meta adicionada ainda.",
  fields: [
    { name: "description", label: "Descrição", type: "text" },
    { name: "target_amount", label: "Valor alvo", type: "money" },
    { name: "current_amount", label: "Valor atual", type: "money" },
    { name: "deadline", label: "Prazo (opcional)", type: "date" },
    { name: "priority", label: "Prioridade", type: "number" },
    { name: "monthly_contribution", label: "Contribuição mensal", type: "money" },
  ],
  schema: goalSchema,
  defaultValues: {
    description: "",
    target_amount: { amount: "", currency: "BRL" },
    current_amount: { amount: "", currency: "BRL" },
    deadline: "",
    priority: 1,
    monthly_contribution: { amount: "", currency: "BRL" },
  },
  create: (profileId, payload) => onboardingApi.createGoal(profileId, payload),
  list: (profileId) => onboardingApi.listGoals(profileId),
  renderSummary: (item) =>
    `${item.description} — alvo ${(item.target_amount as any).amount} ${(item.target_amount as any).currency}`,
};

export const eventStepConfig: ResourceStepConfig<any> = {
  key: "events",
  title: "Eventos futuros",
  emptyLabel: "Nenhum evento adicionado ainda.",
  fields: [
    { name: "description", label: "Descrição", type: "text" },
    { name: "event_type", label: "Tipo de evento", type: "text" },
    { name: "amount", label: "Valor", type: "money" },
    { name: "date", label: "Data", type: "date" },
    { name: "recurrence", label: "Recorrência (opcional)", type: "select", options: recurrenceOptions },
    { name: "direction", label: "Direção", type: "select", options: directionOptions },
  ],
  schema: eventSchema,
  defaultValues: {
    description: "",
    event_type: "",
    amount: { amount: "", currency: "BRL" },
    date: "",
    recurrence: undefined,
    direction: "expense",
  },
  create: (profileId, payload) => onboardingApi.createEvent(profileId, payload),
  list: (profileId) => onboardingApi.listEvents(profileId),
  renderSummary: (item) => `${item.description} — ${(item.amount as any).amount} ${(item.amount as any).currency}`,
};

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

export type PlanStatus = "proposed" | "approved" | "rejected" | "in_progress" | "completed" | "cancelled";

export const RISK_CODE_LABELS: Record<string, string> = {
  INCOME_CONCENTRATION: "Renda concentrada",
  ESSENTIAL_EXPENSE_RATIO: "Despesas essenciais elevadas",
  DEBT_SERVICE_RATIO: "Serviço da dívida elevado",
  RECURRING_CREDIT_FOR_ESSENTIALS: "Uso recorrente de crédito para despesas essenciais",
  PROJECTED_RESERVE_DECLINE: "Tendência de queda na reserva",
  CONCENTRATED_DUE_DATES: "Vencimentos concentrados",
  PROJECTED_DEFICIT_90_DAYS: "Déficit projetado em 90 dias",
  RESERVE_BELOW_THREE_MONTHS: "Reserva abaixo de três meses",
  UNPROVISIONED_ANNUAL_EXPENSE: "Despesa anual sem provisionamento",
  UNCOVERED_FUTURE_INSTALLMENTS: "Parcelas futuras não cobertas pela renda",
  INCOMPATIBLE_GOAL: "Meta incompatível com o fluxo atual",
};

export const STATUS_LABELS: Record<PlanStatus, string> = {
  proposed: "Proposto",
  approved: "Aprovado",
  rejected: "Rejeitado",
  in_progress: "Em andamento",
  completed: "Concluído",
  cancelled: "Cancelado",
};

export interface MoneyDto {
  amount: string;
  currency: string;
}

export interface PlanActionDto {
  description: string;
  expected_monthly_impact: MoneyDto | null;
  due_date: string;
}

export interface ExpectedResultDto {
  deficit_avoided: boolean;
  autonomy_change_months: string | null;
}

export interface PreventivePlanDto {
  id: string;
  profile_id: string;
  risk_code: string;
  status: PlanStatus;
  actions: PlanActionDto[];
  expected_result: ExpectedResultDto;
  created_at: string;
  approved_at: string | null;
}

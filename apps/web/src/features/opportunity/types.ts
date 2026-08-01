/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import type { MoneyDto } from "@/features/onboarding/types";

/** Desfechos do motor. "analisando" e "erro" são estados do cliente, não do motor. */
export type OpportunityStatus = "available" | "no_action" | "insufficient_data";

export type ScenarioKey = "conservative" | "recommended" | "accelerated" | "custom";

export type AnalysisDecision = "pending" | "approved" | "rejected";

export interface EvidenceItemDto {
  key: string;
  label: string;
  money: MoneyDto | null;
  percentage: string | null;
  months: string | null;
  text: string | null;
}

export interface FundingSourceDto {
  label: string;
  amount: MoneyDto;
  essential: boolean;
}

export interface OpportunityScenarioDto {
  key: ScenarioKey;
  additional_pct: string;
  additional_amount: MoneyDto;
  new_monthly_contribution: MoneyDto;
  months_to_goal: string | null;
  months_saved: string | null;
  projected_completion: string | null;
  monthly_surplus_after: MoneyDto;
  autonomy_months_after: string | null;
  first_deficit_period: string | null;
  lowest_balance: MoneyDto;
  safe: boolean;
  risks: string[];
}

export interface OpportunityResultDto {
  status: OpportunityStatus;
  currency: string;
  generated_at: string;
  reason: string | null;
  missing_data: string[];

  monthly_income: MoneyDto | null;
  monthly_obligations: MoneyDto | null;
  income_commitment: string | null;
  essential_expenses_monthly: MoneyDto | null;
  recurring_surplus: MoneyDto | null;
  reserve_months: string | null;

  goal_description: string | null;
  goal_target: MoneyDto | null;
  goal_current: MoneyDto | null;
  current_contribution: MoneyDto | null;
  current_contribution_pct: string | null;
  baseline_months_to_goal: string | null;
  baseline_completion: string | null;

  recommended: OpportunityScenarioDto | null;
  scenarios: OpportunityScenarioDto[];
  funding_sources: FundingSourceDto[];
  evidence: EvidenceItemDto[];
  risks: string[];
  assumptions: string[];
}

/**
 * Envelope versionado. `analysis_id` é o que a URL carrega, e `stale` é a única
 * coisa aqui que depende do agora — o `result` é o snapshot congelado.
 */
export interface OpportunityAnalysisDto {
  analysis_id: string;
  profile_id: string;
  generated_at: string;
  scenario: string;
  stale: boolean;
  decision: AnalysisDecision;
  decided_at: string | null;
  selected_scenario: ScenarioKey | null;
  result: OpportunityResultDto;
}

export const SCENARIO_LABELS: Record<ScenarioKey, string> = {
  conservative: "Conservador",
  recommended: "Recomendado",
  accelerated: "Acelerado",
  custom: "Personalizado",
};

export const SCENARIO_HINTS: Record<ScenarioKey, string> = {
  conservative: "Menor impacto no caixa",
  recommended: "Melhor equilíbrio entre segurança e velocidade",
  accelerated: "Meta antecipada, com menos margem mensal",
  custom: "Valor definido por você",
};

/** Ordem de exibição fixa — nunca a ordem em que o backend devolveu. */
export const SCENARIO_ORDER: ScenarioKey[] = ["conservative", "recommended", "accelerated", "custom"];

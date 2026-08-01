/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import type { BadgeTone } from "@/design-system/components/Badge";
import type { MoneyDto } from "@/features/onboarding/types";

/** Desfecho do motor. "analisando" e "erro" são estados do cliente, não do motor. */
export type OpportunityStatus = "available" | "no_action" | "insufficient_data";

export type ScenarioKey = "conservative" | "recommended" | "accelerated" | "custom";

/** Ciclo de vida do registro. Só `pending` aparece no card Insight. */
export type RecommendationStatus = "pending" | "approved" | "rejected" | "expired" | "superseded";

export type RecommendationSource = "engine" | "conversation";

export type RecommendationKind = "goal_acceleration" | "conversation_advice";

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

/** Snapshot do motor — congelado na detecção, nunca recalculado. */
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

  /**
   * Texto da resposta da IA, quando a recomendação nasceu numa conversa.
   * Nesse caso não há cenários nem evidências: o motor não rodou, e inventar
   * números seria pior que não tê-los.
   */
  summary?: string;
}

/** Uma entrada do Registro de Recomendações. */
export interface RecommendationDto {
  id: string;
  profile_id: string;
  kind: RecommendationKind;
  source: RecommendationSource;
  status: RecommendationStatus;
  generated_at: string;
  scenario: string;
  stale: boolean;
  decided_at: string | null;
  selected_scenario: ScenarioKey | null;
  supersedes_id: string | null;
  superseded_by_id: string | null;
  plan_id: string | null;
  conversation_id: string | null;
  message_id: string | null;
  payload: OpportunityResultDto;
}

/**
 * O que o card Insight consome: ou uma pendente, ou o diagnóstico corrente
 * explicando por que não há ação. Nunca as duas coisas.
 */
export interface InsightDto {
  recommendation: RecommendationDto | null;
  diagnosis: OpportunityResultDto | null;
  /** Plano em execução para o assunto — o card cita e segue monitorando. */
  active_plan_id: string | null;
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
export const SCENARIO_ORDER: ScenarioKey[] = [
  "conservative",
  "recommended",
  "accelerated",
  "custom",
];

export const STATUS_LABELS: Record<RecommendationStatus, string> = {
  pending: "Pendente",
  approved: "Aprovada",
  rejected: "Rejeitada",
  expired: "Expirada",
  superseded: "Substituída",
};

export const STATUS_TONES: Record<RecommendationStatus, BadgeTone> = {
  pending: "purple",
  approved: "success",
  rejected: "neutral",
  expired: "warning",
  superseded: "neutral",
};

/** O que cada status quer dizer — o registro precisa se explicar sozinho. */
export const STATUS_HINTS: Record<RecommendationStatus, string> = {
  pending: "Aguardando sua decisão.",
  approved: "Virou plano preventivo.",
  rejected: "Você recusou esta ação.",
  expired: "Os dados mudaram e a oportunidade deixou de existir.",
  superseded: "Uma análise posterior encontrou outra coisa.",
};

export const SOURCE_LABELS: Record<RecommendationSource, string> = {
  engine: "Detecção automática",
  conversation: "Conversa com a IA",
};

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { apiClient } from "@/lib/api-client";

import type { OpportunityAnalysisDto } from "./types";

export const opportunityApi = {
  /** Gera uma análise nova. É POST porque cria um registro auditável. */
  create: (profileId: string, customPct?: string) =>
    apiClient.post<OpportunityAnalysisDto>(`/api/v1/profiles/${profileId}/opportunity-analyses`, {
      custom_pct: customPct ?? null,
    }),

  /** Última análise do perfil, ou `null` se nunca houve uma. Não cria registro. */
  getLatest: (profileId: string) =>
    apiClient.get<OpportunityAnalysisDto | null>(
      `/api/v1/profiles/${profileId}/opportunity-analyses/latest`
    ),

  /** Abre uma análise existente. Não recalcula nada. */
  get: (analysisId: string) =>
    apiClient.get<OpportunityAnalysisDto>(`/api/v1/opportunity-analyses/${analysisId}`),

  /** Registra a decisão humana. Não movimenta dinheiro. */
  decide: (analysisId: string, decision: "approved" | "rejected", selectedScenario?: string) =>
    apiClient.patch<OpportunityAnalysisDto>(`/api/v1/opportunity-analyses/${analysisId}/decision`, {
      decision,
      selected_scenario: selectedScenario ?? null,
    }),
};

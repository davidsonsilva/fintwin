/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { apiClient } from "@/lib/api-client";

import type { InsightDto, RecommendationDto, RecommendationStatus } from "./types";

export const recommendationApi = {
  /** O que o card mostra agora. Leitura pura: não cria registro. */
  getInsight: (profileId: string) =>
    apiClient.get<InsightDto>(`/api/v1/profiles/${profileId}/insight`),

  /** Roda o motor e registra o que encontrar. É POST porque escreve. */
  detect: (profileId: string, customPct?: string) =>
    apiClient.post<InsightDto>(`/api/v1/profiles/${profileId}/recommendations/detect`, {
      custom_pct: customPct ?? null,
    }),

  /** O registro completo, opcionalmente filtrado por status. */
  list: (profileId: string, status?: RecommendationStatus) => {
    const query = status ? `?status=${encodeURIComponent(status)}` : "";
    return apiClient.get<RecommendationDto[]>(
      `/api/v1/profiles/${profileId}/recommendations${query}`
    );
  },

  /** Abre uma recomendação do registro. Não recalcula nada. */
  get: (recommendationId: string) =>
    apiClient.get<RecommendationDto>(`/api/v1/recommendations/${recommendationId}`),

  /** Aprovar cria o plano preventivo. Não movimenta dinheiro. */
  decide: (recommendationId: string, decision: "approved" | "rejected", selectedScenario?: string) =>
    apiClient.patch<RecommendationDto>(`/api/v1/recommendations/${recommendationId}/decision`, {
      decision,
      selected_scenario: selectedScenario ?? null,
    }),

  /** "Salvar como recomendação" — só por gesto explícito na conversa. */
  saveFromConversation: (
    profileId: string,
    payload: { conversation_id: string; message_id: string; payload: Record<string, unknown> }
  ) =>
    apiClient.post<RecommendationDto>(
      `/api/v1/profiles/${profileId}/recommendations/from-conversation`,
      payload
    ),
};

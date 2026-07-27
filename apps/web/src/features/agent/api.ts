/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { apiClient } from "@/lib/api-client";

import type { AgentMessageHistoryItemDto, AgentMessageResponseDto } from "./types";

export const agentApi = {
  sendMessage: (profileId: string, message: string, conversationId: string | null) =>
    apiClient.post<AgentMessageResponseDto>(`/api/v1/profiles/${profileId}/agent/messages`, {
      conversation_id: conversationId,
      message,
    }),
  confirmAction: (profileId: string, actionId: string) =>
    apiClient.post(`/api/v1/profiles/${profileId}/agent/actions/${actionId}/confirm`),
  listMessages: (profileId: string, conversationId: string) =>
    apiClient.get<AgentMessageHistoryItemDto[]>(
      `/api/v1/profiles/${profileId}/agent/conversations/${conversationId}/messages`
    ),
};

export const AGENT_COMPONENT_QUERY_KEYS: Record<string, string> = {
  dashboard_summary: "dashboard-summary",
  autonomy: "autonomy",
  fragilities: "fragilities",
  simulations: "simulations",
};

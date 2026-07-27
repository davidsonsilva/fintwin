/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { apiClient } from "@/lib/api-client";

import type {
  AutonomyResponseDto,
  DashboardSummaryDto,
  ProjectionRequestDto,
  ProjectionResponseDto,
} from "./types";

export const dashboardApi = {
  getSummary: (profileId: string) => apiClient.get<DashboardSummaryDto>(`/api/v1/profiles/${profileId}/dashboard`),
  getProjection: (profileId: string, request: ProjectionRequestDto) =>
    apiClient.post<ProjectionResponseDto>(`/api/v1/profiles/${profileId}/projections`, request),
  getAutonomy: (profileId: string) =>
    apiClient.post<AutonomyResponseDto>(`/api/v1/profiles/${profileId}/autonomy`),
};

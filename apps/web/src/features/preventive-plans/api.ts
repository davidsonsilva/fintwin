/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { apiClient } from "@/lib/api-client";

import type { PlanStatus, PreventivePlanDto } from "./types";

export const preventivePlanApi = {
  generate: (profileId: string) =>
    apiClient.post<PreventivePlanDto[]>(`/api/v1/profiles/${profileId}/plans/generate`),
  list: (profileId: string, status?: PlanStatus) => {
    const query = status ? `?status=${encodeURIComponent(status)}` : "";
    return apiClient.get<PreventivePlanDto[]>(`/api/v1/profiles/${profileId}/plans${query}`);
  },
  updateStatus: (planId: string, status: PlanStatus) =>
    apiClient.patch<PreventivePlanDto>(`/api/v1/plans/${planId}/status`, { status }),
};

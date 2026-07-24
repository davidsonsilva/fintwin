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

import { apiClient } from "@/lib/api-client";

import type { FragilityFindingDto } from "./types";

export const fragilityApi = {
  detect: (profileId: string) =>
    apiClient.post<FragilityFindingDto[]>(`/api/v1/profiles/${profileId}/fragilities/detect`),
  list: (profileId: string, severity?: string) => {
    const query = severity ? `?severity=${encodeURIComponent(severity)}` : "";
    return apiClient.get<FragilityFindingDto[]>(`/api/v1/profiles/${profileId}/fragilities${query}`);
  },
};

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

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

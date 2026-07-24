import { apiClient } from "@/lib/api-client";

import type { SimulationDto, SimulationRequestPayload } from "./types";

export const simulationApi = {
  create: (profileId: string, payload: SimulationRequestPayload) =>
    apiClient.post<SimulationDto>(`/api/v1/profiles/${profileId}/simulations`, payload),
  list: (profileId: string) => apiClient.get<SimulationDto[]>(`/api/v1/profiles/${profileId}/simulations`),
  get: (simulationId: string) => apiClient.get<SimulationDto>(`/api/v1/simulations/${simulationId}`),
  remove: (simulationId: string) => apiClient.delete(`/api/v1/simulations/${simulationId}`),
};

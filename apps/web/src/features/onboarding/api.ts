/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { apiClient } from "@/lib/api-client";
import type {
  AccountDto,
  DebtDto,
  EventDto,
  GoalDto,
  IncomeDto,
  ObligationDto,
  ProfileDto,
} from "./types";

export const onboardingApi = {
  createProfile: (payload: Record<string, unknown>) => apiClient.post<ProfileDto>("/api/v1/profiles", payload),
  getProfile: (profileId: string) => apiClient.get<ProfileDto>(`/api/v1/profiles/${profileId}`),

  createAccount: (profileId: string, payload: Record<string, unknown>) =>
    apiClient.post<AccountDto>(`/api/v1/profiles/${profileId}/accounts`, payload),
  listAccounts: (profileId: string) => apiClient.get<AccountDto[]>(`/api/v1/profiles/${profileId}/accounts`),

  createIncome: (profileId: string, payload: Record<string, unknown>) =>
    apiClient.post<IncomeDto>(`/api/v1/profiles/${profileId}/incomes`, payload),
  listIncomes: (profileId: string) => apiClient.get<IncomeDto[]>(`/api/v1/profiles/${profileId}/incomes`),

  createObligation: (profileId: string, payload: Record<string, unknown>) =>
    apiClient.post<ObligationDto>(`/api/v1/profiles/${profileId}/obligations`, payload),
  listObligations: (profileId: string) =>
    apiClient.get<ObligationDto[]>(`/api/v1/profiles/${profileId}/obligations`),

  createDebt: (profileId: string, payload: Record<string, unknown>) =>
    apiClient.post<DebtDto>(`/api/v1/profiles/${profileId}/debts`, payload),
  listDebts: (profileId: string) => apiClient.get<DebtDto[]>(`/api/v1/profiles/${profileId}/debts`),

  createGoal: (profileId: string, payload: Record<string, unknown>) =>
    apiClient.post<GoalDto>(`/api/v1/profiles/${profileId}/goals`, payload),
  listGoals: (profileId: string) => apiClient.get<GoalDto[]>(`/api/v1/profiles/${profileId}/goals`),

  createEvent: (profileId: string, payload: Record<string, unknown>) =>
    apiClient.post<EventDto>(`/api/v1/profiles/${profileId}/events`, payload),
  listEvents: (profileId: string) => apiClient.get<EventDto[]>(`/api/v1/profiles/${profileId}/events`),

  loadDemo: (profileId: string) => apiClient.post<void>(`/api/v1/profiles/${profileId}/demo`),
};

"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */


import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

import { onboardingApi } from "./api";

const REVIEW_ITEMS = (data: {
  currency?: string;
  dependents?: number;
  accounts: number;
  incomes: number;
  obligations: number;
  debts: number;
  goals: number;
  events: number;
}) => [
  { label: "Moeda", value: data.currency },
  { label: "Dependentes", value: data.dependents },
  { label: "Contas", value: data.accounts },
  { label: "Rendas", value: data.incomes },
  { label: "Obrigações", value: data.obligations },
  { label: "Dívidas", value: data.debts },
  { label: "Metas", value: data.goals },
  { label: "Eventos futuros", value: data.events },
];

export function ReviewStep({ profileId, onBack }: { profileId: string; onBack?: () => void }) {
  const profileQuery = useQuery({ queryKey: ["profile", profileId], queryFn: () => onboardingApi.getProfile(profileId) });
  const accountsQuery = useQuery({ queryKey: ["accounts", profileId], queryFn: () => onboardingApi.listAccounts(profileId) });
  const incomesQuery = useQuery({ queryKey: ["incomes", profileId], queryFn: () => onboardingApi.listIncomes(profileId) });
  const obligationsQuery = useQuery({
    queryKey: ["obligations", profileId],
    queryFn: () => onboardingApi.listObligations(profileId),
  });
  const debtsQuery = useQuery({ queryKey: ["debts", profileId], queryFn: () => onboardingApi.listDebts(profileId) });
  const goalsQuery = useQuery({ queryKey: ["goals", profileId], queryFn: () => onboardingApi.listGoals(profileId) });
  const eventsQuery = useQuery({ queryKey: ["events", profileId], queryFn: () => onboardingApi.listEvents(profileId) });

  const isLoading =
    profileQuery.isLoading ||
    accountsQuery.isLoading ||
    incomesQuery.isLoading ||
    obligationsQuery.isLoading ||
    debtsQuery.isLoading ||
    goalsQuery.isLoading ||
    eventsQuery.isLoading;

  const isError =
    profileQuery.isError ||
    accountsQuery.isError ||
    incomesQuery.isError ||
    obligationsQuery.isError ||
    debtsQuery.isError ||
    goalsQuery.isError ||
    eventsQuery.isError;

  return (
    <Card className="ft-form-card">
      <CardContent className="space-y-6 p-0">
        <div>
          <h2 className="ft-form-title">Revisão</h2>
          <p className="ft-form-description">Confira o que foi cadastrado antes de ir para o dashboard.</p>
        </div>

        {isLoading && <p className="text-sm text-muted-foreground">Carregando resumo do perfil...</p>}
        {isError && <p className="text-sm text-red-500">Erro ao carregar o resumo. Tente recarregar a página.</p>}

        {!isLoading && !isError && (
          <ul className="ft-review-grid">
            {REVIEW_ITEMS({
              currency: profileQuery.data?.currency,
              dependents: profileQuery.data?.dependents,
              accounts: accountsQuery.data?.length ?? 0,
              incomes: incomesQuery.data?.length ?? 0,
              obligations: obligationsQuery.data?.length ?? 0,
              debts: debtsQuery.data?.length ?? 0,
              goals: goalsQuery.data?.length ?? 0,
              events: eventsQuery.data?.length ?? 0,
            }).map((item) => (
              <li key={item.label} className="ft-review-item">
                <p className="ft-review-label">{item.label}</p>
                <p className="ft-review-value">{item.value}</p>
              </li>
            ))}
          </ul>
        )}

        <div className="ft-form-actions">
          {onBack ? (
            <Button type="button" variant="outline" onClick={onBack}>
              Voltar
            </Button>
          ) : (
            <span />
          )}
          <Button nativeButton={false} render={<Link href={`/dashboard/${profileId}`}>Ver dashboard</Link>} />
        </div>
      </CardContent>
    </Card>
  );
}

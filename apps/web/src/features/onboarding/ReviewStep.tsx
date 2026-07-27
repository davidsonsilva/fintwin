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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { onboardingApi } from "./api";

export function ReviewStep({ profileId, onBack }: { profileId: string; onBack: () => void }) {
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
    <Card>
      <CardHeader>
        <CardTitle>Revisão</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading && <p className="text-sm text-muted-foreground">Carregando resumo do perfil...</p>}
        {isError && <p className="text-sm text-red-500">Erro ao carregar o resumo. Tente recarregar a página.</p>}

        {!isLoading && !isError && (
          <ul className="space-y-1 text-sm">
            <li>Moeda: {profileQuery.data?.currency}</li>
            <li>Dependentes: {profileQuery.data?.dependents}</li>
            <li>Contas: {accountsQuery.data?.length ?? 0}</li>
            <li>Rendas: {incomesQuery.data?.length ?? 0}</li>
            <li>Obrigações: {obligationsQuery.data?.length ?? 0}</li>
            <li>Dívidas: {debtsQuery.data?.length ?? 0}</li>
            <li>Metas: {goalsQuery.data?.length ?? 0}</li>
            <li>Eventos futuros: {eventsQuery.data?.length ?? 0}</li>
          </ul>
        )}

        <div className="flex justify-between pt-4">
          <Button type="button" variant="outline" onClick={onBack}>
            Voltar
          </Button>
          <Button nativeButton={false} render={<Link href={`/dashboard/${profileId}`}>Ver dashboard</Link>} />
        </div>
      </CardContent>
    </Card>
  );
}

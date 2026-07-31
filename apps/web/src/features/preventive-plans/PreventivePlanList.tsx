"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */


import { useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { preventivePlanApi } from "./api";
import { PlanCard } from "./PlanCard";

export function PreventivePlanList({ profileId }: { profileId: string }) {
  const queryClient = useQueryClient();
  const queryKey = ["preventive-plans", profileId];

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey,
    queryFn: () => preventivePlanApi.list(profileId),
  });

  const generatePlans = () =>
    preventivePlanApi.generate(profileId).then(() => {
      queryClient.invalidateQueries({ queryKey });
    });

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-4">
        <CardTitle>Planos preventivos</CardTitle>
        <Button onClick={() => generatePlans()}>Gerar planos</Button>
      </CardHeader>
      <div className="mx-(--card-spacing) mb-2 border-b" />
      <CardContent className="space-y-3">
        {isLoading && <p className="text-sm text-muted-foreground">Carregando planos...</p>}
        {isError && (
          <div className="space-y-2 text-sm">
            <p className="text-red-500">Não foi possível carregar os planos.</p>
            <Button variant="outline" onClick={() => refetch()}>
              Tentar novamente
            </Button>
          </div>
        )}

        {data && data.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Nenhum plano preventivo ainda. Clique em &quot;Gerar planos&quot; para propor ações a partir das
            fragilidades detectadas.
          </p>
        )}

        {data?.map((plan) => <PlanCard key={plan.id} plan={plan} />)}
      </CardContent>
    </Card>
  );
}

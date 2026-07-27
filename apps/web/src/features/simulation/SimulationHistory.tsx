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

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { simulationApi } from "./api";
import { DECISION_LABELS } from "./decisionFields";

export function SimulationHistory({ profileId }: { profileId: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["simulations", profileId],
    queryFn: () => simulationApi.list(profileId),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Histórico de simulações</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {isLoading && <p className="text-sm text-muted-foreground">Carregando histórico...</p>}
        {isError && <p className="text-sm text-red-500">Não foi possível carregar o histórico.</p>}
        {data && data.length === 0 && <p className="text-sm text-muted-foreground">Nenhuma simulação registrada ainda.</p>}
        {data?.map((simulation) => (
          <Link
            key={simulation.id}
            href={`/dashboard/${profileId}/simulations/${simulation.id}`}
            className="flex justify-between rounded-md border px-3 py-2 text-sm hover:bg-muted"
          >
            <span>{DECISION_LABELS[simulation.type]}</span>
            <span className="text-muted-foreground">{new Date(simulation.created_at).toLocaleString("pt-BR")}</span>
          </Link>
        ))}
      </CardContent>
    </Card>
  );
}

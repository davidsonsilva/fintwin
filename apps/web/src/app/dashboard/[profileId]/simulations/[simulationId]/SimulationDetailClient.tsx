"use client";

import { useQuery } from "@tanstack/react-query";

import { simulationApi } from "@/features/simulation/api";
import { SimulationComparison } from "@/features/simulation/SimulationComparison";

export function SimulationDetailClient({ simulationId }: { simulationId: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["simulation", simulationId],
    queryFn: () => simulationApi.get(simulationId),
  });

  if (isLoading) return <p className="text-sm text-muted-foreground">Carregando simulação...</p>;
  if (isError || !data) return <p className="text-sm text-red-500">Não foi possível carregar a simulação.</p>;

  return <SimulationComparison simulation={data} />;
}

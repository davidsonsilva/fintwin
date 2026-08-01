"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { opportunityApi } from "./api";

/**
 * "Analisar e abrir a recomendação" — o gesto que os dois pontos de entrada do
 * dashboard compartilham (o card de oportunidade e o botão do card de insight).
 *
 * `run()` ignora chamadas enquanto uma análise está em voo. Só desabilitar o
 * botão não basta: o segundo clique de um duplo-clique chega antes do React
 * repintar, e criaria uma segunda análise que tornaria a primeira órfã.
 */
export function useAnalyzeOpportunity(profileId: string) {
  const router = useRouter();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (customPct?: string) => opportunityApi.create(profileId, customPct),
    onSuccess: (analysis) => {
      queryClient.invalidateQueries({ queryKey: ["opportunity-latest", profileId] });
      router.push(`/dashboard/${profileId}/recomendacoes/${analysis.analysis_id}`);
    },
  });

  function run(customPct?: string) {
    if (mutation.isPending) return;
    mutation.mutate(customPct);
  }

  return { run, analyzing: mutation.isPending, failed: mutation.isError, reset: mutation.reset };
}

"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

import { fragilityApi } from "./api";

const SEVERITY_OPTIONS = [
  { value: "all", label: "Todas as severidades" },
  { value: "critical", label: "Crítica" },
  { value: "high", label: "Alta" },
  { value: "medium", label: "Média" },
  { value: "low", label: "Baixa" },
] as const;

export function FragilityList({ profileId }: { profileId: string }) {
  const [severity, setSeverity] = useState<string>("all");
  const queryClient = useQueryClient();
  const queryKey = ["fragilities", profileId, severity];

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey,
    queryFn: () => fragilityApi.list(profileId, severity === "all" ? undefined : severity),
  });

  const detectMutation = () =>
    fragilityApi.detect(profileId).then(() => {
      queryClient.invalidateQueries({ queryKey: ["fragilities", profileId] });
    });

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-4">
        <CardTitle>Radar de fragilidade</CardTitle>
        <div className="flex gap-2">
          <Select value={severity} onValueChange={setSeverity}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {SEVERITY_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={() => detectMutation()}>Detectar fragilidades</Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading && <p className="text-sm text-muted-foreground">Carregando fragilidades...</p>}
        {isError && (
          <div className="space-y-2 text-sm">
            <p className="text-red-500">Não foi possível carregar as fragilidades.</p>
            <Button variant="outline" onClick={() => refetch()}>
              Tentar novamente
            </Button>
          </div>
        )}

        {data && data.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Nenhuma fragilidade encontrada. Clique em &quot;Detectar fragilidades&quot; para rodar a análise.
          </p>
        )}

        {data?.map((finding) => (
          <details key={finding.id} className="rounded-md border px-3 py-2 text-sm">
            <summary className="flex cursor-pointer items-center justify-between gap-2">
              <span className="font-medium">{finding.title}</span>
              <span className="rounded bg-muted px-2 py-0.5 text-xs uppercase text-muted-foreground">
                {finding.severity}
              </span>
            </summary>
            <div className="mt-2 space-y-1 text-muted-foreground">
              <p>{finding.description}</p>
              <p>
                <span className="font-medium text-foreground">Fórmula:</span> {finding.formula}
              </p>
              <p>
                <span className="font-medium text-foreground">Limite:</span> {finding.threshold}
              </p>
              <p>
                <span className="font-medium text-foreground">Evidência:</span>{" "}
                {JSON.stringify(finding.evidence)}
              </p>
              <p>
                <span className="font-medium text-foreground">Detectado em:</span> {finding.detected_at}
              </p>
              <p>
                <span className="font-medium text-foreground">Plano recomendado:</span> Disponível na VS-08
              </p>
            </div>
          </details>
        ))}
      </CardContent>
    </Card>
  );
}

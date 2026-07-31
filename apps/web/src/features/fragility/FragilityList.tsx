"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */


import { useState } from "react";
import { RadarIcon, ShieldCheck } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { Badge, type BadgeTone } from "@/design-system/components/Badge";
import { Button as FtButton } from "@/design-system/components/Button";
import { Card as FtCard } from "@/design-system/components/Card";
import { IconChip } from "@/design-system/components/IconChip";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

import { fragilityApi } from "./api";
import type { FragilityFindingDto } from "./types";

const SEVERITY_OPTIONS = [
  { value: "all", label: "Todas as severidades" },
  { value: "critical", label: "Crítica" },
  { value: "high", label: "Alta" },
  { value: "medium", label: "Média" },
  { value: "low", label: "Baixa" },
] as const;

const SEVERITY_META: Record<FragilityFindingDto["severity"], { label: string; tone: BadgeTone }> = {
  critical: { label: "Crítica", tone: "danger" },
  high: { label: "Alta", tone: "warning" },
  medium: { label: "Média", tone: "purple" },
  low: { label: "Baixa", tone: "success" },
};

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
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Select items={SEVERITY_OPTIONS} value={severity} onValueChange={(value) => setSeverity(value ?? "all")}>
          <SelectTrigger className="w-52" aria-label="Filtrar por severidade">
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
        <FtButton onClick={() => detectMutation()}>
          <RadarIcon size={16} />
          Detectar fragilidades
        </FtButton>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Carregando fragilidades...</p>}

      {isError && (
        <FtCard className="space-y-3 text-sm">
          <p className="text-red-400">Não foi possível carregar as fragilidades.</p>
          <FtButton variant="outline" onClick={() => refetch()}>
            Tentar novamente
          </FtButton>
        </FtCard>
      )}

      {data && data.length === 0 && (
        <FtCard className="flex flex-col items-center gap-3 py-10 text-center">
          <IconChip icon={ShieldCheck} tone="primary" size="sm" iconSize={22} />
          <div className="space-y-1">
            <p className="ft-card-title">Nenhuma fragilidade encontrada</p>
            <p className="max-w-md text-sm text-muted-foreground">
              Rode a análise para verificar riscos no seu perfil com base em regras verificáveis. Quanto mais
              dados cadastrados, mais precisa fica a detecção.
            </p>
          </div>
        </FtCard>
      )}

      {data?.map((finding) => {
        const meta = SEVERITY_META[finding.severity];
        return (
          <FtCard key={finding.id} interactive as="details" className="text-sm">
            <summary className="flex cursor-pointer items-center justify-between gap-3">
              <span className="ft-card-title">{finding.title}</span>
              <Badge tone={meta.tone}>{meta.label}</Badge>
            </summary>
            <div className="mt-3 space-y-2 text-muted-foreground">
              <p>{finding.description}</p>
              <p>
                <span className="font-medium text-foreground">Fórmula:</span> {finding.formula}
              </p>
              <p>
                <span className="font-medium text-foreground">Limite:</span> {finding.threshold}
              </p>
              <p>
                <span className="font-medium text-foreground">Evidência:</span> {JSON.stringify(finding.evidence)}
              </p>
              <p>
                <span className="font-medium text-foreground">Detectado em:</span> {finding.detected_at}
              </p>
              <p>
                <span className="font-medium text-foreground">Plano recomendado:</span> Disponível na VS-08
              </p>
            </div>
          </FtCard>
        );
      })}
    </div>
  );
}

"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { ArrowRight, Bot, Cpu, Loader2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/design-system/components/Badge";
import { Button } from "@/design-system/components/Button";
import { Card } from "@/design-system/components/Card";

import { recommendationApi } from "./api";
import { formatDateTime, formatMoney, formatPercent } from "./format";
import {
  SCENARIO_LABELS,
  SOURCE_LABELS,
  STATUS_HINTS,
  STATUS_LABELS,
  STATUS_TONES,
  type RecommendationDto,
  type RecommendationStatus,
} from "./types";

const FILTERS: { key: RecommendationStatus | "all"; label: string }[] = [
  { key: "all", label: "Todas" },
  { key: "pending", label: "Pendentes" },
  { key: "approved", label: "Aprovadas" },
  { key: "rejected", label: "Rejeitadas" },
  { key: "expired", label: "Expiradas" },
  { key: "superseded", label: "Substituídas" },
];

/*
 * Registro de Recomendações — a memória de decisão do FinTwin.
 *
 * O card Insight mostra o próximo assunto; aqui fica tudo o que já foi
 * recomendado, com o desfecho de cada uma. É o que torna o sistema auditável:
 * dá para voltar meses depois e ver o que foi sugerido, com quais números, e
 * o que a pessoa decidiu.
 */
export function RecommendationRegistry({ profileId }: { profileId: string }) {
  const [filter, setFilter] = useState<RecommendationStatus | "all">("all");

  const query = useQuery({
    queryKey: ["recommendations", profileId, filter],
    queryFn: () => recommendationApi.list(profileId, filter === "all" ? undefined : filter),
    retry: false,
  });

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap gap-2" role="group" aria-label="Filtrar por status">
        {FILTERS.map((item) => (
          <Button
            key={item.key}
            size="sm"
            variant={filter === item.key ? "primary" : "outline"}
            onClick={() => setFilter(item.key)}
            aria-pressed={filter === item.key}
          >
            {item.label}
          </Button>
        ))}
      </div>

      {query.isLoading && (
        <p className="flex items-center gap-2 text-sm text-[color:var(--ft-text-secondary)]">
          <Loader2 size={16} className="animate-spin" />
          Carregando o registro…
        </p>
      )}

      {query.isError && (
        <p className="text-sm text-[color:var(--ft-danger)]">Não foi possível carregar o registro.</p>
      )}

      {query.data?.length === 0 && (
        <Card.Root className="h-auto">
          <Card.Content className="flex flex-none flex-col gap-2 py-6">
            <p className="m-0 text-[15px] font-semibold">
              {filter === "all" ? "Nenhuma recomendação registrada ainda" : "Nada com este status"}
            </p>
            <p className="m-0 text-[13px] text-[color:var(--ft-text-secondary)]">
              {filter === "all"
                ? "Assim que o Gêmeo encontrar uma oportunidade nos seus números, ela aparece aqui."
                : "Experimente outro filtro."}
            </p>
          </Card.Content>
        </Card.Root>
      )}

      <div className="flex flex-col gap-3">
        {query.data?.map((item) => (
          <RegistryRow key={item.id} profileId={profileId} recommendation={item} />
        ))}
      </div>
    </div>
  );
}

function RegistryRow({
  profileId,
  recommendation,
}: {
  profileId: string;
  recommendation: RecommendationDto;
}) {
  const { payload } = recommendation;
  const chosen =
    payload.scenarios?.find((s) => s.key === recommendation.selected_scenario) ??
    payload.recommended ??
    null;
  const SourceIcon = recommendation.source === "conversation" ? Bot : Cpu;

  return (
    <Card.Root interactive className="h-auto">
      <Card.Content className="flex flex-none flex-col gap-3 py-5">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={STATUS_TONES[recommendation.status]}>
            {STATUS_LABELS[recommendation.status]}
          </Badge>
          {recommendation.stale && <Badge tone="warning">Desatualizada</Badge>}
          <span className="flex items-center gap-1.5 text-[12px] text-[color:var(--ft-text-secondary)]">
            <SourceIcon size={13} />
            {SOURCE_LABELS[recommendation.source]}
          </span>
          <span className="text-[12px] text-[color:var(--ft-text-secondary)]">
            · {formatDateTime(recommendation.generated_at)}
          </span>
        </div>

        <p className="m-0 text-[15px] leading-snug font-semibold">
          {chosen && payload.goal_description
            ? `Direcionar ${formatMoney(chosen.additional_amount)} a mais por mês para “${payload.goal_description}”`
            : /* Vinda da conversa: o conteúdo é o que a IA de fato disse. */
              (payload.summary ?? payload.reason ?? "Recomendação registrada")}
        </p>

        <p className="m-0 text-[13px] text-[color:var(--ft-text-secondary)]">
          {STATUS_HINTS[recommendation.status]}
          {recommendation.selected_scenario &&
            ` Cenário escolhido: ${SCENARIO_LABELS[recommendation.selected_scenario]}.`}
          {chosen && ` Aporte de +${formatPercent(chosen.additional_pct)} da renda.`}
        </p>

        {/* Encadeamento de versões: dado novo nunca sobrescreve o anterior. */}
        {(recommendation.supersedes_id || recommendation.superseded_by_id) && (
          <p className="m-0 text-[12px] text-[color:var(--ft-text-secondary)]">
            {recommendation.superseded_by_id && (
              <Link
                href={`/dashboard/${profileId}/recomendacoes/${recommendation.superseded_by_id}`}
                className="text-[#b49cff]"
              >
                Substituída por uma análise mais recente
              </Link>
            )}
            {recommendation.supersedes_id && recommendation.superseded_by_id && " · "}
            {recommendation.supersedes_id && (
              <Link
                href={`/dashboard/${profileId}/recomendacoes/${recommendation.supersedes_id}`}
                className="text-[#b49cff]"
              >
                Ver a versão anterior
              </Link>
            )}
          </p>
        )}

        <div className="flex flex-wrap items-center gap-4">
          <Link
            href={`/dashboard/${profileId}/recomendacoes/${recommendation.id}`}
            className="flex items-center gap-2 text-[13px] text-[#b49cff]"
          >
            Ver análise completa
            <ArrowRight size={15} />
          </Link>
          {recommendation.plan_id && (
            <Link
              href={`/dashboard/${profileId}/plans`}
              className="flex items-center gap-2 text-[13px] text-[color:var(--ft-text-secondary)]"
            >
              Acompanhar o plano
              <ArrowRight size={15} />
            </Link>
          )}
        </div>
      </Card.Content>
    </Card.Root>
  );
}

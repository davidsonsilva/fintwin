"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { ArrowRight, Bot, Cpu } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/design-system/components/Badge";
import { Button } from "@/design-system/components/Button";
import { Card } from "@/design-system/components/Card";
import { cn } from "@/lib/utils";

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
 * Trilho de 3px à esquerda da linha. É o que diferencia os cinco status à
 * primeira vista, num registro em que o badge de `rejected` e o de `superseded`
 * compartilham o tom neutro.
 *
 * As cores saem de §13 (estados financeiros) lidas por §2.3 (cor com
 * significado): roxo = análise, verde = concluído, amarelo = atenção, azul =
 * informativo, cinza = encerrado. É mapa de APRESENTAÇÃO, local a esta tela —
 * `STATUS_TONES` em `types.ts` não muda, e nenhuma regra de domínio é criada.
 */
const STATUS_RAIL: Record<RecommendationStatus, string> = {
  pending: "bg-[color:var(--ft-purple)]",
  approved: "bg-[color:var(--ft-success)]",
  rejected: "bg-[color:var(--ft-text-disabled)]",
  expired: "bg-[color:var(--ft-warning)]",
  superseded: "bg-[color:var(--ft-info)]",
};

/* Escala tipográfica do §4.4. Body Small e Caption aparecem em quase toda
 * linha; declarar uma vez evita a classe arbitrária espalhada. */
const TEXT_CAPTION = "text-[length:var(--ft-font-size-caption)] leading-4";
const TEXT_BODY_SM = "text-[length:var(--ft-font-size-body-sm)] leading-[18px]";
const TEXT_HEADING_3 = "text-[length:var(--ft-font-size-heading-3)] leading-6 font-semibold";

/* Link secundário: `--color-action-secondary` do §4.2 (o mesmo `--ft-purple`).
 * Substitui o `#b49cff` que estava hardcoded em três lugares. */
const LINK = cn(
  TEXT_BODY_SM,
  "inline-flex items-center gap-2 text-[color:var(--ft-purple)]",
  "hover:underline hover:underline-offset-4",
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[color:var(--ft-primary)]"
);

/* Padding da linha: 20px na horizontal (§5, "padding de card"), 16px na
 * vertical. É o ÚNICO padding do registro — a moldura externa vai com `p-0`,
 * senão os dois se somam, que era o defeito da versão anterior. */
const ROW_PADDING = "px-[var(--ft-space-5)] py-[var(--ft-space-4)]";

/*
 * Registro de Recomendações — a memória de decisão do FinTwin.
 *
 * O card Insight mostra o próximo assunto; aqui fica tudo o que já foi
 * recomendado, com o desfecho de cada uma. É o que torna o sistema auditável:
 * dá para voltar meses depois e ver o que foi sugerido, com quais números, e
 * o que a pessoa decidiu.
 *
 * Uma recomendação é uma LINHA DE LISTA, não um card. O §11.2 define card como
 * Header/Content/Footer em torno de um valor principal e uma visualização —
 * um registro não tem nem um nem outro. E o §7 manda separar superfícies
 * próximas com borda discreta em vez de acumular sombra. Por isso a moldura é
 * uma só, e as entradas se separam por `--ft-divider`.
 */
export function RecommendationRegistry({ profileId }: { profileId: string }) {
  const [filter, setFilter] = useState<RecommendationStatus | "all">("all");

  const query = useQuery({
    queryKey: ["recommendations", profileId, filter],
    queryFn: () => recommendationApi.list(profileId, filter === "all" ? undefined : filter),
    retry: false,
  });

  const items = query.data ?? [];

  return (
    <div className="flex min-w-0 flex-col gap-[var(--ft-space-4)]">
      <div className="flex flex-wrap gap-[var(--ft-space-2)]" role="group" aria-label="Filtrar por status">
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

      {/* `p-0`: o padding mora na linha. `h-auto` desfaz o `h-full` do CardRoot,
       * que só faz sentido para card dentro de célula de grid. */}
      <Card.Root as="div" className="h-auto p-0">
        {query.isLoading && <RegistrySkeleton />}

        {query.isError && (
          <p
            role="alert"
            className={cn(ROW_PADDING, TEXT_BODY_SM, "m-0 text-[color:var(--ft-danger)]")}
          >
            Não foi possível carregar o registro.
          </p>
        )}

        {!query.isLoading && !query.isError && items.length === 0 && (
          <div className={cn(ROW_PADDING, "flex flex-col gap-[var(--ft-space-1)]")}>
            <p className={cn(TEXT_HEADING_3, "m-0")}>
              {filter === "all" ? "Nenhuma recomendação registrada ainda" : "Nada com este status"}
            </p>
            <p className={cn(TEXT_BODY_SM, "m-0 text-[color:var(--ft-text-secondary)]")}>
              {filter === "all"
                ? "Assim que o Gêmeo encontrar uma oportunidade nos seus números, ela aparece aqui."
                : "Experimente outro filtro."}
            </p>
          </div>
        )}

        {items.length > 0 && (
          <ul className="m-0 flex list-none flex-col p-0">
            {items.map((item) => (
              <RegistryRow key={item.id} profileId={profileId} recommendation={item} />
            ))}
          </ul>
        )}
      </Card.Root>
    </div>
  );
}

/*
 * §11.12: durante o carregamento, preservar o tamanho e não usar spinner
 * central. Três linhas esqueleto ocupam aproximadamente a altura de três
 * registros, então a lista não salta quando os dados chegam.
 */
function RegistrySkeleton() {
  return (
    <div role="status" aria-label="Carregando o registro" className="flex flex-col">
      {[0, 1, 2].map((row) => (
        <div
          key={row}
          className={cn(
            ROW_PADDING,
            "flex flex-col gap-[var(--ft-space-3)]",
            "border-t border-[color:var(--ft-divider)] first:border-t-0"
          )}
        >
          <div className="flex gap-[var(--ft-space-2)]">
            <span className="h-[22px] w-[76px] animate-pulse rounded-[var(--ft-radius-xs)] bg-[color:var(--ft-bg-surface-soft)]" />
            <span className="h-[22px] w-[120px] animate-pulse rounded-[var(--ft-radius-xs)] bg-[color:var(--ft-bg-surface-soft)]" />
          </div>
          <span className="h-4 w-[min(100%,420px)] animate-pulse rounded-[var(--ft-radius-xs)] bg-[color:var(--ft-bg-surface-soft)]" />
          <span className="h-3 w-[min(100%,260px)] animate-pulse rounded-[var(--ft-radius-xs)] bg-[color:var(--ft-bg-surface-soft)]" />
        </div>
      ))}
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
    <li
      className={cn(
        "relative min-w-0",
        "border-t border-[color:var(--ft-divider)] first:border-t-0",
        /* Sem `translateY`: numa lista, deslocar a linha sob o cursor empurra
         * as vizinhas. Realce é só de fundo (§11.2 reserva o hover elevado ao
         * card interativo, e a linha não é integralmente clicável). */
        "transition-colors duration-200 hover:bg-[color:var(--ft-bg-surface-soft)]"
      )}
    >
      <span aria-hidden className={cn("absolute inset-y-0 left-0 w-[3px]", STATUS_RAIL[recommendation.status])} />

      <div className={cn(ROW_PADDING, "flex flex-col gap-[var(--ft-space-3)]")}>
        <div className={cn(TEXT_CAPTION, "flex flex-wrap items-center gap-[var(--ft-space-2)]")}>
          {/* `mt-0` anula o `mt-[10px]` embutido na base do Badge, que
           * desalinharia a pill numa linha de metadados. */}
          <Badge tone={STATUS_TONES[recommendation.status]} className="mt-0">
            {STATUS_LABELS[recommendation.status]}
          </Badge>
          {recommendation.stale && (
            <Badge tone="warning" className="mt-0">
              Desatualizada
            </Badge>
          )}
          <span className="inline-flex items-center gap-[var(--ft-space-2)] text-[color:var(--ft-text-secondary)]">
            <SourceIcon size={13} aria-hidden />
            {SOURCE_LABELS[recommendation.source]}
          </span>
          <span aria-hidden className="text-[color:var(--ft-text-disabled)]">
            ·
          </span>
          <time
            dateTime={recommendation.generated_at}
            className="text-[color:var(--ft-text-secondary)]"
          >
            {formatDateTime(recommendation.generated_at)}
          </time>
        </div>

        {/* Título e descrição a 4px (§5) — são a mesma unidade de leitura. */}
        <div className="flex flex-col gap-[var(--ft-space-1)]">
          <p className={cn(TEXT_HEADING_3, "m-0 break-words")}>
            {chosen && payload.goal_description
              ? `Direcionar ${formatMoney(chosen.additional_amount)} a mais por mês para “${payload.goal_description}”`
              : /* Vinda da conversa: o conteúdo é o que a IA de fato disse. */
                (payload.summary ?? payload.reason ?? "Recomendação registrada")}
          </p>

          <p className={cn(TEXT_BODY_SM, "m-0 break-words text-[color:var(--ft-text-secondary)]")}>
            {STATUS_HINTS[recommendation.status]}
            {recommendation.selected_scenario &&
              ` Cenário escolhido: ${SCENARIO_LABELS[recommendation.selected_scenario]}.`}
            {chosen && ` Aporte de +${formatPercent(chosen.additional_pct)} da renda.`}
          </p>
        </div>

        {/* Encadeamento de versões: dado novo nunca sobrescreve o anterior. */}
        {(recommendation.supersedes_id || recommendation.superseded_by_id) && (
          <div className={cn(TEXT_CAPTION, "flex flex-wrap items-center gap-x-[var(--ft-space-4)] gap-y-[var(--ft-space-1)]")}>
            {recommendation.superseded_by_id && (
              <Link
                href={`/dashboard/${profileId}/recomendacoes/${recommendation.superseded_by_id}`}
                className={cn(LINK, TEXT_CAPTION)}
              >
                Substituída por uma análise mais recente
              </Link>
            )}
            {recommendation.supersedes_id && (
              <Link
                href={`/dashboard/${profileId}/recomendacoes/${recommendation.supersedes_id}`}
                className={cn(LINK, TEXT_CAPTION)}
              >
                Ver a versão anterior
              </Link>
            )}
          </div>
        )}

        {/* §17 (mobile): as ações empilham em vez de espremer. */}
        <div className="flex flex-wrap items-center gap-x-[var(--ft-space-5)] gap-y-[var(--ft-space-2)]">
          <Link href={`/dashboard/${profileId}/recomendacoes/${recommendation.id}`} className={LINK}>
            Ver análise completa
            <ArrowRight size={15} aria-hidden />
          </Link>
          {recommendation.plan_id && (
            <Link
              href={`/dashboard/${profileId}/plans`}
              className={cn(LINK, "text-[color:var(--ft-text-secondary)]")}
            >
              Acompanhar o plano
              <ArrowRight size={15} aria-hidden />
            </Link>
          )}
        </div>
      </div>
    </li>
  );
}

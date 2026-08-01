"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */


import { CalendarClock, ShieldAlert, ShieldCheck, Sparkles, TrendingDown, Wallet } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useSyncExternalStore } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { PageHeader } from "@/components/shell/PageHeader";
import { useSidebarContext } from "@/components/shell/SidebarContext";
import { Button as FtButton } from "@/design-system/components/Button";
import { CompactStatCard } from "@/design-system/components/CompactStatCard";
import { MetricCard } from "@/design-system/components/MetricCard";
import { ApiError } from "@/lib/api-client";

import { fragilityApi } from "@/features/fragility/api";

import { dashboardApi } from "./api";
import { AdaptiveDashboardSection } from "./AdaptiveDashboardSection";
import { AutonomyPanel } from "./AutonomyPanel";
import { BalanceHistoryChart } from "./BalanceHistoryChart";
import { ExpenseBreakdownChart } from "./ExpenseBreakdownChart";
import { FragilitiesSummaryCard } from "./FragilitiesSummaryCard";
import { IncomeCommitmentCard } from "./IncomeCommitmentCard";
import { NextDeficitCard } from "./NextDeficitCard";
import { ProjectionChart } from "./ProjectionChart";
import { UpcomingEventsCard } from "./UpcomingEventsCard";

function formatMoney(amount: string, currency: string) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(Number(amount));
}

function formatPercent(fraction: string) {
  return `${(Number(fraction) * 100).toFixed(1)}%`;
}

function formatMonths(months: string | null) {
  return months !== null ? `${Number(months).toFixed(1)} meses` : "Não aplicável";
}

function subscribeToNothing() {
  return () => {};
}

/* Só em desenvolvimento, e mesmo lá desligado por padrão (precisa de
 * `?debug=layout` na URL). Em produção o selo não existe em hipótese alguma. */
function getLayoutDebugSnapshot() {
  if (process.env.NODE_ENV === "production") return false;
  return new URLSearchParams(window.location.search).get("debug") === "layout";
}

function getLayoutDebugServerSnapshot() {
  return false;
}

export function DashboardView({ profileId }: { profileId: string }) {
  const { openAgent } = useSidebarContext();

  // `useSyncExternalStore`, não `useEffect`+`setState`: a URL é estado externo ao
  // React, e este é o jeito de ler estado externo sem o padrão "efeito que só
  // serve para disparar um novo render" (o linter barra `setState` direto num
  // efeito). `getServerSnapshot` devolve `false` sem tocar em `window`, então não
  // há mismatch de hidratação mesmo se a URL real tiver `?debug=layout`.
  const showLayoutDebug = useSyncExternalStore(
    subscribeToNothing,
    getLayoutDebugSnapshot,
    getLayoutDebugServerSnapshot
  );

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["dashboard-summary", profileId],
    queryFn: () => dashboardApi.getSummary(profileId),
    retry: false,
  });

  const profileQuery = useQuery({
    queryKey: ["profile", profileId],
    queryFn: () => dashboardApi.getProfile(profileId),
    retry: false,
  });

  const firstName = profileQuery.data?.name?.trim().split(" ")[0];

  const projectionQuery = useQuery({
    queryKey: ["projection", profileId, "probable", 12],
    queryFn: () => dashboardApi.getProjection(profileId, { scenario: "probable", months: 12 }),
    enabled: !!data,
  });

  const fragilitiesQuery = useQuery({
    queryKey: ["fragilities", profileId, "all"],
    queryFn: () => fragilityApi.list(profileId),
    enabled: !!data,
  });

  const autonomyQuery = useQuery({
    queryKey: ["autonomy", profileId],
    queryFn: () => dashboardApi.getAutonomy(profileId),
    enabled: !!data,
  });

  const isNotFound = error instanceof ApiError && error.status === 404;

  return (
    <div className="ft-section flex flex-col gap-6 pb-8">
      <PageHeader
        title={firstName ? `Olá, ${firstName}! 👋` : "Olá! 👋"}
        description="Aqui está o panorama da sua vida financeira."
      />

      {isLoading && <p className="text-sm text-muted-foreground">Carregando resumo financeiro...</p>}

      {isError && isNotFound && (
        <Card>
          <CardContent className="space-y-3 pt-6 text-sm">
            <p>Perfil não encontrado.</p>
            <Button nativeButton={false} render={<Link href="/onboarding">Completar onboarding</Link>} />
          </CardContent>
        </Card>
      )}

      {isError && !isNotFound && (
        <Card>
          <CardContent className="space-y-3 pt-6 text-sm">
            <p className="text-red-400">Não foi possível carregar o resumo financeiro.</p>
            <Button variant="outline" onClick={() => refetch()}>
              Tentar novamente
            </Button>
          </CardContent>
        </Card>
      )}

      {data && (
        <>
          <section className="ft-grid ft-grid--metrics">
            <MetricCard
              icon={Wallet}
              tone="primary"
              label="Saldo líquido disponível"
              hint="Quanto você tem disponível somando as contas elegíveis, já descontado o que está comprometido."
              value={formatMoney(data.net_balance.amount, data.net_balance.currency)}
            />

            <MetricCard
              icon={CalendarClock}
              tone="warning"
              label="Obrigações mensais"
              hint="Soma de tudo que você paga todo mês: contas fixas, dívidas e despesas recorrentes."
              value={formatMoney(data.monthly_obligations_total.amount, data.monthly_obligations_total.currency)}
            />

            <MetricCard
              icon={TrendingDown}
              tone="purple"
              label="Comprometimento da renda"
              hint="Quanto da sua renda mensal já está comprometido com obrigações. Quanto menor, mais folga você tem."
              value={data.income_commitment_pct !== null ? formatPercent(data.income_commitment_pct) : "—"}
              helper={data.income_commitment_pct === null ? "Sem renda cadastrada" : "Da renda mensal"}
            />

            <MetricCard
              icon={ShieldCheck}
              tone="info"
              label="Progresso da meta principal"
              hint="Quanto você já juntou da sua meta prioritária em relação ao valor-alvo."
              value={data.main_goal ? formatPercent(data.main_goal.progress_pct) : "—"}
              helper={data.main_goal?.description ?? "Nenhuma meta cadastrada"}
            />
          </section>

          <AdaptiveDashboardSection
            compactCards={[
              {
                key: "autonomia-basica",
                node: (
                  <CompactStatCard
                    icon={ShieldCheck}
                    tone="primary"
                    label="Autonomia básica"
                    hint="Por quantos meses suas reservas cobririam só as despesas essenciais, se a renda parasse."
                    loading={autonomyQuery.isLoading}
                    value={formatMonths(autonomyQuery.data?.basic_autonomy_months ?? null)}
                  />
                ),
              },
              {
                key: "autonomia-provavel",
                node: (
                  <CompactStatCard
                    icon={ShieldCheck}
                    tone="info"
                    label="Autonomia provável"
                    hint="Meses de autonomia no cenário provável, incluindo dívidas, metas e eventos futuros."
                    loading={autonomyQuery.isLoading}
                    value={formatMonths(autonomyQuery.data?.probable_autonomy_months ?? null)}
                  />
                ),
              },
              {
                key: "autonomia-adversa",
                node: (
                  <CompactStatCard
                    icon={ShieldAlert}
                    tone="purple"
                    label="Autonomia adversa"
                    hint="Meses de autonomia num cenário de aperto: menos renda e mais custos que o normal."
                    loading={autonomyQuery.isLoading}
                    value={formatMonths(autonomyQuery.data?.adverse_autonomy_months ?? null)}
                  />
                ),
              },
              {
                key: "perda-de-renda",
                node: (
                  <CompactStatCard
                    icon={ShieldAlert}
                    tone="warning"
                    label="Perda de renda"
                    hint="Por quanto tempo você se manteria se perdesse toda a sua renda."
                    loading={autonomyQuery.isLoading}
                    value={formatMonths(autonomyQuery.data?.income_loss_autonomy_months ?? null)}
                  />
                ),
              },
              {
                key: "proximo-deficit",
                node: (
                  <NextDeficitCard
                    loading={projectionQuery.isLoading}
                    deficitPeriod={projectionQuery.data?.first_deficit_period}
                  />
                ),
              },
              {
                key: "fragilidades",
                node: (
                  <FragilitiesSummaryCard
                    profileId={profileId}
                    loading={fragilitiesQuery.isLoading}
                    count={fragilitiesQuery.data?.length ?? 0}
                  />
                ),
              },
            ]}
            eventsCard={<UpcomingEventsCard profileId={profileId} events={data.upcoming_events} />}
            debug={showLayoutDebug}
          />

          <AutonomyPanel profileId={profileId} />

          {/*
           * Analytics: três composições determinísticas, escolhidas por container
           * query sobre a largura real da seção (não da viewport — a sidebar entra
           * em 1024px e desloca tudo). Nada de ResizeObserver ou score aqui: são
           * três cards fixos, a decisão cabe no CSS.
           *
           *   >= 1112px  [Distribuição] [Evolução] [Comprometimento]
           *   >=  760px  [Distribuição              ]
           *              [Evolução] [Comprometimento]
           *    <  760px  uma coluna
           *
           * Os limites saem da menor largura de card já validada nesta fileira
           * (~360px de área útil, com o gap de 16px entre colunas):
           * 3 x 360 + 2 x 16 = 1112 e 2 x 372 + 16 = 760.
           *
           * Na faixa intermediária o donut é o card principal e fica sozinho na
           * linha de cima, com a largura toda; os outros dois são secundários e
           * dividem a linha de baixo. É hierarquia declarada, não equilíbrio de
           * alturas — nenhuma altura entra nessa decisão.
           *
           * Em widescreen o wrapper dos dois secundários vira `display: contents`,
           * então eles passam a ser itens diretos da seção — três colunas `flex-1`
           * iguais, ninguém ocupando duas linhas.
           *
           * Cada card vai dentro de um `<div>` porque os três trazem `self-start`
           * (para não esticarem no grid antigo) e, num pai flex-column, `self-start`
           * age no eixo horizontal — encolheria a largura. O wrapper block neutraliza
           * isso sem tocar em nenhum dos cards.
           */}
          <div className="@container/analytics">
            <section className="flex flex-col gap-4 @min-[1112px]/analytics:flex-row @min-[1112px]/analytics:items-start">
              <div className="min-w-0 @min-[1112px]/analytics:flex-1">
                <ExpenseBreakdownChart profileId={profileId} />
              </div>
              <div className="flex min-w-0 flex-col gap-4 @min-[760px]/analytics:flex-row @min-[760px]/analytics:items-start @min-[1112px]/analytics:contents">
                <div className="min-w-0 @min-[760px]/analytics:flex-1">
                  <BalanceHistoryChart profileId={profileId} />
                </div>
                <div className="min-w-0 @min-[760px]/analytics:flex-1">
                  <IncomeCommitmentCard profileId={profileId} incomeCommitmentPct={data.income_commitment_pct} />
                </div>
              </div>
            </section>
          </div>

          <ProjectionChart profileId={profileId} />

          <div className="ft-ai-insight">
            <div className="ft-ai-avatar">
              <Image src="/agent-icon.png" alt="" width={76} height={76} className="rounded-full object-cover" />
            </div>
            <div>
              <p className="ft-ai-title">Insight do seu Gêmeo Financeiro</p>
              <p className="ft-ai-text">
                Converse com o Gêmeo Financeiro para receber recomendações personalizadas com base nos dados reais
                do seu perfil.
              </p>
            </div>
            <FtButton onClick={openAgent} className="[@media(max-width:1024px)]:col-[1/-1]">
              <Sparkles size={16} />
              Ver recomendações
            </FtButton>
          </div>
        </>
      )}
    </div>
  );
}

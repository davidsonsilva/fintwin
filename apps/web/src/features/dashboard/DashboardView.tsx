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

export function DashboardView({ profileId }: { profileId: string }) {
  const { openAgent } = useSidebarContext();

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

          <section className="ft-grid ft-grid--indicators">
            <CompactStatCard
              icon={ShieldCheck}
              tone="primary"
              label="Autonomia básica"
              hint="Por quantos meses suas reservas cobririam só as despesas essenciais, se a renda parasse."
              loading={autonomyQuery.isLoading}
              value={formatMonths(autonomyQuery.data?.basic_autonomy_months ?? null)}
            />

            <CompactStatCard
              icon={ShieldCheck}
              tone="info"
              label="Autonomia provável"
              hint="Meses de autonomia no cenário provável, incluindo dívidas, metas e eventos futuros."
              loading={autonomyQuery.isLoading}
              value={formatMonths(autonomyQuery.data?.probable_autonomy_months ?? null)}
            />

            <CompactStatCard
              icon={ShieldAlert}
              tone="purple"
              label="Autonomia adversa"
              hint="Meses de autonomia num cenário de aperto: menos renda e mais custos que o normal."
              loading={autonomyQuery.isLoading}
              value={formatMonths(autonomyQuery.data?.adverse_autonomy_months ?? null)}
            />

            <CompactStatCard
              icon={ShieldAlert}
              tone="warning"
              label="Perda de renda"
              hint="Por quanto tempo você se manteria se perdesse toda a sua renda."
              loading={autonomyQuery.isLoading}
              value={formatMonths(autonomyQuery.data?.income_loss_autonomy_months ?? null)}
            />

            <NextDeficitCard
              loading={projectionQuery.isLoading}
              deficitPeriod={projectionQuery.data?.first_deficit_period}
            />

            <FragilitiesSummaryCard
              profileId={profileId}
              loading={fragilitiesQuery.isLoading}
              count={fragilitiesQuery.data?.length ?? 0}
            />

            <UpcomingEventsCard profileId={profileId} events={data.upcoming_events} />
          </section>

          <AutonomyPanel profileId={profileId} />

          <section className="ft-grid ft-grid--analytics">
            <ExpenseBreakdownChart profileId={profileId} />
            <BalanceHistoryChart profileId={profileId} />
            <IncomeCommitmentCard profileId={profileId} incomeCommitmentPct={data.income_commitment_pct} />
          </section>

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

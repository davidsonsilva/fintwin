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
import { InfoTooltip } from "@/components/ui/tooltip";
import { PageHeader } from "@/components/shell/PageHeader";
import { useSidebarContext } from "@/components/shell/SidebarContext";
import { Button as FtButton } from "@/design-system/components/Button";
import { Card as FtCard } from "@/design-system/components/Card";
import { IconChip } from "@/design-system/components/IconChip";
import { StatusCard } from "@/design-system/components/StatusCard";
import { ApiError } from "@/lib/api-client";

import { fragilityApi } from "@/features/fragility/api";

import { dashboardApi } from "./api";
import { AutonomyPanel } from "./AutonomyPanel";
import { BalanceHistoryChart } from "./BalanceHistoryChart";
import { ExpenseBreakdownChart } from "./ExpenseBreakdownChart";
import { IncomeCommitmentCard } from "./IncomeCommitmentCard";
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
            <FtCard as="article" interactive className="ft-metric-card">
              <IconChip icon={Wallet} tone="primary" size="md" />
              <div className="ft-metric-content">
                <p className="ft-metric-label ft-label-info">
                  Saldo líquido disponível
                  <InfoTooltip
                    label="Quanto você tem disponível somando as contas elegíveis, já descontado o que está comprometido."
                    iconSize={12}
                  />
                </p>
                <p className="ft-metric-value">{formatMoney(data.net_balance.amount, data.net_balance.currency)}</p>
              </div>
            </FtCard>

            <FtCard as="article" interactive className="ft-metric-card">
              <IconChip icon={CalendarClock} tone="warning" size="md" />
              <div className="ft-metric-content">
                <p className="ft-metric-label ft-label-info">
                  Obrigações mensais
                  <InfoTooltip
                    label="Soma de tudo que você paga todo mês: contas fixas, dívidas e despesas recorrentes."
                    iconSize={12}
                  />
                </p>
                <p className="ft-metric-value">
                  {formatMoney(data.monthly_obligations_total.amount, data.monthly_obligations_total.currency)}
                </p>
              </div>
            </FtCard>

            <FtCard as="article" interactive className="ft-metric-card">
              <IconChip icon={TrendingDown} tone="purple" size="md" />
              <div className="ft-metric-content">
                <p className="ft-metric-label ft-label-info">
                  Comprometimento da renda
                  <InfoTooltip
                    label="Quanto da sua renda mensal já está comprometido com obrigações. Quanto menor, mais folga você tem."
                    iconSize={12}
                  />
                </p>
                <p className="ft-metric-value">
                  {data.income_commitment_pct !== null ? formatPercent(data.income_commitment_pct) : "—"}
                </p>
                <p className="ft-metric-helper">
                  {data.income_commitment_pct === null ? "Sem renda cadastrada" : "Da renda mensal"}
                </p>
              </div>
            </FtCard>

            <FtCard as="article" interactive className="ft-metric-card">
              <IconChip icon={ShieldCheck} tone="info" size="md" />
              <div className="ft-metric-content">
                <p className="ft-metric-label ft-label-info">
                  Progresso da meta principal
                  <InfoTooltip
                    label="Quanto você já juntou da sua meta prioritária em relação ao valor-alvo."
                    iconSize={12}
                  />
                </p>
                <p className="ft-metric-value">{data.main_goal ? formatPercent(data.main_goal.progress_pct) : "—"}</p>
                <p className="ft-metric-helper">{data.main_goal?.description ?? "Nenhuma meta cadastrada"}</p>
              </div>
            </FtCard>
          </section>

          <section className="ft-grid ft-grid--indicators">
            <StatusCard
              icon={ShieldCheck}
              tone="primary"
              label="Autonomia básica"
              hint="Por quantos meses suas reservas cobririam só as despesas essenciais, se a renda parasse."
              loading={autonomyQuery.isLoading}
              value={formatMonths(autonomyQuery.data?.basic_autonomy_months ?? null)}
            />

            <StatusCard
              icon={ShieldCheck}
              tone="info"
              label="Autonomia provável"
              hint="Meses de autonomia no cenário provável, incluindo dívidas, metas e eventos futuros."
              loading={autonomyQuery.isLoading}
              value={formatMonths(autonomyQuery.data?.probable_autonomy_months ?? null)}
            />

            <StatusCard
              icon={ShieldAlert}
              tone="purple"
              label="Autonomia adversa"
              hint="Meses de autonomia num cenário de aperto: menos renda e mais custos que o normal."
              loading={autonomyQuery.isLoading}
              value={formatMonths(autonomyQuery.data?.adverse_autonomy_months ?? null)}
            />

            <StatusCard
              icon={ShieldAlert}
              tone="warning"
              label="Perda de renda"
              hint="Por quanto tempo você se manteria se perdesse toda a sua renda."
              loading={autonomyQuery.isLoading}
              value={formatMonths(autonomyQuery.data?.income_loss_autonomy_months ?? null)}
            />

            <StatusCard
              icon={CalendarClock}
              tone="info"
              label="Próximo déficit previsto"
              hint="Primeiro mês em que o saldo projetado ficaria negativo, se nada mudar (cenário provável, 12 meses)."
              loading={projectionQuery.isLoading}
              value={
                projectionQuery.data?.first_deficit_period ??
                "Sem déficit projetado (12 meses, cenário provável)"
              }
            />

            <StatusCard
              icon={TrendingDown}
              tone="warning"
              label="Fragilidades detectadas"
              hint="Riscos financeiros no seu perfil detectados por regras verificáveis — como renda concentrada em uma única fonte, reserva de emergência baixa ou endividamento alto."
              loading={fragilitiesQuery.isLoading}
              value={`${fragilitiesQuery.data?.length ?? 0} encontradas`}
              action={{
                href: `/dashboard/${profileId}/fragilities`,
                label: "Ver radar de fragilidade",
              }}
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

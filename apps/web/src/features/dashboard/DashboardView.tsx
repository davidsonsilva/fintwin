"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */


import { CalendarClock, ShieldCheck, TrendingDown, Wallet } from "lucide-react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { RadialBar, RadialBarChart, ResponsiveContainer } from "recharts";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ApiError } from "@/lib/api-client";

import { fragilityApi } from "@/features/fragility/api";

import { dashboardApi } from "./api";
import { AutonomyPanel } from "./AutonomyPanel";
import { ProjectionChart } from "./ProjectionChart";

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
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["dashboard-summary", profileId],
    queryFn: () => dashboardApi.getSummary(profileId),
    retry: false,
  });

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

  const commitmentPct = data?.income_commitment_pct ? Number(data.income_commitment_pct) * 100 : 0;
  const gaugeData = [{ name: "comprometimento", value: commitmentPct, fill: "var(--ft-primary)" }];

  return (
    <div className="ft-section flex flex-col gap-6 py-8">
      <header className="ft-header">
        <div className="ft-header-left">
          <div>
            <h2 className="ft-page-title">Olá! 👋</h2>
            <p className="ft-page-description">Aqui está o panorama da sua vida financeira.</p>
          </div>
        </div>
      </header>

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
            <article className="ft-card ft-metric-card">
              <div className="ft-metric-icon ft-metric-icon--primary">
                <Wallet size={20} />
              </div>
              <div className="ft-metric-content">
                <p className="ft-metric-label">Saldo líquido disponível</p>
                <p className="ft-metric-value">{formatMoney(data.net_balance.amount, data.net_balance.currency)}</p>
              </div>
            </article>

            <article className="ft-card ft-metric-card">
              <div className="ft-metric-icon ft-metric-icon--warning">
                <CalendarClock size={20} />
              </div>
              <div className="ft-metric-content">
                <p className="ft-metric-label">Obrigações mensais</p>
                <p className="ft-metric-value">
                  {formatMoney(data.monthly_obligations_total.amount, data.monthly_obligations_total.currency)}
                </p>
              </div>
            </article>

            <article className="ft-card ft-metric-card">
              <div className="ft-metric-icon ft-metric-icon--purple">
                <TrendingDown size={20} />
              </div>
              <div className="ft-metric-content">
                <p className="ft-metric-label">Comprometimento da renda</p>
                <p className="ft-metric-value">
                  {data.income_commitment_pct !== null ? formatPercent(data.income_commitment_pct) : "—"}
                </p>
                <p className="ft-metric-helper">
                  {data.income_commitment_pct === null ? "Sem renda cadastrada" : "Da renda mensal"}
                </p>
              </div>
            </article>

            <article className="ft-card ft-metric-card">
              <div className="ft-metric-icon ft-metric-icon--info">
                <ShieldCheck size={20} />
              </div>
              <div className="ft-metric-content">
                <p className="ft-metric-label">Progresso da meta principal</p>
                <p className="ft-metric-value">{data.main_goal ? formatPercent(data.main_goal.progress_pct) : "—"}</p>
                <p className="ft-metric-helper">{data.main_goal?.description ?? "Nenhuma meta cadastrada"}</p>
              </div>
            </article>
          </section>

          <section className="ft-grid ft-grid--indicators">
            <div className="ft-card ft-status-card">
              <div className="ft-status-icon ft-metric-icon--primary">
                <ShieldCheck size={18} />
              </div>
              <div>
                <p className="ft-status-title">Autonomia básica</p>
                <p className="ft-status-description">
                  {autonomyQuery.isLoading ? "Calculando..." : formatMonths(autonomyQuery.data?.basic_autonomy_months ?? null)}
                </p>
              </div>
            </div>

            <div className="ft-card ft-status-card">
              <div className="ft-status-icon ft-metric-icon--info">
                <CalendarClock size={18} />
              </div>
              <div>
                <p className="ft-status-title">Próximo déficit previsto</p>
                <p className="ft-status-description">
                  {projectionQuery.isLoading
                    ? "Calculando..."
                    : (projectionQuery.data?.first_deficit_period ??
                      "Sem déficit projetado (12 meses, cenário provável)")}
                </p>
              </div>
            </div>

            <Link href={`/dashboard/${profileId}/fragilities`} className="ft-card ft-status-card">
              <div className="ft-status-icon ft-metric-icon--warning">
                <TrendingDown size={18} />
              </div>
              <div>
                <p className="ft-status-title">Fragilidades detectadas</p>
                <p className="ft-status-description">
                  {fragilitiesQuery.isLoading ? "Calculando..." : `${fragilitiesQuery.data?.length ?? 0} encontradas`}
                </p>
                <span className="ft-badge">Ver radar de fragilidade</span>
              </div>
            </Link>
          </section>

          <section className="ft-grid ft-grid--analytics">
            <ProjectionChart profileId={profileId} />

            <div className="ft-col-span-2">
              <AutonomyPanel profileId={profileId} />
            </div>
          </section>

          <div className="ft-card">
            <div className="ft-card-header">
              <div>
                <h3 className="ft-card-title">Comprometimento da renda</h3>
                <p className="ft-card-subtitle">Percentual da renda mensal comprometido com obrigações</p>
              </div>
            </div>
            <div className="ft-chart-container" style={{ minHeight: 180 }}>
              <ResponsiveContainer width="100%" height={180}>
                <RadialBarChart
                  data={gaugeData}
                  innerRadius="70%"
                  outerRadius="100%"
                  startAngle={180}
                  endAngle={0}
                  barSize={16}
                >
                  <RadialBar background dataKey="value" cornerRadius={8} />
                </RadialBarChart>
              </ResponsiveContainer>
              <p className="ft-metric-value" style={{ textAlign: "center", marginTop: -60 }}>
                {commitmentPct.toFixed(1)}%
              </p>
            </div>
          </div>

          <div className="ft-card">
            <div className="ft-card-header">
              <h3 className="ft-card-title">Próximos eventos financeiros</h3>
            </div>
            <div className="ft-event-list">
              {data.upcoming_events.length === 0 && (
                <p className="text-sm text-muted-foreground">Nenhum evento futuro cadastrado.</p>
              )}
              {data.upcoming_events.map((event) => (
                <div key={event.id} className="ft-event-item">
                  <div className="ft-event-date">{event.date.slice(8, 10)}</div>
                  <div>
                    <p className="ft-event-title">{event.description}</p>
                    <p className="ft-event-description">{event.date}</p>
                  </div>
                  <span className="ft-event-amount">{formatMoney(event.amount.amount, event.amount.currency)}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="ft-ai-insight">
            <div className="ft-ai-avatar">🤖</div>
            <div>
              <p className="ft-ai-title">Insight do seu Gêmeo Financeiro</p>
              <p className="ft-ai-text">
                O agente conversacional do FinTwin AI chega em breve para responder perguntas sobre a sua vida
                financeira com base nos seus dados reais.
              </p>
            </div>
            <button className="ft-button ft-button--primary" disabled>
              Em breve
            </button>
          </div>
        </>
      )}
    </div>
  );
}

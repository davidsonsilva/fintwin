"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiError } from "@/lib/api-client";

import { fragilityApi } from "@/features/fragility/api";

import { dashboardApi } from "./api";
import { AutonomyPanel } from "./AutonomyPanel";
import { ProjectionChart } from "./ProjectionChart";

function formatMoney(amount: string, currency: string) {
  return `${amount} ${currency}`;
}

function formatPercent(fraction: string) {
  return `${(Number(fraction) * 100).toFixed(1)}%`;
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

  const isNotFound = error instanceof ApiError && error.status === 404;

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 py-12">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">FinTwin AI</h1>
        <Button variant="outline" nativeButton={false} render={<Link href="/">Início</Link>} />
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
            <p className="text-red-500">Não foi possível carregar o resumo financeiro.</p>
            <Button variant="outline" onClick={() => refetch()}>
              Tentar novamente
            </Button>
          </CardContent>
        </Card>
      )}

      {data && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium text-muted-foreground">Saldo líquido disponível</CardTitle>
              </CardHeader>
              <CardContent className="text-xl font-semibold">
                {formatMoney(data.net_balance.amount, data.net_balance.currency)}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium text-muted-foreground">Obrigações mensais</CardTitle>
              </CardHeader>
              <CardContent className="text-xl font-semibold">
                {formatMoney(data.monthly_obligations_total.amount, data.monthly_obligations_total.currency)}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium text-muted-foreground">Comprometimento da renda</CardTitle>
              </CardHeader>
              <CardContent className="text-xl font-semibold">
                {data.income_commitment_pct !== null ? formatPercent(data.income_commitment_pct) : "Sem renda cadastrada"}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium text-muted-foreground">Progresso da meta principal</CardTitle>
              </CardHeader>
              <CardContent className="text-xl font-semibold">
                {data.main_goal ? (
                  <>
                    {formatPercent(data.main_goal.progress_pct)}
                    <p className="text-sm font-normal text-muted-foreground">{data.main_goal.description}</p>
                  </>
                ) : (
                  "Nenhuma meta cadastrada"
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium text-muted-foreground">Próximo déficit previsto</CardTitle>
              </CardHeader>
              <CardContent className="text-xl font-semibold">
                {projectionQuery.isLoading && <span className="text-sm font-normal text-muted-foreground">Calculando...</span>}
                {projectionQuery.data &&
                  (projectionQuery.data.first_deficit_period ?? "Sem déficit projetado (12 meses, cenário provável)")}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium text-muted-foreground">Quantidade de fragilidades</CardTitle>
              </CardHeader>
              <CardContent className="space-y-1 text-xl font-semibold">
                {fragilitiesQuery.isLoading && (
                  <span className="text-sm font-normal text-muted-foreground">Calculando...</span>
                )}
                {fragilitiesQuery.data && <span>{fragilitiesQuery.data.length}</span>}
                <Button
                  variant="link"
                  className="block h-auto p-0 text-sm font-normal"
                  nativeButton={false}
                  render={<Link href={`/dashboard/${profileId}/fragilities`}>Ver radar de fragilidade</Link>}
                />
              </CardContent>
            </Card>
          </div>

          <ProjectionChart profileId={profileId} />

          <AutonomyPanel profileId={profileId} />

          <Card>
            <CardHeader>
              <CardTitle>Próximos eventos financeiros</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {data.upcoming_events.length === 0 && (
                <p className="text-sm text-muted-foreground">Nenhum evento futuro cadastrado.</p>
              )}
              {data.upcoming_events.map((event) => (
                <div key={event.id} className="flex justify-between rounded-md border px-3 py-2 text-sm">
                  <span>
                    {event.description} ({event.date})
                  </span>
                  <span>{formatMoney(event.amount.amount, event.amount.currency)}</span>
                </div>
              ))}
            </CardContent>
          </Card>

          <Button
            variant="outline"
            className="w-fit"
            nativeButton={false}
            render={<Link href={`/dashboard/${profileId}/simulations`}>Simular decisão</Link>}
          />
        </>
      )}
    </div>
  );
}

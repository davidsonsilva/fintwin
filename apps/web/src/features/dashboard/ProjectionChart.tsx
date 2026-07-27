"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

import { dashboardApi } from "./api";
import type { PeriodProjectionDto } from "./types";

const SCENARIO_OPTIONS = [
  { value: "probable", label: "Cenário provável" },
  { value: "adverse", label: "Cenário adverso" },
] as const;

const HORIZON_OPTIONS = [
  { value: "3", label: "3 meses" },
  { value: "6", label: "6 meses" },
  { value: "12", label: "12 meses" },
] as const;

function toChartPoint(period: PeriodProjectionDto) {
  return {
    period: period.period,
    income: Number(period.income_total.amount),
    expense: -Number(period.expense_total.amount),
    balance: Number(period.closing_balance.amount),
    deficit: period.deficit,
  };
}

export function ProjectionChart({ profileId }: { profileId: string }) {
  const [scenario, setScenario] = useState<"probable" | "adverse">("probable");
  const [months, setMonths] = useState<3 | 6 | 12>(12);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["projection", profileId, scenario, months],
    queryFn: () => dashboardApi.getProjection(profileId, { scenario, months }),
  });

  const chartData = data?.periods.map(toChartPoint) ?? [];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-4">
        <CardTitle>Projeção de fluxo de caixa</CardTitle>
        <div className="flex gap-2">
          <Select value={scenario} onValueChange={(value) => setScenario(value as "probable" | "adverse")}>
            <SelectTrigger className="w-44" aria-label="Cenário da projeção">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {SCENARIO_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={String(months)} onValueChange={(value) => setMonths(Number(value) as 3 | 6 | 12)}>
            <SelectTrigger className="w-32" aria-label="Horizonte da projeção">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {HORIZON_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading && <p className="text-sm text-muted-foreground">Carregando projeção...</p>}
        {isError && <p className="text-sm text-red-500">Não foi possível carregar a projeção.</p>}

        {data && (
          <>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="period" />
                  <YAxis />
                  <Tooltip
                    formatter={(value: number, name: string) => [value.toFixed(2), name]}
                    labelFormatter={(label) => `Período: ${label}`}
                  />
                  <ReferenceLine y={0} stroke="currentColor" strokeDasharray="4 4" />
                  <Bar dataKey="income" name="Entradas" fill="#16a34a" />
                  <Bar dataKey="expense" name="Saídas" fill="#dc2626" />
                  <Line type="monotone" dataKey="balance" name="Saldo acumulado" stroke="#2563eb" strokeWidth={2} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {data.first_deficit_period ? (
              <p className="mt-2 text-sm text-red-500">
                Primeiro mês com déficit projetado: {data.first_deficit_period}
              </p>
            ) : (
              <p className="mt-2 text-sm text-muted-foreground">Sem déficit projetado neste horizonte.</p>
            )}

            <ul className="mt-3 space-y-1 text-xs text-muted-foreground">
              {data.assumptions.map((assumption) => (
                <li key={assumption}>{assumption}</li>
              ))}
            </ul>
          </>
        )}
      </CardContent>
    </Card>
  );
}

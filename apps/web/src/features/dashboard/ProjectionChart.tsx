"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */


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

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { InfoTooltip } from "@/components/ui/tooltip";
import { Card as FtCard } from "@/design-system/components/Card";

import { ChartTooltip } from "./ChartTooltip";
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

function formatMoney(value: number | string, currency: string) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(Number(value));
}

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
  const currency = data?.periods[0]?.income_total.currency ?? "BRL";

  return (
    <FtCard interactive>
      <div className="ft-card-header">
        <h3 className="ft-card-title ft-label-info">
          Projeção de fluxo de caixa
          <InfoTooltip label="Estimativa de entradas, saídas e saldo acumulado nos próximos meses, conforme o cenário e o horizonte escolhidos." iconSize={13} />
        </h3>
        <div className="flex gap-2">
          <Select
            items={SCENARIO_OPTIONS}
            value={scenario}
            onValueChange={(value) => setScenario(value as "probable" | "adverse")}
          >
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
          <Select
            items={HORIZON_OPTIONS}
            value={String(months)}
            onValueChange={(value) => setMonths(Number(value) as 3 | 6 | 12)}
          >
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
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Carregando projeção...</p>}
      {isError && <p className="text-sm text-red-500">Não foi possível carregar a projeção.</p>}

      {data && (
        <>
          <div className="ft-chart-container" style={{ minHeight: 288 }}>
            <ResponsiveContainer width="100%" height={288}>
              <ComposedChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--ft-border)" />
                <XAxis dataKey="period" tick={{ fontSize: 11, fill: "var(--ft-text-secondary)" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "var(--ft-text-secondary)" }} axisLine={false} tickLine={false} />
                <Tooltip
                  content={<ChartTooltip formatter={(value) => formatMoney(value, currency)} />}
                  cursor={{ fill: "var(--ft-bg-surface-hover)" }}
                />
                <ReferenceLine y={0} stroke="var(--ft-border-hover)" strokeDasharray="4 4" />
                <Bar dataKey="income" name="Entradas" fill="var(--ft-success)" />
                <Bar dataKey="expense" name="Saídas" fill="var(--ft-danger)" />
                <Line type="monotone" dataKey="balance" name="Saldo acumulado" stroke="var(--ft-info)" strokeWidth={2} />
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

          <div className="mt-3 text-xs text-muted-foreground">
            <p className="mb-1 flex items-center gap-1.5 font-medium text-foreground">
              Premissas desta simulação
              <InfoTooltip
                label="A projeção não é uma previsão exata: ela aplica ajustes ao seu fluxo atual. O cenário provável mantém tudo como está; o adverso simula um aperto (menos renda, mais custos)."
                iconSize={13}
              />
            </p>
            <ul className="ft-assumptions-list">
              {data.assumptions.map((assumption) => (
                <li key={assumption}>{assumption}</li>
              ))}
            </ul>
          </div>
        </>
      )}
    </FtCard>
  );
}

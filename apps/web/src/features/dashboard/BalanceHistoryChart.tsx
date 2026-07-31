"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { InfoTooltip } from "@/components/ui/tooltip";
import { Card as FtCard } from "@/design-system/components/Card";
import { cn } from "@/lib/utils";

import { ChartTooltip } from "./ChartTooltip";
import { dashboardApi } from "./api";

const MONTH_ABBREVIATIONS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];

function formatMoneyPlain(amount: number, currency: string) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(amount);
}

function formatPeriodLabel(period: string) {
  const month = Number(period.slice(5, 7)) - 1;
  return MONTH_ABBREVIATIONS[month] ?? period;
}

function formatAxisTick(value: number) {
  if (Math.abs(value) >= 1000) return `${(value / 1000).toFixed(0)}K`;
  return `${value}`;
}

function LastPointDot({ cx, cy, index, dataLength }: { cx?: number; cy?: number; index?: number; dataLength: number }) {
  if (cx === undefined || cy === undefined) return null;
  const isLast = index === dataLength - 1;
  return (
    <circle
      cx={cx}
      cy={cy}
      r={isLast ? 5 : 3}
      fill={isLast ? "var(--ft-primary)" : "var(--ft-bg-surface)"}
      stroke="var(--ft-primary)"
      strokeWidth={2}
    />
  );
}

export function BalanceHistoryChart({
  profileId,
  months = 6,
  height = 220,
  showFooterLink = true,
}: {
  profileId: string;
  months?: number;
  height?: number;
  showFooterLink?: boolean;
}) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["balance-history", profileId, months],
    queryFn: () => dashboardApi.getBalanceHistory(profileId, months),
  });

  const currency = data?.[0]?.net_balance.currency ?? "BRL";
  const chartData = (data ?? []).map((snapshot) => ({
    period: formatPeriodLabel(snapshot.period),
    fullPeriod: snapshot.period,
    balance: Number(snapshot.net_balance.amount),
  }));

  return (
    <FtCard interactive className={cn("flex flex-col", showFooterLink && "ft-analytics-card")}>
      <div className="ft-card-header">
        <div>
          <h3 className="ft-card-title ft-label-info">
            Evolução do saldo líquido
            <InfoTooltip label="Como o seu saldo líquido variou mês a mês. Uma linha subindo indica que você está acumulando reservas." iconSize={13} />
          </h3>
          <p className="ft-card-subtitle">Últimos {months} meses</p>
        </div>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Carregando histórico...</p>}
      {isError && <p className="text-sm text-red-400">Não foi possível carregar o histórico.</p>}

      {data && data.length === 0 && (
        <p className="text-sm text-muted-foreground">Ainda não há histórico de saldo suficiente.</p>
      )}

      {data && data.length > 0 && (
        <div className="ft-chart-container" style={{ minHeight: height }}>
          <ResponsiveContainer width="100%" height={height}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="balanceGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--ft-primary)" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="var(--ft-primary)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid vertical={false} stroke="var(--ft-border)" strokeDasharray="3 3" />
              <XAxis dataKey="period" tick={{ fontSize: 11, fill: "var(--ft-text-secondary)" }} axisLine={false} tickLine={false} />
              <YAxis
                tick={{ fontSize: 11, fill: "var(--ft-text-secondary)" }}
                axisLine={false}
                tickLine={false}
                tickFormatter={formatAxisTick}
                domain={["auto", "auto"]}
                width={40}
              />
              <Tooltip
                content={<ChartTooltip formatter={(value) => formatMoneyPlain(Number(value), currency)} />}
                labelFormatter={(_, payload) => {
                  const fullPeriod = payload?.[0]?.payload?.fullPeriod as string | undefined;
                  if (!fullPeriod) return "";
                  const [year, month] = fullPeriod.split("-");
                  return `${MONTH_ABBREVIATIONS[Number(month) - 1]}/${year}`;
                }}
                cursor={{ stroke: "var(--ft-border-hover)" }}
              />
              <Area
                type="monotone"
                dataKey="balance"
                name="Saldo líquido"
                stroke="var(--ft-primary)"
                strokeWidth={2}
                fill="url(#balanceGradient)"
                dot={(props: { cx?: number; cy?: number; index?: number }) => (
                  <LastPointDot key={props.index} {...props} dataLength={chartData.length} />
                )}
                activeDot={{ r: 5, fill: "var(--ft-primary)", stroke: "var(--ft-bg-surface)", strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {showFooterLink && (
        <Link href={`/dashboard/${profileId}/balance-history`} className="ft-card-footer mt-auto">
          Ver histórico completo
          <ArrowRight size={16} />
        </Link>
      )}
    </FtCard>
  );
}

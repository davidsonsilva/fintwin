"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { useQuery } from "@tanstack/react-query";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card as FtCard } from "@/design-system/components/Card";

import { dashboardApi } from "./api";

function formatMoneyPlain(amount: number, currency: string) {
  return `${amount.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${currency}`;
}

export function BalanceHistoryChart({ profileId }: { profileId: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["balance-history", profileId],
    queryFn: () => dashboardApi.getBalanceHistory(profileId, 6),
  });

  const currency = data?.[0]?.net_balance.currency ?? "BRL";
  const chartData = (data ?? []).map((snapshot) => ({
    period: snapshot.period,
    balance: Number(snapshot.net_balance.amount),
  }));

  return (
    <FtCard interactive className="flex flex-col">
      <div className="ft-card-header">
        <div>
          <h3 className="ft-card-title">Evolução do saldo líquido</h3>
          <p className="ft-card-subtitle">Últimos 6 meses</p>
        </div>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Carregando histórico...</p>}
      {isError && <p className="text-sm text-red-400">Não foi possível carregar o histórico.</p>}

      {data && data.length === 0 && (
        <p className="text-sm text-muted-foreground">Ainda não há histórico de saldo suficiente.</p>
      )}

      {data && data.length > 0 && (
        <div className="ft-chart-container" style={{ minHeight: 180 }}>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={chartData}>
              <XAxis dataKey="period" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis hide domain={["auto", "auto"]} />
              <Tooltip
                formatter={(value) => [formatMoneyPlain(Number(value), currency), "Saldo líquido"]}
                labelFormatter={(label) => `Período: ${label}`}
              />
              <Line
                type="monotone"
                dataKey="balance"
                name="Saldo líquido"
                stroke="var(--ft-primary)"
                strokeWidth={2}
                dot={{ r: 3 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </FtCard>
  );
}

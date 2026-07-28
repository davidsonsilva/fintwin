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
import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";

import { buttonVariants } from "@/design-system/components/Button";
import { Card as FtCard } from "@/design-system/components/Card";
import { cn } from "@/lib/utils";

import { dashboardApi } from "./api";

const SLICE_COLORS = [
  "var(--ft-primary)",
  "var(--ft-secondary)",
  "var(--ft-purple)",
  "var(--ft-warning)",
  "var(--ft-danger)",
  "var(--ft-info)",
];

function formatPercent(fraction: string) {
  return `${(Number(fraction) * 100).toFixed(1)}%`;
}

export function ExpenseBreakdownChart({ profileId }: { profileId: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["expense-breakdown", profileId],
    queryFn: () => dashboardApi.getExpenseBreakdown(profileId),
  });

  const chartData = (data ?? []).map((item) => ({
    name: item.category,
    value: Number(item.amount.amount),
  }));

  return (
    <FtCard interactive className="flex flex-col">
      <div className="ft-card-header">
        <div>
          <h3 className="ft-card-title">Distribuição das despesas</h3>
          <p className="ft-card-subtitle">Obrigações mensais agrupadas por categoria</p>
        </div>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Carregando distribuição...</p>}
      {isError && <p className="text-sm text-red-400">Não foi possível carregar a distribuição.</p>}

      {data && data.length === 0 && <p className="text-sm text-muted-foreground">Nenhuma obrigação cadastrada.</p>}

      {data && data.length > 0 && (
        <>
          <div className="ft-chart-container" style={{ minHeight: 180 }}>
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie data={chartData} dataKey="value" nameKey="name" innerRadius="60%" outerRadius="90%" paddingAngle={2}>
                  {chartData.map((entry, index) => (
                    <Cell key={entry.name} fill={SLICE_COLORS[index % SLICE_COLORS.length]} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="ft-chart-legend">
            {data.map((item, index) => (
              <div key={item.category} className="ft-legend-item">
                <span className="ft-legend-dot" style={{ background: SLICE_COLORS[index % SLICE_COLORS.length] }} />
                <span className="capitalize">{item.category}</span>
                <span>{formatPercent(item.percentage)}</span>
              </div>
            ))}
          </div>
        </>
      )}

      <Link
        href={`/dashboard/${profileId}/resources/obligations`}
        className={cn(buttonVariants({ variant: "ghost-purple", fullWidth: true }), "mt-3 justify-between")}
      >
        Ver obrigações
        <ArrowRight size={16} />
      </Link>
    </FtCard>
  );
}

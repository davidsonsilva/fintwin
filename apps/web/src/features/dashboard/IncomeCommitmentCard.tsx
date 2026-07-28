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
import { RadialBar, RadialBarChart, ResponsiveContainer } from "recharts";

import { Card as FtCard } from "@/design-system/components/Card";
import { buttonVariants } from "@/design-system/components/Button";
import { cn } from "@/lib/utils";

type RiskTier = {
  label: string;
  className: string;
  color: string;
};

function riskTierFor(pct: number): RiskTier {
  if (pct <= 40) return { label: "Saudável", className: "ft-badge--success", color: "var(--ft-success)" };
  if (pct <= 60) return { label: "Atenção", className: "ft-badge--warning", color: "var(--ft-warning)" };
  if (pct <= 75) return { label: "Elevado", className: "ft-badge--purple", color: "var(--ft-purple)" };
  return { label: "Crítico", className: "ft-badge--danger", color: "var(--ft-danger)" };
}

export function IncomeCommitmentCard({
  profileId,
  incomeCommitmentPct,
}: {
  profileId: string;
  incomeCommitmentPct: string | null;
}) {
  const hasData = incomeCommitmentPct !== null;
  const commitmentPct = hasData ? Number(incomeCommitmentPct) * 100 : 0;
  const tier = riskTierFor(commitmentPct);
  const gaugeData = [{ name: "comprometimento", value: commitmentPct, fill: tier.color }];

  return (
    <FtCard interactive className="flex flex-col">
      <div className="ft-card-header">
        <div>
          <h3 className="ft-card-title">Comprometimento da renda</h3>
          <p className="ft-card-subtitle">Percentual da renda mensal comprometido com obrigações</p>
        </div>
      </div>

      {hasData ? (
        <>
          <div className="ft-chart-container" style={{ minHeight: 180 }}>
            <ResponsiveContainer width="100%" height={180}>
              <RadialBarChart data={gaugeData} innerRadius="70%" outerRadius="100%" startAngle={180} endAngle={0} barSize={16}>
                <RadialBar background dataKey="value" cornerRadius={8} />
              </RadialBarChart>
            </ResponsiveContainer>
            <p className="ft-metric-value" style={{ textAlign: "center", marginTop: -60 }}>
              {commitmentPct.toFixed(1)}%
            </p>
          </div>
          <span className={cn("ft-badge", tier.className)} style={{ alignSelf: "center" }}>
            {tier.label}
          </span>
        </>
      ) : (
        <p className="text-sm text-muted-foreground">Sem renda cadastrada para calcular o comprometimento.</p>
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

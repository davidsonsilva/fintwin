"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { AlertCircle, AlertOctagon, AlertTriangle, ArrowRight, CheckCircle2, type LucideIcon } from "lucide-react";
import Link from "next/link";

import { Card as FtCard } from "@/design-system/components/Card";
import { InfoTooltip } from "@/components/ui/tooltip";

type RiskTier = {
  Icon: LucideIcon;
  color: string;
  text: string;
};

function riskTierFor(pct: number): RiskTier {
  if (pct <= 40) return { Icon: CheckCircle2, color: "var(--ft-success)", text: "Dentro do limite saudável" };
  if (pct <= 60) return { Icon: AlertCircle, color: "var(--ft-warning)", text: "Atenção ao comprometimento" };
  if (pct <= 75) return { Icon: AlertTriangle, color: "var(--ft-purple)", text: "Comprometimento elevado" };
  return { Icon: AlertOctagon, color: "var(--ft-danger)", text: "Comprometimento crítico" };
}

// Geometria fixa do gauge (coordenadas do viewBox). Traço fino e raio grande,
// nas mesmas proporções da referência (strokeWidth/raio ≈ 0.16). Desenhar em
// SVG à mão torna a posição do número e a espessura determinísticas, sem
// depender do cálculo interno de raio do recharts.
const CX = 100;
const CY = 100;
const R = 92;
const STROKE = 15;

function arcPath(fraction: number): string {
  const clamped = Math.min(Math.max(fraction, 0), 1);
  const angleDeg = 180 - clamped * 180;
  const angleRad = (angleDeg * Math.PI) / 180;
  const endX = CX + R * Math.cos(angleRad);
  const endY = CY - R * Math.sin(angleRad);
  return `M ${CX - R} ${CY} A ${R} ${R} 0 0 1 ${endX.toFixed(2)} ${endY.toFixed(2)}`;
}

const TRACK_PATH = `M ${CX - R} ${CY} A ${R} ${R} 0 0 1 ${CX + R} ${CY}`;

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
  const formatted = `${commitmentPct.toFixed(1).replace(".", ",")}%`;

  return (
    <FtCard interactive className="ft-analytics-card flex flex-col">
      <div className="ft-card-header">
        <div>
          <h3 className="ft-card-title ft-label-info">
            Comprometimento da renda
            <InfoTooltip label="Fatia da sua renda mensal comprometida com obrigações. Abaixo de 40% é saudável; acima de 60% pede atenção." iconSize={13} />
          </h3>
          <p className="ft-card-subtitle">Percentual da renda mensal comprometido com obrigações</p>
        </div>
      </div>

      {hasData ? (
        <div className="ft-gauge-stack">
          <svg className="ft-gauge-svg" viewBox="0 0 200 108" role="img" aria-label={`${formatted} do rendimento`}>
            <defs>
              <linearGradient id="commitmentFill" x1="0" y1="1" x2="1" y2="0">
                <stop offset="0%" stopColor="#f97316" />
                <stop offset="100%" stopColor="var(--ft-warning)" />
              </linearGradient>
            </defs>
            <path
              d={TRACK_PATH}
              fill="none"
              stroke="var(--ft-success)"
              strokeWidth={STROKE}
              strokeLinecap="round"
            />
            <path
              d={arcPath(commitmentPct / 100)}
              fill="none"
              stroke="url(#commitmentFill)"
              strokeWidth={STROKE}
              strokeLinecap="round"
            />
            <text x={CX} y="72" className="ft-gauge-svg-number" textAnchor="middle">
              {formatted}
            </text>
            <text x={CX} y="90" className="ft-gauge-svg-label" textAnchor="middle">
              do rendimento
            </text>
          </svg>

          <div className="ft-gauge-status" style={{ color: tier.color }}>
            <tier.Icon size={16} />
            <span>{tier.text}</span>
          </div>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">Sem renda cadastrada para calcular o comprometimento.</p>
      )}

      <Link href={`/dashboard/${profileId}/resources/obligations`} className="ft-card-footer mt-auto">
        Ver obrigações
        <ArrowRight size={16} />
      </Link>
    </FtCard>
  );
}

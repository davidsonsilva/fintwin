"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import type { LucideIcon } from "lucide-react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { InfoTooltip } from "@/components/ui/tooltip";
import { badgeVariants } from "@/design-system/components/Badge";
import { Card } from "@/design-system/components/Card";
import { IconChip, type IconChipTone } from "@/design-system/components/IconChip";

export type StatusCardProps = {
  icon: LucideIcon;
  tone: IconChipTone;
  /** Nome do indicador. */
  label: string;
  /** Explicação em linguagem acessível, exibida no tooltip ao lado do rótulo. */
  hint: string;
  /** Valor já formatado. Ignorado enquanto `loading` for true. */
  value: string;
  loading?: boolean;
  /** Só alguns indicadores levam a uma tela de detalhe. */
  action?: { href: string; label: string };
};

/**
 * Indicador compacto da linha de status do dashboard.
 *
 * Substitui `.ft-status-card`, `.ft-status-icon`, `.ft-status-title` e
 * `.ft-status-description`, removidas de `design-system.css`. É cópia fiel delas —
 * mesmas medidas, mesmo empilhamento, mesma quebra de texto:
 *
 *   .ft-status-card         flex; min-height 104px; align-items flex-start; gap 13px
 *   .ft-status-title        margin 1px 0 6px; 14px; weight 700
 *   .ft-status-description  margin 0; --ft-text-secondary; 13px
 *
 * Sem container query aqui, de propósito. Uma versão anterior mandava o valor para a
 * direita do rótulo quando havia espaço; com valores longos ("Sem déficit projetado
 * (12 meses, cenário provável)") o resultado ficava ruim — e, sobretudo, era mudança
 * visual num passo que devia ser só troca de estrutura. Decisões de layout ficam para
 * depois que a migração terminar.
 */
export function StatusCard({ icon, tone, label, hint, value, loading, action }: StatusCardProps) {
  return (
    <Card interactive className="flex min-h-[104px] items-start gap-[13px]">
      <IconChip icon={icon} tone={tone} size="sm" />

      <div>
        <p className="ft-label-info mt-px mb-[6px] text-[14px] font-bold">
          {label}
          <InfoTooltip label={hint} iconSize={12} />
        </p>

        <p className="text-[13px] text-[color:var(--ft-text-secondary)]">
          {loading ? "Calculando..." : value}
        </p>

        {action ? (
          <Link href={action.href} className={badgeVariants({ tone: "link" })}>
            {action.label}
            <ArrowRight size={12} />
          </Link>
        ) : null}
      </div>
    </Card>
  );
}

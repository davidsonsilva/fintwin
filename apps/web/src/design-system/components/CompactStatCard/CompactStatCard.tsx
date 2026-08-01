/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import type { LucideIcon } from "lucide-react";

import { InfoTooltip } from "@/components/ui/tooltip";
import { Card } from "@/design-system/components/Card";
import { IconChip, type IconChipTone } from "@/design-system/components/IconChip";

export type CompactStatCardProps = {
  icon: LucideIcon;
  tone: IconChipTone;
  /** Nome do indicador. */
  label: string;
  /** Explicação em linguagem acessível, exibida no tooltip ao lado do rótulo. */
  hint: string;
  /** Valor já formatado. Ignorado enquanto `loading` for true. */
  value: string;
  loading?: boolean;
};

/*
 * Primeira versão (descartada) montava um `<div>` flex local em vez de usar
 * `Card.Header`/`Card.Content` — fugia do padrão oficial (ver `CardHeader.tsx`) e,
 * como a tipografia ficou igual à do antigo `StatusCard`, o resultado era
 * visualmente indistinguível dele. Esta versão usa a mesma moldura do `MetricCard`:
 * `Card.Header` (ícone/título/help na grade oficial de 3 colunas) e o valor em
 * `Card.Content`, com a separação real entre os dois blocos que o padrão exige —
 * não é só diferença de fonte, é espaçamento estrutural (`mt-3`).
 *
 * Ícone `size="sm"` (38px, não os 48px do `MetricCard`): estes cards dividem a
 * fileira de indicadores com `NextDeficitCard`/`FragilitiesSummaryCard`, que usam
 * o mesmo ícone menor.
 *
 * `h-auto self-start`, sem `min-h`: a grade externa (`DashboardView.tsx`) usa
 * `items-start`, não `stretch` — cada card já fica só com a própria altura, então
 * uma altura mínima artificial para "empatar" com os vizinhos não faz falta (e o
 * pedido explícito foi remover justamente isso).
 */
export function CompactStatCard({ icon, tone, label, hint, value, loading }: CompactStatCardProps) {
  return (
    <Card.Root as="article" interactive className="h-auto self-start">
      <Card.Header
        icon={<IconChip icon={icon} tone={tone} size="sm" />}
        title={
          <h3 className="m-0 text-[13px] font-normal text-[color:var(--ft-text-secondary)]">{label}</h3>
        }
        help={<InfoTooltip label={hint} iconSize={12} />}
      />

      <Card.Content className="mt-3 flex flex-none flex-col">
        <p className="m-0 text-[length:clamp(18px,7.5cqi,24px)] leading-[1.15] font-bold tabular-nums tracking-[-0.02em] break-normal [overflow-wrap:normal] [word-break:normal]">
          {loading ? "Calculando..." : value}
        </p>
      </Card.Content>
    </Card.Root>
  );
}

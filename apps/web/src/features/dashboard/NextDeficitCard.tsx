"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { CalendarClock } from "lucide-react";

import { InfoTooltip } from "@/components/ui/tooltip";
import { Card } from "@/design-system/components/Card";
import { IconChip } from "@/design-system/components/IconChip";

/*
 * Sexto card migrado da fileira de indicadores — `StatusCard` (padrão anterior) trocado
 * por `Card.Root`+`Card.Header`+`Card.Content`, mesma moldura do `CompactStatCard`.
 *
 * Não reaproveita o `CompactStatCard`: aquele componente é para um valor curto e
 * numérico (clamp grande, `tabular-nums`); aqui o conteúdo é uma frase inteira ("Sem
 * déficit projetado (12 meses, cenário provável)" ou um período tipo "2026-11") — texto
 * corrido, não estatística. Tipografia igual à que o `StatusCard` sempre teve (13px,
 * cor secundária), preservando a identidade visual atual desse conteúdo específico.
 */
export function NextDeficitCard({
  loading,
  deficitPeriod,
}: {
  loading: boolean;
  deficitPeriod: string | null | undefined;
}) {
  return (
    <Card.Root as="article" interactive className="h-auto self-start">
      <Card.Header
        icon={<IconChip icon={CalendarClock} tone="info" size="sm" />}
        title={
          <h3 className="m-0 text-[13px] font-normal text-[color:var(--ft-text-secondary)]">
            Próximo déficit previsto
          </h3>
        }
        help={
          <InfoTooltip
            label="Primeiro mês em que o saldo projetado ficaria negativo, se nada mudar (cenário provável, 12 meses)."
            iconSize={12}
          />
        }
      />

      <Card.Content className="mt-3 flex flex-none flex-col">
        <p className="m-0 text-[13px] leading-[1.4] text-[color:var(--ft-text-secondary)] break-normal [overflow-wrap:normal] [word-break:normal]">
          {loading ? "Calculando..." : (deficitPeriod ?? "Sem déficit projetado (12 meses, cenário provável)")}
        </p>
      </Card.Content>
    </Card.Root>
  );
}

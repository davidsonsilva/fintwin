"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { ArrowRight, TrendingDown } from "lucide-react";
import Link from "next/link";

import { InfoTooltip } from "@/components/ui/tooltip";
import { Card } from "@/design-system/components/Card";
import { IconChip } from "@/design-system/components/IconChip";

/*
 * Sétimo (e último) card migrado da fileira de indicadores — `StatusCard` trocado por
 * `Card.Root`+`Card.Header`+`Card.Content`, mesma moldura do `CompactStatCard`.
 *
 * A quantidade usa a mesma tipografia grande/`tabular-nums` do `CompactStatCard`
 * (é um valor, "N encontradas", igual em espírito aos meses de autonomia) — mas o CTA
 * abaixo dele exige um segundo componente: nenhum card já migrado tem ação dentro do
 * `Card.Content` (os que têm link usam `Card.Footer`, empurrado para o fundo com
 * `mt-auto`). Aqui a instrução foi explícita: CTA fica no `Content`, não no rodapé.
 *
 * O link é `flex` (não `inline-flex`, como o antigo badge `tone="link"`): sem isso ele
 * fica do tamanho do próprio conteúdo e nada o impede de vazar a borda do card num
 * card estreito. `w-fit max-w-full` deixa que ele ocupe só o espaço necessário, mas
 * nunca mais que o card; o texto tem `min-w-0` para poder quebrar dentro do próprio
 * limite em vez de estourar.
 */
export function FragilitiesSummaryCard({
  profileId,
  loading,
  count,
}: {
  profileId: string;
  loading: boolean;
  count: number;
}) {
  return (
    <Card.Root as="article" interactive className="h-auto self-start">
      <Card.Header
        icon={<IconChip icon={TrendingDown} tone="warning" size="sm" />}
        title={
          <h3 className="m-0 text-[13px] font-normal text-[color:var(--ft-text-secondary)]">
            Fragilidades detectadas
          </h3>
        }
        help={
          <InfoTooltip
            label="Riscos financeiros no seu perfil detectados por regras verificáveis — como renda concentrada em uma única fonte, reserva de emergência baixa ou endividamento alto."
            iconSize={12}
          />
        }
      />

      <Card.Content className="mt-3 flex flex-none flex-col gap-3">
        <p className="m-0 text-[length:clamp(18px,7.5cqi,24px)] leading-[1.15] font-bold tabular-nums tracking-[-0.02em] break-normal [overflow-wrap:normal] [word-break:normal]">
          {loading ? "Calculando..." : `${count} encontradas`}
        </p>

        <Link
          href={`/dashboard/${profileId}/fragilities`}
          className="flex w-fit max-w-full min-w-0 items-center gap-2 text-[13px] font-semibold text-[#b49cff] transition-colors duration-150 ease-[ease] hover:text-[#c8b7ff]"
        >
          <span className="min-w-0 break-normal [overflow-wrap:normal] [word-break:normal]">
            Ver radar de fragilidade
          </span>
          <ArrowRight size={12} className="flex-none" />
        </Link>
      </Card.Content>
    </Card.Root>
  );
}

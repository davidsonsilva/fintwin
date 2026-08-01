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

export type MetricCardProps = {
  icon: LucideIcon;
  tone: IconChipTone;
  /** Nome do indicador. */
  label: string;
  /** Explicação em linguagem acessível, exibida no tooltip ao lado do rótulo. */
  hint: string;
  /** Valor já formatado. */
  value: string;
  /** Linha secundária opcional. Quando ausente, não reserva espaço nenhum. */
  helper?: string;
};

/**
 * Card compacto da linha de resumo no topo do dashboard (saldo, obrigações,
 * comprometimento, meta principal). Substitui `.ft-metric-card`,
 * `.ft-metric-content`, `.ft-metric-label`, `.ft-metric-value` e
 * `.ft-metric-helper`.
 *
 * Segunda versão: a primeira colocava ícone, título e valor dentro do mesmo
 * bloco flexível — sem fronteira estrutural entre "cabeçalho" e "conteúdo", o
 * valor parecia mais uma continuação do título do que o dado em destaque.
 * Terceira versão: o header agora é uma grade de três colunas própria
 * (`grid grid-cols-[auto_minmax(0,1fr)_auto]`), não o `Card.Header`
 * compartilhado. Motivo: `Card.Header` põe ícone/título/help como irmãos num
 * `flex` — quando o título quebra em várias linhas (rótulos longos em card
 * estreito, ex. 220px), o tooltip é só mais um item nessa mesma linha flex e
 * pode ser empurrado para baixo/para o lado junto com a quebra. A grade fixa
 * a coluna do help em `auto` (largura do próprio ícone, nunca mais) e a do
 * título em `minmax(0,1fr)` — o título quebra sozinho, dentro da própria
 * coluna, sem arrastar o help.
 *
 * O valor e a descrição opcional continuam no `Card.Content`, abaixo do
 * header, com espaçamento real entre os dois blocos (`mt-4`, maior que o
 * `mt-2` entre valor e descrição — a hierarquia que a estrutura garante).
 *
 * Sem `.ft-card-header` (a classe traz `border-bottom` — os metric cards
 * originais nunca tiveram divisória entre título e valor; usá-la introduziria
 * uma linha que não existia no design).
 *
 * `min-height: 132px` mantido: é o que faz os quatro cards da fileira — dois
 * com `helper`, dois sem — alinharem na grade real, não reserva de espaço
 * para o helper (que segue condicional; sem ele, nenhuma linha vazia entra).
 */
export function MetricCard({ icon, tone, label, hint, value, helper }: MetricCardProps) {
  return (
    <Card.Root as="article" interactive className="min-h-[132px]">
      {/*
       * `pr-1`: sem essa folga, a coluna `1fr` do título consome literalmente
       * 100% do espaço até a borda de padding do card, e o ícone de ajuda
       * (coluna `auto`) fica com zero pixels de respiro antes do padding —
       * tecnicamente dentro do card, mas visualmente colado na borda, como se
       * estivesse cortado. 4px é suficiente para o olho perceber uma margem
       * de verdade sem tirar espaço relevante do título.
       */}
      <header className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-start gap-x-3 pr-1">
        <IconChip icon={icon} tone={tone} size="md" className="shrink-0" />

        <h3 className="m-0 min-w-0 text-[13px] font-normal text-[color:var(--ft-text-secondary)] break-normal [overflow-wrap:normal] [word-break:normal]">
          {label}
        </h3>

        <InfoTooltip label={hint} iconSize={12} className="mt-0.5 shrink-0 self-start" />
      </header>

      <Card.Content className="mt-4 flex flex-none flex-col">
        {/*
         * `9.2cqi`, não os `7cqi` sugeridos originalmente: na grade real de 4
         * colunas o card mede ~304px (content box ~262px), e a 7cqi isso dá
         * 18.3px — preso no piso do clamp, abaixo dos 24px que
         * `.ft-metric-value` sempre teve. 9.2cqi bate 24px exatamente nessa
         * largura, preservando o desenho aprovado; piso/teto (20/28) seguem
         * os sugeridos.
         */}
        <p className="m-0 text-[length:clamp(20px,9.2cqi,28px)] leading-[1.15] font-bold tabular-nums tracking-[-0.02em] break-normal [overflow-wrap:normal] [word-break:normal]">
          {value}
        </p>

        {helper ? (
          <p className="mt-2 text-[13px] text-[color:var(--ft-text-secondary)] break-normal [overflow-wrap:normal] [word-break:normal]">
            {helper}
          </p>
        ) : null}
      </Card.Content>
    </Card.Root>
  );
}

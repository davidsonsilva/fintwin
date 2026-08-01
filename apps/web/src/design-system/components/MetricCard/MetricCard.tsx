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
 * Terceira versão trocou por um `<header>` com grid de três colunas próprio,
 * porque na época o `Card.Header` compartilhado ainda usava `flex` (o tooltip
 * podia ser arrastado quando o título quebrava em várias linhas). Essa grade
 * virou o padrão oficial do `Card.Header` — quarta versão volta a usá-lo, sem
 * duplicar a estrutura aqui.
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
      <Card.Header
        icon={<IconChip icon={icon} tone={tone} size="md" />}
        title={
          <h3 className="m-0 text-[13px] font-normal text-[color:var(--ft-text-secondary)]">{label}</h3>
        }
        help={<InfoTooltip label={hint} iconSize={12} />}
      />

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

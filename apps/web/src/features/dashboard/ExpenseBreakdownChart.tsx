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
import { useId } from "react";
import { useQuery } from "@tanstack/react-query";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { Card } from "@/design-system/components/Card";
import { cn } from "@/lib/utils";

import { ChartTooltip } from "./ChartTooltip";
import { dashboardApi } from "./api";

const SLICE_COLORS = [
  "var(--ft-primary)",
  "var(--ft-secondary)",
  "var(--ft-purple)",
  "var(--ft-warning)",
  "var(--ft-danger)",
  "var(--ft-info)",
];

/** Escurecimento aplicado nas duas pontas de cada fatia. */
const EDGE_DARKEN = "42%";

/** Compartilhado entre o `<Pie>` e o cálculo dos ângulos do gradiente. */
const PADDING_ANGLE = 2;

/**
 * Eixo do gradiente de uma fatia, em coordenadas do bounding box.
 *
 * O degradê tem que correr ao longo do arco (do meio da fatia para as duas
 * pontas), não ao longo do raio. Como o Recharts posiciona pontos em
 * `(cx + r·cos θ, cy − r·sin θ)`, a direção radial é `(cos θ, −sin θ)` e a
 * tangente — a que interessa — é a perpendicular `(sin θ, cos θ)`.
 */
function gradientAxis(midAngleDeg: number) {
  const rad = (midAngleDeg * Math.PI) / 180;
  const ux = Math.sin(rad);
  const uy = Math.cos(rad);
  return {
    x1: 0.5 - ux / 2,
    y1: 0.5 - uy / 2,
    x2: 0.5 + ux / 2,
    y2: 0.5 + uy / 2,
  };
}

/** "0.444" -> "44,4%" | "0.30" -> "30%" (pt-BR, decimal só quando necessário). */
function formatPercent(fraction: string) {
  return new Intl.NumberFormat("pt-BR", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(Number(fraction));
}

/** Valor sem símbolo de moeda: a moeda aparece uma vez, no centro do donut. */
function formatAmount(value: number | string) {
  return new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value));
}

export function ExpenseBreakdownChart({ profileId }: { profileId: string }) {
  // useId devolve delimitadores (`:r0:` / `«r0»`) que não sobrevivem a `url(#...)`.
  const gradientId = `ft-expense-${useId().replace(/[^a-zA-Z0-9]/g, "")}`;
  const { data, isLoading, isError } = useQuery({
    queryKey: ["expense-breakdown", profileId],
    queryFn: () => dashboardApi.getExpenseBreakdown(profileId),
  });

  const currency = data?.[0]?.amount.currency ?? "BRL";
  const chartData = (data ?? []).map((item) => ({
    name: item.category,
    value: Number(item.amount.amount),
  }));
  const total = chartData.reduce((sum, item) => sum + item.value, 0);

  // Ângulo do meio de cada fatia, para orientar o gradiente ao longo do arco.
  // Reproduz o layout do Recharts: varre 360° a partir de 0°, descontando o
  // paddingAngle que ele reserva entre as fatias.
  const usableAngle = 360 - PADDING_ANGLE * chartData.length;
  let sweptAngle = 0;
  const slices = chartData.map((item, index) => {
    const span = total > 0 ? (item.value / total) * usableAngle : 0;
    const midAngle = index * PADDING_ANGLE + sweptAngle + span / 2;
    sweptAngle += span;
    return {
      id: `${gradientId}-slice-${index}`,
      color: SLICE_COLORS[index % SLICE_COLORS.length],
      axis: gradientAxis(midAngle),
    };
  });

  function formatMoney(value: number | string) {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(Number(value));
  }

  return (
    /*
     * Último card da fileira de analytics. Com ele, `.ft-analytics-card` deixa de
     * ter qualquer uso — ver o relatório: a classe e a `@container ft-card` viram
     * CSS morto em design-system.css.
     *
     * A armadilha aqui é diferente dos dois cards anteriores. Este card tinha uma
     * container query **própria** — `@container ft-card (max-width: 440px)` — que
     * dependia do `container: ft-card` declarado por `.ft-analytics-card`. Largar a
     * classe sem mais nada mataria essa query em silêncio e o layout nunca mais
     * empilharia. Ela está traduzida para `@max-[440px]/card:` aqui embaixo.
     *
     * A tradução é 1:1: as duas queries medem o content box do mesmo elemento, só
     * muda o nome do container (`ft-card` → `card`).
     */
    <Card.Root interactive className="h-auto self-start">
      <Card.Header
        /* Sem `.ft-card-header`: só este card não leva a linha divisória entre
           título e dados. A classe traz `border-bottom` não-layered (um utility
           como `border-b-0` perde em especificidade); `CardHeader` já cobre
           flex/items-start/justify-between/gap, então só falta reproduzir o
           afastamento inferior. */
        className="mb-[18px]"
        title={
          /* Sem `.ft-card-title`: a regra não-layered fixaria 16px e venceria o
             clamp. Valores reproduzidos. */
          <div className="min-w-0">
            <h3 className="m-0 text-[length:clamp(15px,3.6cqi,20px)] leading-[1.3] font-semibold break-normal [overflow-wrap:normal] [word-break:normal]">
              Distribuição das despesas
            </h3>
            <p className="m-0 mt-1.5 text-[length:clamp(12px,2.8cqi,14px)] text-[color:var(--ft-text-secondary)]">Visão geral por categoria</p>
          </div>
        }
      />

      <Card.Content className="flex flex-none flex-col pb-5">
        {isLoading && <p className="text-sm text-muted-foreground">Carregando distribuição...</p>}
        {isError && <p className="text-sm text-red-400">Não foi possível carregar a distribuição.</p>}

        {data && data.length === 0 && <p className="text-sm text-muted-foreground">Nenhuma obrigação cadastrada.</p>}

        {data && data.length > 0 && (
          /*
           * `.ft-expense-layout` reproduzido aqui.
           *
           * A coluna do donut era `minmax(120px,246px)`: ou 246px cheios, ou nada
           * entre isso e o mínimo. Num card de 484px sobravam ~190px para a legenda
           * e o nome da categoria virava "Mor...". Agora o diâmetro é fluido
           * (`clamp(118px, 44cqi, 246px)` — os mesmos 246px a partir de ~560px de
           * content box, encolhendo proporcionalmente daí para baixo), e a fonte da
           * legenda encolhe junto (ver `.ft-chart-legend`). Nome nenhum é truncado.
           *
           * O empilhamento caiu de 440px para 330px de content box porque agora é
           * o ponto onde a legenda deixa de caber de fato, não onde ela perderia o
           * tamanho de widescreen. Abaixo disso a redução acabou e a saída é
           * reorganizar: donut em cima, legenda com a largura toda.
           *
           * A coluna da legenda era `minmax(0,1fr)`: estica para preencher toda a
           * sobra do card. Isso é inofensivo quando o card é um entre três na
           * fileira (~414px), mas na faixa intermediária este card fica sozinho na
           * linha e ocupa a largura cheia da seção (~860-960px) — aí o `1fr` vira
           * um vácuo entre o nome da categoria e as colunas de %/valor, que ficam
           * pregadas na borda direita. `fit-content(300px)` resolve: a legenda cresce
           * até o que o conteúdo pede (nome mais comprido incluso), nunca além de
           * 300px, e a sobra vira respiro à direita — não um vão no meio.
           */
          <div
            className={cn(
              "grid grid-cols-[clamp(118px,44cqi,246px)_fit-content(300px)] items-center gap-[clamp(8px,2.4cqi,16px)]",
              "@max-[330px]/card:grid-cols-[minmax(0,1fr)] @max-[330px]/card:justify-items-center"
            )}
          >
            {/*
             * `aspect-square` em vez de altura fixa de 246px: o donut é redondo e
             * seu raio já era limitado pela menor dimensão. Lado a lado a coluna
             * mede 246px e o resultado é o mesmo 246x246 de antes; empilhado o
             * container cai para 220x220 em vez de 220x246, cortando 26px de vazio
             * vertical sem mudar o diâmetro do donut.
             */}
            <div className="relative aspect-square w-full min-w-0 @max-[330px]/card:max-w-[220px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <defs>
                    {slices.map((slice) => (
                      <linearGradient key={slice.id} id={slice.id} {...slice.axis}>
                        <stop offset="0%" stopColor={`color-mix(in srgb, ${slice.color}, #000 ${EDGE_DARKEN})`} />
                        <stop offset="50%" stopColor={slice.color} />
                        <stop offset="100%" stopColor={`color-mix(in srgb, ${slice.color}, #000 ${EDGE_DARKEN})`} />
                      </linearGradient>
                    ))}
                  </defs>
                  <Pie
                    data={chartData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius="60%"
                    outerRadius="92%"
                    paddingAngle={PADDING_ANGLE}
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={entry.name} fill={`url(#${slices[index].id})`} />
                    ))}
                  </Pie>
                  <Tooltip content={<ChartTooltip formatter={formatMoney} />} />
                </PieChart>
              </ResponsiveContainer>

              <div className="ft-donut-center" aria-hidden="true">
                <span className="ft-donut-total-value">{formatAmount(total)}</span>
                <span className="ft-donut-total-currency">{currency}</span>
                <span className="ft-donut-total-label">Total mensal</span>
              </div>
            </div>

            {/* `w-full` no empilhado vinha da mesma container query. */}
            <div className="ft-chart-legend @max-[330px]/card:w-full">
              {data.map((item, index) => (
                <div key={item.category} className="ft-legend-item">
                  <span className="ft-legend-category">
                    <span className="ft-legend-dot" style={{ background: SLICE_COLORS[index % SLICE_COLORS.length] }} />
                    <span className="ft-legend-name capitalize">{item.category}</span>
                  </span>
                  <span className="ft-legend-percent">{formatPercent(item.percentage)}</span>
                  <span className="ft-legend-value">{formatAmount(item.amount.amount)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card.Content>

      {/* Sem `.ft-card-footer`: o `margin-top: 20px` não-layered venceria o
          `mt-auto` do `Card.Footer`. Valores reproduzidos. */}
      <Card.Footer className="mt-0">
        <Link
          href={`/dashboard/${profileId}/resources/obligations`}
          className="flex min-w-0 items-center justify-between gap-2 border-t border-[color:var(--ft-border)] pt-4 text-[length:clamp(13px,3cqi,16px)] text-[#b49cff]"
        >
          Ver detalhes das despesas
          <ArrowRight size={16} className="flex-none" />
        </Link>
      </Card.Footer>
    </Card.Root>
  );
}

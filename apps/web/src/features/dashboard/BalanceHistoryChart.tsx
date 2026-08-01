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
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { InfoTooltip } from "@/components/ui/tooltip";
import { Card } from "@/design-system/components/Card";
import { cn } from "@/lib/utils";

import { ChartTooltip } from "./ChartTooltip";
import { dashboardApi } from "./api";

const MONTH_ABBREVIATIONS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];

function formatMoneyPlain(amount: number, currency: string) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(amount);
}

function formatPeriodLabel(period: string) {
  const month = Number(period.slice(5, 7)) - 1;
  return MONTH_ABBREVIATIONS[month] ?? period;
}

function formatAxisTick(value: number) {
  if (Math.abs(value) >= 1000) return `${(value / 1000).toFixed(0)}K`;
  return `${value}`;
}

function LastPointDot({ cx, cy, index, dataLength }: { cx?: number; cy?: number; index?: number; dataLength: number }) {
  if (cx === undefined || cy === undefined) return null;
  const isLast = index === dataLength - 1;
  return (
    <circle
      cx={cx}
      cy={cy}
      r={isLast ? 5 : 3}
      fill={isLast ? "var(--ft-primary)" : "var(--ft-bg-surface)"}
      stroke="var(--ft-primary)"
      strokeWidth={2}
    />
  );
}

/*
 * Segundo card migrado para a moldura composta (`Card.Root/Header/Content/Footer`).
 *
 * Por que este card **deixou de usar `.ft-analytics-card`**:
 *
 * 1. Aquela classe declara `container: ft-card / inline-size`. Como
 *    `design-system.css` entra sem `@layer`, esse shorthand vence o
 *    `container-name` que o `@container/card` do `Card.Root` define — e as
 *    variantes `@max-[…]/card:` deixariam de casar **em silêncio**, sem erro
 *    nenhum. Mesma família de armadilha do content box.
 * 2. Ela impunha `min-height: 420px` e `padding-bottom: 64px` para reservar
 *    espaço a um rodapé `position: absolute`. Isso é exatamente o "grande espaço
 *    vazio" que sobrava embaixo do gráfico.
 *
 * A classe continua intacta em `design-system.css`, servindo os outros dois cards
 * da linha de analytics, que ainda não foram migrados. O que ela fazia aqui está
 * reproduzido nos utilitários abaixo, com os mesmos valores:
 *
 * - título `clamp(15px, 4.18cqi, 23px)` / line-height 1.3 (medido: 20.23px no
 *   card de 526px do dashboard — idêntico ao anterior);
 * - rodapé com borda superior, `space-between` e cor `#b49cff`;
 * - a folga de 20px entre conteúdo e rodapé virou `pb-5` no `Card.Content`,
 *   para o `mt-auto` do `Card.Footer` continuar podendo empurrar o rodapé.
 *
 * Altura: o card não impõe mais nenhuma. Ele cresce com o conteúdo e só encosta o
 * rodapé no fundo quando o grid externo lhe dá altura maior — que é o caso no
 * dashboard, onde os outros dois cards da linha ainda esticam a fileira.
 *
 * O gráfico usa proporção (`aspect-[22/10]`) em vez de altura fixa. A razão foi
 * escolhida para reproduzir o tamanho atual: no dashboard o content box tem 484px
 * e 484 ÷ 2,2 = 220px, exatamente a altura que o gráfico tinha. Abaixo de ~374px
 * de content box a proporção ficaria baixa demais para ler os eixos, e aí o piso
 * `min-h-[170px]` assume.
 */
export function BalanceHistoryChart({
  profileId,
  months = 6,
  minChartHeight,
  showFooterLink = true,
}: {
  profileId: string;
  months?: number;
  /** Piso de altura do gráfico, em px. Só para a página dedicada, que tem espaço
   *  de sobra e quer um gráfico maior que a proporção padrão daria. */
  minChartHeight?: number;
  showFooterLink?: boolean;
}) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["balance-history", profileId, months],
    queryFn: () => dashboardApi.getBalanceHistory(profileId, months),
  });

  const currency = data?.[0]?.net_balance.currency ?? "BRL";
  const chartData = (data ?? []).map((snapshot) => ({
    period: formatPeriodLabel(snapshot.period),
    fullPeriod: snapshot.period,
    balance: Number(snapshot.net_balance.amount),
  }));

  return (
    <Card.Root
      interactive
      /*
       * Altura automática, só neste card.
       *
       * `.ft-grid--analytics` não declara `align-items`, então vale o `stretch`
       * padrão do CSS Grid: os itens da fileira esticam até a altura da linha. E a
       * linha tem 420px porque os outros dois cards de analytics ainda carregam o
       * `min-height: 420px` de `.ft-analytics-card`. Resultado: este card era
       * esticado e sobrava um vão entre o gráfico e o rodapé.
       *
       * `self-start` (align-self: start) desliga o stretch **para este item**, sem
       * mexer no grid nem no `CardRoot` compartilhado. `h-auto` anula o `h-full`
       * que o `CardRoot` traz na base — ele existe para o caso normal, em que o
       * card deve preencher a célula.
       */
      className="h-auto self-start"
    >
      <Card.Header
        className="ft-card-header"
        title={
          /*
           * Tooltip movido para o slot `help` (grid, coluna própria) — antes
           * ficava embutido no `<h3>` via `ft-label-info` (inline-flex), que é
           * exatamente o padrão que o `Card.Header` agora proíbe: o help vira
           * só mais um item na linha do título e pode ser arrastado quando o
           * título quebra. Com o help numa coluna `auto` fixa e `self-start`,
           * ele fica alinhado à primeira linha do título mesmo com o
           * subtítulo embaixo — a preocupação original ("o ícone ficaria
           * centralizado ao lado do bloco inteiro") não existe mais: isso era
           * comportamento do `flex` antigo, não da grade.
           *
           * Sem `.ft-card-title`: a regra não-layered fixaria 16px e venceria o
           * clamp. Os valores dela estão reproduzidos aqui.
           */
          <div className="min-w-0">
            <h3 className="m-0 text-[length:clamp(15px,4.18cqi,23px)] leading-[1.3] font-semibold">
              Evolução do saldo líquido
            </h3>
            <p className="ft-card-subtitle">Últimos {months} meses</p>
          </div>
        }
        help={
          <InfoTooltip
            label="Como o seu saldo líquido variou mês a mês. Uma linha subindo indica que você está acumulando reservas."
            iconSize={13}
          />
        }
      />

      {/*
       * `flex-none` anula o `flex-1` da base do `Card.Content`: aqui o conteúdo
       * não deve crescer para preencher sobra vertical, ele define a altura.
       * O `pb-5` é a folga normal até o rodapé — os mesmos 20px que o
       * `margin-top` de `.ft-card-footer` dava antes.
       */}
      <Card.Content className={cn("flex flex-none flex-col", showFooterLink && "pb-5")}>
        {isLoading && <p className="text-sm text-muted-foreground">Carregando histórico...</p>}
        {isError && <p className="text-sm text-red-400">Não foi possível carregar o histórico.</p>}

        {data && data.length === 0 && (
          <p className="text-sm text-muted-foreground">Ainda não há histórico de saldo suficiente.</p>
        )}

        {data && data.length > 0 && (
          /*
           * Sem `.ft-chart-container`: aquela classe fixava `min-height: 250px`,
           * que num card estreito deixava o gráfico alto e magro. `relative` era
           * a outra coisa que ela dava e está reproduzido.
           */
          <div
            className="relative aspect-[22/10] w-full min-w-0 min-h-[170px]"
            style={minChartHeight ? { minHeight: minChartHeight } : undefined}
          >
            <ResponsiveContainer width="100%" height="100%">
              {/*
               * Margens >= 8px porque o ponto do último mês tem raio 5 (e o
               * `activeDot` também): com 4px de margem superior, um saldo no topo
               * da escala fazia o círculo passar da borda do SVG e ser cortado.
               */}
              <AreaChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                <defs>
                  <linearGradient id="balanceGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--ft-primary)" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="var(--ft-primary)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} stroke="var(--ft-border)" strokeDasharray="3 3" />
                {/*
                 * `preserveStartEnd` + `minTickGap` baixo: os rótulos de mês têm
                 * ~20px e cabem todos os seis mesmo num card de 280px (238px de
                 * content box, menos 40px do eixo Y). Um gap maior fazia o
                 * Recharts descartar "Jul" sem necessidade. Se algum dia não
                 * couberem, ele descarta os do meio e preserva primeiro e último
                 * — melhor que sobrepor.
                 */}
                <XAxis
                  dataKey="period"
                  tick={{ fontSize: 11, fill: "var(--ft-text-secondary)" }}
                  axisLine={false}
                  tickLine={false}
                  interval="preserveStartEnd"
                  minTickGap={2}
                  height={20}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: "var(--ft-text-secondary)" }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={formatAxisTick}
                  domain={["auto", "auto"]}
                  width={40}
                />
                <Tooltip
                  content={<ChartTooltip formatter={(value) => formatMoneyPlain(Number(value), currency)} />}
                  labelFormatter={(_, payload) => {
                    const fullPeriod = payload?.[0]?.payload?.fullPeriod as string | undefined;
                    if (!fullPeriod) return "";
                    const [year, month] = fullPeriod.split("-");
                    return `${MONTH_ABBREVIATIONS[Number(month) - 1]}/${year}`;
                  }}
                  cursor={{ stroke: "var(--ft-border-hover)" }}
                />
                <Area
                  type="monotone"
                  dataKey="balance"
                  name="Saldo líquido"
                  stroke="var(--ft-primary)"
                  strokeWidth={2}
                  fill="url(#balanceGradient)"
                  dot={(props: { cx?: number; cy?: number; index?: number }) => (
                    <LastPointDot key={props.index} {...props} dataLength={chartData.length} />
                  )}
                  activeDot={{ r: 5, fill: "var(--ft-primary)", stroke: "var(--ft-bg-surface)", strokeWidth: 2 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </Card.Content>

      {showFooterLink && (
        /*
         * Sem `.ft-card-footer`: a regra traz `margin-top: 20px` não-layered, que
         * venceria o `mt-auto` do `Card.Footer` e impediria o rodapé de descer
         * até o fundo quando o grid dá altura extra. Valores reproduzidos.
         */
        <Card.Footer className="mt-0">
          <Link
            href={`/dashboard/${profileId}/balance-history`}
            className="flex min-w-0 items-center justify-between gap-2 border-t border-[color:var(--ft-border)] pt-4 text-[#b49cff]"
          >
            Ver histórico completo
            <ArrowRight size={16} className="flex-none" />
          </Link>
        </Card.Footer>
      )}
    </Card.Root>
  );
}

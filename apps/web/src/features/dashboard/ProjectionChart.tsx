"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { useCallback, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { InfoTooltip } from "@/components/ui/tooltip";
import { Card } from "@/design-system/components/Card";
import { cn } from "@/lib/utils";

import { ChartTooltip } from "./ChartTooltip";
import { dashboardApi } from "./api";
import type { PeriodProjectionDto } from "./types";

const SCENARIO_OPTIONS = [
  { value: "probable", label: "Cenário provável" },
  { value: "adverse", label: "Cenário adverso" },
] as const;

const HORIZON_OPTIONS = [
  { value: "3", label: "3 meses" },
  { value: "6", label: "6 meses" },
  { value: "12", label: "12 meses" },
] as const;

const MONTH_ABBREVIATIONS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];

function formatMoney(value: number | string, currency: string) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(Number(value));
}

function formatAxisTick(value: number) {
  if (Math.abs(value) >= 1000) return `${(value / 1000).toFixed(0)}K`;
  return `${value}`;
}

/* "2026-08" -> "Ago/26". Rótulo do eixo X e do tooltip. A causa da sobreposição
   original: o eixo mostrava o período cru ("2026-08", 7 caracteres) em todos os
   12 pontos — não cabe. Isto não remove dado nenhum, só encurta o texto exibido. */
function formatPeriodShort(period: string) {
  const [year, month] = period.split("-");
  return `${MONTH_ABBREVIATIONS[Number(month) - 1]}/${year.slice(2)}`;
}

function formatPeriodFull(period: string) {
  const [year, month] = period.split("-");
  return `${MONTH_ABBREVIATIONS[Number(month) - 1]}/${year}`;
}

function toChartPoint(period: PeriodProjectionDto) {
  return {
    period: period.period,
    income: Number(period.income_total.amount),
    expense: -Number(period.expense_total.amount),
    balance: Number(period.closing_balance.amount),
    deficit: period.deficit,
  };
}

/*
 * Mede a largura real do elemento em px via ResizeObserver. Necessário porque a
 * densidade de labels do eixo X e a altura do gráfico são decididas pelo
 * Recharts na renderização do SVG — não existe equivalente a container query
 * para isso, então a única forma de reagir à largura do card é medir em JS.
 *
 * Callback ref, não `useRef` + `useEffect([])`: a div medida só existe no DOM
 * depois que `data` chega (`{data && (<div ref={...}>)}`), e um efeito com
 * dependências vazias roda uma vez no mount do componente — antes da div
 * existir — e nunca mais. `width` ficava travado em 0 para sempre, mesmo com o
 * card em 1217px reais. Callback ref dispara toda vez que o nó entra ou sai do
 * DOM, então funciona também para nós montados depois.
 */
function useElementWidth<T extends HTMLElement>() {
  const [width, setWidth] = useState(0);
  const observerRef = useRef<ResizeObserver | null>(null);

  const ref = useCallback((el: T | null) => {
    observerRef.current?.disconnect();
    observerRef.current = null;
    if (!el) return;
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width));
    observer.observe(el);
    observerRef.current = observer;
  }, []);

  return [ref, width] as const;
}

/*
 * Escolhe `count` itens de `items` distribuídos uniformemente, sempre incluindo
 * o primeiro e o último. Usado para controlar a QUANTIDADE exata de labels do
 * eixo X — o `interval` numérico do Recharts só pula "1 a cada N", o que não
 * bate com contagens não-divisoras de 12 (ex.: pedir 5 labels de 12 pontos).
 */
function pickEvenly<T>(items: readonly T[], count: number): T[] {
  if (count >= items.length) return [...items];
  if (count <= 1) return items.length > 0 ? [items[0]] : [];
  const step = (items.length - 1) / (count - 1);
  const picked = Array.from({ length: count }, (_, i) => items[Math.round(i * step)]);
  return [...new Set(picked)];
}

/*
 * Quantidade de labels do eixo X por largura de gráfico. Limiares calibrados
 * para bater os tamanhos de card pedidos na validação:
 * >= 900px de gráfico (dashboard real, ~1217px de content box) → 12 labels,
 * o mês inteiro — só nessa largura sobra espaço para todos sem sobrepor.
 * 520px de card ≈ 478px de gráfico → 6 labels
 * 400px de card ≈ 358px de gráfico → 5 labels
 * 320px de card ≈ 278px de gráfico → 4 labels
 * 280px de card ≈ 238px de gráfico → 3 labels
 */
function xAxisTickCount(width: number) {
  if (width === 0) return 6;
  if (width >= 900) return 12;
  if (width >= 420) return 6;
  if (width >= 340) return 5;
  if (width >= 260) return 4;
  return 3;
}

/*
 * Altura do gráfico em função da própria largura — mede-se em JS (não em CSS)
 * porque `ResponsiveContainer` do Recharts precisa de um número de pixels real
 * para desenhar o SVG; `min-height` sozinho não basta (não é uma altura
 * definida para fins de cálculo de percentuais) e `aspect-ratio` sozinho não
 * bate as quatro faixas pedidas (160–190 / 170–200 / 180–210 / 190–220) porque
 * a mesma razão que dá 288px em 1217px de largura real do dashboard dá menos de
 * 100px nas larguras de teste, sempre no piso.
 *
 * Reta ajustada para dois pontos: 238px de gráfico → 175px de altura (piso da
 * faixa de 280px de card) e 1217px de gráfico → 288px de altura (medida real no
 * dashboard, preservando o desenho já aprovado). Os quatro tamanhos de teste
 * caem dentro das faixas pedidas: 478→~203px, 358→~189px, 278→~180px,
 * 238→175px.
 */
function chartHeight(width: number) {
  if (width === 0) return 288;
  return Math.min(300, Math.max(160, 147 + width * 0.115));
}

export function ProjectionChart({ profileId }: { profileId: string }) {
  const [scenario, setScenario] = useState<"probable" | "adverse">("probable");
  const [months, setMonths] = useState<3 | 6 | 12>(12);
  const [chartRef, chartWidth] = useElementWidth<HTMLDivElement>();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["projection", profileId, scenario, months],
    queryFn: () => dashboardApi.getProjection(profileId, { scenario, months }),
  });

  const chartData = data?.periods.map(toChartPoint) ?? [];
  const currency = data?.periods[0]?.income_total.currency ?? "BRL";
  const visibleTicks = pickEvenly(
    chartData.map((point) => point.period),
    xAxisTickCount(chartWidth)
  );

  return (
    /*
     * `h-auto`, mas SEM `self-start`. O pai direto deste card é `.ft-section`
     * (flex-direction: column), não um CSS Grid como os três cards de
     * analytics. `self-start`/`align-self` atua no eixo CRUZADO do flex — numa
     * coluna, o eixo cruzado é o HORIZONTAL, não o vertical. Aplicá-lo aqui
     * fazia o card encolher para a largura do conteúdo intrínseco (medido:
     * 43px) em vez de ocupar a largura da coluna, e o texto reagia quebrando
     * caractere por caractere — 1243px de altura, a "esticada até o fim da
     * viewport" que o usuário reportou. As duas queixas eram o mesmo bug.
     *
     * `h-full` da base do CardRoot não precisava de correção alguma: o
     * ancestral mais próximo com altura definida está muitos níveis acima
     * (não há `h-screen`/`min-h-screen` na cadeia até `.ft-section`), então a
     * porcentagem de `height:100%` já resolvia para `auto` — o card sempre
     * cresceu só com o conteúdo. `h-auto` é redundante nesta cadeia
     * específica, mas mantido por clareza e para não depender desse detalhe
     * frágil da árvore de ancestrais.
     */
    <Card.Root interactive className="h-auto">
      <Card.Header
        className={cn(
          "ft-card-header",
          /*
           * Abaixo de 460px de content box (card ~502px) os selects saem da
           * linha do título. `flex-wrap` sozinho não bastaria: o título tem
           * `min-w-0` e encolheria para caber ao lado dos selects em vez de
           * empurrá-los para baixo — por isso o wrapper de ações (marcado com
           * `data-slot=card-header-actions` na moldura compartilhada) é forçado
           * a `w-full` no mesmo ponto, o que obriga a quebra de linha
           * independente de quanto o título ainda conseguiria encolher.
           */
          "@max-[460px]/card:flex-wrap",
          "@max-[460px]/card:[&_[data-slot=card-header-actions]]:w-full"
        )}
        title={<h3 className="ft-card-title m-0">Projeção de fluxo de caixa</h3>}
        help={
          <InfoTooltip
            label="Estimativa de entradas, saídas e saldo acumulado nos próximos meses, conforme o cenário e o horizonte escolhidos."
            iconSize={13}
          />
        }
        actions={
          <div
            className={cn(
              "flex w-full justify-end gap-2",
              /* Abaixo de 300px de content box (card ~340px) os dois selects
                 empilham e cada um ocupa a largura toda, em vez de dividir a
                 linha — únicas larguras (320/280) em que os selects, em suas
                 larguras naturais (176px + 128px + gap), não cabem lado a lado. */
              "@max-[300px]/card:flex-col"
            )}
          >
            <Select
              items={SCENARIO_OPTIONS}
              value={scenario}
              onValueChange={(value) => setScenario(value as "probable" | "adverse")}
            >
              {/*
               * Larguras naturais (`w-44`/`w-32`), não `flex-1`/`min-w-0`: a
               * versão anterior dividia o espaço igualmente entre os dois
               * selects, o que podia espremer "Cenário provável" abaixo do
               * necessário. Nas duas únicas larguras onde os selects não
               * compartilham linha com o título (abaixo de 460px), eles têm a
               * largura inteira do card só para si — cabem no tamanho natural
               * até ficarem estreitos demais, onde então empilham (300px).
               */}
              <SelectTrigger className="w-44 @max-[300px]/card:w-full" aria-label="Cenário da projeção">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SCENARIO_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              items={HORIZON_OPTIONS}
              value={String(months)}
              onValueChange={(value) => setMonths(Number(value) as 3 | 6 | 12)}
            >
              <SelectTrigger className="w-32 @max-[300px]/card:w-full" aria-label="Horizonte da projeção">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {HORIZON_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        }
      />

      {/* `flex-none` anula o `flex-1` da base do Card.Content: o conteúdo
          define a altura, não cresce para preencher espaço vazio. */}
      <Card.Content className="flex flex-none flex-col">
        {isLoading && <p className="text-sm text-muted-foreground">Carregando projeção...</p>}
        {isError && <p className="text-sm text-red-500">Não foi possível carregar a projeção.</p>}

        {data && (
          <>
            {/*
             * Sem `.ft-chart-container`: era o único consumidor da classe, e ela
             * fixava `min-height: 250px` sem se importar com a largura. A altura
             * real vem de `chartHeight(chartWidth)`, calculada em JS e passada
             * direto para o `height` do ResponsiveContainer — não depende de
             * nenhuma regra CSS de altura no wrapper, então não há necessidade
             * de aspect-ratio nem min-height aqui.
             */}
            <div ref={chartRef} className="relative w-full min-w-0">
              <ResponsiveContainer width="100%" height={chartHeight(chartWidth)}>
                <ComposedChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--ft-border)" />
                  <XAxis
                    dataKey="period"
                    tick={{ fontSize: 11, fill: "var(--ft-text-secondary)" }}
                    axisLine={false}
                    tickLine={false}
                    height={20}
                    interval={0}
                    ticks={visibleTicks}
                    tickFormatter={formatPeriodShort}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: "var(--ft-text-secondary)" }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={formatAxisTick}
                    width={40}
                  />
                  <Tooltip
                    content={<ChartTooltip formatter={(value) => formatMoney(value, currency)} />}
                    labelFormatter={(label) => formatPeriodFull(String(label))}
                    cursor={{ fill: "var(--ft-bg-surface-hover)" }}
                  />
                  <ReferenceLine y={0} stroke="var(--ft-border-hover)" strokeDasharray="4 4" />
                  <Bar dataKey="income" name="Entradas" fill="var(--ft-success)" />
                  <Bar dataKey="expense" name="Saídas" fill="var(--ft-danger)" />
                  <Line type="monotone" dataKey="balance" name="Saldo acumulado" stroke="var(--ft-info)" strokeWidth={2} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {data.first_deficit_period ? (
              <p className="mt-2 text-sm text-red-500">
                Primeiro mês com déficit projetado: {data.first_deficit_period}
              </p>
            ) : (
              <p className="mt-2 text-sm text-muted-foreground">Sem déficit projetado neste horizonte.</p>
            )}

            <div className="mt-3 text-xs text-muted-foreground">
              <p className="mb-1 flex items-center gap-1.5 font-medium text-foreground">
                Premissas desta simulação
                <InfoTooltip
                  label="A projeção não é uma previsão exata: ela aplica ajustes ao seu fluxo atual. O cenário provável mantém tudo como está; o adverso simula um aperto (menos renda, mais custos)."
                  iconSize={13}
                />
              </p>
              <ul className="ft-assumptions-list">
                {data.assumptions.map((assumption) => (
                  <li key={assumption}>{assumption}</li>
                ))}
              </ul>
            </div>
          </>
        )}
      </Card.Content>
    </Card.Root>
  );
}

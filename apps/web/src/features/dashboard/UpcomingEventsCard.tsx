"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { ArrowRight, Calendar } from "lucide-react";
import Link from "next/link";

import { InfoTooltip } from "@/components/ui/tooltip";
import { buttonVariants } from "@/design-system/components/Button";
import { Card } from "@/design-system/components/Card";
import { IconChip } from "@/design-system/components/IconChip";
import { cn } from "@/lib/utils";

import type { UpcomingEventDto } from "./types";

const MONTH_ABBREVIATIONS = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"];

function formatMoney(amount: string, currency: string) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(Number(amount));
}

function formatEventMonth(date: string) {
  return MONTH_ABBREVIATIONS[Number(date.slice(5, 7)) - 1];
}

function describeEventDirection(direction: string) {
  return direction === "income" ? "Recebimento previsto" : "Pagamento previsto";
}

/*
 * Card piloto da refatoração estrutural.
 *
 * O que mudou não é o visual, é de que largura a reorganização depende. Antes,
 * a linha do evento só saía de três colunas para duas dentro de
 * `@media (max-width: 720px)` — largura da JANELA. Só que este card vive numa
 * coluna `1.1fr` de quatro (`.ft-grid--indicators`): num monitor de 1440px ele
 * mede ~320px e a media query nunca dispara. Resultado: as três colunas
 * continuavam valendo, a coluna `auto` do valor não encolhia (`white-space:
 * nowrap`) e o `overflow: hidden` do card cortava o valor em silêncio.
 *
 * Agora a reorganização depende da largura do próprio card (`@container/card`,
 * declarado em `Card.Root`).
 *
 * ATENÇÃO ao ler os breakpoints abaixo: uma container query mede o *content box*
 * do container, não o border box. O card tem 20px de padding e 1px de borda de
 * cada lado, então **content box = largura do card − 42px**. Ignorar isso foi o
 * erro da primeira versão: um `@max-[380px]` disparava já num card de 422px, e
 * como no dashboard o card mede 413px (content box 371px), o valor aparecia
 * empilhado embaixo do título mesmo num monitor de 1920px. Os números aqui são
 * de content box, com a largura de card equivalente ao lado:
 *
 * - content < 330px (card < 372px) → valor desce   [data] [titulo] / [valor]
 * - content < 150px (card < 192px) → tudo empilha  [data] / [titulo] / [valor]
 *
 * Tipografia e espaçamentos são fluidos em `cqi` (1cqi = 1% do content box do
 * card). Os `clamp()` estão calibrados para que **no máximo eles batam exatamente
 * o tamanho atual** — 14px no título, 13px na descrição, 14px no valor, 16px no
 * dia — atingido em content box de 371px, que é a largura real no dashboard.
 * Ou seja: o desenho de hoje é preservado onde o card já cabia, e só encolhe
 * abaixo disso, em vez de estourar. O piso do clamp garante legibilidade.
 *
 * Os demais valores visuais (raio 12, cores, pesos, `tabular-nums`) são os de
 * `.ft-event-*` em design-system.css, reproduzidos aqui porque a regra responsiva
 * é específica deste card, não da moldura. O design system não foi alterado.
 *
 * Três exceções deliberadas, todas exigidas por "nenhum conteúdo pode ser
 * cortado":
 *
 * - o título perdeu `-webkit-line-clamp: 2` e quebra em quantas linhas precisar;
 * - o valor mantém `nowrap` na faixa larga (onde sempre coube), mas pode quebrar
 *   abaixo de 330px de content box, onde nem uma coluna inteira comporta
 *   "R$ 850.000.000,00";
 * - o link do rodapé sobrescreve o `whitespace-nowrap` da base de `buttonVariants`.
 */
export function UpcomingEventsCard({
  profileId,
  events,
}: {
  profileId: string;
  events: UpcomingEventDto[];
}) {
  return (
    <Card.Root interactive className="ft-indicators-events">
      <Card.Header
        className={cn(
          "ft-card-header",
          /*
           * Ícone, título e tooltip ficam na mesma linha. A versão anterior
           * empilhava o título abaixo do ícone em card estreito; isso saiu junto
           * com a correção do grid, que é onde o problema realmente estava — o
           * card não fica mais espremido a ponto de precisar empilhar.
           *
           * O `flex-wrap` de `Card.Header` continua como rede de segurança: se um
           * dia o título não couber mesmo, ele desce para a linha de baixo em vez
           * de espremer ou cortar. Mas não é mais o caminho normal.
           */
          // Gap ícone↔título fluido: 6px de base + margem do ícone = 8px..12px.
          "[&_[data-slot=card-header-icon]]:me-[clamp(2px,3cqi,6px)]"
        )}
        icon={
          /*
           * Chip fluido. `size-[38px]` da variante `sm` do IconChip é sobrescrito
           * aqui — 10.3cqi bate exatamente 38px no content box de 371px (largura
           * real no dashboard) e desce até 32px no card espremido.
           */
          <IconChip icon={Calendar} tone="purple" size="sm" className="size-[clamp(32px,10.3cqi,38px)]" />
        }
        title={
          /*
           * Sem `.ft-card-title` de propósito: `design-system.css` entra sem
           * `@layer`, então `.ft-card-title { font-size: 16px }` venceria o
           * utilitário do Tailwind e o título nunca ficaria fluido. Os valores da
           * classe (16px / 600 / line-height 1.5) estão reproduzidos aqui.
           *
           * `6cqi` faz a fonte variar de fato na faixa útil (12px no card
           * espremido, 16px no dashboard). O teto ficou em 16px, e não nos 14px
           * sugeridos, para não encolher o título no dashboard — ver comentário no
           * topo do arquivo sobre preservar o desenho atual.
           *
           * Quebra só entre palavras: nada de partir "financeiros" ao meio.
           */
          <h3 className="min-w-0 text-[length:clamp(12px,6cqi,16px)] leading-[1.5] font-semibold break-normal [overflow-wrap:normal] [word-break:normal]">
            Próximos eventos financeiros
          </h3>
        }
        help={
          <InfoTooltip
            label="Recebimentos e pagamentos futuros já previstos, como impostos, férias e 13º salário."
            iconSize={13}
          />
        }
      />

      {/*
       * Sem `.ft-event-list` pelo mesmo motivo do título: a regra não-layered
       * fixaria `gap: 12px` e impediria o gap fluido. `overflow-y-auto` vinha de
       * `.ft-indicators-events .ft-event-list` e está reproduzido aqui.
       */}
      <Card.Content className="grid content-start gap-[clamp(8px,3.2cqi,12px)] overflow-y-auto">
        {events.length === 0 && <p className="text-sm text-muted-foreground">Nenhum evento futuro cadastrado.</p>}

        {events.map((event) => (
          <div
            key={event.id}
            className={cn(
              "grid grid-cols-[clamp(46px,14.6cqi,54px)_minmax(0,1fr)] items-center",
              "gap-x-[clamp(10px,3.8cqi,14px)]",
              "rounded-[12px] border border-[color:var(--ft-border)] bg-[rgba(17,38,56,0.75)]",
              "px-[clamp(10px,4.3cqi,16px)] py-[clamp(10px,3.8cqi,14px)]",
              // Espaço só para a data: empilha tudo numa coluna.
              "@max-[150px]/card:grid-cols-1 @max-[150px]/card:items-start @max-[150px]/card:gap-y-[8px]"
            )}
          >
            <div
              className={cn(
                "grid h-[clamp(42px,13.5cqi,50px)] w-[clamp(38px,11.8cqi,44px)] flex-none place-items-center",
                "rounded-[10px] bg-[color:var(--ft-primary-soft)]",
                "text-[length:clamp(13px,4.3cqi,16px)] font-bold leading-none text-[color:var(--ft-primary)]"
              )}
            >
              {event.date.slice(8, 10)}
              <small className="text-[length:clamp(9px,2.7cqi,10px)] font-bold">{formatEventMonth(event.date)}</small>
            </div>

            <div
              className={cn(
                "flex min-w-0 items-center gap-[clamp(10px,3.8cqi,14px)]",
                // Sem espaço para título e valor lado a lado: valor desce.
                "@max-[330px]/card:flex-col @max-[330px]/card:items-start @max-[330px]/card:gap-y-[4px]"
              )}
            >
              <div className="min-w-0 flex-1">
                <p className="text-[length:clamp(13px,3.77cqi,14px)] font-semibold [overflow-wrap:anywhere]">
                  {event.description}
                </p>
                <p className="mt-[5px] text-[length:clamp(12px,3.5cqi,13px)] text-[color:var(--ft-text-secondary)] [overflow-wrap:anywhere]">
                  {describeEventDirection(event.direction)}
                </p>
              </div>

              <span
                className={cn(
                  "min-w-0 flex-none whitespace-nowrap text-right",
                  "text-[length:clamp(13px,3.77cqi,14px)] font-bold text-[color:var(--ft-success)]",
                  "tabular-nums tracking-[-0.02em]",
                  "@max-[330px]/card:whitespace-normal @max-[330px]/card:text-left @max-[330px]/card:[overflow-wrap:anywhere]"
                )}
              >
                {formatMoney(event.amount.amount, event.amount.currency)}
              </span>
            </div>
          </div>
        ))}
      </Card.Content>

      <Card.Footer className="mt-3">
        <Link
          href={`/dashboard/${profileId}/resources/events`}
          className={cn(
            buttonVariants({ variant: "ghost-purple", fullWidth: true }),
            "justify-between",
            /*
             * `buttonVariants` traz `whitespace-nowrap` na base: num card muito
             * estreito o rótulo não quebrava e empurrava a seta 44px para fora da
             * borda. Liberado aqui, no card concreto, para não mexer no botão do
             * design system — `min-h-10` já deixa o botão crescer em altura.
             */
            "min-w-0 whitespace-normal py-2 text-left [overflow-wrap:anywhere]",
            /*
             * "Ver todos os eventos" ocupa ~128px a 13px. Com padding 10 e gap 8
             * o rótulo precisava de 156px e quebrava em duas linhas já num card de
             * 215px, faltando só 3px. Os três pisos foram baixados juntos —
             * padding 10→8, gap 8→4, fonte 13→12 — o que devolve ~22px e mantém o
             * rótulo numa linha até ~197px de card.
             *
             * Os tetos continuam batendo o desenho atual no dashboard (content box
             * 371px): fonte 14px, padding 16px, gap 8px.
             */
            "text-[length:clamp(12px,3.77cqi,14px)]",
            "px-[clamp(8px,4.3cqi,16px)] gap-[clamp(4px,2.2cqi,8px)]"
          )}
        >
          Ver todos os eventos
          <ArrowRight size={16} className="flex-none" />
        </Link>
      </Card.Footer>
    </Card.Root>
  );
}

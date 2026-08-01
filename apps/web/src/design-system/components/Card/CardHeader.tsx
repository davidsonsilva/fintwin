/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { cn } from "@/lib/utils";

import type { CardHeaderProps } from "./card.types";

/*
 * Cabeçalho do card: ícone opcional, título, ajuda opcional e ações opcionais.
 *
 * Só trata alinhamento e quebra segura. O visual (divisória, margem, tamanho da
 * fonte) vem das classes que o card concreto passa em `className`.
 *
 * Padrão oficial (icone/título/help): `grid grid-cols-[auto_minmax(0,1fr)_auto]`,
 * não `flex`. Um flex simples falha assim que o título quebra em mais de uma
 * linha — o help é só mais um item na mesma linha flex e pode ser empurrado
 * para baixo ou para o lado junto com a quebra. A grade evita isso: a coluna
 * do ícone e a do help ficam fixas em `auto` (nunca maiores que o próprio
 * conteúdo), a do título em `minmax(0,1fr)` — ele quebra sozinho, dentro da
 * própria coluna, sem arrastar ícone nem help.
 *
 * As colunas da grade são calculadas conforme `icon`/`help` existem ou não —
 * não é sempre `auto minmax(0,1fr) auto`. Um card sem ícone (os de analytics,
 * por exemplo, só têm título+tooltip) não pode ganhar uma coluna `auto`
 * fantasma: mesmo vazia, ela ainda participaria do `gap-x-3`, empurrando o
 * título 12px para a direita à toa. As quatro combinações são strings
 * literais (não construídas em runtime) de propósito — o Tailwind só
 * reconhece classes arbitrárias que aparecem como texto estático no código,
 * não geradas por template string.
 *
 * `pr-1` na grade: sem essa folga, a coluna do título consome 100% do espaço
 * até a próxima coluna, deixando o help com zero pixels de respiro antes do
 * padding do card — não estoura, mas parece colado/cortado numa largura
 * estreita (achado migrando o MetricCard, card ~220px).
 *
 * `actions` fica FORA dessa grade, num `flex` externo — é um grupo semântico
 * diferente (controles, não identificação do card) e alguns cards concretos
 * (ex. seletores de cenário/horizonte) precisam dele quebrando para uma linha
 * própria em telas estreitas, comportamento que cada card ainda decide via
 * container query própria no `data-slot=card-header-actions`.
 *
 * Os `data-slot` são o ponto de ancoragem para um card concreto reorganizar
 * por container query (mesma convenção do `ui/card` do shadcn já usado no
 * projeto). A moldura não decide *quando* reorganizar.
 */
const GRID_COLS = {
  iconHelp: "grid-cols-[auto_minmax(0,1fr)_auto]",
  iconOnly: "grid-cols-[auto_minmax(0,1fr)]",
  helpOnly: "grid-cols-[minmax(0,1fr)_auto]",
  neither: "grid-cols-[minmax(0,1fr)]",
} as const;

export function CardHeader({ icon, title, help, actions, className }: CardHeaderProps) {
  const gridColsClass = icon
    ? help
      ? GRID_COLS.iconHelp
      : GRID_COLS.iconOnly
    : help
      ? GRID_COLS.helpOnly
      : GRID_COLS.neither;

  return (
    <div data-slot="card-header" className={cn("flex min-w-0 items-start justify-between gap-4", className)}>
      <div
        data-slot="card-header-main"
        className={cn("grid min-w-0 flex-1 items-start gap-x-3 pr-1", gridColsClass)}
      >
        {icon ? (
          <span data-slot="card-header-icon" className="shrink-0">
            {icon}
          </span>
        ) : null}

        <div data-slot="card-header-title" className="min-w-0 break-normal [overflow-wrap:normal] [word-break:normal]">
          {title}
        </div>

        {help ? (
          <span data-slot="card-header-help" className="mt-0.5 shrink-0 self-start">
            {help}
          </span>
        ) : null}
      </div>

      {actions ? (
        <div data-slot="card-header-actions" className="flex flex-none items-center gap-2">
          {actions}
        </div>
      ) : null}
    </div>
  );
}

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
 * Ícone, título e ajuda são **irmãos** num flex com `flex-wrap`, não aninhados.
 * Isso é o que permite a um card concreto reorganizá-los por container query —
 * mandar o título para uma linha própria e deixar ícone e tooltip na de cima, por
 * exemplo. Com o título aninhado junto do tooltip isso era impossível de fora.
 *
 * Os `data-slot` são o ponto de ancoragem dessa reorganização (mesma convenção do
 * `ui/card` do shadcn já usado no projeto). A moldura não decide *quando*
 * reorganizar — isso é regra do card concreto.
 *
 * A ajuda é `flex-none` para o tooltip nunca ser espremido quando o título é
 * longo. O espaçamento base é 6px; o ícone acrescenta a própria margem para
 * chegar aos 12px entre ícone e título.
 */
export function CardHeader({ icon, title, help, actions, className }: CardHeaderProps) {
  return (
    <div data-slot="card-header" className={cn("flex min-w-0 items-start justify-between gap-4", className)}>
      {/*
       * Sem `flex-wrap`: com wrap, o flex quebra a linha assim que o tamanho
       * *natural* do título não cabe, em vez de deixá-lo encolher — o título
       * caía para a linha de baixo mesmo sobrando espaço. Sem wrap, ele encolhe
       * (`min-w-0`) e quebra o próprio texto em duas linhas, que é o desejado:
       * ícone, título e tooltip permanecem sempre na mesma linha.
       */}
      <div data-slot="card-header-main" className="flex min-w-0 flex-1 items-center gap-x-[6px]">
        {icon ? (
          <span data-slot="card-header-icon" className="flex flex-none items-center me-[6px]">
            {icon}
          </span>
        ) : null}
        {title}
        {help ? (
          <span data-slot="card-header-help" className="flex flex-none items-center">
            {help}
          </span>
        ) : null}
      </div>
      {actions ? <div className="flex flex-none items-center gap-2">{actions}</div> : null}
    </div>
  );
}

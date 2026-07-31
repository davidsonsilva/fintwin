/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { cn } from "@/lib/utils";

import { Card } from "./Card";
import type { CardRootProps } from "./card.types";

/*
 * Moldura estrutural do card. Reaproveita a superfície de `Card` (mesmo
 * gradiente, borda, raio e sombra) e acrescenta só o que é estrutura:
 *
 * - `@container/card`: a responsividade dos cards passa a depender da largura
 *   do próprio card, não da viewport. Container nomeado `card`, distinto do
 *   `ft-card` que `.ft-analytics-card` já declara em design-system.css — assim
 *   as `@container ft-card (...)` existentes continuam valendo sem interferência.
 * - `flex-col`: header, content e footer empilhados, com o footer podendo usar
 *   `mt-auto`.
 * - `h-full`: preenche a célula do grid onde o card foi colocado. Quem decide
 *   colunas, span e ordenação é o grid do dashboard, não o card.
 * - `min-h-0 min-w-0`: sem isso o conteúdo impõe um tamanho mínimo ao card e
 *   estoura a célula em vez de reorganizar.
 *
 * `CardRoot` não conhece valor, gráfico, métrica, data ou tipo de conteúdo.
 */
export function CardRoot({ as = "article", className, children, ...props }: CardRootProps) {
  return (
    <Card
      as={as}
      className={cn("@container/card flex h-full min-h-0 min-w-0 flex-col", className)}
      {...props}
    >
      {children}
    </Card>
  );
}

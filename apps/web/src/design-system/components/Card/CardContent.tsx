/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { cn } from "@/lib/utils";

import type { CardContentProps } from "./card.types";

/*
 * Área de conteúdo. Fornece só o espaço estrutural — `flex-1` para ocupar a
 * sobra vertical (empurrando o footer para o fim) e `min-h-0`/`min-w-0` para
 * poder encolher em vez de estourar a moldura.
 *
 * O layout interno (grid, flex, auto-fit, container queries, mudança de
 * orientação) é responsabilidade do card concreto.
 */
export function CardContent({ children, className }: CardContentProps) {
  return <div className={cn("min-h-0 min-w-0 flex-1", className)}>{children}</div>;
}

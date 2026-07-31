/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { cn } from "@/lib/utils";

import type { CardFooterProps } from "./card.types";

/*
 * Rodapé opcional. `mt-auto` mantém o rodapé no fim do card mesmo quando o
 * conteúdo é curto.
 *
 * Não presume botão: recebe link, botão, grupo de ações ou qualquer conteúdo.
 */
export function CardFooter({ children, className }: CardFooterProps) {
  return <div className={cn("mt-auto min-w-0", className)}>{children}</div>;
}

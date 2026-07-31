/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { cva, type VariantProps } from "class-variance-authority";

/*
 * Chip de ícone colorido. Espelha `.ft-metric-icon` (48px) e `.ft-status-icon` (38px)
 * de `design-system.css`, incluindo a diferença entre os dois: só o de 48px tem
 * `border: 1px solid transparent`. Por isso a borda mora na variante de tamanho, e
 * não na base — no de 38px ela não existe, como no CSS original.
 */
export const iconChipVariants = cva(["grid flex-none place-items-center"], {
    variants: {
      tone: {
        primary: [
          "text-[color:var(--ft-primary)]",
          "bg-[color:var(--ft-primary-soft)]",
          "border-[rgba(34,230,177,0.16)]",
        ],
        info: ["text-[color:var(--ft-secondary)]", "bg-[color:var(--ft-secondary-soft)]"],
        purple: ["text-[#c178ff]", "bg-[color:var(--ft-purple-soft)]"],
        warning: ["text-[color:var(--ft-warning)]", "bg-[color:var(--ft-warning-soft)]"],
      },
      size: {
        sm: "size-[38px] rounded-[12px]",
        md: "size-[48px] rounded-[15px] border border-transparent",
      },
    },
    defaultVariants: {
      tone: "info",
      size: "sm",
    },
  }
);

export type IconChipTone = NonNullable<VariantProps<typeof iconChipVariants>["tone"]>;
export type IconChipVariantProps = VariantProps<typeof iconChipVariants>;

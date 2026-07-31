/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { cva, type VariantProps } from "class-variance-authority";

/*
 * Pill de status. Espelha `.ft-badge` e seus modificadores, removidos de
 * `design-system.css`.
 *
 * O `mt-[10px]` da base vem do CSS original (`margin-top: 10px`), que embutia
 * espaçamento externo no próprio badge. Mantido para a migração ficar visualmente
 * neutra — se for para tirar, é decisão de layout, não desta troca.
 *
 * `link` é o único tom que não substitui fundo e borda da base: no CSS,
 * `.ft-badge--link` só trocava a cor do texto e acrescentava hover e cursor.
 */
export const badgeVariants = cva(
  [
    "inline-flex min-h-[22px] items-center",
    "mt-[10px] px-2 py-[2px]",
    "rounded-[var(--ft-radius-xs)] border",
    "bg-[rgba(255,255,255,0.045)] border-[color:var(--ft-border)]",
    "text-[length:var(--ft-font-size-caption)] leading-4 font-semibold",
  ],
  {
    variants: {
      tone: {
        neutral: "text-[color:var(--ft-text-secondary)]",
        success: [
          "text-[color:var(--ft-success)]",
          "bg-[color:var(--ft-success-soft)]",
          "border-[rgba(49,230,174,0.24)]",
        ],
        warning: [
          "text-[color:var(--ft-warning)]",
          "bg-[color:var(--ft-warning-soft)]",
          "border-[rgba(255,184,21,0.24)]",
        ],
        purple: [
          "text-[color:var(--ft-purple)]",
          "bg-[color:var(--ft-purple-soft)]",
          "border-[rgba(167,106,247,0.24)]",
        ],
        danger: [
          "text-[color:var(--ft-danger)]",
          "bg-[color:var(--ft-danger-soft)]",
          "border-[rgba(242,76,95,0.24)]",
        ],
        link: [
          "gap-[5px] cursor-pointer text-[#b49cff]",
          // `ease-[ease]` e não `ease-in-out`: o CSS original era `0.15s ease`, e o
          // Tailwind não expõe utilitário para a curva `ease` pura.
          "transition-[color,border-color] duration-150 ease-[ease]",
          "hover:text-[#c8b7ff] hover:border-[color:var(--ft-border-hover)]",
        ],
      },
    },
    defaultVariants: {
      tone: "neutral",
    },
  }
);

export type BadgeTone = NonNullable<VariantProps<typeof badgeVariants>["tone"]>;
export type BadgeVariantProps = VariantProps<typeof badgeVariants>;

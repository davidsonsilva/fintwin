/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

import { iconChipVariants, type IconChipVariantProps } from "./iconChipVariants";

const GLYPH_SIZE = { sm: 18, md: 22 } as const;

export type IconChipProps = IconChipVariantProps & {
  icon: LucideIcon;
  /**
   * Sobrescreve o tamanho do glifo. O CSS original não amarrava glifo a chip: o chip
   * de 38px aparecia com glifo de 18px no dashboard e de 22px no radar de fragilidade.
   * O default cobre o caso comum; quem precisa do outro passa explicitamente.
   */
  iconSize?: number;
  className?: string;
};

/**
 * Chip colorido que envolve um ícone. Por padrão o tamanho do glifo acompanha o do
 * chip, para quem usa não precisar acertar os dois separadamente.
 */
export function IconChip({ icon: Icon, tone, size = "sm", iconSize, className }: IconChipProps) {
  return (
    <span aria-hidden className={cn(iconChipVariants({ tone, size }), className)}>
      <Icon size={iconSize ?? GLYPH_SIZE[size ?? "sm"]} />
    </span>
  );
}

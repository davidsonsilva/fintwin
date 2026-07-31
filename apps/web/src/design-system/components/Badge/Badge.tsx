/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

import { badgeVariants, type BadgeVariantProps } from "./badgeVariants";

export type BadgeProps = BadgeVariantProps & {
  children: ReactNode;
  className?: string;
};

/**
 * Pill de status, renderizado como `<span>`.
 *
 * Quando o badge precisa ser outro elemento — um `<Link>`, por exemplo — use
 * `badgeVariants()` direto no `className` dele, como já se faz com `buttonVariants`.
 */
export function Badge({ tone, className, children }: BadgeProps) {
  return <span className={cn(badgeVariants({ tone }), className)}>{children}</span>;
}

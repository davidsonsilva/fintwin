/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import type { ElementType, HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

import { cardVariants, type CardVariantProps } from "./cardVariants";

type CardProps = HTMLAttributes<HTMLElement> &
  CardVariantProps & {
    as?: ElementType;
  };

export function Card({ className, size, interactive, disabled, as: Component = "div", ...props }: CardProps) {
  return <Component className={cn(cardVariants({ size, interactive, disabled }), className)} {...props} />;
}

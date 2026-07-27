/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

import { cardVariants, type CardVariantProps } from "./cardVariants";

type CardProps = HTMLAttributes<HTMLDivElement> & CardVariantProps;

export function Card({ className, size, interactive, disabled, ...props }: CardProps) {
  return <div className={cn(cardVariants({ size, interactive, disabled }), className)} {...props} />;
}

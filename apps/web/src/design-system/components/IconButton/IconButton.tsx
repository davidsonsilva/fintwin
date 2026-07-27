/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

import { iconButtonVariants, type IconButtonVariantProps } from "./iconButtonVariants";

type IconButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & IconButtonVariantProps;

export function IconButton({ className, variant, type = "button", ...props }: IconButtonProps) {
  return <button type={type} className={cn(iconButtonVariants({ variant }), className)} {...props} />;
}

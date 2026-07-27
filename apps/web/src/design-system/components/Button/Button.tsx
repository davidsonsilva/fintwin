/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

import { buttonVariants, type ButtonVariantProps } from "./buttonVariants";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & ButtonVariantProps;

export function Button({ className, variant, size, fullWidth, type = "button", ...props }: ButtonProps) {
  return <button type={type} className={cn(buttonVariants({ variant, size, fullWidth }), className)} {...props} />;
}

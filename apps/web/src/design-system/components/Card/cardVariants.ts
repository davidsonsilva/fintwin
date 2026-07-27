/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { cva, type VariantProps } from "class-variance-authority";

export const cardVariants = cva(
  [
    "relative min-w-0 overflow-hidden",
    "border border-[color:var(--ft-border)] rounded-[16px]",
    "bg-[linear-gradient(145deg,rgba(15,31,49,0.96),rgba(9,23,38,0.98))]",
    "shadow-[0_12px_30px_rgba(0,0,0,0.18)]",
    "backdrop-blur-[14px]",
    "transition-[transform,border-color,box-shadow] duration-200",
  ],
  {
    variants: {
      size: {
        default: "p-5",
        compact: "px-[18px] py-4",
      },
      interactive: {
        true: [
          "hover:-translate-y-0.5",
          "hover:border-[color:var(--ft-border-hover)]",
          "hover:shadow-[0_18px_40px_rgba(0,0,0,0.24)]",
        ],
        false: "",
      },
      disabled: {
        true: "pointer-events-none opacity-[0.62]",
        false: "",
      },
    },
    defaultVariants: {
      size: "default",
      interactive: false,
      disabled: false,
    },
  }
);

export type CardVariantProps = VariantProps<typeof cardVariants>;

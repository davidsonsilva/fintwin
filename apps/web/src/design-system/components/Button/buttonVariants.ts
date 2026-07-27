/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { cva, type VariantProps } from "class-variance-authority";

export const buttonVariants = cva(
  [
    "inline-flex flex-shrink-0 items-center justify-center gap-2",
    "whitespace-nowrap rounded-[11px] border border-transparent",
    "font-semibold transition-[transform,background,border-color,box-shadow] duration-150",
    "cursor-pointer hover:-translate-y-px active:translate-y-0",
    "disabled:cursor-not-allowed disabled:opacity-55",
  ],
  {
    variants: {
      variant: {
        primary: [
          "text-[#64f2c7] bg-[rgba(49,230,174,0.12)] border-[color:var(--ft-primary)]",
          "hover:bg-[rgba(49,230,174,0.2)]",
        ],
        secondary: [
          "text-[color:var(--ft-text-primary)] bg-white/[0.035] border-[color:var(--ft-border)]",
          "hover:bg-white/[0.07] hover:border-[color:var(--ft-border-hover)]",
        ],
        premium: [
          "text-white bg-[linear-gradient(135deg,#7135b8,#a348df,#8448d0)]",
        ],
        "ghost-purple": [
          "text-[#bda9ff] bg-[rgba(94,71,170,0.1)] border-[rgba(130,108,255,0.38)]",
        ],
        outline: [
          "text-[#b7c0ca] bg-[rgba(10,24,38,0.9)] border-[color:var(--ft-border)]",
          "hover:bg-[rgba(10,24,38,1)] hover:border-[color:var(--ft-border-hover)]",
        ],
      },
      size: {
        md: "min-h-10 px-4 text-[length:var(--ft-font-size-body-md)]",
        sm: "h-7 px-2.5 text-[11px] font-normal rounded-[9px] gap-[7px]",
      },
      fullWidth: {
        true: "w-full",
        false: "w-auto",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
      fullWidth: false,
    },
  }
);

export type ButtonVariantProps = VariantProps<typeof buttonVariants>;

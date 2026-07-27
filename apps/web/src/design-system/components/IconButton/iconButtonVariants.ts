/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { cva, type VariantProps } from "class-variance-authority";

export const iconButtonVariants = cva(
  ["relative grid flex-shrink-0 place-items-center", "cursor-pointer disabled:cursor-not-allowed disabled:opacity-55"],
  {
    variants: {
      variant: {
        ghost: [
          "size-[42px] rounded-xl border border-transparent",
          "text-[color:var(--ft-text-secondary)] bg-transparent transition-colors",
          "hover:text-[color:var(--ft-text-primary)] hover:bg-white/[0.04] hover:border-[color:var(--ft-border)]",
          "disabled:hover:text-[color:var(--ft-text-secondary)] disabled:hover:bg-transparent disabled:hover:border-transparent",
        ],
        avatar: [
          "size-[41px] rounded-full border-2 border-[#43505e]",
          "text-[color:var(--ft-text-secondary)] bg-[#283441]",
        ],
      },
    },
    defaultVariants: {
      variant: "ghost",
    },
  }
);

export type IconButtonVariantProps = VariantProps<typeof iconButtonVariants>;

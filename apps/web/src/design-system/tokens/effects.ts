/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

export const radius = {
  xs: "6px",
  sm: "8px",
  md: "12px",
  lg: "16px",
  xl: "20px",
  "2xl": "24px",
  pill: "999px",
} as const;

export const shadows = {
  sm: "0 12px 30px rgba(0, 0, 0, 0.18)",
  md: "0 18px 40px rgba(0, 0, 0, 0.24)",
  primary: "0 0 24px rgba(49, 230, 174, 0.2)",
  purple: "0 0 24px rgba(167, 106, 247, 0.2)",
} as const;

export const backdropBlur = "blur(14px)" as const;

export const motion = {
  duration: {
    fast: "120ms",
    base: "180ms",
    medium: "240ms",
    slow: "360ms",
  },
  easing: "ease" as const,
} as const;

export type RadiusTokens = typeof radius;
export type ShadowTokens = typeof shadows;
export type MotionTokens = typeof motion;

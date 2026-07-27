/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

export const typography = {
  fontFamily: {
    sans: '"Inter", "Segoe UI", Arial, sans-serif',
    mono: '"Geist Mono", "JetBrains Mono", monospace',
  },

  fontSize: {
    displayLarge: "32px",
    displayMedium: "28px",
    heading1: "24px",
    heading2: "20px",
    heading3: "16px",
    bodyLarge: "16px",
    bodyMedium: "14px",
    bodySmall: "13px",
    caption: "12px",
  },

  fontWeight: {
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
} as const;

export type TypographyTokens = typeof typography;

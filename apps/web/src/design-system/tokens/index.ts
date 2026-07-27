/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { colors } from "./colors";
import { backdropBlur, motion, radius, shadows } from "./effects";
import { layout } from "./layout";
import { spacing } from "./spacing";
import { typography } from "./typography";

export * from "./colors";
export * from "./effects";
export * from "./layout";
export * from "./spacing";
export * from "./typography";

export const finTwinTheme = {
  colors,
  spacing,
  typography,
  layout,
  motion,
  radius,
  shadows,
  backdropBlur,
} as const;

export type FinTwinTheme = typeof finTwinTheme;

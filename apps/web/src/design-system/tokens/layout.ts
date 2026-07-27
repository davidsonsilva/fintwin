/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

export const layout = {
  sidebarWidth: "270px",
  headerHeight: "98px",
  agentWidth: "340px",
  contentMaxWidth: "1600px",
  gridGap: "14px",
} as const;

export type LayoutTokens = typeof layout;

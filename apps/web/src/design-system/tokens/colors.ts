/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

export const colors = {
  background: {
    page: "#03111f",
    sidebar: "#020c18",
    surface: "#0c1a29",
    surfaceSoft: "#102131",
    surfaceHover: "#16283a",
    elevated: "rgba(16, 33, 49, 0.88)",
  },

  brand: {
    primary: "#31e6ae",
    primaryStrong: "#087a61",
    primarySoft: "rgba(49, 230, 174, 0.14)",

    secondary: "#2dddeb",
    secondarySoft: "rgba(45, 221, 235, 0.13)",

    purple: "#a76af7",
    purpleStrong: "#5a2b92",
    purpleSoft: "rgba(167, 106, 247, 0.15)",
  },

  accent: {
    blue: "#5595ff",
    blueSoft: "rgba(85, 149, 255, 0.14)",

    pink: "#e64dad",
    pinkSoft: "rgba(230, 77, 173, 0.14)",

    orange: "#f17b2d",
    orangeSoft: "rgba(241, 123, 45, 0.14)",
  },

  status: {
    success: "#31e6ae",
    successSoft: "rgba(49, 230, 174, 0.14)",

    warning: "#ffb815",
    warningSoft: "rgba(255, 184, 21, 0.14)",

    danger: "#f24c5f",
    dangerSoft: "rgba(242, 76, 95, 0.14)",

    info: "#5595ff",
    infoSoft: "rgba(85, 149, 255, 0.14)",
  },

  text: {
    primary: "#f7f9fc",
    secondary: "#b4bcc8",
    muted: "#8793a2",
    disabled: "#637182",
  },

  border: {
    default: "#263849",
    hover: "#3c5368",
    primary: "rgba(49, 230, 174, 0.45)",
    divider: "#203244",
  },
} as const;

export type ColorTokens = typeof colors;

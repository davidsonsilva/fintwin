/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import type { MoneyDto } from "@/features/onboarding/types";

export function formatMoney(money: MoneyDto | null | undefined) {
  if (!money) return "—";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: money.currency }).format(
    Number(money.amount)
  );
}

export function formatPercent(fraction: string | null | undefined, fractionDigits = 0) {
  if (fraction === null || fraction === undefined) return "—";
  return new Intl.NumberFormat("pt-BR", {
    style: "percent",
    maximumFractionDigits: fractionDigits,
  }).format(Number(fraction));
}

export function formatMonths(months: string | null | undefined) {
  if (months === null || months === undefined) return "—";
  const value = Number(months);
  const label = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 }).format(value);
  return `${label} ${value === 1 ? "mês" : "meses"}`;
}

/** Meses inteiros, sem casa decimal — prazos não têm meia unidade. */
export function formatMonthCount(months: string | null | undefined) {
  if (months === null || months === undefined) return "—";
  const value = Math.round(Number(months));
  return `${value} ${value === 1 ? "mês" : "meses"}`;
}

const MONTH_NAMES = [
  "janeiro",
  "fevereiro",
  "março",
  "abril",
  "maio",
  "junho",
  "julho",
  "agosto",
  "setembro",
  "outubro",
  "novembro",
  "dezembro",
];

/** "2028-01" -> "janeiro/2028". */
export function formatPeriod(period: string | null | undefined) {
  if (!period) return "—";
  const [year, month] = period.split("-");
  const index = Number(month) - 1;
  if (Number.isNaN(index) || !MONTH_NAMES[index]) return period;
  return `${MONTH_NAMES[index]}/${year}`;
}

export function formatDateTime(iso: string) {
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(iso));
}

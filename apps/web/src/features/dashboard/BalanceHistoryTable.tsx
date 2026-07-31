"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { Card as FtCard } from "@/design-system/components/Card";

import { dashboardApi } from "./api";

const MONTH_NAMES = [
  "Janeiro",
  "Fevereiro",
  "Março",
  "Abril",
  "Maio",
  "Junho",
  "Julho",
  "Agosto",
  "Setembro",
  "Outubro",
  "Novembro",
  "Dezembro",
];

function formatPeriodFull(period: string) {
  const [year, month] = period.split("-");
  return `${MONTH_NAMES[Number(month) - 1] ?? month} de ${year}`;
}

function formatMoney(amount: number, currency: string) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(amount);
}

function formatPercent(value: number) {
  return `${value > 0 ? "+" : ""}${value.toFixed(1)}%`;
}

type Row = {
  period: string;
  balance: number;
  currency: string;
  delta: number | null;
  deltaPct: number | null;
};

export function BalanceHistoryTable({ profileId, months = 24 }: { profileId: string; months?: number }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["balance-history-table", profileId, months],
    queryFn: () => dashboardApi.getBalanceHistory(profileId, months),
  });

  const rows: Row[] = (data ?? []).map((snapshot, index, snapshots) => {
    const previous = snapshots[index - 1];
    const balance = Number(snapshot.net_balance.amount);
    const previousBalance = previous ? Number(previous.net_balance.amount) : null;
    const delta = previousBalance !== null ? balance - previousBalance : null;
    const deltaPct = previousBalance ? (delta! / Math.abs(previousBalance)) * 100 : null;
    return { period: snapshot.period, balance, currency: snapshot.net_balance.currency, delta, deltaPct };
  });

  const rowsDescending = [...rows].reverse();

  return (
    <FtCard>
      <div className="ft-card-header">
        <div>
          <h3 className="ft-card-title">Histórico mês a mês</h3>
          <p className="ft-card-subtitle">Saldo líquido registrado e variação em relação ao mês anterior</p>
        </div>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Carregando histórico...</p>}
      {isError && <p className="text-sm text-red-400">Não foi possível carregar o histórico.</p>}

      {data && data.length === 0 && (
        <p className="text-sm text-muted-foreground">Ainda não há histórico de saldo suficiente.</p>
      )}

      {data && data.length > 0 && (
        <div className="ft-history-table-wrap">
          <table className="ft-history-table">
            <thead>
              <tr>
                <th>Período</th>
                <th>Saldo líquido</th>
                <th>Variação</th>
              </tr>
            </thead>
            <tbody>
              {rowsDescending.map((row) => (
                <tr key={row.period}>
                  <td>{formatPeriodFull(row.period)}</td>
                  <td className="ft-history-balance">{formatMoney(row.balance, row.currency)}</td>
                  <td>
                    {row.delta === null ? (
                      <span className="ft-history-delta ft-history-delta--neutral">
                        <Minus size={14} />
                        Primeiro registro
                      </span>
                    ) : (
                      <span
                        className={`ft-history-delta ${
                          row.delta > 0
                            ? "ft-history-delta--up"
                            : row.delta < 0
                              ? "ft-history-delta--down"
                              : "ft-history-delta--neutral"
                        }`}
                      >
                        {row.delta > 0 ? (
                          <ArrowUpRight size={14} />
                        ) : row.delta < 0 ? (
                          <ArrowDownRight size={14} />
                        ) : (
                          <Minus size={14} />
                        )}
                        {formatMoney(row.delta, row.currency)}
                        {row.deltaPct !== null && ` (${formatPercent(row.deltaPct)})`}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </FtCard>
  );
}

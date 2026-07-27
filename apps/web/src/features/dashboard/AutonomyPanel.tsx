"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */


import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { dashboardApi } from "./api";

function formatMonths(months: string | null) {
  return months !== null ? `${Number(months).toFixed(1)} meses` : "Não aplicável";
}

function formatMoney(amount: string, currency: string) {
  return `${amount} ${currency}`;
}

export function AutonomyPanel({ profileId }: { profileId: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["autonomy", profileId],
    queryFn: () => dashboardApi.getAutonomy(profileId),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Autonomia financeira</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading && <p className="text-sm text-muted-foreground">Calculando autonomia...</p>}
        {isError && <p className="text-sm text-red-500">Não foi possível calcular a autonomia financeira.</p>}

        {data && (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <p className="text-sm text-muted-foreground">Autonomia básica</p>
                <p className="text-xl font-semibold">{formatMonths(data.basic_autonomy_months)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Cenário provável</p>
                <p className="text-xl font-semibold">{formatMonths(data.probable_autonomy_months)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Cenário adverso</p>
                <p className="text-xl font-semibold">{formatMonths(data.adverse_autonomy_months)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Perda de renda</p>
                <p className="text-xl font-semibold">{formatMonths(data.income_loss_autonomy_months)}</p>
              </div>
            </div>

            <div className="space-y-1 text-sm">
              <p>
                Ativos líquidos elegíveis: {formatMoney(data.eligible_assets.amount, data.eligible_assets.currency)}
              </p>
              <p>
                Despesas essenciais mensais:{" "}
                {formatMoney(data.essential_expenses_monthly.amount, data.essential_expenses_monthly.currency)}
              </p>
            </div>

            <details className="text-sm">
              <summary className="cursor-pointer text-muted-foreground">
                Ver ativos e despesas consideradas (evidências)
              </summary>
              <div className="mt-2 space-y-2">
                <div>
                  <p className="font-medium">Contas elegíveis</p>
                  {data.eligible_accounts.length === 0 && (
                    <p className="text-muted-foreground">Nenhuma conta marcada como elegível para autonomia.</p>
                  )}
                  {data.eligible_accounts.map((account) => (
                    <p key={account.id}>
                      {account.description}: {formatMoney(account.balance.amount, account.balance.currency)}
                    </p>
                  ))}
                </div>
                <div>
                  <p className="font-medium">Obrigações essenciais</p>
                  {data.essential_obligations.length === 0 && (
                    <p className="text-muted-foreground">Nenhuma obrigação essencial cadastrada.</p>
                  )}
                  {data.essential_obligations.map((obligation) => (
                    <p key={obligation.id}>
                      {obligation.description}: {formatMoney(obligation.amount.amount, obligation.amount.currency)}
                    </p>
                  ))}
                </div>
              </div>
            </details>

            <ul className="space-y-1 text-xs text-muted-foreground">
              {data.assumptions.map((assumption) => (
                <li key={assumption}>{assumption}</li>
              ))}
            </ul>
            <p className="text-xs italic text-muted-foreground">
              Os valores representam simulações baseadas nas premissas disponíveis.
            </p>
          </>
        )}
      </CardContent>
    </Card>
  );
}

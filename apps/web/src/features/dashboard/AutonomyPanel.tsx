"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */


import { ShieldCheck } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { Card as FtCard } from "@/design-system/components/Card";
import { IconChip } from "@/design-system/components/IconChip";
import { InfoTooltip } from "@/components/ui/tooltip";

import { dashboardApi } from "./api";

function formatMoney(amount: string, currency: string) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(Number(amount));
}

export function AutonomyPanel({ profileId }: { profileId: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["autonomy", profileId],
    queryFn: () => dashboardApi.getAutonomy(profileId),
  });

  return (
    <FtCard interactive>
      <div className="ft-card-header">
        <div className="flex items-center gap-3">
          <IconChip icon={ShieldCheck} tone="primary" size="sm" />
          <h3 className="ft-card-title ft-label-info">
            Detalhamento da autonomia financeira
            <InfoTooltip label="Mostra os ativos e despesas usados no cálculo de autonomia e as premissas de cada cenário." iconSize={13} />
          </h3>
        </div>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Calculando autonomia...</p>}
      {isError && <p className="text-sm text-red-500">Não foi possível calcular a autonomia financeira.</p>}

      {data && (
        <div className="flex flex-col gap-4">
          <div className="space-y-1 text-sm text-muted-foreground">
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
            <div className="mt-3 space-y-4">
              <div>
                <p className="font-medium">Contas elegíveis</p>
                {data.eligible_accounts.length === 0 && (
                  <p className="mt-1 text-muted-foreground">Nenhuma conta marcada como elegível para autonomia.</p>
                )}
                {data.eligible_accounts.length > 0 && (
                  <ul className="ft-evidence-list">
                    {data.eligible_accounts.map((account) => (
                      <li key={account.id} className="ft-evidence-item">
                        <span className="ft-evidence-dot" />
                        <span>{account.description}</span>
                        <span>{formatMoney(account.balance.amount, account.balance.currency)}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <div>
                <p className="font-medium">Obrigações essenciais</p>
                {data.essential_obligations.length === 0 && (
                  <p className="mt-1 text-muted-foreground">Nenhuma obrigação essencial cadastrada.</p>
                )}
                {data.essential_obligations.length > 0 && (
                  <ul className="ft-evidence-list">
                    {data.essential_obligations.map((obligation) => (
                      <li key={obligation.id} className="ft-evidence-item">
                        <span className="ft-evidence-dot" />
                        <span>{obligation.description}</span>
                        <span>{formatMoney(obligation.amount.amount, obligation.amount.currency)}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </details>

          <div className="text-xs text-muted-foreground">
            <p className="mb-1 flex items-center gap-1.5 font-medium text-foreground">
              Como calculamos os números de autonomia acima:
              <InfoTooltip
                label="Autonomia é por quanto tempo suas reservas cobririam os gastos se a renda parasse. A básica considera só o essencial; a ajustada usa a projeção completa (dívidas, metas e eventos) em cada cenário."
                iconSize={13}
              />
            </p>
            <ul className="ft-assumptions-list">
              {data.assumptions.map((assumption) => (
                <li key={assumption}>{assumption}</li>
              ))}
            </ul>
          </div>
          <p className="text-xs italic text-muted-foreground">
            Os valores representam simulações baseadas nas premissas disponíveis.
          </p>
        </div>
      )}
    </FtCard>
  );
}

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

import { Card } from "@/design-system/components/Card";
import { IconChip } from "@/design-system/components/IconChip";
import { InfoTooltip } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

import { dashboardApi } from "./api";

/*
 * `AccountRow` substitui `.ft-evidence-item` (fixo em 3 colunas, sempre lado a
 * lado — nunca empilhava em card estreito). Único consumidor daquela classe era
 * este arquivo; CSS órfão pendente da mesma decisão do usuário sobre
 * `.ft-analytics-card` nos quatro cards anteriores.
 *
 * Breakpoint em content box: card 360px → content box 318px (padding 20px +
 * borda 1px de cada lado = -42px). Em 360px ou menos o valor desce, alinhado à
 * esquerda sob o nome — não sob o ponto, que é só um marcador decorativo.
 * Ajustado de 310px para 360px depois que a versão anterior ainda ficava
 * apertada em 320px com descrição longa + valor grande ("R$ 1.850.000,00")
 * disputando espaço horizontal.
 *
 * `max-w-[480px]`: sem isso, num card largo (este não vive em grid — pode
 * passar de 1150px de largura real no dashboard) o nome curto ("Poupança")
 * deixaria o valor colado na borda direita, com um vão vazio enorme entre os
 * dois. Delimita o conteúdo a uma largura de leitura razoável em vez de esticar
 * borda a borda.
 */
function AccountRow({ label, value }: { label: string; value: string }) {
  return (
    <li className="flex max-w-[480px] items-start gap-[10px]">
      <span className="mt-[7px] size-[6px] flex-none rounded-full bg-[color:var(--ft-border-hover)]" />
      <div
        className={cn(
          "grid min-w-0 flex-1 items-baseline gap-x-[10px] gap-y-1",
          "grid-cols-[minmax(0,1fr)_auto]",
          "@max-[318px]/card:grid-cols-1"
        )}
      >
        <span className="min-w-0 break-normal [overflow-wrap:normal] [word-break:normal]">{label}</span>
        <span
          className={cn(
            "whitespace-nowrap text-right tabular-nums",
            "@max-[318px]/card:whitespace-normal @max-[318px]/card:text-left @max-[318px]/card:[overflow-wrap:anywhere]"
          )}
        >
          {value}
        </span>
      </div>
    </li>
  );
}

function formatMoney(amount: string, currency: string) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(Number(amount));
}

export function AutonomyPanel({ profileId }: { profileId: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["autonomy", profileId],
    queryFn: () => dashboardApi.getAutonomy(profileId),
  });

  return (
    /*
     * Quinto card migrado. Diferente dos quatro anteriores, este não vive num
     * grid — fica solto entre seções em `DashboardView` — então não há irmão
     * que force `stretch`. Sem necessidade de `self-start`/`flex-none`, e sem
     * `.ft-analytics-card` para largar (nunca usou).
     *
     * `.ft-card-title` continua em uso aqui, ao contrário dos cards de
     * analytics: sua regra base é `font-size: 16px` fixo, sem clamp — não havia
     * tipografia fluida a preservar, então a classe não atrapalha.
     */
    <Card.Root interactive>
      <Card.Header
        className="ft-card-header"
        icon={<IconChip icon={ShieldCheck} tone="primary" size="sm" />}
        title={
          <h3 className="ft-card-title min-w-0 break-normal [overflow-wrap:normal] [word-break:normal]">
            Detalhamento da autonomia financeira
          </h3>
        }
        help={
          <InfoTooltip label="Mostra os ativos e despesas usados no cálculo de autonomia e as premissas de cada cenário." iconSize={13} />
        }
      />

      <Card.Content className="flex flex-col gap-4">
        {isLoading && <p className="text-sm text-muted-foreground">Calculando autonomia...</p>}
        {isError && <p className="text-sm text-red-500">Não foi possível calcular a autonomia financeira.</p>}

        {data && (
          <>
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
                    <ul className="grid gap-2 mt-2">
                      {data.eligible_accounts.map((account) => (
                        <AccountRow
                          key={account.id}
                          label={account.description}
                          value={formatMoney(account.balance.amount, account.balance.currency)}
                        />
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
                    <ul className="grid gap-2 mt-2">
                      {data.essential_obligations.map((obligation) => (
                        <AccountRow
                          key={obligation.id}
                          label={obligation.description}
                          value={formatMoney(obligation.amount.amount, obligation.amount.currency)}
                        />
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
          </>
        )}
      </Card.Content>
    </Card.Root>
  );
}

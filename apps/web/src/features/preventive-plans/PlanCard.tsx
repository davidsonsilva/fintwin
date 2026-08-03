"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */


import { useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/design-system/components/Badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

import { preventivePlanApi } from "./api";
import { RISK_CODE_LABELS, STATUS_LABELS, type PlanStatus, type PreventivePlanDto } from "./types";

function formatMoney(amount: string, currency: string) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(Number(amount));
}

const TRACKING_OPTIONS: Record<string, { value: PlanStatus; label: string }[]> = {
  approved: [
    { value: "in_progress", label: "Em andamento" },
    { value: "cancelled", label: "Cancelar" },
  ],
  in_progress: [
    { value: "completed", label: "Concluído" },
    { value: "cancelled", label: "Cancelar" },
  ],
};

/** "2028-05-01" -> "01/05/2028". A data crua vinha do domínio em ISO. */
function formatDueDate(value: string) {
  const [year, month, day] = value.split("-");
  return day ? `${day}/${month}/${year}` : value;
}

function formatAutonomyChange(value: string) {
  const months = Number(value);
  const label = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 }).format(Math.abs(months));
  const noun = Math.abs(months) === 1 ? "mês" : "meses";
  if (months < 0) return `Custo em autonomia: ${label} ${noun} a menos`;
  if (months > 0) return `Ganho de autonomia estimado: ${label} ${noun}`;
  return "Sem impacto na autonomia";
}

export function PlanCard({ plan }: { plan: PreventivePlanDto }) {
  const queryClient = useQueryClient();

  const updateStatus = (status: PlanStatus) =>
    preventivePlanApi.updateStatus(plan.id, status).then(() => {
      queryClient.invalidateQueries({ queryKey: ["preventive-plans", plan.profile_id] });
    });

  const trackingOptions = TRACKING_OPTIONS[plan.status];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-4">
        <CardTitle className="text-base">{RISK_CODE_LABELS[plan.risk_code] ?? plan.risk_code}</CardTitle>
        <Badge>{STATUS_LABELS[plan.status]}</Badge>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div className="space-y-2">
          {plan.actions.map((action, index) => (
            <div key={index} className="rounded-md border px-3 py-2">
              <p>{action.description}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {action.expected_monthly_impact && (
                  <>
                    Impacto mensal estimado:{" "}
                    {formatMoney(action.expected_monthly_impact.amount, action.expected_monthly_impact.currency)} ·{" "}
                  </>
                )}
                Prazo: {formatDueDate(action.due_date)}
              </p>
            </div>
          ))}
        </div>

        <div className="text-xs text-muted-foreground">
          <p>Déficit evitado: {plan.expected_result.deficit_avoided ? "sim" : "não"}</p>
          {plan.expected_result.autonomy_change_months && (
            /* "Ganho" era mentira quando o número vinha negativo: acelerar uma
               meta custa autonomia, e o plano precisa dizer isso sem maquiar. */
            <p>{formatAutonomyChange(plan.expected_result.autonomy_change_months)}</p>
          )}
        </div>

        {plan.status === "proposed" && (
          <div className="flex gap-2">
            <Button size="sm" onClick={() => updateStatus("approved")}>
              Aprovar
            </Button>
            <Button size="sm" variant="outline" onClick={() => updateStatus("rejected")}>
              Rejeitar
            </Button>
          </div>
        )}

        {trackingOptions && (
          <Select onValueChange={(value) => value && updateStatus(value as PlanStatus)}>
            <SelectTrigger className="w-48" aria-label="Atualizar acompanhamento">
              <SelectValue placeholder="Atualizar acompanhamento" />
            </SelectTrigger>
            <SelectContent>
              {trackingOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </CardContent>
    </Card>
  );
}

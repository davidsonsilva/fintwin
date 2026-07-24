"use client";

import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { DECISION_LABELS } from "./decisionFields";
import type { SimulationDto } from "./types";

function formatMoney(amount: string, currency: string) {
  return `${amount} ${currency}`;
}

export function SimulationComparison({ simulation }: { simulation: SimulationDto }) {
  const { baseline_result: baseline, simulated_result: simulated } = simulation;
  const { impact, total_cost, assumptions } = simulated;

  const chartData = [
    {
      metric: "Saldo final",
      base: Number(baseline.final_balance.amount),
      simulado: Number(simulated.final_balance.amount),
    },
    {
      metric: "Menor saldo",
      base: Number(baseline.lowest_balance.amount),
      simulado: Number(simulated.lowest_balance.amount),
    },
  ];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>{DECISION_LABELS[simulation.type]}</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2 rounded-md border p-3">
            <h3 className="text-sm font-medium text-muted-foreground">Cenário-base</h3>
            <p className="text-lg font-semibold">{formatMoney(baseline.final_balance.amount, baseline.final_balance.currency)}</p>
            <p className="text-sm text-muted-foreground">
              {baseline.first_deficit_period ? `Déficit em ${baseline.first_deficit_period}` : "Sem déficit projetado"}
            </p>
          </div>
          <div className="space-y-2 rounded-md border p-3">
            <h3 className="text-sm font-medium text-muted-foreground">Cenário simulado ({simulated.scenario})</h3>
            <p className="text-lg font-semibold">{formatMoney(simulated.final_balance.amount, simulated.final_balance.currency)}</p>
            <p className="text-sm text-muted-foreground">
              {simulated.first_deficit_period ? `Déficit em ${simulated.first_deficit_period}` : "Sem déficit projetado"}
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Comparação de saldo</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="metric" />
                <YAxis />
                <Tooltip formatter={(value) => Number(value).toFixed(2)} />
                <Legend />
                <Bar dataKey="base" name="Base" fill="#94a3b8" />
                <Bar dataKey="simulado" name="Simulado" fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Impacto da decisão</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-md border p-3">
            <p className="text-sm text-muted-foreground">Delta de autonomia</p>
            <p className="text-lg font-semibold">
              {impact.autonomy_delta_months !== null ? `${impact.autonomy_delta_months} meses` : "Não aplicável"}
            </p>
          </div>
          <div className="rounded-md border p-3">
            <p className="text-sm text-muted-foreground">Delta de saldo final</p>
            <p className="text-lg font-semibold">{impact.closing_balance_delta}</p>
          </div>
          <div className="rounded-md border p-3">
            <p className="text-sm text-muted-foreground">Novo primeiro déficit</p>
            <p className="text-lg font-semibold">{impact.new_first_deficit_period ?? "Sem mudança"}</p>
          </div>
          <div className="rounded-md border p-3">
            <p className="text-sm text-muted-foreground">Atraso na meta principal</p>
            <p className="text-lg font-semibold">
              {impact.goal_delay_months !== null ? `${impact.goal_delay_months} meses` : "Não aplicável"}
            </p>
          </div>
        </CardContent>
      </Card>

      {total_cost && (
        <Card>
          <CardHeader>
            <CardTitle>Custo total</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-semibold">
              {formatMoney(total_cost.total_cost.amount, total_cost.total_cost.currency)}
            </p>
          </CardContent>
        </Card>
      )}

      <ul className="space-y-1 text-xs text-muted-foreground">
        {assumptions.map((assumption) => (
          <li key={assumption}>{assumption}</li>
        ))}
      </ul>
    </div>
  );
}

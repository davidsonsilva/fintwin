"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { onboardingApi } from "@/features/onboarding/api";

import { simulationApi } from "./api";
import { buildParameters, DECISION_FIELDS, DECISION_LABELS } from "./decisionFields";
import type { DecisionType, ScenarioOverrideInput } from "./types";

const DECISION_TYPES = Object.keys(DECISION_LABELS) as DecisionType[];

export function DecisionForm({ profileId, onCreated }: { profileId: string; onCreated: (simulationId: string) => void }) {
  const queryClient = useQueryClient();
  const [decisionType, setDecisionType] = useState<DecisionType>("CASH_PURCHASE");
  const [values, setValues] = useState<Record<string, string | boolean>>({});
  const [horizonMonths, setHorizonMonths] = useState<"3" | "6" | "12">("12");
  const [showScenarioOverride, setShowScenarioOverride] = useState(false);
  const [scenarioOverride, setScenarioOverride] = useState<ScenarioOverrideInput>({});

  const incomesQuery = useQuery({
    queryKey: ["incomes", profileId],
    queryFn: () => onboardingApi.listIncomes(profileId),
  });

  const mutation = useMutation({
    mutationFn: () =>
      simulationApi.create(profileId, {
        decision_type: decisionType,
        parameters: buildParameters(decisionType, values),
        scenario_override: showScenarioOverride ? scenarioOverride : undefined,
        horizon_months: Number(horizonMonths) as 3 | 6 | 12,
      }),
    onSuccess: (simulation) => {
      queryClient.invalidateQueries({ queryKey: ["simulations", profileId] });
      setValues({});
      onCreated(simulation.id);
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Nova simulação</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1">
            <Label htmlFor="decision-type">Tipo de decisão</Label>
            <Select value={decisionType} onValueChange={(next) => { setDecisionType(next as DecisionType); setValues({}); }}>
              <SelectTrigger id="decision-type" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {DECISION_TYPES.map((type) => (
                  <SelectItem key={type} value={type}>
                    {DECISION_LABELS[type]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1">
            <Label htmlFor="horizon">Horizonte</Label>
            <Select value={horizonMonths} onValueChange={(next) => setHorizonMonths(next as "3" | "6" | "12")}>
              <SelectTrigger id="horizon" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="3">3 meses</SelectItem>
                <SelectItem value="6">6 meses</SelectItem>
                <SelectItem value="12">12 meses</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          {DECISION_FIELDS[decisionType].map((field) => {
            if (field.type === "income-select") {
              return (
                <div key={field.name} className="space-y-1">
                  <Label htmlFor={field.name}>{field.label}</Label>
                  <Select
                    value={(values[field.name] as string) ?? ""}
                    onValueChange={(next) => setValues((prev) => ({ ...prev, [field.name]: next ?? "" }))}
                  >
                    <SelectTrigger id={field.name} className="w-full">
                      <SelectValue placeholder="Selecione" />
                    </SelectTrigger>
                    <SelectContent>
                      {(incomesQuery.data ?? []).map((income) => (
                        <SelectItem key={income.id} value={income.id}>
                          {income.description}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              );
            }

            if (field.type === "checkbox") {
              return (
                <div key={field.name} className="flex items-center gap-2">
                  <Checkbox
                    id={field.name}
                    checked={!!values[field.name]}
                    onCheckedChange={(checked) => setValues((prev) => ({ ...prev, [field.name]: !!checked }))}
                  />
                  <Label htmlFor={field.name}>{field.label}</Label>
                </div>
              );
            }

            return (
              <div key={field.name} className="space-y-1">
                <Label htmlFor={field.name}>{field.label}</Label>
                <Input
                  id={field.name}
                  type={field.type === "number" ? "number" : field.type === "date" ? "date" : "text"}
                  value={(values[field.name] as string) ?? ""}
                  onChange={(event) => setValues((prev) => ({ ...prev, [field.name]: event.target.value }))}
                />
              </div>
            );
          })}
        </div>

        <div className="space-y-2 border-t pt-4">
          <div className="flex items-center gap-2">
            <Checkbox
              id="scenario-override-toggle"
              checked={showScenarioOverride}
              onCheckedChange={(checked) => setShowScenarioOverride(!!checked)}
            />
            <Label htmlFor="scenario-override-toggle">Personalizar cenário simulado</Label>
          </div>
          {showScenarioOverride && (
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1">
                <Label htmlFor="income-multiplier">Multiplicador de renda</Label>
                <Input
                  id="income-multiplier"
                  type="number"
                  step="0.01"
                  value={scenarioOverride.income_multiplier ?? ""}
                  onChange={(event) => setScenarioOverride((prev) => ({ ...prev, income_multiplier: event.target.value }))}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="essential-multiplier">Multiplicador de despesas essenciais</Label>
                <Input
                  id="essential-multiplier"
                  type="number"
                  step="0.01"
                  value={scenarioOverride.essential_expense_multiplier ?? ""}
                  onChange={(event) =>
                    setScenarioOverride((prev) => ({ ...prev, essential_expense_multiplier: event.target.value }))
                  }
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="nonessential-multiplier">Multiplicador de despesas não essenciais</Label>
                <Input
                  id="nonessential-multiplier"
                  type="number"
                  step="0.01"
                  value={scenarioOverride.nonessential_expense_multiplier ?? ""}
                  onChange={(event) =>
                    setScenarioOverride((prev) => ({ ...prev, nonessential_expense_multiplier: event.target.value }))
                  }
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="unexpected-expense">Despesa inesperada</Label>
                <Input
                  id="unexpected-expense"
                  type="number"
                  step="0.01"
                  value={scenarioOverride.unexpected_expense ?? ""}
                  onChange={(event) => setScenarioOverride((prev) => ({ ...prev, unexpected_expense: event.target.value }))}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="expense-reduction-capacity">Capacidade de redução de despesas (0 a 1)</Label>
                <Input
                  id="expense-reduction-capacity"
                  type="number"
                  step="0.01"
                  value={scenarioOverride.expense_reduction_capacity ?? ""}
                  onChange={(event) =>
                    setScenarioOverride((prev) => ({ ...prev, expense_reduction_capacity: event.target.value }))
                  }
                />
              </div>
            </div>
          )}
        </div>

        <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
          {mutation.isPending ? "Simulando..." : "Simular decisão"}
        </Button>
        {mutation.isError && <p className="text-sm text-red-500">Não foi possível simular. Verifique os campos.</p>}
      </CardContent>
    </Card>
  );
}

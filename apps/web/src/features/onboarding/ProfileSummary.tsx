"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { useQuery } from "@tanstack/react-query";

import { Card, CardContent } from "@/components/ui/card";

import { onboardingApi } from "./api";

export function ProfileSummary({ profileId }: { profileId: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["profile", profileId],
    queryFn: () => onboardingApi.getProfile(profileId),
  });

  return (
    <Card className="ft-form-card">
      <CardContent className="space-y-6 p-0">
        <div className="ft-form-header">
          <h2 className="ft-form-title">Perfil financeiro</h2>
          <p className="ft-form-description">Dados básicos usados para calibrar sua projeção e autonomia.</p>
        </div>

        {isLoading && <p className="text-sm text-muted-foreground">Carregando perfil...</p>}
        {isError && <p className="text-sm text-red-500">Não foi possível carregar o perfil.</p>}

        {data && (
          <ul className="ft-review-grid">
            <li className="ft-review-item">
              <p className="ft-review-label">Moeda</p>
              <p className="ft-review-value">{data.currency}</p>
            </li>
            <li className="ft-review-item">
              <p className="ft-review-label">Dependentes</p>
              <p className="ft-review-value">{data.dependents}</p>
            </li>
            <li className="ft-review-item ft-field--full">
              <p className="ft-review-label">Capacidade de redução de despesas</p>
              <p className="ft-review-value">{data.monthly_expense_reduction_capacity ?? "Não informado"}</p>
            </li>
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

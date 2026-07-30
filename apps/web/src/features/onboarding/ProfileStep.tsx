"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */


import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { onboardingApi } from "./api";
import { profileSchema, type ProfileFormValues } from "./schemas";

export function ProfileStep({
  onCreated,
  onDemoLoaded,
}: {
  onCreated: (profileId: string) => void;
  onDemoLoaded: (profileId: string) => void;
}) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: { name: "", currency: "BRL", dependents: 0, monthly_expense_reduction_capacity: "" },
  });

  const createProfileMutation = useMutation({
    mutationFn: (values: ProfileFormValues) =>
      onboardingApi.createProfile({
        name: values.name || null,
        currency: values.currency,
        dependents: values.dependents,
        monthly_expense_reduction_capacity: values.monthly_expense_reduction_capacity || null,
      }),
    onSuccess: (profile) => onCreated(profile.id),
  });

  const demoMutation = useMutation({
    mutationFn: async () => {
      const profile = await onboardingApi.createProfile({ currency: "BRL", dependents: 2 });
      await onboardingApi.loadDemo(profile.id);
      return profile;
    },
    onSuccess: (profile) => onDemoLoaded(profile.id),
  });

  return (
    <Card className="ft-form-card">
      <CardContent className="space-y-6 p-0">
        <div className="ft-form-header">
          <h2 className="ft-form-title">Perfil financeiro</h2>
          <p className="ft-form-description">Alguns dados básicos para calibrar sua projeção e autonomia.</p>
        </div>
        <form
          onSubmit={handleSubmit((values) => createProfileMutation.mutate(values))}
          className="ft-form-grid"
        >
          <div className="ft-field ft-field--full">
            <Label className="ft-label" htmlFor="name">Nome (opcional)</Label>
            <Input id="name" placeholder="Como podemos te chamar?" {...register("name")} />
            {errors.name && <p className="text-sm text-red-500">{errors.name.message}</p>}
          </div>
          <div className="ft-field">
            <Label className="ft-label" htmlFor="currency">Moeda</Label>
            <Input id="currency" maxLength={3} {...register("currency")} />
            {errors.currency && <p className="text-sm text-red-500">{errors.currency.message}</p>}
          </div>
          <div className="ft-field">
            <Label className="ft-label" htmlFor="dependents">Dependentes</Label>
            <Input id="dependents" type="number" {...register("dependents")} />
            {errors.dependents && <p className="text-sm text-red-500">{errors.dependents.message}</p>}
          </div>
          <div className="ft-field ft-field--full">
            <Label className="ft-label" htmlFor="monthly_expense_reduction_capacity">
              Capacidade de redução de despesas (fração 0–1, opcional)
            </Label>
            <Input
              id="monthly_expense_reduction_capacity"
              placeholder="0.15"
              {...register("monthly_expense_reduction_capacity")}
            />
            {errors.monthly_expense_reduction_capacity && (
              <p className="text-sm text-red-500">{errors.monthly_expense_reduction_capacity.message}</p>
            )}
          </div>
          <div className="ft-field--full ft-form-actions">
            <Button
              type="button"
              variant="outline"
              onClick={() => demoMutation.mutate()}
              disabled={demoMutation.isPending}
            >
              {demoMutation.isPending ? "Carregando demonstração..." : "Carregar dados de demonstração"}
            </Button>
            <Button type="submit" disabled={createProfileMutation.isPending}>
              {createProfileMutation.isPending ? "Criando..." : "Iniciar onboarding"}
            </Button>
          </div>
        </form>
        {createProfileMutation.isError && (
          <p className="text-sm text-red-500">Não foi possível criar o perfil. Tente novamente.</p>
        )}
        {demoMutation.isError && (
          <p className="text-sm text-red-500">Não foi possível carregar a demonstração. Tente novamente.</p>
        )}
      </CardContent>
    </Card>
  );
}

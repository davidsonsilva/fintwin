"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
    defaultValues: { currency: "BRL", dependents: 0, monthly_expense_reduction_capacity: "" },
  });

  const createProfileMutation = useMutation({
    mutationFn: (values: ProfileFormValues) =>
      onboardingApi.createProfile({
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
    <Card>
      <CardHeader>
        <CardTitle>Perfil financeiro</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <form
          onSubmit={handleSubmit((values) => createProfileMutation.mutate(values))}
          className="grid gap-4 sm:grid-cols-2"
        >
          <div className="space-y-1">
            <Label htmlFor="currency">Moeda</Label>
            <Input id="currency" maxLength={3} {...register("currency")} />
            {errors.currency && <p className="text-sm text-red-500">{errors.currency.message}</p>}
          </div>
          <div className="space-y-1">
            <Label htmlFor="dependents">Dependentes</Label>
            <Input id="dependents" type="number" {...register("dependents")} />
            {errors.dependents && <p className="text-sm text-red-500">{errors.dependents.message}</p>}
          </div>
          <div className="space-y-1 sm:col-span-2">
            <Label htmlFor="monthly_expense_reduction_capacity">
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
          <div className="sm:col-span-2 flex flex-wrap gap-3">
            <Button type="submit" disabled={createProfileMutation.isPending}>
              {createProfileMutation.isPending ? "Criando..." : "Iniciar onboarding"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => demoMutation.mutate()}
              disabled={demoMutation.isPending}
            >
              {demoMutation.isPending ? "Carregando demonstração..." : "Carregar dados de demonstração"}
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

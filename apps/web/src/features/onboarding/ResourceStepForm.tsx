"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */


import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

import type { FieldConfig, ResourceStepConfig } from "./resourceConfigs";

function nullifyEmptyStrings(value: unknown): unknown {
  if (typeof value === "string") {
    return value === "" ? null : value;
  }
  if (Array.isArray(value)) {
    return value.map(nullifyEmptyStrings);
  }
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([key, val]) => [key, nullifyEmptyStrings(val)])
    );
  }
  return value;
}

function Field({ field, register, watch, setValue }: { field: FieldConfig; register: any; watch: any; setValue: any }) {
  if (field.type === "money") {
    return (
      <div className="grid grid-cols-2 gap-2">
        <div className="ft-field">
          <Label className="ft-label" htmlFor={`${field.name}.amount`}>{field.label}</Label>
          <Input id={`${field.name}.amount`} placeholder="0.00" {...register(`${field.name}.amount`)} />
        </div>
        <div className="ft-field">
          <Label className="ft-label" htmlFor={`${field.name}.currency`}>Moeda</Label>
          <Input id={`${field.name}.currency`} maxLength={3} {...register(`${field.name}.currency`)} />
        </div>
      </div>
    );
  }

  if (field.type === "select") {
    const value = watch(field.name);
    return (
      <div className="ft-field">
        <Label className="ft-label" htmlFor={field.name}>{field.label}</Label>
        <Select value={value ?? ""} onValueChange={(next) => setValue(field.name, next)}>
          <SelectTrigger id={field.name} className="w-full">
            <SelectValue placeholder="Selecione" />
          </SelectTrigger>
          <SelectContent>
            {field.options.map((option) => (
              <SelectItem key={option} value={option}>
                {option}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    );
  }

  if (field.type === "checkbox") {
    const value = watch(field.name);
    return (
      <div className="flex flex-row items-center gap-2 self-end pb-2.5">
        <Checkbox id={field.name} checked={!!value} onCheckedChange={(checked) => setValue(field.name, !!checked)} />
        <Label className="ft-label" htmlFor={field.name}>{field.label}</Label>
      </div>
    );
  }

  return (
    <div className="ft-field">
      <Label className="ft-label" htmlFor={field.name}>{field.label}</Label>
      <Input
        id={field.name}
        type={field.type === "number" ? "number" : field.type === "date" ? "date" : "text"}
        {...register(field.name)}
      />
    </div>
  );
}

export function ResourceStepForm({
  profileId,
  config,
  onNext,
  onBack,
}: {
  profileId: string;
  config: ResourceStepConfig<any>;
  onNext?: () => void;
  onBack?: () => void;
}) {
  const queryClient = useQueryClient();
  const queryKey = [config.key, profileId];

  const { data: items, isLoading, isError } = useQuery({
    queryKey,
    queryFn: () => config.list(profileId),
  });

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(config.schema),
    defaultValues: config.defaultValues,
  });

  const mutation = useMutation({
    mutationFn: (payload: unknown) => config.create(profileId, nullifyEmptyStrings(payload)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      reset(config.defaultValues);
    },
  });

  return (
    <Card className="ft-form-card">
      <CardContent className="space-y-6 p-0">
        <h2 className="ft-form-title">{config.title}</h2>

        <form
          onSubmit={handleSubmit((values) => mutation.mutate(values))}
          className="ft-form-grid"
        >
          {config.fields.map((field) => (
            <Field key={field.name} field={field} register={register} watch={watch} setValue={setValue} />
          ))}
          <div className="ft-field--full">
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Adicionando..." : "Adicionar"}
            </Button>
          </div>
        </form>

        {Object.keys(errors).length > 0 && (
          <p className="text-sm text-red-500">Verifique os campos destacados antes de adicionar.</p>
        )}
        {mutation.isError && <p className="text-sm text-red-500">Não foi possível salvar. Tente novamente.</p>}

        <div className="space-y-2">
          {isLoading && <p className="text-sm text-muted-foreground">Carregando itens...</p>}
          {isError && <p className="text-sm text-red-500">Erro ao carregar itens já adicionados.</p>}
          {!isLoading && !isError && (items as any[])?.length === 0 && (
            <p className="text-sm text-muted-foreground">{config.emptyLabel}</p>
          )}
          {!isLoading &&
            !isError &&
            (items as any[])?.map((item) => (
              <div key={item.id} className="ft-review-item text-sm">
                {config.renderSummary(item)}
              </div>
            ))}
        </div>

        {(onBack || onNext) && (
          <div className="ft-form-actions">
            {onBack ? (
              <Button type="button" variant="outline" onClick={onBack}>
                Voltar
              </Button>
            ) : (
              <span />
            )}
            {onNext && (
              <Button type="button" onClick={onNext}>
                Próximo
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

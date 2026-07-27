/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { z } from "zod";

export const moneySchema = z.object({
  amount: z
    .string()
    .min(1, "Informe um valor.")
    .regex(/^\d+(\.\d{1,2})?$/, "Use um valor numérico com até duas casas decimais."),
  currency: z.string().length(3, "Use o código de 3 letras da moeda (ex: BRL)."),
});

export const liquidityTypeOptions = [
  "checking_account",
  "savings_account",
  "emergency_fund",
  "investment",
  "other",
] as const;

export const recurrenceOptions = ["one_off", "monthly", "weekly", "yearly"] as const;
export const incomeStabilityOptions = ["stable", "variable"] as const;
export const directionOptions = ["income", "expense"] as const;

export const profileSchema = z.object({
  currency: z.string().length(3, "Use o código de 3 letras da moeda (ex: BRL)."),
  dependents: z.coerce.number().int().min(0, "Não pode ser negativo."),
  monthly_expense_reduction_capacity: z
    .string()
    .regex(/^0(\.\d{1,4})?$|^1(\.0{1,4})?$/, "Informe uma fração entre 0 e 1 (ex: 0.15).")
    .optional()
    .or(z.literal("")),
});

export const accountSchema = z.object({
  description: z.string().min(1, "Descrição obrigatória."),
  balance: moneySchema,
  liquidity_type: z.enum(liquidityTypeOptions),
  eligible_for_autonomy: z.boolean().default(false),
});

export const incomeSchema = z.object({
  description: z.string().min(1, "Descrição obrigatória."),
  amount: moneySchema,
  frequency: z.enum(recurrenceOptions),
  start_date: z.string().min(1, "Data de início obrigatória."),
  end_date: z.string().optional().or(z.literal("")),
  stability: z.enum(incomeStabilityOptions),
});

export const obligationSchema = z.object({
  description: z.string().min(1, "Descrição obrigatória."),
  amount: moneySchema,
  category: z.string().min(1, "Categoria obrigatória."),
  frequency: z.enum(recurrenceOptions),
  due_day: z.coerce.number().int().min(1).max(31),
  start_date: z.string().min(1, "Data de início obrigatória."),
  end_date: z.string().optional().or(z.literal("")),
  essential: z.boolean().default(true),
  debt_related: z.boolean().default(false),
});

export const debtSchema = z.object({
  description: z.string().min(1, "Descrição obrigatória."),
  outstanding_balance: moneySchema,
  installment_amount: moneySchema,
  remaining_installments: z.coerce.number().int().min(0),
  interest_rate_optional: z.string().optional().or(z.literal("")),
  due_day: z.coerce.number().int().min(1).max(31),
});

export const goalSchema = z.object({
  description: z.string().min(1, "Descrição obrigatória."),
  target_amount: moneySchema,
  current_amount: moneySchema,
  deadline: z.string().optional().or(z.literal("")),
  priority: z.coerce.number().int().min(1),
  monthly_contribution: moneySchema,
});

export const eventSchema = z.object({
  description: z.string().min(1, "Descrição obrigatória."),
  event_type: z.string().min(1, "Tipo de evento obrigatório."),
  amount: moneySchema,
  date: z.string().min(1, "Data obrigatória."),
  recurrence: z.enum(recurrenceOptions).optional(),
  direction: z.enum(directionOptions),
});

export type ProfileFormValues = z.infer<typeof profileSchema>;
export type AccountFormValues = z.infer<typeof accountSchema>;
export type IncomeFormValues = z.infer<typeof incomeSchema>;
export type ObligationFormValues = z.infer<typeof obligationSchema>;
export type DebtFormValues = z.infer<typeof debtSchema>;
export type GoalFormValues = z.infer<typeof goalSchema>;
export type EventFormValues = z.infer<typeof eventSchema>;

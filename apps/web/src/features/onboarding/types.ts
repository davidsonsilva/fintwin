/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

export interface MoneyDto {
  amount: string;
  currency: string;
}

export interface ProfileDto {
  id: string;
  name: string | null;
  currency: string;
  dependents: number;
  monthly_expense_reduction_capacity: string | null;
  created_at: string;
  updated_at: string;
}

export interface AccountDto {
  id: string;
  profile_id: string;
  description: string;
  balance: MoneyDto;
  liquidity_type: string;
  eligible_for_autonomy: boolean;
}

export interface IncomeDto {
  id: string;
  profile_id: string;
  description: string;
  amount: MoneyDto;
  frequency: string;
  start_date: string;
  end_date: string | null;
  stability: string;
}

export interface ObligationDto {
  id: string;
  profile_id: string;
  description: string;
  amount: MoneyDto;
  category: string;
  frequency: string;
  due_day: number;
  start_date: string;
  end_date: string | null;
  essential: boolean;
  debt_related: boolean;
}

export interface DebtDto {
  id: string;
  profile_id: string;
  description: string;
  outstanding_balance: MoneyDto;
  installment_amount: MoneyDto;
  remaining_installments: number;
  interest_rate_optional: string | null;
  due_day: number;
}

export interface GoalDto {
  id: string;
  profile_id: string;
  description: string;
  target_amount: MoneyDto;
  current_amount: MoneyDto;
  deadline: string | null;
  priority: number;
  monthly_contribution: MoneyDto;
}

export interface EventDto {
  id: string;
  profile_id: string;
  description: string;
  event_type: string;
  amount: MoneyDto;
  date: string;
  recurrence: string | null;
  direction: string;
}

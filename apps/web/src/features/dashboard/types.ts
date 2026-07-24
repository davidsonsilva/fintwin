import type { AccountDto, MoneyDto, ObligationDto } from "@/features/onboarding/types";

export interface MainGoalSummaryDto {
  description: string;
  progress_pct: string;
}

export interface UpcomingEventDto {
  id: string;
  description: string;
  event_type: string;
  amount: MoneyDto;
  date: string;
  direction: string;
}

export interface DashboardSummaryDto {
  net_balance: MoneyDto;
  monthly_obligations_total: MoneyDto;
  income_commitment_pct: string | null;
  main_goal: MainGoalSummaryDto | null;
  upcoming_events: UpcomingEventDto[];
}

export interface ProjectionRequestDto {
  months?: 3 | 6 | 12;
  scenario?: "probable" | "adverse";
}

export interface PeriodProjectionDto {
  period: string;
  opening_balance: MoneyDto;
  income_total: MoneyDto;
  expense_total: MoneyDto;
  net_cashflow: MoneyDto;
  closing_balance: MoneyDto;
  income_commitment_percentage: string | null;
  deficit: boolean;
}

export interface ProjectionResponseDto {
  scenario: string;
  periods: PeriodProjectionDto[];
  first_deficit_period: string | null;
  lowest_balance: MoneyDto;
  final_balance: MoneyDto;
  total_income: MoneyDto;
  total_expenses: MoneyDto;
  main_pressures: string[];
  relevant_events: UpcomingEventDto[];
  assumptions: string[];
}

export interface AutonomyResponseDto {
  eligible_assets: MoneyDto;
  essential_expenses_monthly: MoneyDto;
  basic_autonomy_months: string | null;
  probable_monthly_burn: MoneyDto;
  adverse_monthly_burn: MoneyDto;
  income_loss_monthly_burn: MoneyDto;
  probable_autonomy_months: string | null;
  adverse_autonomy_months: string | null;
  income_loss_autonomy_months: string | null;
  eligible_accounts: AccountDto[];
  essential_obligations: ObligationDto[];
  assumptions: string[];
}

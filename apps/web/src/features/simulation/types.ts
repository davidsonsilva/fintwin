export type DecisionType =
  | "CASH_PURCHASE"
  | "INSTALLMENT_PURCHASE"
  | "FINANCING"
  | "LOAN"
  | "INCOME_LOSS"
  | "SALARY_REDUCTION"
  | "NEW_RECURRING_EXPENSE"
  | "NEW_GOAL"
  | "RESERVE_INCREASE";

export interface ScenarioOverrideInput {
  income_multiplier?: string;
  essential_expense_multiplier?: string;
  nonessential_expense_multiplier?: string;
  unexpected_expense?: string;
  expense_reduction_capacity?: string;
}

export interface SimulationRequestPayload {
  decision_type: DecisionType;
  parameters: Record<string, unknown>;
  scenario_override?: ScenarioOverrideInput;
  horizon_months?: 3 | 6 | 12;
}

export interface MoneyDto {
  amount: string;
  currency: string;
}

export interface ProjectionSummaryDto {
  scenario: string;
  first_deficit_period: string | null;
  lowest_balance: MoneyDto;
  final_balance: MoneyDto;
  total_income: MoneyDto;
  total_expenses: MoneyDto;
  basic_autonomy_months: string | null;
  probable_autonomy_months: string | null;
  adverse_autonomy_months: string | null;
  income_loss_autonomy_months: string | null;
}

export interface SimulationImpactDto {
  autonomy_delta_months: string | null;
  closing_balance_delta: string;
  new_first_deficit_period: string | null;
  goal_delay_months: number | null;
}

export interface TotalCostDto {
  down_payment: MoneyDto;
  installments_total: MoneyDto;
  recurring_costs_total: MoneyDto;
  one_off_costs_total: MoneyDto;
  total_cost: MoneyDto;
}

export interface SimulatedResultDto extends ProjectionSummaryDto {
  impact: SimulationImpactDto;
  total_cost: TotalCostDto | null;
  assumptions: string[];
}

export interface SimulationDto {
  id: string;
  profile_id: string;
  type: DecisionType;
  parameters: Record<string, unknown>;
  baseline_result: ProjectionSummaryDto;
  simulated_result: SimulatedResultDto;
  created_at: string;
}

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SimulationComparison } from "../SimulationComparison";
import type { SimulationDto } from "../types";

const SIMULATION: SimulationDto = {
  id: "sim-1",
  profile_id: "profile-1",
  type: "CASH_PURCHASE",
  parameters: { amount: "3000.00", description: "Notebook" },
  baseline_result: {
    scenario: "probable",
    first_deficit_period: null,
    lowest_balance: { amount: "5000.00", currency: "BRL" },
    final_balance: { amount: "8000.00", currency: "BRL" },
    total_income: { amount: "18000.00", currency: "BRL" },
    total_expenses: { amount: "10000.00", currency: "BRL" },
    basic_autonomy_months: "2.0",
    probable_autonomy_months: "2.0",
    adverse_autonomy_months: "1.8",
    income_loss_autonomy_months: "1.5",
  },
  simulated_result: {
    scenario: "probable",
    first_deficit_period: "2026-09",
    lowest_balance: { amount: "2000.00", currency: "BRL" },
    final_balance: { amount: "5000.00", currency: "BRL" },
    total_income: { amount: "18000.00", currency: "BRL" },
    total_expenses: { amount: "13000.00", currency: "BRL" },
    basic_autonomy_months: "2.0",
    probable_autonomy_months: "2.0",
    adverse_autonomy_months: "1.8",
    income_loss_autonomy_months: "1.5",
    impact: {
      autonomy_delta_months: "0",
      closing_balance_delta: "-3000.00",
      new_first_deficit_period: "2026-09",
      goal_delay_months: null,
    },
    total_cost: null,
    assumptions: ["Cenário-base sempre usa o cenário provável."],
  },
  created_at: "2026-07-24T00:00:00Z",
};

describe("SimulationComparison", () => {
  it("renders baseline vs simulated balances and the impact deltas", () => {
    render(<SimulationComparison simulation={SIMULATION} />);

    expect(screen.getByText("Compra à vista")).toBeInTheDocument();
    expect(screen.getByText("8000.00 BRL")).toBeInTheDocument();
    expect(screen.getByText("5000.00 BRL")).toBeInTheDocument();
    expect(screen.getByText("-3000.00")).toBeInTheDocument();
    expect(screen.getByText("Déficit em 2026-09")).toBeInTheDocument();
  });

  it("shows the total cost card only when total_cost is present", () => {
    render(<SimulationComparison simulation={SIMULATION} />);
    expect(screen.queryByText("Custo total")).not.toBeInTheDocument();
  });
});

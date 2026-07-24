import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { dashboardApi } from "../api";
import { ProjectionChart } from "../ProjectionChart";

vi.mock("../api", () => ({
  dashboardApi: {
    getProjection: vi.fn(),
  },
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

const BASE_PERIOD = {
  opening_balance: { amount: "1000.00", currency: "BRL" },
  income_total: { amount: "3000.00", currency: "BRL" },
  expense_total: { amount: "2000.00", currency: "BRL" },
  net_cashflow: { amount: "1000.00", currency: "BRL" },
  closing_balance: { amount: "2000.00", currency: "BRL" },
  income_commitment_percentage: "0.6666",
  deficit: false,
};

describe("ProjectionChart", () => {
  it("shows a loading state while fetching the projection", () => {
    vi.mocked(dashboardApi.getProjection).mockReturnValue(new Promise(() => {}));
    renderWithClient(<ProjectionChart profileId="profile-1" />);
    expect(screen.getByText(/carregando projeção/i)).toBeInTheDocument();
  });

  it("renders the deficit message and assumptions when there is a projected deficit", async () => {
    vi.mocked(dashboardApi.getProjection).mockResolvedValue({
      scenario: "adverse",
      periods: [{ ...BASE_PERIOD, period: "2026-08", deficit: true }],
      first_deficit_period: "2026-08",
      lowest_balance: { amount: "-500.00", currency: "BRL" },
      final_balance: { amount: "-500.00", currency: "BRL" },
      total_income: { amount: "3000.00", currency: "BRL" },
      total_expenses: { amount: "3500.00", currency: "BRL" },
      main_pressures: ["moradia"],
      relevant_events: [],
      assumptions: ["Cenário adverse: renda x0.75, despesas essenciais x1.05, despesas não essenciais x0.90."],
    });

    renderWithClient(<ProjectionChart profileId="profile-1" />);

    expect(await screen.findByText(/primeiro mês com déficit projetado: 2026-08/i)).toBeInTheDocument();
    expect(screen.getByText(/cenário adverse/i)).toBeInTheDocument();
  });

  it("shows an error message when the projection request fails", async () => {
    vi.mocked(dashboardApi.getProjection).mockRejectedValue(new Error("network error"));

    renderWithClient(<ProjectionChart profileId="profile-1" />);

    await waitFor(() => expect(screen.getByText(/não foi possível carregar a projeção/i)).toBeInTheDocument());
  });
});

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { dashboardApi } from "../api";
import { AutonomyPanel } from "../AutonomyPanel";

vi.mock("../api", () => ({
  dashboardApi: {
    getAutonomy: vi.fn(),
  },
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("AutonomyPanel", () => {
  it("shows a loading state while calculating autonomy", () => {
    vi.mocked(dashboardApi.getAutonomy).mockReturnValue(new Promise(() => {}));
    renderWithClient(<AutonomyPanel profileId="profile-1" />);
    expect(screen.getByText(/calculando autonomia/i)).toBeInTheDocument();
  });

  it("renders the four autonomy figures, evidence and assumptions", async () => {
    vi.mocked(dashboardApi.getAutonomy).mockResolvedValue({
      eligible_assets: { amount: "9000.00", currency: "BRL" },
      essential_expenses_monthly: { amount: "4950.00", currency: "BRL" },
      basic_autonomy_months: "1.8",
      probable_monthly_burn: { amount: "7200.00", currency: "BRL" },
      adverse_monthly_burn: { amount: "7367.50", currency: "BRL" },
      income_loss_monthly_burn: { amount: "6960.00", currency: "BRL" },
      probable_autonomy_months: "1.5",
      adverse_autonomy_months: "1.2",
      income_loss_autonomy_months: "1.9",
      eligible_accounts: [
        {
          id: "acc-1",
          profile_id: "profile-1",
          description: "Reserva de emergência",
          balance: { amount: "9000.00", currency: "BRL" },
          liquidity_type: "emergency_fund",
          eligible_for_autonomy: true,
        },
      ],
      essential_obligations: [
        {
          id: "obl-1",
          profile_id: "profile-1",
          description: "Aluguel",
          amount: { amount: "2200.00", currency: "BRL" },
          category: "moradia",
          frequency: "monthly",
          due_day: 5,
          start_date: "2024-01-01",
          end_date: null,
          essential: true,
          debt_related: false,
        },
      ],
      assumptions: ["Concentração de renda e número de dependentes não são incorporados nesta versão."],
    });

    renderWithClient(<AutonomyPanel profileId="profile-1" />);

    expect(await screen.findByText("1.8 meses")).toBeInTheDocument();
    expect(screen.getByText("1.5 meses")).toBeInTheDocument();
    expect(screen.getByText("1.2 meses")).toBeInTheDocument();
    expect(screen.getByText("1.9 meses")).toBeInTheDocument();
    expect(screen.getByText(/reserva de emergência/i)).toBeInTheDocument();
    expect(screen.getByText(/aluguel/i)).toBeInTheDocument();
    expect(screen.getByText(/concentração de renda/i)).toBeInTheDocument();
  });

  it("shows 'não aplicável' when there are no essential expenses", async () => {
    vi.mocked(dashboardApi.getAutonomy).mockResolvedValue({
      eligible_assets: { amount: "1000.00", currency: "BRL" },
      essential_expenses_monthly: { amount: "0.00", currency: "BRL" },
      basic_autonomy_months: null,
      probable_monthly_burn: { amount: "0.00", currency: "BRL" },
      adverse_monthly_burn: { amount: "0.00", currency: "BRL" },
      income_loss_monthly_burn: { amount: "0.00", currency: "BRL" },
      probable_autonomy_months: null,
      adverse_autonomy_months: null,
      income_loss_autonomy_months: null,
      eligible_accounts: [],
      essential_obligations: [],
      assumptions: [],
    });

    renderWithClient(<AutonomyPanel profileId="profile-1" />);

    expect((await screen.findAllByText("Não aplicável")).length).toBe(4);
  });
});

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SidebarProvider } from "@/components/shell/SidebarContext";
import { fragilityApi } from "@/features/fragility/api";
import { ApiError } from "@/lib/api-client";

import { dashboardApi } from "../api";
import { DashboardView } from "../DashboardView";

// `useRouter` só existe dentro do App Router; o card Insight navega para a
// tela da recomendação depois de detectar.
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), prefetch: vi.fn() }),
  usePathname: () => "/dashboard/profile-1",
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("../api", () => ({
  dashboardApi: {
    getSummary: vi.fn(),
    getProjection: vi.fn(),
    getAutonomy: vi.fn(),
  },
}));

// O card Insight consulta o registro de recomendações; aqui interessa o
// dashboard, não a superfície de detecção (coberta pelos testes do ciclo).
vi.mock("@/features/recommendations/api", () => ({
  recommendationApi: {
    getInsight: vi.fn().mockResolvedValue({
      recommendation: null,
      diagnosis: null,
      active_plan_id: null,
    }),
    detect: vi.fn(),
  },
}));

vi.mock("@/features/fragility/api", () => ({
  fragilityApi: {
    list: vi.fn(),
    detect: vi.fn(),
  },
}));

const PROJECTION_FIXTURE = {
  scenario: "probable",
  periods: [],
  first_deficit_period: null,
  lowest_balance: { amount: "0.00", currency: "BRL" },
  final_balance: { amount: "0.00", currency: "BRL" },
  total_income: { amount: "0.00", currency: "BRL" },
  total_expenses: { amount: "0.00", currency: "BRL" },
  main_pressures: [],
  relevant_events: [],
  assumptions: [],
};

const AUTONOMY_FIXTURE = {
  eligible_assets: { amount: "9000.00", currency: "BRL" },
  essential_expenses_monthly: { amount: "4950.00", currency: "BRL" },
  basic_autonomy_months: "1.8",
  probable_monthly_burn: { amount: "7200.00", currency: "BRL" },
  adverse_monthly_burn: { amount: "7367.50", currency: "BRL" },
  income_loss_monthly_burn: { amount: "6960.00", currency: "BRL" },
  probable_autonomy_months: "1.25",
  adverse_autonomy_months: "1.22",
  income_loss_autonomy_months: "1.29",
  eligible_accounts: [],
  essential_obligations: [],
  assumptions: [],
};

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <SidebarProvider>{ui}</SidebarProvider>
    </QueryClientProvider>
  );
}

describe("DashboardView", () => {
  it("shows a loading state while fetching the summary", () => {
    vi.mocked(dashboardApi.getSummary).mockReturnValue(new Promise(() => {}));
    renderWithClient(<DashboardView profileId="profile-1" />);
    expect(screen.getByText(/carregando resumo financeiro/i)).toBeInTheDocument();
  });

  it("renders the summary cards and upcoming events when data loads", async () => {
    vi.mocked(dashboardApi.getSummary).mockResolvedValue({
      net_balance: { amount: "12500.00", currency: "BRL" },
      monthly_obligations_total: { amount: "4950.00", currency: "BRL" },
      income_commitment_pct: "0.5",
      income_commitment_status: { tier: "attention" as const, label: "Atenção ao comprometimento" },
      main_goal: { description: "Entrada de imóvel próprio", progress_pct: "0.15" },
      upcoming_events: [
        {
          id: "evt-1",
          description: "13º salário",
          event_type: "bonus",
          amount: { amount: "8500.00", currency: "BRL" },
          date: "2026-12-20",
          direction: "income",
        },
      ],
    });
    vi.mocked(dashboardApi.getProjection).mockResolvedValue(PROJECTION_FIXTURE);
    vi.mocked(dashboardApi.getAutonomy).mockResolvedValue(AUTONOMY_FIXTURE);
    vi.mocked(fragilityApi.list).mockResolvedValue([]);

    renderWithClient(<DashboardView profileId="profile-1" />);

    expect(await screen.findByText("R$ 12.500,00")).toBeInTheDocument();
    expect(screen.getByText("R$ 4.950,00")).toBeInTheDocument();
    expect(screen.getAllByText("50.0%").length).toBeGreaterThan(0);
    expect(screen.getByText("Entrada de imóvel próprio")).toBeInTheDocument();
    expect(screen.getByText(/13º salário/)).toBeInTheDocument();
    expect((await screen.findAllByText(/sem déficit projetado/i)).length).toBeGreaterThan(0);
    expect((await screen.findAllByText("1.8 meses")).length).toBeGreaterThan(0);
    expect(await screen.findByText("Ver radar de fragilidade")).toBeInTheDocument();
  });

  it("shows an empty state with a call to action when the profile is not found", async () => {
    vi.mocked(dashboardApi.getSummary).mockRejectedValue(new ApiError(404, "not found"));

    renderWithClient(<DashboardView profileId="missing-profile" />);

    expect(await screen.findByText(/perfil não encontrado/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /completar onboarding/i })).toBeInTheDocument();
  });

  it("shows a retryable error state on network failure", async () => {
    vi.mocked(dashboardApi.getSummary).mockRejectedValue(new ApiError(500, "boom"));

    renderWithClient(<DashboardView profileId="profile-1" />);

    expect(await screen.findByText(/não foi possível carregar o resumo financeiro/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /tentar novamente/i })).toBeInTheDocument();
  });
});

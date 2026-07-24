import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { preventivePlanApi } from "../api";
import { PreventivePlanList } from "../PreventivePlanList";
import type { PreventivePlanDto } from "../types";

vi.mock("../api", () => ({
  preventivePlanApi: {
    list: vi.fn(),
    generate: vi.fn(),
  },
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

const PLAN: PreventivePlanDto = {
  id: "plan-1",
  profile_id: "profile-1",
  risk_code: "UNPROVISIONED_ANNUAL_EXPENSE",
  status: "proposed",
  actions: [
    {
      description: "Provisionar R$ 100,00 por mês.",
      expected_monthly_impact: { amount: "100.00", currency: "BRL" },
      due_date: "2026-10-01",
    },
  ],
  expected_result: { deficit_avoided: false, autonomy_change_months: null },
  created_at: "2026-07-24T00:00:00Z",
  approved_at: null,
};

describe("PreventivePlanList", () => {
  it("shows an empty state when there are no plans", async () => {
    vi.mocked(preventivePlanApi.list).mockResolvedValue([]);
    renderWithClient(<PreventivePlanList profileId="profile-1" />);
    expect(await screen.findByText(/nenhum plano preventivo ainda/i)).toBeInTheDocument();
  });

  it("lists generated plans as cards", async () => {
    vi.mocked(preventivePlanApi.list).mockResolvedValue([PLAN]);
    renderWithClient(<PreventivePlanList profileId="profile-1" />);
    expect(await screen.findByText("Despesa anual sem provisionamento")).toBeInTheDocument();
  });

  it("calls the generate endpoint when the button is clicked", async () => {
    const user = userEvent.setup();
    vi.mocked(preventivePlanApi.list).mockResolvedValue([]);
    vi.mocked(preventivePlanApi.generate).mockResolvedValue([PLAN]);
    renderWithClient(<PreventivePlanList profileId="profile-1" />);

    await user.click(await screen.findByRole("button", { name: "Gerar planos" }));

    expect(preventivePlanApi.generate).toHaveBeenCalledWith("profile-1");
  });
});

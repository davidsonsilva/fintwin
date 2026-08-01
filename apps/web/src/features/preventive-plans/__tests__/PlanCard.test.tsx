import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { preventivePlanApi } from "../api";
import { PlanCard } from "../PlanCard";
import type { PreventivePlanDto } from "../types";

vi.mock("../api", () => ({
  preventivePlanApi: {
    updateStatus: vi.fn(),
  },
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

function makePlan(overrides: Partial<PreventivePlanDto> = {}): PreventivePlanDto {
  return {
    id: "plan-1",
    profile_id: "profile-1",
    risk_code: "RESERVE_BELOW_THREE_MONTHS",
    status: "proposed",
    actions: [
      {
        description: "Aumentar a reserva de emergência em R$ 100,00 por mês.",
        expected_monthly_impact: { amount: "100.00", currency: "BRL" },
        due_date: "2026-10-01",
      },
    ],
    expected_result: { deficit_avoided: true, autonomy_change_months: "1.0" },
    created_at: "2026-07-24T00:00:00Z",
    approved_at: null,
    ...overrides,
  };
}

describe("PlanCard", () => {
  it("shows the risk label, actions and expected impact", () => {
    renderWithClient(<PlanCard plan={makePlan()} />);
    expect(screen.getByText("Reserva abaixo de três meses")).toBeInTheDocument();
    expect(screen.getByText(/Aumentar a reserva de emergência/)).toBeInTheDocument();
    // pt-BR com singular correto: "1.0 meses" era saída de desenvolvedor.
    expect(screen.getByText("Ganho de autonomia estimado: 1 mês")).toBeInTheDocument();
    // A data ISO do domínio não chega à tela.
    expect(screen.getByText(/Prazo: 01\/10\/2026/)).toBeInTheDocument();
  });

  it("mostra o custo em autonomia quando a mudança é negativa", () => {
    // Acelerar uma meta custa autonomia; chamar isso de "ganho" maquiava o
    // preço da decisão.
    renderWithClient(
      <PlanCard
        plan={makePlan({
          expected_result: { deficit_avoided: true, autonomy_change_months: "-2.5" },
        })}
      />
    );
    expect(screen.getByText("Custo em autonomia: 2,5 meses a menos")).toBeInTheDocument();
  });

  it("approves a proposed plan when the button is clicked", async () => {
    const user = userEvent.setup();
    vi.mocked(preventivePlanApi.updateStatus).mockResolvedValue(makePlan({ status: "approved" }));
    renderWithClient(<PlanCard plan={makePlan()} />);

    await user.click(screen.getByRole("button", { name: "Aprovar" }));

    expect(preventivePlanApi.updateStatus).toHaveBeenCalledWith("plan-1", "approved");
  });

  it("rejects a proposed plan when the button is clicked", async () => {
    const user = userEvent.setup();
    vi.mocked(preventivePlanApi.updateStatus).mockResolvedValue(makePlan({ status: "rejected" }));
    renderWithClient(<PlanCard plan={makePlan()} />);

    await user.click(screen.getByRole("button", { name: "Rejeitar" }));

    expect(preventivePlanApi.updateStatus).toHaveBeenCalledWith("plan-1", "rejected");
  });

  it("does not show approve/reject buttons for a plan that is already approved", () => {
    renderWithClient(<PlanCard plan={makePlan({ status: "approved" })} />);
    expect(screen.queryByRole("button", { name: "Aprovar" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Rejeitar" })).not.toBeInTheDocument();
  });
});

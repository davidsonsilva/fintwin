import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { onboardingApi } from "@/features/onboarding/api";

import { simulationApi } from "../api";
import { DecisionForm } from "../DecisionForm";

vi.mock("../api", () => ({
  simulationApi: {
    create: vi.fn(),
  },
}));

vi.mock("@/features/onboarding/api", () => ({
  onboardingApi: {
    listIncomes: vi.fn(),
  },
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("DecisionForm", () => {
  it("submits a cash purchase with the entered amount and description", async () => {
    const user = userEvent.setup();
    vi.mocked(onboardingApi.listIncomes).mockResolvedValue([]);
    vi.mocked(simulationApi.create).mockResolvedValue({
      id: "sim-1",
      profile_id: "profile-1",
      type: "CASH_PURCHASE",
      parameters: {},
      baseline_result: {} as never,
      simulated_result: {} as never,
      created_at: "2026-07-24T00:00:00Z",
    });

    renderWithClient(<DecisionForm profileId="profile-1" onCreated={vi.fn()} />);

    await user.type(screen.getByLabelText("Descrição"), "Notebook novo");
    await user.type(screen.getByLabelText("Valor"), "3500");
    await user.click(screen.getByRole("button", { name: /simular decisão/i }));

    expect(simulationApi.create).toHaveBeenCalledWith("profile-1", {
      decision_type: "CASH_PURCHASE",
      parameters: { description: "Notebook novo", amount: "3500" },
      scenario_override: undefined,
      horizon_months: 12,
    });
  });

  it("calls onCreated with the new simulation id after a successful submission", async () => {
    const user = userEvent.setup();
    const onCreated = vi.fn();
    vi.mocked(onboardingApi.listIncomes).mockResolvedValue([]);
    vi.mocked(simulationApi.create).mockResolvedValue({
      id: "sim-42",
      profile_id: "profile-1",
      type: "CASH_PURCHASE",
      parameters: {},
      baseline_result: {} as never,
      simulated_result: {} as never,
      created_at: "2026-07-24T00:00:00Z",
    });

    renderWithClient(<DecisionForm profileId="profile-1" onCreated={onCreated} />);

    await user.type(screen.getByLabelText("Descrição"), "Compra qualquer");
    await user.type(screen.getByLabelText("Valor"), "100");
    await user.click(screen.getByRole("button", { name: /simular decisão/i }));

    await vi.waitFor(() => expect(onCreated).toHaveBeenCalledWith("sim-42"));
  });
});

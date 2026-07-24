import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { simulationApi } from "../api";
import { SimulationHistory } from "../SimulationHistory";
import type { SimulationDto } from "../types";

vi.mock("../api", () => ({
  simulationApi: {
    list: vi.fn(),
  },
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

const SIMULATION: SimulationDto = {
  id: "sim-1",
  profile_id: "profile-1",
  type: "NEW_GOAL",
  parameters: {},
  baseline_result: {} as never,
  simulated_result: {} as never,
  created_at: "2026-07-24T10:00:00Z",
};

describe("SimulationHistory", () => {
  it("shows an empty state when there are no simulations", async () => {
    vi.mocked(simulationApi.list).mockResolvedValue([]);
    renderWithClient(<SimulationHistory profileId="profile-1" />);
    expect(await screen.findByText(/nenhuma simulação registrada/i)).toBeInTheDocument();
  });

  it("lists past simulations with a link to their detail page", async () => {
    vi.mocked(simulationApi.list).mockResolvedValue([SIMULATION]);
    renderWithClient(<SimulationHistory profileId="profile-1" />);

    const link = await screen.findByRole("link", { name: /nova meta/i });
    expect(link).toHaveAttribute("href", "/dashboard/profile-1/simulations/sim-1");
  });
});

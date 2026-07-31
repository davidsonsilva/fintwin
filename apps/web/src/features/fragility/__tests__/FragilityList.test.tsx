import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { fragilityApi } from "../api";
import { FragilityList } from "../FragilityList";

vi.mock("../api", () => ({
  fragilityApi: {
    list: vi.fn(),
    detect: vi.fn(),
  },
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

const FINDING = {
  id: "finding-1",
  profile_id: "profile-1",
  code: "INCOME_CONCENTRATION",
  title: "Renda concentrada",
  description: "Mais de 80% da renda depende de uma única fonte.",
  formula: "main_source_income / total_income",
  threshold: "0.80",
  severity: "high" as const,
  evidence: { main_source_percentage: "1" },
  detected_at: "2026-07-23",
  status: "active",
};

describe("FragilityList", () => {
  it("shows a loading state while fetching fragilities", () => {
    vi.mocked(fragilityApi.list).mockReturnValue(new Promise(() => {}));
    renderWithClient(<FragilityList profileId="profile-1" />);
    expect(screen.getByText(/carregando fragilidades/i)).toBeInTheDocument();
  });

  it("renders findings with expandable evidence", async () => {
    vi.mocked(fragilityApi.list).mockResolvedValue([FINDING]);

    renderWithClient(<FragilityList profileId="profile-1" />);

    expect(await screen.findByText("Renda concentrada")).toBeInTheDocument();
    expect(screen.getByText("Alta")).toBeInTheDocument();
    expect(screen.getByText(/main_source_percentage/)).toBeInTheDocument();
  });

  it("shows an empty state when there are no findings", async () => {
    vi.mocked(fragilityApi.list).mockResolvedValue([]);

    renderWithClient(<FragilityList profileId="profile-1" />);

    expect(await screen.findByText(/nenhuma fragilidade encontrada/i)).toBeInTheDocument();
  });

  it("calls detect when the button is clicked", async () => {
    const user = userEvent.setup();
    vi.mocked(fragilityApi.list).mockResolvedValue([]);
    vi.mocked(fragilityApi.detect).mockResolvedValue([FINDING]);

    renderWithClient(<FragilityList profileId="profile-1" />);

    await screen.findByText(/nenhuma fragilidade encontrada/i);
    await user.click(screen.getByRole("button", { name: /detectar fragilidades/i }));

    expect(fragilityApi.detect).toHaveBeenCalledWith("profile-1");
  });
});

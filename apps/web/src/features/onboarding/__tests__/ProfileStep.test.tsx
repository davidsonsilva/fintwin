import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { onboardingApi } from "../api";
import { ProfileStep } from "../ProfileStep";

vi.mock("../api", () => ({
  onboardingApi: {
    createProfile: vi.fn(),
    loadDemo: vi.fn(),
  },
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("ProfileStep", () => {
  it("shows a validation error when the currency field is invalid", async () => {
    const user = userEvent.setup();
    renderWithClient(<ProfileStep onCreated={vi.fn()} onDemoLoaded={vi.fn()} />);

    const currencyInput = screen.getByLabelText("Moeda");
    await user.clear(currencyInput);
    await user.type(currencyInput, "XY");
    await user.click(screen.getByRole("button", { name: "Iniciar onboarding" }));

    expect(await screen.findByText(/3 letras da moeda/i)).toBeInTheDocument();
    expect(onboardingApi.createProfile).not.toHaveBeenCalled();
  });

  it("creates the profile and calls onCreated when the form is valid", async () => {
    const user = userEvent.setup();
    const onCreated = vi.fn();
    vi.mocked(onboardingApi.createProfile).mockResolvedValue({
      id: "profile-1",
      name: null,
      currency: "BRL",
      dependents: 0,
      monthly_expense_reduction_capacity: null,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    });

    renderWithClient(<ProfileStep onCreated={onCreated} onDemoLoaded={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "Iniciar onboarding" }));

    await waitFor(() => expect(onCreated).toHaveBeenCalledWith("profile-1"));
    expect(onboardingApi.createProfile).toHaveBeenCalled();
  });

  it("loads the demo profile and calls onDemoLoaded when the demo button is clicked", async () => {
    const user = userEvent.setup();
    const onDemoLoaded = vi.fn();
    vi.mocked(onboardingApi.createProfile).mockResolvedValue({
      id: "demo-profile",
      name: null,
      currency: "BRL",
      dependents: 2,
      monthly_expense_reduction_capacity: null,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    });
    vi.mocked(onboardingApi.loadDemo).mockResolvedValue(undefined);

    renderWithClient(<ProfileStep onCreated={vi.fn()} onDemoLoaded={onDemoLoaded} />);

    await user.click(screen.getByRole("button", { name: /carregar dados de demonstração/i }));

    await waitFor(() => expect(onDemoLoaded).toHaveBeenCalledWith("demo-profile"));
    expect(onboardingApi.loadDemo).toHaveBeenCalledWith("demo-profile");
  });
});

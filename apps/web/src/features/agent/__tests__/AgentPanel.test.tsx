import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { agentApi } from "../api";
import { AgentPanel } from "../AgentPanel";
import type { AgentMessageResponseDto } from "../types";

vi.mock("../api", () => ({
  agentApi: {
    sendMessage: vi.fn(),
    confirmAction: vi.fn(),
  },
  AGENT_COMPONENT_QUERY_KEYS: {
    dashboard_summary: "dashboard-summary",
    autonomy: "autonomy",
    fragilities: "fragilities",
    simulations: "simulations",
  },
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return { ...render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>), queryClient };
}

function makeReply(overrides: Partial<AgentMessageResponseDto["data"]> = {}): AgentMessageResponseDto {
  return {
    data: {
      conversation_id: "conv-1",
      message_id: "msg-1",
      reply: "Seu saldo é R$1000,00.",
      tool_calls: [],
      pending_action: null,
      components_to_update: [],
      pending_questions: [],
      ...overrides,
    },
    evidence: [],
    assumptions: [],
    limitations: ["O FinTwin AI MVP é uma ferramenta educacional e de simulação."],
    generated_at: "2026-07-25T00:00:00Z",
    version: "v1",
  };
}

describe("AgentPanel", () => {
  it("shows an empty state before any message is sent", () => {
    renderWithClient(<AgentPanel profileId="profile-1" onClose={() => {}} />);
    expect(screen.getByText(/ainda não há mensagens/i)).toBeInTheDocument();
  });

  it("sends a message and renders the user and assistant bubbles", async () => {
    const user = userEvent.setup();
    vi.mocked(agentApi.sendMessage).mockResolvedValue(makeReply());
    renderWithClient(<AgentPanel profileId="profile-1" onClose={() => {}} />);

    await user.type(screen.getByPlaceholderText("Pergunte algo..."), "Qual meu saldo?");
    await user.click(screen.getByRole("button", { name: "Enviar" }));

    expect(agentApi.sendMessage).toHaveBeenCalledWith("profile-1", "Qual meu saldo?", null);
    expect(await screen.findByText("Qual meu saldo?")).toBeInTheDocument();
    expect(await screen.findByText("Seu saldo é R$1000,00.")).toBeInTheDocument();
  });

  it("shows pending questions when required fields are missing", async () => {
    const user = userEvent.setup();
    vi.mocked(agentApi.sendMessage).mockResolvedValue(
      makeReply({ reply: "Preciso de mais dados.", pending_questions: ["Preciso do campo 'amount'."] })
    );
    renderWithClient(<AgentPanel profileId="profile-1" onClose={() => {}} />);

    await user.type(screen.getByPlaceholderText("Pergunte algo..."), "Quero comprar algo");
    await user.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText("Preciso do campo 'amount'.")).toBeInTheDocument();
  });

  it("renders a pending action and confirms it on click", async () => {
    const user = userEvent.setup();
    vi.mocked(agentApi.sendMessage).mockResolvedValue(
      makeReply({
        reply: "Proposta pronta.",
        pending_action: {
          action_id: "msg-1",
          decision_type: "CASH_PURCHASE",
          parameters: { amount: "100.00", description: "Compra teste" },
          confirmed: false,
        },
      })
    );
    vi.mocked(agentApi.confirmAction).mockResolvedValue({});
    renderWithClient(<AgentPanel profileId="profile-1" onClose={() => {}} />);

    await user.type(screen.getByPlaceholderText("Pergunte algo..."), "Comprar item de 100 reais");
    await user.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText(/Proposta de simulação: Compra à vista/)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Confirmar" }));

    expect(agentApi.confirmAction).toHaveBeenCalledWith("profile-1", "msg-1");
    expect(await screen.findByText(/Simulação confirmada/)).toBeInTheDocument();
  });
});

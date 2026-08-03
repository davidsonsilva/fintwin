import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { recommendationApi } from "@/features/recommendations/api";
import { ApiError } from "@/lib/api-client";

import { agentApi } from "../api";
import { AgentPanel } from "../AgentPanel";
import type { AgentMessageResponseDto, OpportunityDto } from "../types";

vi.mock("@/features/recommendations/api", () => ({
  recommendationApi: { saveFromConversation: vi.fn() },
}));

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

function makeOpportunity(overrides: Partial<OpportunityDto> = {}): OpportunityDto {
  return {
    id: "opp-1",
    topic: "income_commitment",
    subject_key: null,
    title: "Comprometimento da renda",
    diagnosis: "Suas obrigações mensais ocupam parte da renda.",
    suggested_actions: ["Revisar as despesas recorrentes"],
    evidence_references: ["ev-1"],
    assessment: null,
    requires_simulation: false,
    simulation_status: "not_required",
    related_recommendation_id: null,
    related_plan_id: null,
    available_actions: ["save"],
    ...overrides,
  };
}

async function enviar(user: ReturnType<typeof userEvent.setup>, texto = "E aí?") {
  await user.type(screen.getByPlaceholderText("Pergunte algo..."), texto);
  await user.click(screen.getByRole("button", { name: "Enviar" }));
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

  it("renders one block per opportunity, without reading the reply text", async () => {
    const user = userEvent.setup();
    vi.mocked(agentApi.sendMessage).mockResolvedValue(
      makeReply({
        reply: "Vi duas coisas por aqui.",
        opportunities: [
          makeOpportunity({ id: "opp-1", title: "Comprometimento da renda" }),
          makeOpportunity({ id: "opp-2", topic: "debt_service", title: "Serviço da dívida" }),
        ],
      })
    );
    renderWithClient(<AgentPanel profileId="profile-1" onClose={() => {}} />);
    await enviar(user);

    // O texto natural continua inteiro na bolha.
    expect(await screen.findByText("Vi duas coisas por aqui.")).toBeInTheDocument();
    expect(screen.getByText("Comprometimento da renda")).toBeInTheDocument();
    expect(screen.getByText("Serviço da dívida")).toBeInTheDocument();
  });

  it("only shows the buttons the backend offered in available_actions", async () => {
    const user = userEvent.setup();
    vi.mocked(agentApi.sendMessage).mockResolvedValue(
      makeReply({
        opportunities: [
          makeOpportunity({
            available_actions: ["view_plan"],
            related_plan_id: "plan-9",
          }),
        ],
      })
    );
    renderWithClient(<AgentPanel profileId="profile-1" onClose={() => {}} />);
    await enviar(user);

    expect(await screen.findByRole("link", { name: /ver plano/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /salvar como recomendação/i })).not.toBeInTheDocument();
  });

  it("sends only the three identifiers when saving", async () => {
    const user = userEvent.setup();
    vi.mocked(agentApi.sendMessage).mockResolvedValue(
      makeReply({ opportunities: [makeOpportunity({ id: "opp-7" })] })
    );
    vi.mocked(recommendationApi.saveFromConversation).mockResolvedValue({ id: "rec-3" } as never);
    renderWithClient(<AgentPanel profileId="profile-1" onClose={() => {}} />);
    await enviar(user);

    await user.click(await screen.findByRole("button", { name: /salvar como recomendação/i }));

    expect(recommendationApi.saveFromConversation).toHaveBeenCalledWith("profile-1", {
      conversation_id: "conv-1",
      message_id: "msg-1",
      opportunity_id: "opp-7",
    });
    expect(await screen.findByText(/salva no registro/i)).toBeInTheDocument();
  });

  it("follows the backend when the action is already outdated (409)", async () => {
    const user = userEvent.setup();
    vi.mocked(agentApi.sendMessage).mockResolvedValue(
      makeReply({ opportunities: [makeOpportunity()] })
    );
    vi.mocked(recommendationApi.saveFromConversation).mockRejectedValue(
      new ApiError(
        409,
        JSON.stringify({
          detail: {
            error: "action_outdated",
            current_action: "view_recommendation",
            related_plan_id: null,
            related_recommendation_id: "rec-existente",
          },
        })
      )
    );
    renderWithClient(<AgentPanel profileId="profile-1" onClose={() => {}} />);
    await enviar(user);

    await user.click(await screen.findByRole("button", { name: /salvar como recomendação/i }));

    const link = await screen.findByRole("link", { name: /ver recomendação/i });
    expect(link).toHaveAttribute("href", "/dashboard/profile-1/recomendacoes/rec-existente");
    expect(screen.queryByRole("button", { name: /salvar como recomendação/i })).not.toBeInTheDocument();
  });

  it("keeps messages without opportunities as plain text", async () => {
    const user = userEvent.setup();
    vi.mocked(agentApi.sendMessage).mockResolvedValue(makeReply({ reply: "Só uma explicação." }));
    renderWithClient(<AgentPanel profileId="profile-1" onClose={() => {}} />);
    await enviar(user);

    expect(await screen.findByText("Só uma explicação.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /salvar como recomendação/i })).not.toBeInTheDocument();
  });
});

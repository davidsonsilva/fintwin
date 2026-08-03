/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

export interface PendingActionDto {
  action_id: string;
  decision_type: string;
  parameters: Record<string, unknown>;
  confirmed: boolean;
}

export interface ToolCallDto {
  tool: string;
  input: Record<string, unknown>;
}

/** As ações que o backend oferece. A interface não deduz nenhuma delas. */
export type OpportunityAction = "simulate" | "save" | "view_recommendation" | "view_plan";

export interface OpportunityAssessmentDto {
  value: string | null;
  tier: string | null;
  severity: string | null;
  policy_id: string | null;
  policy_version: string | null;
}

/**
 * Um bloco acionável já estruturado pelo backend.
 *
 * O cliente não lê o Markdown da resposta para descobrir o que é acionável, não
 * classifica nada e não decide quais botões existem: `available_actions` é o
 * que foi exibido naquele momento — e mesmo ele é revalidado no clique.
 */
export interface OpportunityDto {
  id: string;
  topic: string;
  subject_key: string | null;
  title: string;
  diagnosis: string;
  suggested_actions: string[];
  evidence_references: string[];
  assessment: OpportunityAssessmentDto | null;
  requires_simulation: boolean;
  simulation_status: string;
  related_recommendation_id: string | null;
  related_plan_id: string | null;
  available_actions: OpportunityAction[];
}

export interface AgentMessageDataDto {
  conversation_id: string;
  message_id: string;
  reply: string;
  tool_calls: ToolCallDto[];
  pending_action: PendingActionDto | null;
  components_to_update: string[];
  pending_questions: string[];
  /** Vazio em mensagens sem oportunidade e nas gravadas antes deste contrato. */
  opportunities?: OpportunityDto[];
}

export interface AgentMessageResponseDto {
  data: AgentMessageDataDto;
  evidence: Array<{ tool: string; result: unknown }>;
  assumptions: string[];
  limitations: string[];
  generated_at: string;
  version: string;
}

export interface AgentMessageHistoryItemDto {
  id: string;
  role: "user" | "assistant";
  content: string;
  tool_calls: ToolCallDto[];
  pending_action: PendingActionDto | null;
  opportunities?: OpportunityDto[];
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  pendingAction?: PendingActionDto | null;
  pendingQuestions?: string[];
  opportunities?: OpportunityDto[];
}

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

export interface AgentMessageDataDto {
  conversation_id: string;
  message_id: string;
  reply: string;
  tool_calls: ToolCallDto[];
  pending_action: PendingActionDto | null;
  components_to_update: string[];
  pending_questions: string[];
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
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  pendingAction?: PendingActionDto | null;
  pendingQuestions?: string[];
}

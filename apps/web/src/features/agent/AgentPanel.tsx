"use client";

import { Sparkles } from "lucide-react";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import { AGENT_COMPONENT_QUERY_KEYS, agentApi } from "./api";
import { PendingActionCard } from "./PendingActionCard";
import type { ChatMessage } from "./types";

export function AgentPanel({ profileId }: { profileId: string }) {
  const queryClient = useQueryClient();
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [dismissedActionIds, setDismissedActionIds] = useState<Set<string>>(new Set());
  const [input, setInput] = useState("");

  const sendMessage = useMutation({
    mutationFn: (message: string) => agentApi.sendMessage(profileId, message, conversationId),
    onSuccess: (response) => {
      const { data } = response;
      setConversationId(data.conversation_id);
      setMessages((prev) => [
        ...prev,
        { id: `${data.message_id}-user`, role: "user", content: input },
        {
          id: data.message_id,
          role: "assistant",
          content: data.reply,
          pendingAction: data.pending_action,
          pendingQuestions: data.pending_questions,
        },
      ]);
      setInput("");
      data.components_to_update.forEach((component) => {
        const queryKey = AGENT_COMPONENT_QUERY_KEYS[component];
        if (queryKey) {
          queryClient.invalidateQueries({ queryKey: [queryKey, profileId] });
        }
      });
    },
  });

  const confirmAction = useMutation({
    mutationFn: (actionId: string) => agentApi.confirmAction(profileId, actionId),
    onSuccess: (_result, actionId) => {
      setMessages((prev) =>
        prev.map((m) =>
          m.pendingAction?.action_id === actionId
            ? { ...m, pendingAction: { ...m.pendingAction, confirmed: true } }
            : m
        )
      );
      queryClient.invalidateQueries({ queryKey: ["simulations", profileId] });
    },
  });

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || sendMessage.isPending) return;
    sendMessage.mutate(trimmed);
  };

  return (
    <aside className="ft-agent-panel">
      <div className="ft-agent-header">
        <Sparkles size={18} />
        <h2 className="ft-agent-title">Assistente FinTwin</h2>
      </div>
      <p className="ft-agent-subtitle">
        Pergunte sobre seus indicadores, fragilidades ou proponha uma simulação. Nenhum número é calculado
        pelo assistente — tudo vem do motor financeiro.
      </p>

      <div className="ft-agent-messages">
        {messages.length === 0 && (
          <p className="ft-agent-empty">Ainda não há mensagens nesta conversa.</p>
        )}
        {messages.map((message) => (
          <div key={message.id} className={`ft-agent-bubble ft-agent-bubble--${message.role}`}>
            {message.content}
            {message.pendingQuestions && message.pendingQuestions.length > 0 && (
              <ul className="ft-agent-questions">
                {message.pendingQuestions.map((question) => (
                  <li key={question}>{question}</li>
                ))}
              </ul>
            )}
            {message.pendingAction && !dismissedActionIds.has(message.pendingAction.action_id) && (
              <PendingActionCard
                pendingAction={message.pendingAction}
                isConfirming={confirmAction.isPending}
                onConfirm={() => confirmAction.mutate(message.pendingAction!.action_id)}
                onCancel={() =>
                  setDismissedActionIds((prev) => new Set(prev).add(message.pendingAction!.action_id))
                }
              />
            )}
          </div>
        ))}
        {sendMessage.isError && <p className="ft-agent-bubble ft-agent-bubble--assistant">Não consegui responder agora. Tente novamente.</p>}
      </div>

      <form className="ft-agent-form" onSubmit={handleSubmit}>
        <Input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Pergunte algo..."
          disabled={sendMessage.isPending}
        />
        <Button type="submit" disabled={sendMessage.isPending || !input.trim()}>
          Enviar
        </Button>
      </form>
    </aside>
  );
}

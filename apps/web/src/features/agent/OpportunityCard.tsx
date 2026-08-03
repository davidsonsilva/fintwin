"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { BookmarkCheck, BookmarkPlus, ExternalLink, Loader2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/design-system/components/Button";
import { recommendationApi } from "@/features/recommendations/api";
import { ApiError } from "@/lib/api-client";

import type { OpportunityAction, OpportunityDto } from "./types";

/**
 * Um bloco acionável da resposta — um por oportunidade.
 *
 * A interface não interpreta o texto da conversa, não classifica nada e não
 * inventa ação: desenha o que o backend estruturou e oferece exatamente as
 * ações de `available_actions`. Esse conjunto é o retrato do momento em que a
 * resposta foi escrita; o backend revalida no clique, e quando o estado já
 * mudou (409) o card passa a mostrar o estado atual.
 */

interface OutdatedAction {
  current_action: OpportunityAction;
  related_plan_id: string | null;
  related_recommendation_id: string | null;
}

/** O corpo do 409 diz para onde levar a pessoa agora. */
function parseOutdatedAction(error: unknown): OutdatedAction | null {
  if (!(error instanceof ApiError) || error.status !== 409) return null;
  try {
    const detail = JSON.parse(error.message)?.detail;
    if (detail?.error !== "action_outdated") return null;
    return detail as OutdatedAction;
  } catch {
    return null;
  }
}

export function OpportunityCard({
  profileId,
  conversationId,
  messageId,
  opportunity,
}: {
  profileId: string;
  conversationId: string;
  messageId: string;
  opportunity: OpportunityDto;
}) {
  const queryClient = useQueryClient();
  const [outdated, setOutdated] = useState<OutdatedAction | null>(null);
  const [savedRecommendationId, setSavedRecommendationId] = useState<string | null>(null);

  const save = useMutation({
    mutationFn: () =>
      recommendationApi.saveFromConversation(profileId, {
        conversation_id: conversationId,
        message_id: messageId,
        opportunity_id: opportunity.id,
      }),
    onSuccess: (saved) => {
      setSavedRecommendationId(saved.id);
      queryClient.invalidateQueries({ queryKey: ["recommendations", profileId] });
    },
    onError: (error) => {
      const current = parseOutdatedAction(error);
      if (current) {
        setOutdated(current);
        queryClient.invalidateQueries({ queryKey: ["recommendations", profileId] });
      }
    },
  });

  const actions: OpportunityAction[] = outdated
    ? [outdated.current_action]
    : opportunity.available_actions;
  const recommendationId = outdated?.related_recommendation_id ?? opportunity.related_recommendation_id;

  return (
    <article className="ft-opportunity">
      <h4 className="ft-opportunity-title">{opportunity.title}</h4>
      <p className="ft-opportunity-diagnosis">{opportunity.diagnosis}</p>

      {opportunity.suggested_actions.length > 0 && (
        <ul className="ft-opportunity-steps">
          {opportunity.suggested_actions.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ul>
      )}

      {savedRecommendationId ? (
        <p className="ft-agent-saved">
          <BookmarkCheck size={14} />
          Salva no registro.{" "}
          <Link href={`/dashboard/${profileId}/recomendacoes/${savedRecommendationId}`}>
            Ver recomendação
          </Link>
        </p>
      ) : (
        <div className="ft-opportunity-actions">
          {actions.map((action) => {
            if (action === "save") {
              return (
                <Button
                  key={action}
                  variant="outline"
                  size="sm"
                  onClick={() => !save.isPending && save.mutate()}
                  disabled={save.isPending}
                >
                  {save.isPending ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : (
                    <BookmarkPlus size={14} />
                  )}
                  Salvar como recomendação
                </Button>
              );
            }
            if (action === "view_recommendation" && recommendationId) {
              return (
                <Link
                  key={action}
                  className="ft-opportunity-link"
                  href={`/dashboard/${profileId}/recomendacoes/${recommendationId}`}
                >
                  <ExternalLink size={14} />
                  Ver recomendação
                </Link>
              );
            }
            if (action === "view_plan") {
              return (
                <Link
                  key={action}
                  className="ft-opportunity-link"
                  href={`/dashboard/${profileId}/plans`}
                >
                  <ExternalLink size={14} />
                  Ver plano
                </Link>
              );
            }
            // `simulate` não é mais oferecido pelo backend enquanto não existir
            // caminho de uma oportunidade até uma simulação. Blocos gravados
            // antes dessa decisão ainda podem carregá-lo; nada a desenhar.
            return null;
          })}
        </div>
      )}

      {outdated && (
        <p className="ft-opportunity-note">
          Este assunto já tem registro. Abra o que existe em vez de criar outro.
        </p>
      )}
      {save.isError && !outdated && (
        <span className="ft-agent-error">Não consegui salvar. Tente de novo.</span>
      )}
    </article>
  );
}

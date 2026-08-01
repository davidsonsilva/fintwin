"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { BookmarkCheck, BookmarkPlus, Loader2 } from "lucide-react";
import Link from "next/link";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/design-system/components/Button";

import { recommendationApi } from "./api";

/*
 * "Salvar como recomendação" — o gesto explícito que leva uma resposta da IA
 * para o registro.
 *
 * Nenhuma resposta do agente vira recomendação sozinha. A ação é do usuário, e
 * o registro guarda de qual conversa e de qual mensagem ela veio, para a
 * decisão continuar auditável meses depois.
 */
export function SaveFromConversation({
  profileId,
  conversationId,
  messageId,
  content,
}: {
  profileId: string;
  conversationId: string;
  messageId: string;
  content: string;
}) {
  const queryClient = useQueryClient();

  const save = useMutation({
    mutationFn: () =>
      recommendationApi.saveFromConversation(profileId, {
        conversation_id: conversationId,
        message_id: messageId,
        // O texto da resposta é o conteúdo da recomendação. Cenários e
        // evidências só existem quando o motor produz a análise — aqui o que
        // se preserva é o que a IA de fato disse, sem inventar números.
        payload: { status: "available", summary: content, source_text: content },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recommendations", profileId] });
    },
  });

  if (save.isSuccess) {
    return (
      <p className="ft-agent-saved">
        <BookmarkCheck size={14} />
        Salva no registro.{" "}
        <Link href={`/dashboard/${profileId}/recomendacoes`}>Ver recomendações</Link>
      </p>
    );
  }

  return (
    <div className="ft-agent-save">
      <Button
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
      {save.isError && <span className="ft-agent-error">Não consegui salvar. Tente de novo.</span>}
    </div>
  );
}

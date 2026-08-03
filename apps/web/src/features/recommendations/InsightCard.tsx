"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { AlertTriangle, ArrowRight, ClipboardCheck, Loader2, RefreshCw, Sparkles } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button as LinkButton } from "@/components/ui/button";
import { Button } from "@/design-system/components/Button";

import { recommendationApi } from "./api";
import { formatMoney, formatMonthCount, formatPercent, formatPeriod } from "./format";
import type { InsightDto } from "./types";

/*
 * Card "Insight do seu Gêmeo Financeiro" — superfície viva de detecção.
 *
 * Ele mostra o *próximo* assunto que merece atenção, nunca um histórico. Uma
 * recomendação decidida sai daqui: o registro guarda o desfecho e os planos
 * preventivos acompanham a execução. Se não há o que fazer, o card diz que
 * segue monitorando, em vez de ficar mudo ou repetir algo já resolvido.
 *
 * Estrutura e classes são as do design system (`.ft-ai-insight`): avatar,
 * texto e ação, com o layout responsivo já validado. Só o conteúdo é novo.
 */
export function InsightCard({ profileId }: { profileId: string }) {
  const router = useRouter();
  const queryClient = useQueryClient();

  const insight = useQuery({
    queryKey: ["insight", profileId],
    queryFn: () => recommendationApi.getInsight(profileId),
    retry: false,
  });

  const detect = useMutation({
    mutationFn: () => recommendationApi.detect(profileId),
    onSuccess: (surface: InsightDto) => {
      queryClient.setQueryData(["insight", profileId], surface);
      queryClient.invalidateQueries({ queryKey: ["recommendations", profileId] });
      if (surface.recommendation) {
        router.push(`/dashboard/${profileId}/recomendacoes/${surface.recommendation.id}`);
      }
    },
  });

  /*
   * Prevenção de clique duplo em duas camadas: `disabled` cobre o caso normal,
   * a guarda aqui cobre o segundo clique que chega antes do React repintar.
   * Sem ela, dois cliques criariam duas análises.
   */
  const analyzing = detect.isPending;
  function runDetection() {
    if (analyzing) return;
    detect.mutate();
  }

  const data = insight.data;
  const pending = data?.recommendation ?? null;
  const diagnosis = data?.diagnosis ?? null;
  const scenario = pending
    ? pending.payload.scenarios.find((item) => item.key === pending.payload.recommended?.key) ??
      pending.payload.recommended
    : null;

  return (
    <div className="ft-ai-insight">
      <div className="ft-ai-avatar">
        <Image src="/agent-icon.png" alt="" width={76} height={76} className="rounded-full object-cover" />
      </div>

      <div className="min-w-0">
        <p className="ft-ai-title">Insight do seu Gêmeo Financeiro</p>

        {(insight.isLoading || analyzing) && (
          <p className="ft-ai-text flex items-center gap-2" role="status" aria-live="polite">
            <Loader2 size={16} className="flex-none animate-spin text-[color:var(--ft-primary)]" />
            {analyzing ? "Analisando seus dados…" : "Verificando se há algo que mereça sua atenção…"}
          </p>
        )}

        {!analyzing && (insight.isError || detect.isError) && (
          <p className="ft-ai-text flex items-start gap-2">
            <AlertTriangle size={16} className="mt-1 flex-none text-[color:var(--ft-danger)]" />
            Não foi possível concluir a análise. Seus dados não foram alterados.
          </p>
        )}

        {/* Recomendação pendente: o assunto do momento. */}
        {!analyzing && !insight.isError && pending && scenario && (
          <>
            <p className="ft-ai-text">
              {/* Sem adjetivo sobre o comprometimento: quem classifica é o
                  domínio, e o gauge já mostra o veredito. Repetir aqui abriria
                  a porta para um quarto classificador divergente. */}
              Seu comprometimento está em{" "}
              <strong>{formatPercent(pending.payload.income_commitment, 1)}</strong> da renda e sobra{" "}
              <strong>{formatMoney(pending.payload.recurring_surplus)}</strong> por mês sem destino. Que
              tal direcionar{" "}
              <strong>
                {formatPercent(scenario.additional_pct)} a mais — {formatMoney(scenario.additional_amount)}
              </strong>{" "}
              para “{pending.payload.goal_description}”?
            </p>
            <p className="ft-ai-text text-[color:var(--ft-text-secondary)]">
              Antecipa a meta em {formatMonthCount(scenario.months_saved)}, até{" "}
              {formatPeriod(scenario.projected_completion)}.
              {pending.stale && " Os dados mudaram desde esta análise — recalcule antes de aprovar."}
            </p>
          </>
        )}

        {/* Oportunidade detectável que ainda não virou recomendação. */}
        {!analyzing && !insight.isError && !pending && diagnosis?.status === "available" && !data?.active_plan_id && (
          <p className="ft-ai-text">
            Encontrei uma oportunidade nos seus números: há sobra recorrente que pode acelerar sua meta
            principal sem criar um novo risco. Quer analisar?
          </p>
        )}

        {/* Plano em execução: o assunto já foi endereçado. */}
        {!analyzing && !insight.isError && !pending && data?.active_plan_id && (
          <p className="ft-ai-text">
            Você já tem um plano em andamento para acelerar sua meta principal. Suas finanças seguem
            sendo monitoradas — aviso aqui assim que surgir uma nova ação relevante.
          </p>
        )}

        {/* Nada a fazer agora. */}
        {!analyzing && !insight.isError && !pending && !data?.active_plan_id && diagnosis?.status === "no_action" && (
          <p className="ft-ai-text">
            Suas finanças estão sendo monitoradas. Nenhuma nova ação é necessária no momento.
            {diagnosis.reason ? ` ${diagnosis.reason}` : ""}
          </p>
        )}

        {/* Sem base para recomendar. */}
        {!analyzing && !insight.isError && !pending && diagnosis?.status === "insufficient_data" && (
          <p className="ft-ai-text">
            Ainda não consigo procurar oportunidades: {diagnosis.missing_data.join(" ")} Complete seus
            dados para o Gêmeo começar a monitorar.
          </p>
        )}
      </div>

      <InsightAction
        profileId={profileId}
        data={data}
        analyzing={analyzing}
        failed={insight.isError || detect.isError}
        loading={insight.isLoading}
        onDetect={runDetection}
      />
    </div>
  );
}

/** A ação muda com o estado — o texto do botão nunca mente sobre o destino. */
function InsightAction({
  profileId,
  data,
  analyzing,
  failed,
  loading,
  onDetect,
}: {
  profileId: string;
  data?: InsightDto;
  analyzing: boolean;
  failed: boolean;
  loading: boolean;
  onDetect: () => void;
}) {
  const className = "[@media(max-width:1024px)]:col-[1/-1]";

  if (analyzing || loading) {
    return (
      <Button disabled className={className}>
        <Loader2 size={16} className="animate-spin" />
        Analisando…
      </Button>
    );
  }

  if (failed) {
    return (
      <Button variant="outline" onClick={onDetect} className={className}>
        <RefreshCw size={16} />
        Tentar novamente
      </Button>
    );
  }

  const pending = data?.recommendation;
  if (pending) {
    return (
      <LinkButton
        nativeButton={false}
        className={className}
        render={
          <Link href={`/dashboard/${profileId}/recomendacoes/${pending.id}`}>
            <Sparkles size={16} />
            Ver recomendações
            <ArrowRight size={16} />
          </Link>
        }
      />
    );
  }

  if (data?.active_plan_id) {
    return (
      <LinkButton
        variant="outline"
        nativeButton={false}
        className={className}
        render={
          <Link href={`/dashboard/${profileId}/plans`}>
            <ClipboardCheck size={16} />
            Ver plano em andamento
          </Link>
        }
      />
    );
  }

  if (data?.diagnosis?.status === "insufficient_data") {
    return (
      <LinkButton
        variant="outline"
        nativeButton={false}
        className={className}
        render={<Link href={`/dashboard/${profileId}/review`}>Completar meus dados</Link>}
      />
    );
  }

  // Sobra o caso de haver oportunidade detectável, ou nada a fazer agora: em
  // ambos o gesto é o mesmo — pedir ao Gêmeo que olhe de novo.
  const hasOpportunity = data?.diagnosis?.status === "available";
  return (
    <Button
      variant={hasOpportunity ? "primary" : "outline"}
      onClick={onDetect}
      className={className}
    >
      {hasOpportunity ? <Sparkles size={16} /> : <RefreshCw size={16} />}
      {hasOpportunity ? "Ver recomendações" : "Analisar de novo"}
    </Button>
  );
}

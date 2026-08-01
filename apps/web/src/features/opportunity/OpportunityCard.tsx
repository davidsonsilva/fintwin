"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { AlertTriangle, ArrowRight, Loader2, RefreshCw, Sparkles, TrendingUp } from "lucide-react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/design-system/components/Badge";
import { Button as LinkButton } from "@/components/ui/button";
import { Button } from "@/design-system/components/Button";
import { Card } from "@/design-system/components/Card";

import { opportunityApi } from "./api";
import { useAnalyzeOpportunity } from "./useAnalyzeOpportunity";
import { formatMoney, formatMonthCount, formatMonths, formatPercent, formatPeriod } from "./format";
import type { OpportunityAnalysisDto } from "./types";

/*
 * Card-resumo da recomendação proativa.
 *
 * A regra que ele obedece: aqui só cabem diagnóstico resumido, ação sugerida e
 * impacto estimado. Cenários, premissas, riscos e evidências ficam na tela
 * `/dashboard/{id}/recomendacoes/{analysisId}` — se coubessem aqui, o card
 * viraria o documento inteiro e ninguém leria nenhum dos dois.
 *
 * Nenhum número é escrito à mão: todos vêm do snapshot que o motor gerou.
 */
export function OpportunityCard({ profileId }: { profileId: string }) {
  const latest = useQuery({
    queryKey: ["opportunity-latest", profileId],
    queryFn: () => opportunityApi.getLatest(profileId),
    retry: false,
  });

  // A prevenção de clique duplo mora no hook; aqui `disabled` é a segunda
  // camada, a visual.
  const { run: runAnalysis, analyzing: busy, failed: analysisFailed } = useAnalyzeOpportunity(profileId);

  const analysis = latest.data ?? null;
  const result = analysis?.result ?? null;

  return (
    <Card.Root interactive className="h-auto self-start">
      <Card.Header
        icon={
          <span className="grid size-9 place-items-center rounded-[11px] bg-[color:var(--ft-purple-soft)] text-[color:var(--ft-purple)]">
            <Sparkles size={18} />
          </span>
        }
        className="ft-card-header"
        title={
          <div className="min-w-0">
            <h3 className="m-0 text-[length:clamp(15px,3.6cqi,20px)] leading-[1.3] font-semibold">
              Recomendação do seu Gêmeo Financeiro
            </h3>
            <p className="m-0 mt-1.5 text-[length:clamp(12px,2.8cqi,14px)] text-[color:var(--ft-text-secondary)]">
              Oportunidade calculada sobre os seus números atuais
            </p>
          </div>
        }
        actions={<StatusBadge analysis={analysis} busy={busy} failed={latest.isError || analysisFailed} />}
      />

      <Card.Content className="flex flex-none flex-col gap-4 pb-5">
        {/* Analisando — vale tanto para a carga inicial quanto para o clique. */}
        {(latest.isLoading || busy) && (
          <Analyzing label={busy ? "Analisando seus dados…" : "Carregando a última análise…"} />
        )}

        {/* Erro na análise. Explícito e com saída, nunca um card mudo. */}
        {!busy && (latest.isError || analysisFailed) && (
          <StateBlock
            tone="danger"
            title="Não foi possível concluir a análise"
            body="O motor não respondeu. Seus dados não foram alterados."
            action={
              <Button variant="outline" onClick={() => (analysisFailed ? runAnalysis() : latest.refetch())}>
                <RefreshCw size={16} />
                Tentar novamente
              </Button>
            }
          />
        )}

        {/* Nunca analisado: estado inicial, não vazio nem erro. */}
        {!latest.isLoading && !busy && !latest.isError && !analysisFailed && !analysis && (
          <StateBlock
            tone="neutral"
            title="Ainda não analisamos oportunidades"
            body="O FinTwin pode procurar folga recorrente capaz de acelerar sua meta principal sem criar um novo risco."
            action={
              <Button onClick={() => runAnalysis()} disabled={busy}>
                <Sparkles size={16} />
                Ver recomendações
              </Button>
            }
          />
        )}

        {!busy && !latest.isError && result?.status === "insufficient_data" && (
          <StateBlock
            tone="warning"
            title="Dados insuficientes para recomendar"
            body="O FinTwin não produz recomendação sem base. Falta:"
            list={result.missing_data}
            action={
              <LinkButton
                variant="outline"
                nativeButton={false}
                render={<Link href={`/dashboard/${profileId}/review`}>Completar meus dados</Link>}
              />
            }
          />
        )}

        {!busy && !latest.isError && result?.status === "no_action" && (
          <StateBlock
            tone="neutral"
            title="Nenhuma ação necessária agora"
            body={result.reason ?? "Seus números não abrem espaço para um novo aporte com segurança."}
            action={
              <Button variant="outline" onClick={() => runAnalysis()} disabled={busy}>
                <RefreshCw size={16} />
                Analisar de novo
              </Button>
            }
          />
        )}

        {!busy && !latest.isError && result?.status === "available" && result.recommended && analysis && (
          <>
            {/* 1. Diagnóstico resumido — uma frase, com o número que a sustenta. */}
            <p className="m-0 text-[length:clamp(13px,3cqi,15px)] leading-relaxed text-[color:var(--ft-text-secondary)]">
              Seu comprometimento está em{" "}
              <strong className="text-[color:var(--ft-text-primary)]">
                {formatPercent(result.income_commitment, 1)}
              </strong>{" "}
              da renda e sobra{" "}
              <strong className="text-[color:var(--ft-text-primary)]">
                {formatMoney(result.recurring_surplus)}
              </strong>{" "}
              por mês sem destino.
            </p>

            {/* 2. Ação sugerida. */}
            <div className="rounded-[14px] border border-[color:var(--ft-border)] bg-white/[0.025] p-4">
              <p className="m-0 flex items-center gap-2 text-[length:clamp(11px,2.4cqi,12px)] font-semibold tracking-wide text-[color:var(--ft-text-secondary)] uppercase">
                <TrendingUp size={14} />
                Ação sugerida
              </p>
              <p className="m-0 mt-2 text-[length:clamp(15px,3.8cqi,19px)] leading-snug font-semibold">
                Direcionar {formatMoney(result.recommended.additional_amount)} a mais por mês
                {result.goal_description ? ` para “${result.goal_description}”` : ""}
              </p>
              <p className="m-0 mt-1.5 text-[length:clamp(12px,2.8cqi,13px)] text-[color:var(--ft-text-secondary)]">
                +{formatPercent(result.recommended.additional_pct)} da renda, por{" "}
                {formatMonthCount(result.recommended.months_to_goal)}
              </p>
            </div>

            {/* 3. Impacto estimado. */}
            <dl className="m-0 grid grid-cols-[repeat(auto-fit,minmax(140px,1fr))] gap-3">
              <Impact
                label="Meta antecipada em"
                value={formatMonthCount(result.recommended.months_saved)}
                tone="positive"
              />
              <Impact label="Conclusão" value={formatPeriod(result.recommended.projected_completion)} />
              <Impact
                label="Autonomia após"
                value={formatMonths(result.recommended.autonomy_months_after)}
              />
            </dl>

            {analysis.stale && <StaleNotice onRecalculate={runAnalysis} busy={busy} />}
          </>
        )}
      </Card.Content>

      {result?.status === "available" && analysis && (
        <Card.Footer className="mt-0">
          <Link
            href={`/dashboard/${profileId}/recomendacoes/${analysis.analysis_id}`}
            className="flex min-w-0 items-center justify-between gap-2 border-t border-[color:var(--ft-border)] pt-4 text-[length:clamp(13px,3cqi,16px)] text-[#b49cff]"
          >
            Ver recomendação completa
            <ArrowRight size={16} className="flex-none" />
          </Link>
        </Card.Footer>
      )}
    </Card.Root>
  );
}

function StatusBadge({
  analysis,
  busy,
  failed,
}: {
  analysis: OpportunityAnalysisDto | null;
  busy: boolean;
  failed: boolean;
}) {
  if (busy) return <Badge tone="purple">Analisando</Badge>;
  if (failed) return <Badge tone="danger">Erro</Badge>;
  if (!analysis) return null;
  if (analysis.stale) return <Badge tone="warning">Desatualizada</Badge>;
  if (analysis.decision === "approved") return <Badge tone="success">Plano aprovado</Badge>;
  if (analysis.decision === "rejected") return <Badge tone="neutral">Rejeitada</Badge>;
  if (analysis.result.status === "available") return <Badge tone="success">Oportunidade</Badge>;
  return null;
}

function Analyzing({ label }: { label: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex items-center gap-3 rounded-[14px] border border-[color:var(--ft-border)] bg-white/[0.025] p-4 text-[length:clamp(12px,2.8cqi,14px)] text-[color:var(--ft-text-secondary)]"
    >
      <Loader2 size={18} className="flex-none animate-spin text-[color:var(--ft-purple)]" />
      {label}
    </div>
  );
}

function StateBlock({
  tone,
  title,
  body,
  list,
  action,
}: {
  tone: "neutral" | "warning" | "danger";
  title: string;
  body: string;
  list?: string[];
  action?: React.ReactNode;
}) {
  const accent = {
    neutral: "var(--ft-border)",
    warning: "var(--ft-warning)",
    danger: "var(--ft-danger)",
  }[tone];

  return (
    <div
      className="flex flex-col items-start gap-3 rounded-[14px] border bg-white/[0.025] p-4"
      style={{ borderColor: accent }}
    >
      <p className="m-0 flex items-center gap-2 text-[length:clamp(13px,3cqi,15px)] font-semibold">
        {tone !== "neutral" && <AlertTriangle size={16} style={{ color: accent }} className="flex-none" />}
        {title}
      </p>
      <p className="m-0 text-[length:clamp(12px,2.8cqi,14px)] leading-relaxed text-[color:var(--ft-text-secondary)]">
        {body}
      </p>
      {list && list.length > 0 && (
        <ul className="m-0 flex list-disc flex-col gap-1 pl-5 text-[length:clamp(12px,2.8cqi,14px)] text-[color:var(--ft-text-secondary)]">
          {list.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
      {action}
    </div>
  );
}

function Impact({ label, value, tone }: { label: string; value: string; tone?: "positive" }) {
  return (
    <div className="min-w-0 rounded-[12px] border border-[color:var(--ft-border)] bg-white/[0.02] px-3 py-2.5">
      <dt className="m-0 text-[length:clamp(10px,2.3cqi,11px)] tracking-wide text-[color:var(--ft-text-secondary)] uppercase">
        {label}
      </dt>
      <dd
        className="m-0 mt-1 text-[length:clamp(14px,3.4cqi,17px)] font-semibold"
        style={tone === "positive" ? { color: "var(--ft-primary)" } : undefined}
      >
        {value}
      </dd>
    </div>
  );
}

function StaleNotice({ onRecalculate, busy }: { onRecalculate: () => void; busy: boolean }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-[12px] border border-[color:var(--ft-warning)] bg-[color:var(--ft-warning-soft)] px-3 py-2.5">
      <p className="m-0 text-[length:clamp(12px,2.7cqi,13px)] text-[color:var(--ft-text-secondary)]">
        Esta recomendação foi gerada com dados anteriores. Recalcule antes de aprovar.
      </p>
      <Button variant="outline" size="sm" onClick={onRecalculate} disabled={busy}>
        <RefreshCw size={14} />
        Recalcular
      </Button>
    </div>
  );
}

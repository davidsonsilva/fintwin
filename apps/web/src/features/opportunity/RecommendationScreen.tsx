"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import {
  AlertTriangle,
  ArrowLeft,
  Check,
  Loader2,
  RefreshCw,
  ShieldCheck,
  SlidersHorizontal,
  X,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Badge } from "@/design-system/components/Badge";
import { Button as LinkButton } from "@/components/ui/button";
import { Button } from "@/design-system/components/Button";
import { Card } from "@/design-system/components/Card";

import { opportunityApi } from "./api";
import { formatDateTime, formatMoney, formatMonthCount, formatMonths, formatPercent, formatPeriod } from "./format";
import {
  SCENARIO_HINTS,
  SCENARIO_LABELS,
  SCENARIO_ORDER,
  type OpportunityScenarioDto,
  type ScenarioKey,
} from "./types";

/*
 * Tela da recomendação. Ela lê um snapshot versionado por `analysisId` e nunca
 * recalcula sozinha: o usuário decide sobre exatamente os números que está
 * vendo. Se os dados financeiros mudarem depois, aparece o aviso de defasagem
 * e o recálculo passa a ser um ato explícito — que gera outra análise, com id
 * próprio, sem apagar esta.
 */
export function RecommendationScreen({
  profileId,
  analysisId,
}: {
  profileId: string;
  analysisId: string;
}) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [selectedKey, setSelectedKey] = useState<ScenarioKey | null>(null);
  const [simulating, setSimulating] = useState(false);
  const [customPct, setCustomPct] = useState("");

  const query = useQuery({
    queryKey: ["opportunity-analysis", analysisId],
    queryFn: () => opportunityApi.get(analysisId),
    retry: false,
  });

  const decide = useMutation({
    mutationFn: (decision: "approved" | "rejected") =>
      opportunityApi.decide(analysisId, decision, decision === "approved" ? selected?.key : undefined),
    onSuccess: (updated) => {
      queryClient.setQueryData(["opportunity-analysis", analysisId], updated);
      queryClient.invalidateQueries({ queryKey: ["opportunity-latest", profileId] });
    },
  });

  const recalc = useMutation({
    mutationFn: (pct?: string) => opportunityApi.create(profileId, pct),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ["opportunity-latest", profileId] });
      router.push(`/dashboard/${profileId}/recomendacoes/${created.analysis_id}`);
    },
  });

  const analysis = query.data;
  const result = analysis?.result;

  const scenarios = useMemo(() => {
    if (!result) return [];
    return [...result.scenarios].sort(
      (a, b) => SCENARIO_ORDER.indexOf(a.key) - SCENARIO_ORDER.indexOf(b.key)
    );
  }, [result]);

  // O cenário recomendado é o padrão; trocar de cenário não perde o original,
  // que continua na lista e volta com um clique.
  const selected =
    scenarios.find((item) => item.key === selectedKey) ?? result?.recommended ?? scenarios[0] ?? null;

  const busy = decide.isPending || recalc.isPending;

  if (query.isLoading) {
    return (
      <StatusPage
        icon={<Loader2 size={22} className="animate-spin text-[color:var(--ft-purple)]" />}
        title="Analisando seus dados"
        body="Carregando o resultado da análise."
      />
    );
  }

  if (query.isError || !analysis || !result) {
    return (
      <StatusPage
        tone="danger"
        icon={<AlertTriangle size={22} className="text-[color:var(--ft-danger)]" />}
        title="Não foi possível abrir esta análise"
        body="O resultado pode ter sido removido ou o motor não respondeu."
        action={
          <LinkButton variant="outline" nativeButton={false} render={<Link href={`/dashboard/${profileId}`}>Voltar ao dashboard</Link>} />
        }
      />
    );
  }

  if (result.status !== "available" || !selected) {
    return (
      <StatusPage
        tone={result.status === "insufficient_data" ? "warning" : "neutral"}
        icon={<ShieldCheck size={22} className="text-[color:var(--ft-text-secondary)]" />}
        title={
          result.status === "insufficient_data"
            ? "Dados insuficientes para recomendar"
            : "Nenhuma ação necessária agora"
        }
        body={result.reason ?? ""}
        list={result.missing_data}
        action={
          <LinkButton variant="outline" nativeButton={false} render={<Link href={`/dashboard/${profileId}`}>Voltar ao dashboard</Link>} />
        }
      />
    );
  }

  const decided = analysis.decision !== "pending";

  return (
    /* `pb-28` reserva a faixa da barra fixa: sem isso o último bloco fica
       coberto por ela em telas curtas. */
    <div className="ft-section flex flex-col gap-6 pb-28">
      {/* 1. Cabeçalho */}
      <header className="flex flex-col gap-3">
        <Link
          href={`/dashboard/${profileId}`}
          className="flex w-fit items-center gap-2 text-[13px] text-[color:var(--ft-text-secondary)] hover:text-[color:var(--ft-text-primary)]"
        >
          <ArrowLeft size={15} />
          Voltar ao dashboard
        </Link>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="m-0 text-[length:clamp(20px,4vw,28px)] leading-tight font-semibold">
            Recomendação do seu Gêmeo Financeiro
          </h1>
          {analysis.stale && <Badge tone="warning">Desatualizada</Badge>}
          {analysis.decision === "approved" && <Badge tone="success">Plano aprovado</Badge>}
          {analysis.decision === "rejected" && <Badge tone="neutral">Rejeitada</Badge>}
        </div>
        <p className="m-0 text-[13px] text-[color:var(--ft-text-secondary)]">
          Análise de {formatDateTime(analysis.generated_at)} · cenário {analysis.scenario === "probable" ? "provável" : analysis.scenario} ·
          referência <code className="text-[12px]">{analysis.analysis_id.slice(0, 8)}</code>
        </p>
      </header>

      {analysis.stale && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-[14px] border border-[color:var(--ft-warning)] bg-[color:var(--ft-warning-soft)] px-4 py-3">
          <p className="m-0 text-[13px] text-[color:var(--ft-text-primary)]">
            Esta recomendação foi gerada com dados anteriores. Recalcule antes de aprovar.
          </p>
          <Button variant="outline" onClick={() => recalc.mutate(undefined)} disabled={busy}>
            <RefreshCw size={15} />
            Recalcular agora
          </Button>
        </div>
      )}

      {/* 2. Recomendação principal */}
      <Card.Root className="h-auto">
        <Card.Content className="flex flex-none flex-col gap-3 py-6">
          <p className="m-0 text-[11px] font-semibold tracking-[0.08em] text-[color:var(--ft-purple)] uppercase">
            {SCENARIO_LABELS[selected.key]}
          </p>
          <h2 className="m-0 text-[length:clamp(19px,3.4vw,26px)] leading-snug font-semibold">
            Aumente temporariamente seu aporte mensal em {formatPercent(selected.additional_pct)}
          </h2>
          <p className="m-0 text-[length:clamp(14px,2.4vw,17px)] leading-relaxed text-[color:var(--ft-text-secondary)]">
            Direcione <strong className="text-[color:var(--ft-text-primary)]">{formatMoney(selected.additional_amount)}</strong>{" "}
            adicionais por mês para{" "}
            <strong className="text-[color:var(--ft-text-primary)]">“{result.goal_description}”</strong> durante{" "}
            <strong className="text-[color:var(--ft-text-primary)]">{formatMonthCount(selected.months_to_goal)}</strong>.
          </p>
        </Card.Content>
      </Card.Root>

      {/* 3. Impacto resumido */}
      <section className="grid grid-cols-[repeat(auto-fit,minmax(170px,1fr))] gap-4">
        <Metric
          label="Meta antecipada em"
          value={formatMonthCount(selected.months_saved)}
          tone="positive"
        />
        <Metric label="Autonomia atual" value={formatMonths(result.reserve_months)} />
        <Metric label="Autonomia após a ação" value={formatMonths(selected.autonomy_months_after)} />
        <Metric label="Sobra mensal restante" value={formatMoney(selected.monthly_surplus_after)} />
        <Metric
          label="Risco projetado"
          value={selected.safe ? "Baixo" : "Atenção"}
          tone={selected.safe ? "positive" : "warning"}
        />
      </section>

      {/* 4. Antes e depois */}
      <Card.Root className="h-auto">
        <Card.Header className="ft-card-header" title={<h3 className="ft-card-title">Antes e depois</h3>} />
        <Card.Content className="flex flex-none flex-col gap-4 pb-6">
          <div className="grid gap-4 [@media(min-width:640px)]:grid-cols-2">
            <ComparisonColumn
              title="Hoje"
              rows={[
                ["Aporte mensal", formatMoney(result.current_contribution)],
                ["Conclusão prevista", formatPeriod(result.baseline_completion)],
                ["Prazo restante", formatMonthCount(result.baseline_months_to_goal)],
                ["Autonomia", formatMonths(result.reserve_months)],
              ]}
            />
            <ComparisonColumn
              title="Com a recomendação"
              highlight
              rows={[
                ["Aporte mensal", formatMoney(selected.new_monthly_contribution)],
                ["Conclusão prevista", formatPeriod(selected.projected_completion)],
                ["Prazo restante", formatMonthCount(selected.months_to_goal)],
                ["Autonomia", formatMonths(selected.autonomy_months_after)],
              ]}
            />
          </div>
        </Card.Content>
      </Card.Root>

      {/* 5. Cenários */}
      <Card.Root className="h-auto">
        <Card.Header
          className="ft-card-header"
          title={<h3 className="ft-card-title">Cenários</h3>}
        />
        <Card.Content className="flex flex-none flex-col gap-3 pb-6">
          <p className="m-0 text-[13px] text-[color:var(--ft-text-secondary)]">
            Trocar de cenário atualiza os números acima. O resultado original continua guardado.
          </p>
          <div className="grid gap-3 [@media(min-width:760px)]:grid-cols-3">
            {scenarios.map((scenario) => (
              <ScenarioOption
                key={scenario.key}
                scenario={scenario}
                active={scenario.key === selected.key}
                isOriginal={scenario.key === result.recommended?.key}
                onSelect={() => setSelectedKey(scenario.key)}
              />
            ))}
          </div>
        </Card.Content>
      </Card.Root>

      {/* 6. Por que o FinTwin recomenda isso */}
      <Card.Root className="h-auto">
        <Card.Header
          className="ft-card-header"
          title={<h3 className="ft-card-title">Por que o FinTwin recomenda isso</h3>}
        />
        <Card.Content className="flex flex-none flex-col gap-5 pb-6">
          <dl className="m-0 grid grid-cols-[repeat(auto-fit,minmax(190px,1fr))] gap-3">
            {result.evidence.map((item) => (
              <div
                key={item.key}
                className="min-w-0 rounded-[12px] border border-[color:var(--ft-border)] bg-white/[0.02] px-3 py-2.5"
              >
                <dt className="m-0 text-[11px] text-[color:var(--ft-text-secondary)]">{item.label}</dt>
                <dd className="m-0 mt-1 text-[15px] font-semibold">
                  {item.money
                    ? formatMoney(item.money)
                    : item.percentage !== null
                      ? formatPercent(item.percentage, 1)
                      : item.months !== null
                        ? formatMonths(item.months)
                        : (item.text ?? "—")}
                </dd>
              </div>
            ))}
          </dl>

          <div>
            <h4 className="m-0 mb-2 text-[13px] font-semibold">Origem sugerida do dinheiro</h4>
            <ul className="m-0 flex list-none flex-col gap-2 p-0">
              {result.funding_sources.map((source) => (
                <li
                  key={source.label}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-[10px] border border-[color:var(--ft-border)] px-3 py-2 text-[13px]"
                >
                  <span className="text-[color:var(--ft-text-secondary)]">{source.label}</span>
                  <span className="font-semibold">{formatMoney(source.amount)}</span>
                </li>
              ))}
            </ul>
            <p className="m-0 mt-2 text-[12px] text-[color:var(--ft-text-secondary)]">
              Nenhuma despesa essencial entra como origem do dinheiro.
            </p>
          </div>

          <div>
            <h4 className="m-0 mb-2 text-[13px] font-semibold">Premissas usadas</h4>
            <ul className="m-0 flex list-disc flex-col gap-1.5 pl-5 text-[13px] leading-relaxed text-[color:var(--ft-text-secondary)]">
              {result.assumptions.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </Card.Content>
      </Card.Root>

      {/* 7. Riscos e limitações */}
      <Card.Root className="h-auto">
        <Card.Header
          className="ft-card-header"
          title={<h3 className="ft-card-title">Riscos e limitações</h3>}
        />
        <Card.Content className="flex flex-none flex-col gap-3 pb-6">
          <ul className="m-0 flex list-none flex-col gap-2 p-0">
            {[...selected.risks, ...result.risks].map((risk) => (
              <li key={risk} className="flex items-start gap-2 text-[13px] leading-relaxed text-[color:var(--ft-text-secondary)]">
                <AlertTriangle size={15} className="mt-0.5 flex-none text-[color:var(--ft-warning)]" />
                {risk}
              </li>
            ))}
          </ul>
          <p className="m-0 text-[12px] leading-relaxed text-[color:var(--ft-text-secondary)]">
            A recomendação perde validade se surgir despesa inesperada, se a renda cair ou se houver
            obrigação futura ainda não cadastrada no FinTwin.
          </p>
        </Card.Content>
      </Card.Root>

      {/* Simular outro valor: gera uma análise nova, com id próprio. */}
      {simulating && (
        <Card.Root className="h-auto">
          <Card.Content className="flex flex-none flex-wrap items-end gap-3 py-5">
            <label className="flex flex-col gap-1.5 text-[13px]">
              <span className="text-[color:var(--ft-text-secondary)]">Percentual da renda a aportar a mais</span>
              <input
                type="number"
                min={1}
                max={100}
                step={1}
                value={customPct}
                onChange={(event) => setCustomPct(event.target.value)}
                placeholder="Ex.: 7"
                className="h-10 w-32 rounded-[10px] border border-[color:var(--ft-border)] bg-white/[0.03] px-3 text-[color:var(--ft-text-primary)]"
              />
            </label>
            <Button
              onClick={() => recalc.mutate((Number(customPct) / 100).toString())}
              disabled={busy || !customPct || Number(customPct) <= 0}
            >
              {recalc.isPending ? <Loader2 size={16} className="animate-spin" /> : <SlidersHorizontal size={16} />}
              Simular
            </Button>
            <Button variant="outline" onClick={() => setSimulating(false)} disabled={busy}>
              Cancelar
            </Button>
          </Card.Content>
        </Card.Root>
      )}

      {decide.isError && (
        <p className="m-0 text-[13px] text-[color:var(--ft-danger)]">
          Não foi possível registrar sua decisão. Tente novamente.
        </p>
      )}

      {/* 8. Ações finais */}
      <div className="fixed inset-x-0 bottom-0 z-30 border-t border-[color:var(--ft-border)] bg-[color:var(--ft-bg-page)]/95 px-4 py-3 backdrop-blur [@media(min-width:1024px)]:left-[var(--ft-sidebar-width)]">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3">
          <p className="m-0 text-[12px] text-[color:var(--ft-text-secondary)]">
            {decided
              ? `Decisão registrada em ${formatDateTime(analysis.decided_at!)}.`
              : "Aprovar registra o plano no FinTwin. Nenhum dinheiro é movimentado."}
          </p>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={() => decide.mutate("rejected")} disabled={busy || decided}>
              <X size={16} />
              Rejeitar
            </Button>
            <Button variant="secondary" onClick={() => setSimulating(true)} disabled={busy}>
              <SlidersHorizontal size={16} />
              Simular outro valor
            </Button>
            <Button onClick={() => decide.mutate("approved")} disabled={busy || decided}>
              {decide.isPending ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}
              Aprovar plano
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Metric({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "positive" | "warning";
}) {
  const color =
    tone === "positive" ? "var(--ft-primary)" : tone === "warning" ? "var(--ft-warning)" : undefined;
  return (
    <div className="min-w-0 rounded-[14px] border border-[color:var(--ft-border)] bg-white/[0.025] px-4 py-3">
      <p className="m-0 text-[11px] tracking-wide text-[color:var(--ft-text-secondary)] uppercase">{label}</p>
      <p className="m-0 mt-1.5 text-[length:clamp(16px,2.6vw,20px)] font-semibold" style={{ color }}>
        {value}
      </p>
    </div>
  );
}

function ComparisonColumn({
  title,
  rows,
  highlight,
}: {
  title: string;
  rows: [string, string][];
  highlight?: boolean;
}) {
  return (
    <div
      className="rounded-[14px] border p-4"
      style={{
        borderColor: highlight ? "var(--ft-primary)" : "var(--ft-border)",
        background: highlight ? "rgba(49,230,174,0.05)" : "rgba(255,255,255,0.02)",
      }}
    >
      <p className="m-0 mb-3 text-[13px] font-semibold">{title}</p>
      <dl className="m-0 flex flex-col gap-2">
        {rows.map(([label, value]) => (
          <div key={label} className="flex flex-wrap items-baseline justify-between gap-2">
            <dt className="m-0 text-[12px] text-[color:var(--ft-text-secondary)]">{label}</dt>
            <dd className="m-0 text-[14px] font-semibold">{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function ScenarioOption({
  scenario,
  active,
  isOriginal,
  onSelect,
}: {
  scenario: OpportunityScenarioDto;
  active: boolean;
  isOriginal: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={active}
      className="flex min-w-0 cursor-pointer flex-col gap-1.5 rounded-[14px] border p-4 text-left transition-colors"
      style={{
        borderColor: active ? "var(--ft-primary)" : "var(--ft-border)",
        background: active ? "rgba(49,230,174,0.06)" : "rgba(255,255,255,0.02)",
      }}
    >
      <span className="flex flex-wrap items-center gap-2 text-[14px] font-semibold">
        {SCENARIO_LABELS[scenario.key]}
        {isOriginal && <Badge tone="success">Original</Badge>}
        {!scenario.safe && <Badge tone="warning">Atenção</Badge>}
      </span>
      <span className="text-[19px] font-semibold text-[color:var(--ft-primary)]">
        +{formatPercent(scenario.additional_pct)}
      </span>
      <span className="text-[13px] text-[color:var(--ft-text-secondary)]">
        {formatMoney(scenario.additional_amount)} por mês · conclusão em{" "}
        {formatPeriod(scenario.projected_completion)}
      </span>
      <span className="text-[12px] text-[color:var(--ft-text-secondary)]">
        {SCENARIO_HINTS[scenario.key]}
      </span>
    </button>
  );
}

function StatusPage({
  icon,
  title,
  body,
  list,
  action,
  tone,
}: {
  icon: React.ReactNode;
  title: string;
  body: string;
  list?: string[];
  action?: React.ReactNode;
  tone?: "neutral" | "warning" | "danger";
}) {
  const accent =
    tone === "danger" ? "var(--ft-danger)" : tone === "warning" ? "var(--ft-warning)" : "var(--ft-border)";
  return (
    <div className="ft-section flex flex-col gap-6 pb-8">
      <div
        className="flex flex-col items-start gap-3 rounded-[16px] border bg-white/[0.025] p-6"
        style={{ borderColor: accent }}
      >
        <span className="flex items-center gap-3 text-[length:clamp(17px,3vw,21px)] font-semibold">
          {icon}
          {title}
        </span>
        {body && (
          <p className="m-0 max-w-prose text-[14px] leading-relaxed text-[color:var(--ft-text-secondary)]">
            {body}
          </p>
        )}
        {list && list.length > 0 && (
          <ul className="m-0 flex list-disc flex-col gap-1 pl-5 text-[14px] text-[color:var(--ft-text-secondary)]">
            {list.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        )}
        {action}
      </div>
    </div>
  );
}

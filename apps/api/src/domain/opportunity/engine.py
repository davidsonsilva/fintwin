# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Motor de oportunidade financeira proativa, puro e determinístico.

A pergunta que ele responde: *existe folga recorrente que possa acelerar a meta
principal sem derrubar a reserva, as despesas essenciais ou o fluxo de caixa?*

Ele não inventa nenhum número. O percentual sugerido sai da sobra recorrente
real do perfil, e o efeito de cada cenário é medido reexecutando o motor de
projeção da VS-04 com o aporte alterado — não com uma fórmula paralela.

Os portões de segurança reaproveitam os limiares já definidos no Radar de
Fragilidade (Spec seção 11), para que "faixa saudável" signifique aqui a mesma
coisa que significa lá.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from typing import Optional

from src.domain.cashflow.entities import FinancialEvent
from src.domain.decisions.entities import FinancialGoal
from src.domain.financial_profile.entities import FinancialAccount
from src.domain.obligations.entities import Debt, FinancialObligation, IncomeSource
from src.domain.opportunity.entities import (
    EvidenceItem,
    FundingSource,
    OpportunityResult,
    OpportunityScenario,
    OpportunityStatus,
    ScenarioKey,
)
from src.domain.projection.engine import project_cashflow
from src.domain.projection.scenario import ScenarioParameters
from src.domain.shared.enums import Direction, IncomeStability
from src.domain.shared.money import Money
from src.domain.shared.percentage import Percentage
from src.domain.shared.recurrence import monthly_equivalent

# --- Política do motor ------------------------------------------------------
# Constantes de política, não valores de recomendação: elas definem o quão
# conservador o motor é, e todas aparecem em `assumptions` no resultado.

#: Piso de reserva, em meses de despesa essencial. Mesmo limiar da regra
#: RESERVE_BELOW_THREE_MONTHS do Radar de Fragilidade.
RESERVE_FLOOR_MONTHS = Decimal("3")

#: Teto de despesas essenciais sobre a renda (regra ESSENTIAL_EXPENSE_RATIO).
ESSENTIAL_RATIO_CEILING = Decimal("0.60")

#: Quanto da sobra recorrente pode virar compromisso mensal novo. Os 40%
#: restantes continuam livres, para o aporte não consumir toda a folga.
SURPLUS_ALLOCATION_RATIO = Decimal("0.60")

#: Teto do aporte adicional sobre a renda mensal, independente da sobra.
MAX_ADDITIONAL_INCOME_PCT = Decimal("0.15")

#: Abaixo disso o aporte não muda nada de material e não vale recomendar.
MIN_ADDITIONAL_INCOME_PCT = Decimal("0.01")

#: Cenários alternativos, como múltiplos do percentual recomendado.
CONSERVATIVE_FACTOR = Decimal("0.4")
ACCELERATED_FACTOR = Decimal("1.6")

#: Horizonte usado tanto na linha de base quanto em cada cenário.
PROJECTION_HORIZON_MONTHS = 12

#: Janela em que eventos futuros de saída entram na lista de riscos.
RISK_EVENT_WINDOW_MONTHS = 6

_PERCENT_STEP = Decimal("0.01")  # 1 ponto percentual
_MONTHS_QUANTUM = Decimal("0.1")


def _sum_money(currency: str, values: list[Money]) -> Money:
    total = Money(Decimal("0"), currency)
    for value in values:
        total = total.add(value)
    return total


def _monthly_total(currency: str, items, amount_of, frequency_of) -> Money:
    monthly = [
        value
        for item in items
        if (value := monthly_equivalent(amount_of(item), frequency_of(item))) is not None
    ]
    return _sum_money(currency, monthly)


def _floor_to_step(fraction: Decimal) -> Decimal:
    """Arredonda para baixo em passos de 1 ponto percentual.

    Para baixo de propósito: entre errar sugerindo mais e errar sugerindo
    menos, o motor erra para o lado que não cria risco.
    """
    return (fraction / _PERCENT_STEP).to_integral_value(rounding=ROUND_FLOOR) * _PERCENT_STEP


def _add_months(reference: date, months: int) -> str:
    total = reference.year * 12 + (reference.month - 1) + months
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def _months_to_goal(remaining: Money, contribution: Money) -> Optional[Decimal]:
    if contribution.amount <= 0 or remaining.amount <= 0:
        return None
    return (remaining.amount / contribution.amount).to_integral_value(rounding=ROUND_CEILING)


def _quantize_months(value: Optional[Decimal]) -> Optional[Decimal]:
    return None if value is None else value.quantize(_MONTHS_QUANTUM)


def _insufficient(currency: str, now: datetime, missing: list[str]) -> OpportunityResult:
    return OpportunityResult(
        status=OpportunityStatus.INSUFFICIENT_DATA,
        currency=currency,
        generated_at=now,
        missing_data=missing,
        reason="Não há dados suficientes para analisar oportunidades com segurança.",
    )


def analyze_opportunity(
    accounts: list[FinancialAccount],
    incomes: list[IncomeSource],
    obligations: list[FinancialObligation],
    debts: list[Debt],
    goals: list[FinancialGoal],
    events: list[FinancialEvent],
    currency: str,
    today: Optional[date] = None,
    now: Optional[datetime] = None,
    custom_pct: Optional[Decimal] = None,
) -> OpportunityResult:
    today = today or date.today()
    now = now or datetime.utcnow()
    zero = Money(Decimal("0"), currency)

    # --- 1. Dados suficientes? ---------------------------------------------
    monthly_income = _monthly_total(currency, incomes, lambda i: i.amount, lambda i: i.frequency)
    essential_obligations = [o for o in obligations if o.essential]
    essential_monthly = _monthly_total(
        currency, essential_obligations, lambda o: o.amount, lambda o: o.frequency
    )

    missing: list[str] = []
    if monthly_income.amount <= 0:
        missing.append("Nenhuma renda mensal recorrente cadastrada.")
    if not goals:
        missing.append("Nenhuma meta financeira cadastrada.")
    if essential_monthly.amount <= 0:
        missing.append("Nenhuma despesa essencial cadastrada — sem ela não dá para medir a reserva.")
    if missing:
        return _insufficient(currency, now, missing)

    # --- 2. Diagnóstico -----------------------------------------------------
    monthly_obligations = _monthly_total(currency, obligations, lambda o: o.amount, lambda o: o.frequency)
    debt_service = _sum_money(
        currency, [d.installment_amount for d in debts if d.remaining_installments > 0]
    )
    goal_contributions = _sum_money(currency, [g.monthly_contribution for g in goals])
    eligible_assets = _sum_money(
        currency, [a.balance for a in accounts if a.eligible_for_autonomy]
    )

    # Sobra *recorrente*: só o que se repete todo mês. Eventos pontuais ficam
    # de fora aqui de propósito — eles entram como risco e pela projeção, não
    # como base de um compromisso mensal permanente.
    recurring_surplus = (
        monthly_income.subtract(monthly_obligations).subtract(debt_service).subtract(goal_contributions)
    )
    income_commitment = Percentage(
        min(monthly_obligations.amount / monthly_income.amount, Decimal("1"))
    )
    essential_ratio = essential_monthly.amount / monthly_income.amount
    reserve_months = eligible_assets.amount / essential_monthly.amount

    main_goal = min(goals, key=lambda goal: goal.priority)
    goal_remaining = main_goal.target_amount.subtract(main_goal.current_amount)
    baseline_months = _months_to_goal(goal_remaining, main_goal.monthly_contribution)

    baseline = project_cashflow(
        accounts=accounts,
        incomes=incomes,
        obligations=obligations,
        debts=debts,
        goals=goals,
        events=events,
        horizon_months=PROJECTION_HORIZON_MONTHS,
        scenario=ScenarioParameters.probable(currency),
        currency=currency,
        today=today,
    )

    def _partial(status: OpportunityStatus, reason: str) -> OpportunityResult:
        """Resultado sem recomendação, mas com o diagnóstico completo.

        O usuário merece saber *por que* não há sugestão, e com quais números —
        um card mudo é pior que nenhum card.
        """
        return OpportunityResult(
            status=status,
            currency=currency,
            generated_at=now,
            reason=reason,
            monthly_income=monthly_income,
            monthly_obligations=monthly_obligations,
            income_commitment=income_commitment,
            essential_expenses_monthly=essential_monthly,
            recurring_surplus=recurring_surplus,
            reserve_months=_quantize_months(reserve_months),
            goal_description=main_goal.description,
            goal_target=main_goal.target_amount,
            goal_current=main_goal.current_amount,
            current_contribution=main_goal.monthly_contribution,
            current_contribution_pct=Percentage(
                min(main_goal.monthly_contribution.amount / monthly_income.amount, Decimal("1"))
            ),
            baseline_months_to_goal=baseline_months,
            baseline_completion=(
                _add_months(today, int(baseline_months)) if baseline_months is not None else None
            ),
            evidence=_build_evidence(
                monthly_income,
                monthly_obligations,
                income_commitment,
                essential_monthly,
                recurring_surplus,
                eligible_assets,
                reserve_months,
                main_goal,
                baseline,
            ),
            assumptions=_build_assumptions(),
        )

    # --- 3. Portões de segurança -------------------------------------------
    # Ordem importa: o primeiro motivo que impede a recomendação é o que o
    # usuário vê. Da ameaça mais concreta para a mais estrutural.
    if baseline.first_deficit_period is not None:
        return _partial(
            OpportunityStatus.NO_ACTION,
            f"Há déficit projetado em {baseline.first_deficit_period}. "
            "Enquanto isso não for resolvido, acelerar a meta aumentaria o risco em vez de reduzir.",
        )
    if reserve_months < RESERVE_FLOOR_MONTHS:
        return _partial(
            OpportunityStatus.NO_ACTION,
            f"Sua reserva cobre {reserve_months.quantize(_MONTHS_QUANTUM)} meses de despesas essenciais, "
            f"abaixo do piso de {RESERVE_FLOOR_MONTHS} meses. Reforçar a reserva vem antes de acelerar metas.",
        )
    if essential_ratio > ESSENTIAL_RATIO_CEILING:
        return _partial(
            OpportunityStatus.NO_ACTION,
            f"Despesas essenciais consomem {Percentage(min(essential_ratio, Decimal('1'))).as_display_percent():.0f}% "
            "da renda, acima do limite saudável. Não há folga estrutural para um novo compromisso mensal.",
        )
    if goal_remaining.amount <= 0:
        return _partial(
            OpportunityStatus.NO_ACTION,
            f"Sua meta principal ({main_goal.description}) já foi atingida. "
            "Cadastre a próxima meta para o FinTwin voltar a procurar oportunidades.",
        )
    if recurring_surplus.amount <= 0:
        return _partial(
            OpportunityStatus.NO_ACTION,
            "Não há sobra recorrente livre: a renda mensal já está inteiramente destinada a "
            "obrigações, dívidas e aos aportes atuais.",
        )

    # --- 4. Percentual recomendado -----------------------------------------
    allocatable = recurring_surplus.multiply(SURPLUS_ALLOCATION_RATIO)
    raw_pct = allocatable.amount / monthly_income.amount
    recommended_pct = _floor_to_step(min(raw_pct, MAX_ADDITIONAL_INCOME_PCT))

    if recommended_pct < MIN_ADDITIONAL_INCOME_PCT:
        return _partial(
            OpportunityStatus.NO_ACTION,
            "A sobra recorrente existe, mas é pequena demais para virar um aporte relevante "
            "sem apertar o fluxo de caixa. Nenhuma ação é necessária agora.",
        )

    # Teto duro: nenhum cenário pode comprometer mais que a sobra recorrente inteira.
    surplus_pct_cap = _floor_to_step(recurring_surplus.amount / monthly_income.amount)

    def _scenario_pct(factor: Decimal) -> Decimal:
        value = _floor_to_step(recommended_pct * factor)
        value = min(value, surplus_pct_cap, MAX_ADDITIONAL_INCOME_PCT)
        return max(value, MIN_ADDITIONAL_INCOME_PCT)

    plan_pcts = {
        ScenarioKey.CONSERVATIVE: _scenario_pct(CONSERVATIVE_FACTOR),
        ScenarioKey.RECOMMENDED: recommended_pct,
        ScenarioKey.ACCELERATED: _scenario_pct(ACCELERATED_FACTOR),
    }

    # "Simular outro valor": o percentual do usuário entra como mais um cenário,
    # calculado pelas mesmas regras. Ele não é filtrado nem corrigido — se for
    # inseguro, os riscos do cenário dizem isso e `safe` fica falso.
    if custom_pct is not None:
        plan_pcts[ScenarioKey.CUSTOM] = _floor_to_step(custom_pct)

    baseline_burn = baseline.periods[0].expense_total

    scenarios = [
        _build_scenario(
            key=key,
            pct=pct,
            monthly_income=monthly_income,
            main_goal=main_goal,
            goal_remaining=goal_remaining,
            baseline_months=baseline_months,
            recurring_surplus=recurring_surplus,
            eligible_assets=eligible_assets,
            baseline_burn=baseline_burn,
            accounts=accounts,
            incomes=incomes,
            obligations=obligations,
            debts=debts,
            goals=goals,
            events=events,
            currency=currency,
            today=today,
        )
        for key, pct in plan_pcts.items()
    ]
    recommended = next(s for s in scenarios if s.key == ScenarioKey.RECOMMENDED)

    return OpportunityResult(
        status=OpportunityStatus.AVAILABLE,
        currency=currency,
        generated_at=now,
        monthly_income=monthly_income,
        monthly_obligations=monthly_obligations,
        income_commitment=income_commitment,
        essential_expenses_monthly=essential_monthly,
        recurring_surplus=recurring_surplus,
        reserve_months=_quantize_months(reserve_months),
        goal_description=main_goal.description,
        goal_target=main_goal.target_amount,
        goal_current=main_goal.current_amount,
        current_contribution=main_goal.monthly_contribution,
        current_contribution_pct=Percentage(
            min(main_goal.monthly_contribution.amount / monthly_income.amount, Decimal("1"))
        ),
        baseline_months_to_goal=baseline_months,
        baseline_completion=(
            _add_months(today, int(baseline_months)) if baseline_months is not None else None
        ),
        recommended=recommended,
        scenarios=scenarios,
        funding_sources=_build_funding_sources(recurring_surplus, obligations, zero),
        evidence=_build_evidence(
            monthly_income,
            monthly_obligations,
            income_commitment,
            essential_monthly,
            recurring_surplus,
            eligible_assets,
            reserve_months,
            main_goal,
            baseline,
        ),
        risks=_build_risks(incomes, events, recommended, today, currency),
        assumptions=_build_assumptions(),
    )


def _build_scenario(
    *,
    key: ScenarioKey,
    pct: Decimal,
    monthly_income: Money,
    main_goal: FinancialGoal,
    goal_remaining: Money,
    baseline_months: Optional[Decimal],
    recurring_surplus: Money,
    eligible_assets: Money,
    baseline_burn: Money,
    accounts: list[FinancialAccount],
    incomes: list[IncomeSource],
    obligations: list[FinancialObligation],
    debts: list[Debt],
    goals: list[FinancialGoal],
    events: list[FinancialEvent],
    currency: str,
    today: date,
) -> OpportunityScenario:
    additional = monthly_income.multiply(pct)
    new_contribution = main_goal.monthly_contribution.add(additional)

    # O efeito no caixa vem de reexecutar o motor de projeção com a meta
    # principal recebendo o aporte maior — nunca de uma fórmula paralela.
    simulated_goals = [
        FinancialGoal(
            id=goal.id,
            profile_id=goal.profile_id,
            description=goal.description,
            target_amount=goal.target_amount,
            current_amount=goal.current_amount,
            deadline=goal.deadline,
            priority=goal.priority,
            monthly_contribution=new_contribution if goal.id == main_goal.id else goal.monthly_contribution,
        )
        for goal in goals
    ]
    simulated = project_cashflow(
        accounts=accounts,
        incomes=incomes,
        obligations=obligations,
        debts=debts,
        goals=simulated_goals,
        events=events,
        horizon_months=PROJECTION_HORIZON_MONTHS,
        scenario=ScenarioParameters.probable(currency),
        currency=currency,
        today=today,
    )

    months = _months_to_goal(goal_remaining, new_contribution)
    months_saved = None
    if months is not None and baseline_months is not None:
        months_saved = baseline_months - months

    surplus_after = recurring_surplus.subtract(additional)
    burn_after = baseline_burn.add(additional)
    autonomy_after = (
        eligible_assets.amount / burn_after.amount if burn_after.amount > 0 else None
    )

    risks: list[str] = []
    if simulated.first_deficit_period is not None:
        risks.append(f"Passa a projetar déficit em {simulated.first_deficit_period}.")
    if surplus_after.amount < 0:
        risks.append("O aporte ultrapassa a sobra recorrente e o mês fecha negativo.")
    if autonomy_after is not None and autonomy_after < RESERVE_FLOOR_MONTHS:
        risks.append(
            f"A autonomia provável cai para {autonomy_after.quantize(_MONTHS_QUANTUM)} meses, "
            f"abaixo do piso de {RESERVE_FLOOR_MONTHS} meses."
        )
    if simulated.lowest_balance.is_negative():
        risks.append("O saldo projetado fica negativo em algum mês do horizonte.")

    return OpportunityScenario(
        key=key,
        additional_pct=Percentage(pct),
        additional_amount=additional,
        new_monthly_contribution=new_contribution,
        months_to_goal=months,
        months_saved=months_saved,
        projected_completion=_add_months(today, int(months)) if months is not None else None,
        monthly_surplus_after=surplus_after,
        autonomy_months_after=_quantize_months(autonomy_after),
        first_deficit_period=simulated.first_deficit_period,
        lowest_balance=simulated.lowest_balance,
        safe=not risks,
        risks=risks,
    )


def _build_funding_sources(
    recurring_surplus: Money,
    obligations: list[FinancialObligation],
    zero: Money,
) -> list[FundingSource]:
    """De onde o dinheiro sai — nunca de despesa essencial.

    Além da sobra livre, aponta as três maiores categorias não essenciais como
    folga negociável. Elas são candidatas, não cortes decididos pelo motor.
    """
    sources = [
        FundingSource(
            label="Saldo mensal não comprometido",
            amount=recurring_surplus,
            essential=False,
        )
    ]

    by_category: dict[str, Money] = {}
    for obligation in obligations:
        if obligation.essential:
            continue
        monthly = monthly_equivalent(obligation.amount, obligation.frequency)
        if monthly is None:
            continue
        by_category[obligation.category] = by_category.get(obligation.category, zero).add(monthly)

    top = sorted(by_category.items(), key=lambda item: item[1].amount, reverse=True)[:3]
    sources.extend(
        FundingSource(label=f"Categoria não essencial: {category}", amount=amount, essential=False)
        for category, amount in top
    )
    return sources


def _build_evidence(
    monthly_income: Money,
    monthly_obligations: Money,
    income_commitment: Percentage,
    essential_monthly: Money,
    recurring_surplus: Money,
    eligible_assets: Money,
    reserve_months: Decimal,
    main_goal: FinancialGoal,
    baseline,
) -> list[EvidenceItem]:
    return [
        EvidenceItem(key="monthly_income", label="Renda mensal recorrente", money=monthly_income),
        EvidenceItem(key="monthly_obligations", label="Obrigações mensais", money=monthly_obligations),
        EvidenceItem(key="income_commitment", label="Comprometimento da renda", percentage=income_commitment),
        EvidenceItem(key="essential_expenses", label="Despesas essenciais", money=essential_monthly),
        EvidenceItem(key="recurring_surplus", label="Sobra recorrente não destinada", money=recurring_surplus),
        EvidenceItem(key="eligible_assets", label="Reserva elegível", money=eligible_assets),
        EvidenceItem(key="reserve_months", label="Reserva em meses de essenciais", months=_quantize_months(reserve_months)),
        EvidenceItem(key="goal_target", label=f"Meta principal: {main_goal.description}", money=main_goal.target_amount),
        EvidenceItem(key="goal_current", label="Já acumulado na meta", money=main_goal.current_amount),
        EvidenceItem(key="goal_contribution", label="Aporte mensal atual", money=main_goal.monthly_contribution),
        EvidenceItem(
            key="first_deficit",
            label="Primeiro déficit projetado (12 meses)",
            text=baseline.first_deficit_period or "Nenhum",
        ),
        EvidenceItem(key="lowest_balance", label="Menor saldo projetado (12 meses)", money=baseline.lowest_balance),
    ]


def _build_risks(
    incomes: list[IncomeSource],
    events: list[FinancialEvent],
    recommended: OpportunityScenario,
    today: date,
    currency: str,
) -> list[str]:
    risks: list[str] = []

    variable = [i for i in incomes if i.stability == IncomeStability.VARIABLE]
    if variable:
        variable_total = _sum_money(
            currency,
            [
                monthly
                for income in variable
                if (monthly := monthly_equivalent(income.amount, income.frequency)) is not None
            ],
        )
        risks.append(
            f"{len(variable)} fonte(s) de renda variável somam {variable_total.amount} {currency} por mês. "
            "Uma queda nelas reduz a sobra que sustenta o aporte."
        )

    horizon_end = _add_months(today, RISK_EVENT_WINDOW_MONTHS)
    upcoming = [
        event
        for event in events
        if event.direction == Direction.EXPENSE
        and event.date >= today
        and event.date.strftime("%Y-%m") <= horizon_end
    ]
    for event in sorted(upcoming, key=lambda e: e.date)[:3]:
        risks.append(
            f"Evento previsto: {event.description} em {event.date.isoformat()}, "
            f"{event.amount.amount} {event.amount.currency} de saída."
        )

    if recommended.autonomy_months_after is not None and recommended.autonomy_months_after < Decimal("6"):
        risks.append(
            f"Com o aporte recomendado a autonomia provável fica em "
            f"{recommended.autonomy_months_after} meses."
        )

    risks.append(
        "Aprovar o plano registra a decisão para você executar. O FinTwin não movimenta dinheiro."
    )
    return risks


def _build_assumptions() -> list[str]:
    return [
        "Sobra recorrente = renda mensal − obrigações mensais − parcelas de dívida − aportes de metas. "
        "Eventos pontuais ficam de fora: eles não sustentam um compromisso mensal permanente.",
        f"No máximo {SURPLUS_ALLOCATION_RATIO * 100:.0f}% da sobra recorrente vira aporte novo; "
        "o restante continua livre.",
        f"O aporte adicional é limitado a {MAX_ADDITIONAL_INCOME_PCT * 100:.0f}% da renda mensal e "
        "arredondado para baixo em passos de 1 ponto percentual.",
        f"Nenhuma recomendação é emitida com reserva abaixo de {RESERVE_FLOOR_MONTHS} meses de despesas "
        "essenciais (mesmo limiar da regra RESERVE_BELOW_THREE_MONTHS do Radar de Fragilidade).",
        f"Nenhuma recomendação é emitida com despesas essenciais acima de "
        f"{ESSENTIAL_RATIO_CEILING * 100:.0f}% da renda (regra ESSENTIAL_EXPENSE_RATIO).",
        f"O efeito de cada cenário vem de reexecutar o motor de projeção por "
        f"{PROJECTION_HORIZON_MONTHS} meses no cenário provável, com o aporte alterado.",
        "Meta principal = a de menor `priority`. Rendimento sobre o valor aportado não é considerado.",
        "Nenhuma despesa essencial é usada como origem do dinheiro.",
    ]

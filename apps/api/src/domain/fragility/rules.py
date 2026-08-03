# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Registro estático de metadados das regras do Radar de Fragilidade (Spec seção 11).

`title`/`description`/`formula`/`threshold` são fixos por `code` — não são
recalculados nem duplicados por instância; só `evidence`, `severity` e
`detected_at` variam a cada detecção (ver `detector.py`).

A regra 6 ("aumento de despesas recorrentes por 3 períodos consecutivos") não
está neste registro: o modelo de domínio não tem despesas que escalam mês a
mês, então essa regra nunca dispararia de forma real com os dados atuais —
documentado como fora de escopo desta versão.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleDefinition:
    code: str
    title: str
    description: str
    formula: str
    threshold: str


#: Versão do conjunto de regras. Acompanha a severidade quando ela é servida
#: fora do Radar (por exemplo, na classificação de uma oportunidade da
#: conversa), para que o consumidor saiba qual régua a produziu.
RULES_VERSION = "1"


RULES: dict[str, RuleDefinition] = {
    "INCOME_CONCENTRATION": RuleDefinition(
        code="INCOME_CONCENTRATION",
        title="Renda concentrada",
        description="Mais de 80% da renda depende de uma única fonte.",
        formula="main_source_income / total_income",
        threshold="0.80",
    ),
    "ESSENTIAL_EXPENSE_RATIO": RuleDefinition(
        code="ESSENTIAL_EXPENSE_RATIO",
        title="Despesas essenciais elevadas",
        description="Despesas essenciais consomem mais de 60% da renda mensal.",
        formula="essential_expenses_monthly / total_income_monthly",
        threshold="0.60",
    ),
    "DEBT_SERVICE_RATIO": RuleDefinition(
        code="DEBT_SERVICE_RATIO",
        title="Serviço da dívida elevado",
        description="O pagamento de parcelas de dívida consome mais de 30% da renda mensal.",
        formula="debt_service_monthly / total_income_monthly",
        threshold="0.30",
    ),
    "RECURRING_CREDIT_FOR_ESSENTIALS": RuleDefinition(
        code="RECURRING_CREDIT_FOR_ESSENTIALS",
        title="Uso recorrente de crédito para despesas essenciais",
        description="Há obrigações essenciais recorrentes marcadas como relacionadas a dívida.",
        formula="existe obrigação com essential=true e debt_related=true",
        threshold="existe ao menos 1",
    ),
    "PROJECTED_RESERVE_DECLINE": RuleDefinition(
        code="PROJECTED_RESERVE_DECLINE",
        title="Tendência de queda na reserva (projeção)",
        description=(
            "A projeção (cenário provável, 3 meses) indica fluxo de caixa líquido negativo em "
            "3 meses consecutivos. Baseado em tendência projetada, não em histórico real."
        ),
        formula="net_cashflow < 0 em 3 períodos consecutivos da projeção",
        threshold="3 períodos seguidos",
    ),
    "CONCENTRATED_DUE_DATES": RuleDefinition(
        code="CONCENTRATED_DUE_DATES",
        title="Vencimentos concentrados",
        description="Três ou mais obrigações essenciais/dívidas vencem numa janela de 7 dias.",
        formula="contagem de vencimentos numa janela de 7 dias",
        threshold="3 ou mais",
    ),
    "PROJECTED_DEFICIT_90_DAYS": RuleDefinition(
        code="PROJECTED_DEFICIT_90_DAYS",
        title="Déficit projetado em 90 dias",
        description="A projeção (cenário provável, 3 meses) indica saldo negativo em algum período.",
        formula="existe período com closing_balance < 0 na projeção de 3 meses",
        threshold="existe ao menos 1",
    ),
    "RESERVE_BELOW_THREE_MONTHS": RuleDefinition(
        code="RESERVE_BELOW_THREE_MONTHS",
        title="Reserva abaixo de três meses",
        description="A autonomia básica é inferior a três meses de despesas essenciais.",
        formula="basic_autonomy_months",
        threshold="< 3",
    ),
    "UNPROVISIONED_ANNUAL_EXPENSE": RuleDefinition(
        code="UNPROVISIONED_ANNUAL_EXPENSE",
        title="Despesa anual sem provisionamento",
        description="Existe obrigação ou evento de despesa com recorrência anual cadastrado.",
        formula="existe obrigação ou evento com frequência/recorrência anual",
        threshold="existe ao menos 1",
    ),
    "UNCOVERED_FUTURE_INSTALLMENTS": RuleDefinition(
        code="UNCOVERED_FUTURE_INSTALLMENTS",
        title="Parcelas futuras não cobertas pela renda",
        description="O serviço da dívida mensal excede a renda disponível após despesas essenciais.",
        formula="debt_service_monthly > (total_income_monthly - essential_expenses_monthly)",
        threshold="> 0",
    ),
    "INCOMPATIBLE_GOAL": RuleDefinition(
        code="INCOMPATIBLE_GOAL",
        title="Meta incompatível com o fluxo atual",
        description="A contribuição mensal da meta principal excede a renda disponível após essenciais e dívidas.",
        formula="(total_income_monthly - essential_expenses_monthly - debt_service_monthly) < contribuição da meta",
        threshold="< 0",
    ),
}

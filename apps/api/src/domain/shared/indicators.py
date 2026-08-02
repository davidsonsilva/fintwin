# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Classificação de indicadores financeiros — fonte única dos limiares.

Um indicador só significa alguma coisa junto do limiar que o interpreta. Se
cada superfície carregar o seu, o mesmo número vira "saudável" no dashboard e
"crítico" na conversa, e o usuário deixa de confiar nos dois.

Por isso a classificação mora aqui, no domínio, e é servida junto do valor:
o gauge, o card de insight e o agente conversacional consomem o mesmo veredito
em vez de cada um aplicar o seu.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class IndicatorTier(str, Enum):
    HEALTHY = "healthy"
    ATTENTION = "attention"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class IndicatorAssessment:
    tier: IndicatorTier
    label: str


#: Identidade da política de classificação, para o consumidor saber *qual*
#: régua produziu o veredito que ele está exibindo. A versão muda sempre que
#: os cortes mudarem — sem isso, um card antigo e um novo diriam coisas
#: diferentes sem nenhum sinal de que a régua é que mudou.
INCOME_COMMITMENT_POLICY_ID = "income_commitment_bands"
INCOME_COMMITMENT_POLICY_VERSION = "1"

#: Faixas do comprometimento da renda (obrigações mensais / renda mensal).
#: Os cortes são os que o gauge do dashboard já usava; centralizá-los aqui
#: apenas tira as cópias de circulação.
INCOME_COMMITMENT_BANDS: tuple[tuple[Decimal, IndicatorTier, str], ...] = (
    (Decimal("0.40"), IndicatorTier.HEALTHY, "Dentro do limite saudável"),
    (Decimal("0.60"), IndicatorTier.ATTENTION, "Atenção ao comprometimento"),
    (Decimal("0.75"), IndicatorTier.HIGH, "Comprometimento elevado"),
)

_INCOME_COMMITMENT_WORST = IndicatorAssessment(IndicatorTier.CRITICAL, "Comprometimento crítico")


def classify_income_commitment(fraction: Decimal) -> IndicatorAssessment:
    """Classifica o comprometimento da renda expresso como fração (0.56 = 56%)."""
    for ceiling, tier, label in INCOME_COMMITMENT_BANDS:
        if fraction <= ceiling:
            return IndicatorAssessment(tier, label)
    return _INCOME_COMMITMENT_WORST

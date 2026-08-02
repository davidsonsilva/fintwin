# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Julgamento no texto de uma oportunidade — o que o domínio sustenta.

Tirar o número inventado do texto não basta. "Sua renda está bastante
comprometida" não cita nenhum valor e ainda assim classifica: contradiz um
`tier: attention` e assusta mais do que a régua autoriza. Adjetivo é veredito.

Por isso o vocabulário de julgamento tem nível, e o nível precisa caber no que
a classificação oficial diz:

- sem classificação oficial, nenhum julgamento — o texto descreve o que foi
  observado e para por aí;
- com classificação, o texto pode usar palavras até o nível dela, nunca acima;
- palavra tranquilizadora só existe quando a régua de fato tranquiliza.

O nível conservador é deliberado: subestimar aborrece, superestimar quebra a
confiança no motor determinístico.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Mapping, Optional

from src.domain.shared.enums import Severity
from src.domain.shared.indicators import IndicatorTier

#: Nível 0 tranquiliza; 1 a 3 alarmam em intensidade crescente.
REASSURING_LEVEL = 0

_JUDGMENT_TERMS: Mapping[str, int] = {
    # Tranquilizadores.
    "saudavel": 0,
    "saudaveis": 0,
    "seguro": 0,
    "segura": 0,
    "confortavel": 0,
    "tranquilo": 0,
    "tranquila": 0,
    "equilibrado": 0,
    "equilibrada": 0,
    "adequado": 0,
    "adequada": 0,
    "folgado": 0,
    "folgada": 0,
    # Atenção.
    "atencao": 1,
    "apertado": 1,
    "apertada": 1,
    # Elevado.
    "elevado": 2,
    "elevada": 2,
    "alto": 2,
    "alta": 2,
    "excessivo": 2,
    "excessiva": 2,
    "preocupante": 2,
    "bastante": 2,
    "muito": 2,
    # Crítico.
    "critico": 3,
    "critica": 3,
    "grave": 3,
    "gravissimo": 3,
    "insustentavel": 3,
    "perigoso": 3,
    "perigosa": 3,
    "alarmante": 3,
    "drastico": 3,
    "extremamente": 3,
    "gravemente": 3,
    "seriamente": 3,
}

#: A faixa do indicador diz até onde o texto pode ir.
_TIER_LEVEL: Mapping[str, int] = {
    IndicatorTier.HEALTHY.value: 0,
    IndicatorTier.ATTENTION.value: 1,
    IndicatorTier.HIGH.value: 2,
    IndicatorTier.CRITICAL.value: 3,
}

#: Severidade baixa e média sustentam "atenção", não "elevado"; só a severidade
#: crítica sustenta a palavra "crítico".
_SEVERITY_LEVEL: Mapping[str, int] = {
    Severity.LOW.value: 1,
    Severity.MEDIUM.value: 1,
    Severity.HIGH.value: 2,
    Severity.CRITICAL.value: 3,
}


def _fold(text: str) -> str:
    """Minúsculas sem acento — "crítico" e "critico" são a mesma palavra."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def supported_level(tier: Optional[str], severity: Optional[str]) -> Optional[int]:
    """Nível de julgamento que a classificação oficial sustenta.

    `None` quando não há classificação — e aí nenhum julgamento se sustenta.
    """
    if tier is not None and tier in _TIER_LEVEL:
        return _TIER_LEVEL[tier]
    if severity is not None and severity in _SEVERITY_LEVEL:
        return _SEVERITY_LEVEL[severity]
    return None


def unsupported_judgment_terms(text: str, level: Optional[int]) -> tuple[str, ...]:
    """Palavras de julgamento que o texto usa e o domínio não sustenta."""
    folded = _fold(text)
    found: list[str] = []
    for term, term_level in _JUDGMENT_TERMS.items():
        if not re.search(rf"\b{term}\b", folded):
            continue
        if level is None:
            found.append(term)
        elif term_level == REASSURING_LEVEL:
            # Tranquilizar quando a régua não tranquiliza é contradizê-la.
            if level != REASSURING_LEVEL:
                found.append(term)
        elif term_level > level:
            found.append(term)
    return tuple(sorted(found))

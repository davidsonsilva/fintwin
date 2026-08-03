"""Rede contra a classe de defeito que apareceu três vezes.

`Money.__str__` devolve "395.83 BRL" e `date.isoformat()` devolve "2028-05-01".
As duas são representações de desenvolvedor, e as duas vazaram para textos que
o usuário lê — nas descrições dos planos preventivos e nos riscos do motor de
oportunidade.

Aqui ficam os formatadores; a varredura dos textos que o domínio realmente
produz está em `tests/integration/test_api_endpoints.py`, exercitando o
gerador de planos pelo perfil de demonstração.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

from src.domain.shared.formatting import format_date, format_money, format_percentage
from src.domain.shared.money import Money
from src.domain.shared.percentage import Percentage

CURRENCY = "BRL"

_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_CURRENCY_CODE = re.compile(r"\d\s*(BRL|USD|EUR)\b")


def assert_human_text(text: str) -> None:
    assert not _CURRENCY_CODE.search(text), f"valor com código ISO: {text!r}"
    assert not _ISO_DATE.search(text), f"data em ISO-8601: {text!r}"


def test_formatadores_produzem_pt_br() -> None:
    assert format_money(Money(Decimal("395.83"), CURRENCY)) == "R$ 395,83"
    assert format_money(Money(Decimal("1350"), CURRENCY)) == "R$ 1.350,00"
    assert format_money(Money(Decimal("-42.5"), CURRENCY)) == "R$ -42,50"
    assert format_date(date(2028, 5, 1)) == "01/05/2028"
    assert format_percentage(Percentage(Decimal("0.8"))) == "80%"
    assert format_percentage(Percentage(Decimal("0.825"))) == "82,5%"

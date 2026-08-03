# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Formatação pt-BR para os textos que o domínio escreve.

O FinTwin é pt-BR e o domínio já redige prosa em português nas descrições de
plano preventivo. Os números dessas frases precisam sair na mesma língua.

Sem isto, `f"Provisionar {money} por mês"` cai no `Money.__str__`, que é uma
representação de desenvolvedor ("395.83 BRL") e nunca deveria alcançar a tela.
O mesmo vale para datas: `date.isoformat()` produz "2028-05-01".

Isto NÃO autoriza formatar dinheiro em qualquer lugar do domínio. Onde a saída
é um valor (e não uma frase), continue devolvendo `Money` e deixe a borda
formatar — é o que os campos `expected_monthly_impact` e afins fazem.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from src.domain.shared.money import Money
from src.domain.shared.percentage import Percentage

_CURRENCY_SYMBOLS = {"BRL": "R$"}


def _group_ptbr(value: Decimal, decimals: int) -> str:
    """Separador de milhar com ponto e decimal com vírgula, sem depender de locale."""
    quantized = f"{abs(value):,.{decimals}f}"
    swapped = quantized.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
    return f"-{swapped}" if value < 0 else swapped


def format_money(money: Money) -> str:
    """`Money(395.83, "BRL")` -> "R$ 395,83"."""
    symbol = _CURRENCY_SYMBOLS.get(money.currency, money.currency)
    return f"{symbol} {_group_ptbr(money.amount, 2)}"


def format_date(value: date) -> str:
    """`date(2028, 5, 1)` -> "01/05/2028"."""
    return value.strftime("%d/%m/%Y")


def format_percentage(percentage: Percentage) -> str:
    """`Percentage(0.8)` -> "80%"; `Percentage(0.805)` -> "80,5%"."""
    display = percentage.as_display_percent().normalize()
    decimals = max(0, -display.as_tuple().exponent)
    return f"{_group_ptbr(display, min(decimals, 1))}%"

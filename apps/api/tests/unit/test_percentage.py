from decimal import Decimal

import pytest

from src.domain.shared.percentage import InvalidPercentageError, Percentage


def test_percentage_accepts_valid_fraction():
    p = Percentage(Decimal("0.80"))
    assert p.as_fraction() == Decimal("0.80")


def test_percentage_rejects_float():
    with pytest.raises(InvalidPercentageError):
        Percentage(0.8)


def test_percentage_rejects_out_of_range():
    with pytest.raises(InvalidPercentageError):
        Percentage(Decimal("1.01"))
    with pytest.raises(InvalidPercentageError):
        Percentage(Decimal("-0.01"))


def test_percentage_as_display_percent():
    p = Percentage(Decimal("0.865"))
    assert p.as_display_percent() == Decimal("86.5")


def test_percentage_serializes_as_string():
    p = Percentage(Decimal("0.5"))
    assert p.to_json() == "0.5"

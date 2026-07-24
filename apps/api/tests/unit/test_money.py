from decimal import Decimal

import pytest

from src.domain.shared.money import CurrencyMismatchError, InvalidMoneyError, Money


def test_money_stores_decimal_and_currency():
    m = Money(Decimal("100.50"), "BRL")
    assert m.amount == Decimal("100.50")
    assert m.currency == "BRL"


def test_money_rejects_float():
    with pytest.raises(InvalidMoneyError):
        Money(100.50, "BRL")


def test_money_rounds_with_half_up():
    m = Money(Decimal("10.005"), "BRL")
    assert m.amount == Decimal("10.01")


def test_money_rejects_invalid_value():
    with pytest.raises(InvalidMoneyError):
        Money("not-a-number", "BRL")


def test_money_add_same_currency():
    result = Money(Decimal("10.00"), "BRL").add(Money(Decimal("5.00"), "BRL"))
    assert result.amount == Decimal("15.00")


def test_money_add_different_currency_raises():
    with pytest.raises(CurrencyMismatchError):
        Money(Decimal("10.00"), "BRL").add(Money(Decimal("5.00"), "USD"))


def test_money_subtract():
    result = Money(Decimal("10.00"), "BRL").subtract(Money(Decimal("3.00"), "BRL"))
    assert result.amount == Decimal("7.00")


def test_money_multiply_rejects_float_factor():
    with pytest.raises(InvalidMoneyError):
        Money(Decimal("10.00"), "BRL").multiply(1.5)


def test_money_is_negative():
    assert Money(Decimal("-1.00"), "BRL").is_negative() is True
    assert Money(Decimal("1.00"), "BRL").is_negative() is False


def test_money_serializes_as_string():
    m = Money(Decimal("1234.56"), "brl")
    assert m.to_json() == "1234.56"
    assert m.currency == "BRL"

from decimal import Decimal

from src.domain.decisions.scenario_override import ScenarioOverride
from src.domain.shared.enums import ScenarioType
from src.domain.shared.money import Money

CURRENCY = "BRL"


def test_empty_override_falls_back_to_probable_defaults():
    override = ScenarioOverride()
    params = override.to_scenario_parameters(CURRENCY)

    assert params.scenario_type == ScenarioType.CUSTOM
    assert params.income_multiplier == Decimal("1.00")
    assert params.essential_expense_multiplier == Decimal("1.00")
    assert params.nonessential_expense_multiplier == Decimal("1.00")
    assert params.unexpected_expense == Money(Decimal("0"), CURRENCY)


def test_partial_override_only_replaces_provided_fields():
    override = ScenarioOverride(income_multiplier=Decimal("0.80"))
    params = override.to_scenario_parameters(CURRENCY)

    assert params.income_multiplier == Decimal("0.80")
    assert params.essential_expense_multiplier == Decimal("1.00")

import pytest

from src.domain.decisions.validation import InvalidDecisionParametersError, validate_decision_parameters


def test_missing_required_parameter_raises():
    with pytest.raises(InvalidDecisionParametersError, match="amount"):
        validate_decision_parameters("CASH_PURCHASE", {"description": "Notebook"})


def test_empty_string_counts_as_missing():
    with pytest.raises(InvalidDecisionParametersError):
        validate_decision_parameters("CASH_PURCHASE", {"description": "Notebook", "amount": ""})


def test_negative_amount_raises():
    with pytest.raises(InvalidDecisionParametersError, match="positivo"):
        validate_decision_parameters("CASH_PURCHASE", {"description": "Notebook", "amount": "-100.00"})


def test_valid_cash_purchase_does_not_raise():
    validate_decision_parameters("CASH_PURCHASE", {"description": "Notebook", "amount": "1500.00"})


def test_non_positive_installments_raises():
    with pytest.raises(InvalidDecisionParametersError, match="installments"):
        validate_decision_parameters(
            "INSTALLMENT_PURCHASE",
            {"description": "TV", "amount": "1200.00", "installments": 0},
        )


def test_invalid_date_raises():
    with pytest.raises(InvalidDecisionParametersError, match="date"):
        validate_decision_parameters(
            "CASH_PURCHASE",
            {"description": "Notebook", "amount": "1500.00", "date": "not-a-date"},
        )


def test_reduction_pct_out_of_range_raises():
    with pytest.raises(InvalidDecisionParametersError, match="reduction_pct"):
        validate_decision_parameters(
            "SALARY_REDUCTION",
            {"income_source_id": "income-1", "reduction_pct": "1.5"},
        )


def test_unknown_decision_type_raises():
    with pytest.raises(InvalidDecisionParametersError):
        validate_decision_parameters("NOT_A_TYPE", {})

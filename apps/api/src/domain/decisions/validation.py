"""Validação dos parâmetros de decisão antes da simulação (Spec seção 12.1)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.domain.decisions.types import DECISION_TYPES

_POSITIVE_AMOUNT_FIELDS = ("amount", "total_amount", "target_amount", "monthly_contribution", "monthly_amount")
_NONNEGATIVE_AMOUNT_FIELDS = ("down_payment",)
_DATE_FIELDS = ("date", "start_date", "deadline")


class InvalidDecisionParametersError(ValueError):
    pass


def _as_decimal(field_name: str, raw: Any) -> Decimal:
    try:
        return Decimal(str(raw))
    except (InvalidOperation, ValueError) as exc:
        raise InvalidDecisionParametersError(f"{field_name} inválido: {raw!r}") from exc


def validate_decision_parameters(decision_type: str, parameters: Mapping[str, Any]) -> None:
    if decision_type not in DECISION_TYPES:
        raise InvalidDecisionParametersError(f"Tipo de decisão desconhecido: {decision_type!r}")

    definition = DECISION_TYPES[decision_type]
    missing = [
        field_name
        for field_name in definition.required_parameters
        if parameters.get(field_name) in (None, "")
    ]
    if missing:
        raise InvalidDecisionParametersError(
            f"Parâmetros obrigatórios ausentes para {decision_type}: {', '.join(missing)}."
        )

    for field_name in _POSITIVE_AMOUNT_FIELDS:
        if parameters.get(field_name) not in (None, ""):
            if _as_decimal(field_name, parameters[field_name]) <= 0:
                raise InvalidDecisionParametersError(f"{field_name} deve ser positivo.")

    for field_name in _NONNEGATIVE_AMOUNT_FIELDS:
        if parameters.get(field_name) not in (None, ""):
            if _as_decimal(field_name, parameters[field_name]) < 0:
                raise InvalidDecisionParametersError(f"{field_name} não pode ser negativo.")

    if parameters.get("installments") not in (None, ""):
        try:
            installments = int(parameters["installments"])
        except (TypeError, ValueError) as exc:
            raise InvalidDecisionParametersError("installments deve ser um número inteiro.") from exc
        if installments <= 0:
            raise InvalidDecisionParametersError("installments deve ser positivo.")

    if parameters.get("months") not in (None, ""):
        try:
            months = int(parameters["months"])
        except (TypeError, ValueError) as exc:
            raise InvalidDecisionParametersError("months deve ser um número inteiro.") from exc
        if months <= 0:
            raise InvalidDecisionParametersError("months deve ser positivo.")

    if parameters.get("reduction_pct") not in (None, ""):
        reduction_pct = _as_decimal("reduction_pct", parameters["reduction_pct"])
        if not (Decimal("0") <= reduction_pct <= Decimal("1")):
            raise InvalidDecisionParametersError("reduction_pct deve estar entre 0 e 1.")

    for field_name in _DATE_FIELDS:
        if parameters.get(field_name) not in (None, ""):
            try:
                date.fromisoformat(str(parameters[field_name]))
            except ValueError as exc:
                raise InvalidDecisionParametersError(
                    f"{field_name} inválido, use o formato YYYY-MM-DD."
                ) from exc

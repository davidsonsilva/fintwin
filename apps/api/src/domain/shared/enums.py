# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Enums compartilhados do domínio financeiro (Spec seção 15.2)."""

from enum import Enum


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Recurrence(str, Enum):
    ONE_OFF = "one_off"
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    YEARLY = "yearly"


class ScenarioType(str, Enum):
    PROBABLE = "probable"
    ADVERSE = "adverse"
    INCOME_LOSS = "income_loss"
    CUSTOM = "custom"


class LiquidityType(str, Enum):
    CHECKING_ACCOUNT = "checking_account"
    SAVINGS_ACCOUNT = "savings_account"
    EMERGENCY_FUND = "emergency_fund"
    INVESTMENT = "investment"
    OTHER = "other"


class PlanStatus(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Direction(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class IncomeStability(str, Enum):
    STABLE = "stable"
    VARIABLE = "variable"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

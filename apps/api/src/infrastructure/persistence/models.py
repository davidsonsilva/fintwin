"""Models SQLAlchemy para as entidades manipuladas no onboarding (VS-02), no
radar de fragilidade (VS-06), no simulador de decisões (VS-07), nos planos
preventivos (VS-08) e no agente conversacional (VS-09).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.shared.enums import (
    Direction,
    IncomeStability,
    LiquidityType,
    MessageRole,
    PlanStatus,
    Recurrence,
    Severity,
)
from src.infrastructure.persistence.base import Base


class ProfileModel(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    dependents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    monthly_expense_reduction_capacity: Mapped[Optional[str]] = mapped_column(Numeric(6, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    accounts: Mapped[list["AccountModel"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    incomes: Mapped[list["IncomeSourceModel"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    obligations: Mapped[list["ObligationModel"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    debts: Mapped[list["DebtModel"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    goals: Mapped[list["GoalModel"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    events: Mapped[list["EventModel"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    fragility_findings: Mapped[list["FragilityFindingModel"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    simulations: Mapped[list["SimulationModel"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    preventive_plans: Mapped[list["PreventivePlanModel"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["ConversationModel"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class AccountModel(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("profiles.id"), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    balance_amount: Mapped[str] = mapped_column(Numeric(14, 2), nullable=False)
    balance_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    liquidity_type: Mapped[LiquidityType] = mapped_column(Enum(LiquidityType), nullable=False)
    eligible_for_autonomy: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    profile: Mapped[ProfileModel] = relationship(back_populates="accounts")


class IncomeSourceModel(Base):
    __tablename__ = "income_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("profiles.id"), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount_amount: Mapped[str] = mapped_column(Numeric(14, 2), nullable=False)
    amount_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    frequency: Mapped[Recurrence] = mapped_column(Enum(Recurrence), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    stability: Mapped[IncomeStability] = mapped_column(Enum(IncomeStability), nullable=False)

    profile: Mapped[ProfileModel] = relationship(back_populates="incomes")


class ObligationModel(Base):
    __tablename__ = "obligations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("profiles.id"), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount_amount: Mapped[str] = mapped_column(Numeric(14, 2), nullable=False)
    amount_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    frequency: Mapped[Recurrence] = mapped_column(Enum(Recurrence), nullable=False)
    due_day: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    essential: Mapped[bool] = mapped_column(Boolean, nullable=False)
    debt_related: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    profile: Mapped[ProfileModel] = relationship(back_populates="obligations")


class DebtModel(Base):
    __tablename__ = "debts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("profiles.id"), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    outstanding_balance_amount: Mapped[str] = mapped_column(Numeric(14, 2), nullable=False)
    outstanding_balance_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    installment_amount_amount: Mapped[str] = mapped_column(Numeric(14, 2), nullable=False)
    installment_amount_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    remaining_installments: Mapped[int] = mapped_column(Integer, nullable=False)
    interest_rate_optional: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    due_day: Mapped[int] = mapped_column(Integer, nullable=False)

    profile: Mapped[ProfileModel] = relationship(back_populates="debts")


class GoalModel(Base):
    __tablename__ = "financial_goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("profiles.id"), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    target_amount_amount: Mapped[str] = mapped_column(Numeric(14, 2), nullable=False)
    target_amount_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    current_amount_amount: Mapped[str] = mapped_column(Numeric(14, 2), nullable=False)
    current_amount_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    monthly_contribution_amount: Mapped[str] = mapped_column(Numeric(14, 2), nullable=False)
    monthly_contribution_currency: Mapped[str] = mapped_column(String(3), nullable=False)

    profile: Mapped[ProfileModel] = relationship(back_populates="goals")


class EventModel(Base):
    __tablename__ = "financial_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("profiles.id"), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    amount_amount: Mapped[str] = mapped_column(Numeric(14, 2), nullable=False)
    amount_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    recurrence: Mapped[Optional[Recurrence]] = mapped_column(Enum(Recurrence), nullable=True)
    direction: Mapped[Direction] = mapped_column(Enum(Direction), nullable=False)

    profile: Mapped[ProfileModel] = relationship(back_populates="events")


class FragilityFindingModel(Base):
    __tablename__ = "fragility_findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("profiles.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[Severity] = mapped_column(Enum(Severity), nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    detected_at: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)

    profile: Mapped[ProfileModel] = relationship(back_populates="fragility_findings")


class SimulationModel(Base):
    __tablename__ = "simulations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("profiles.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    baseline_result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    simulated_result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    profile: Mapped[ProfileModel] = relationship(back_populates="simulations")


class PreventivePlanModel(Base):
    __tablename__ = "preventive_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("profiles.id"), nullable=False)
    risk_code: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[PlanStatus] = mapped_column(Enum(PlanStatus), nullable=False)
    actions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    expected_result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    profile: Mapped[ProfileModel] = relationship(back_populates="preventive_plans")


class ConversationModel(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("profiles.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    profile: Mapped[ProfileModel] = relationship(back_populates="conversations")
    messages: Mapped[list["AgentMessageModel"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )


class AgentMessageModel(Base):
    __tablename__ = "agent_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"), nullable=False)
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_calls: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    pending_action: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    conversation: Mapped[ConversationModel] = relationship(back_populates="messages")

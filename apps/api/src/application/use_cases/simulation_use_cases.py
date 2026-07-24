"""Casos de uso do Simulador de Decisões (Spec seção 18.9)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Optional
from uuid import uuid4

from src.domain.decisions.context import DecisionContext
from src.domain.decisions.engine import simulate_decision
from src.domain.decisions.entities import Simulation
from src.domain.decisions.scenario_override import ScenarioOverride
from src.domain.decisions.validation import validate_decision_parameters


class SimulateDecisionUseCase:
    def __init__(
        self,
        account_repo: Any,
        income_repo: Any,
        obligation_repo: Any,
        debt_repo: Any,
        goal_repo: Any,
        event_repo: Any,
        simulation_repo: Any,
    ) -> None:
        self._account_repo = account_repo
        self._income_repo = income_repo
        self._obligation_repo = obligation_repo
        self._debt_repo = debt_repo
        self._goal_repo = goal_repo
        self._event_repo = event_repo
        self._simulation_repo = simulation_repo

    def execute(
        self,
        profile_id: str,
        decision_type: str,
        parameters: Mapping[str, Any],
        scenario_override: Optional[ScenarioOverride],
        horizon_months: int,
        currency: str,
    ) -> Simulation:
        validate_decision_parameters(decision_type, parameters)

        context = DecisionContext(
            accounts=self._account_repo.list_by_profile(profile_id),
            incomes=self._income_repo.list_by_profile(profile_id),
            obligations=self._obligation_repo.list_by_profile(profile_id),
            debts=self._debt_repo.list_by_profile(profile_id),
            goals=self._goal_repo.list_by_profile(profile_id),
            events=self._event_repo.list_by_profile(profile_id),
        )

        outcome = simulate_decision(
            context=context,
            decision_type=decision_type,
            parameters=parameters,
            scenario_override=scenario_override,
            horizon_months=horizon_months,
            currency=currency,
        )

        simulated_result = dict(outcome.simulated_result)
        simulated_result["impact"] = outcome.impact
        simulated_result["total_cost"] = outcome.total_cost
        simulated_result["assumptions"] = outcome.assumptions

        persisted_parameters = dict(parameters)
        if scenario_override is not None:
            persisted_parameters["scenario_override"] = scenario_override.to_dict()

        simulation = Simulation(
            id=str(uuid4()),
            profile_id=profile_id,
            type=decision_type,
            parameters=persisted_parameters,
            baseline_result=dict(outcome.baseline_result),
            simulated_result=simulated_result,
            created_at=datetime.utcnow(),
        )
        self._simulation_repo.add(simulation)
        return simulation


class ListSimulationsUseCase:
    def __init__(self, simulation_repo: Any) -> None:
        self._simulation_repo = simulation_repo

    def execute(self, profile_id: str) -> list[Simulation]:
        return self._simulation_repo.list_by_profile(profile_id)


class GetSimulationUseCase:
    def __init__(self, simulation_repo: Any) -> None:
        self._simulation_repo = simulation_repo

    def execute(self, simulation_id: str) -> Optional[Simulation]:
        return self._simulation_repo.get(simulation_id)


class DeleteSimulationUseCase:
    def __init__(self, simulation_repo: Any) -> None:
        self._simulation_repo = simulation_repo

    def execute(self, simulation_id: str) -> None:
        self._simulation_repo.delete(simulation_id)

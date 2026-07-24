from __future__ import annotations

from sqlalchemy.orm import Session

from src.domain.decisions.entities import Simulation
from src.infrastructure.persistence.models import SimulationModel
from src.infrastructure.repositories.sqlalchemy_repository import SqlAlchemyRepository


def _to_model(simulation: Simulation) -> SimulationModel:
    return SimulationModel(
        id=simulation.id,
        profile_id=simulation.profile_id,
        type=simulation.type,
        parameters=dict(simulation.parameters),
        baseline_result=dict(simulation.baseline_result),
        simulated_result=dict(simulation.simulated_result),
        created_at=simulation.created_at,
    )


def _to_entity(model: SimulationModel) -> Simulation:
    return Simulation(
        id=model.id,
        profile_id=model.profile_id,
        type=model.type,
        parameters=dict(model.parameters),
        baseline_result=dict(model.baseline_result),
        simulated_result=dict(model.simulated_result),
        created_at=model.created_at,
    )


class SqlAlchemySimulationRepository(SqlAlchemyRepository[SimulationModel, Simulation]):
    model = SimulationModel

    def __init__(self, session: Session) -> None:
        super().__init__(session, _to_model, _to_entity)

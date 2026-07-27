# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.application.use_cases.crud_use_cases import DeleteUseCase, GetUseCase, ListByProfileUseCase, UpdateUseCase
from src.application.use_cases.goal_use_cases import CreateGoalUseCase
from src.infrastructure.persistence.session import get_session
from src.infrastructure.repositories.goal_repository import SqlAlchemyGoalRepository
from src.interfaces.http.schemas.goal import GoalCreateRequest, GoalResponse

profiles_router = APIRouter(prefix="/api/v1/profiles", tags=["goals"])
goals_router = APIRouter(prefix="/api/v1/goals", tags=["goals"])


@profiles_router.post("/{profile_id}/goals", response_model=GoalResponse, status_code=201)
def create_goal(
    profile_id: str, payload: GoalCreateRequest, session: Session = Depends(get_session)
) -> GoalResponse:
    repo = SqlAlchemyGoalRepository(session)
    goal = CreateGoalUseCase(repo).execute(
        profile_id=profile_id,
        description=payload.description,
        target_amount=payload.target_amount.to_domain(),
        current_amount=payload.current_amount.to_domain(),
        deadline=payload.deadline,
        priority=payload.priority,
        monthly_contribution=payload.monthly_contribution.to_domain(),
    )
    return GoalResponse.from_domain(goal)


@profiles_router.get("/{profile_id}/goals", response_model=list[GoalResponse])
def list_goals(profile_id: str, session: Session = Depends(get_session)) -> list[GoalResponse]:
    repo = SqlAlchemyGoalRepository(session)
    goals = ListByProfileUseCase(repo).execute(profile_id)
    return [GoalResponse.from_domain(goal) for goal in goals]


@goals_router.put("/{goal_id}", response_model=GoalResponse)
def update_goal(goal_id: str, payload: GoalCreateRequest, session: Session = Depends(get_session)) -> GoalResponse:
    repo = SqlAlchemyGoalRepository(session)
    goal = GetUseCase(repo).execute(goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Meta não encontrada.")
    goal.description = payload.description
    goal.target_amount = payload.target_amount.to_domain()
    goal.current_amount = payload.current_amount.to_domain()
    goal.deadline = payload.deadline
    goal.priority = payload.priority
    goal.monthly_contribution = payload.monthly_contribution.to_domain()
    UpdateUseCase(repo).execute(goal)
    return GoalResponse.from_domain(goal)


@goals_router.delete("/{goal_id}", status_code=204)
def delete_goal(goal_id: str, session: Session = Depends(get_session)) -> None:
    repo = SqlAlchemyGoalRepository(session)
    DeleteUseCase(repo).execute(goal_id)

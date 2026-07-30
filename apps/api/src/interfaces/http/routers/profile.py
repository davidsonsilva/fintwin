# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.application.use_cases.profile_use_cases import (
    CreateProfileUseCase,
    GetProfileUseCase,
    UpdateProfileUseCase,
)
from src.domain.shared.percentage import Percentage
from src.infrastructure.persistence.session import get_session
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository
from src.interfaces.http.schemas.profile import ProfileCreateRequest, ProfileResponse

router = APIRouter(prefix="/api/v1/profiles", tags=["profiles"])


@router.post("", response_model=ProfileResponse, status_code=201)
def create_profile(payload: ProfileCreateRequest, session: Session = Depends(get_session)) -> ProfileResponse:
    repo = SqlAlchemyProfileRepository(session)
    capacity = (
        Percentage(payload.monthly_expense_reduction_capacity)
        if payload.monthly_expense_reduction_capacity is not None
        else None
    )
    profile = CreateProfileUseCase(repo).execute(
        currency=payload.currency,
        dependents=payload.dependents,
        monthly_expense_reduction_capacity=capacity,
        name=payload.name,
    )
    return ProfileResponse.from_domain(profile)


@router.get("/{profile_id}", response_model=ProfileResponse)
def get_profile(profile_id: str, session: Session = Depends(get_session)) -> ProfileResponse:
    repo = SqlAlchemyProfileRepository(session)
    profile = GetProfileUseCase(repo).execute(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Perfil não encontrado.")
    return ProfileResponse.from_domain(profile)


@router.put("/{profile_id}", response_model=ProfileResponse)
def update_profile(
    profile_id: str, payload: ProfileCreateRequest, session: Session = Depends(get_session)
) -> ProfileResponse:
    repo = SqlAlchemyProfileRepository(session)
    profile = GetProfileUseCase(repo).execute(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Perfil não encontrado.")
    profile.currency = payload.currency
    profile.dependents = payload.dependents
    profile.monthly_expense_reduction_capacity = (
        Percentage(payload.monthly_expense_reduction_capacity)
        if payload.monthly_expense_reduction_capacity is not None
        else None
    )
    profile.name = payload.name
    UpdateProfileUseCase(repo).execute(profile)
    return ProfileResponse.from_domain(profile)

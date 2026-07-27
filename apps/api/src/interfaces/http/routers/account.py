# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.application.use_cases.account_use_cases import CreateAccountUseCase
from src.application.use_cases.crud_use_cases import DeleteUseCase, GetUseCase, ListByProfileUseCase, UpdateUseCase
from src.infrastructure.persistence.session import get_session
from src.infrastructure.repositories.account_repository import SqlAlchemyAccountRepository
from src.interfaces.http.schemas.account import AccountCreateRequest, AccountResponse

profiles_router = APIRouter(prefix="/api/v1/profiles", tags=["accounts"])
accounts_router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


@profiles_router.post("/{profile_id}/accounts", response_model=AccountResponse, status_code=201)
def create_account(
    profile_id: str, payload: AccountCreateRequest, session: Session = Depends(get_session)
) -> AccountResponse:
    repo = SqlAlchemyAccountRepository(session)
    account = CreateAccountUseCase(repo).execute(
        profile_id=profile_id,
        description=payload.description,
        balance=payload.balance.to_domain(),
        liquidity_type=payload.liquidity_type,
        eligible_for_autonomy=payload.eligible_for_autonomy,
    )
    return AccountResponse.from_domain(account)


@profiles_router.get("/{profile_id}/accounts", response_model=list[AccountResponse])
def list_accounts(profile_id: str, session: Session = Depends(get_session)) -> list[AccountResponse]:
    repo = SqlAlchemyAccountRepository(session)
    accounts = ListByProfileUseCase(repo).execute(profile_id)
    return [AccountResponse.from_domain(account) for account in accounts]


@accounts_router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: str, payload: AccountCreateRequest, session: Session = Depends(get_session)
) -> AccountResponse:
    repo = SqlAlchemyAccountRepository(session)
    account = GetUseCase(repo).execute(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Conta não encontrada.")
    account.description = payload.description
    account.balance = payload.balance.to_domain()
    account.liquidity_type = payload.liquidity_type
    account.eligible_for_autonomy = payload.eligible_for_autonomy
    UpdateUseCase(repo).execute(account)
    return AccountResponse.from_domain(account)


@accounts_router.delete("/{account_id}", status_code=204)
def delete_account(account_id: str, session: Session = Depends(get_session)) -> None:
    repo = SqlAlchemyAccountRepository(session)
    DeleteUseCase(repo).execute(account_id)

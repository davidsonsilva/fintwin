from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.application.use_cases.crud_use_cases import DeleteUseCase, GetUseCase, ListByProfileUseCase, UpdateUseCase
from src.application.use_cases.event_use_cases import CreateEventUseCase
from src.infrastructure.persistence.session import get_session
from src.infrastructure.repositories.event_repository import SqlAlchemyEventRepository
from src.interfaces.http.schemas.event import EventCreateRequest, EventResponse

profiles_router = APIRouter(prefix="/api/v1/profiles", tags=["events"])
events_router = APIRouter(prefix="/api/v1/events", tags=["events"])


@profiles_router.post("/{profile_id}/events", response_model=EventResponse, status_code=201)
def create_event(
    profile_id: str, payload: EventCreateRequest, session: Session = Depends(get_session)
) -> EventResponse:
    repo = SqlAlchemyEventRepository(session)
    event = CreateEventUseCase(repo).execute(
        profile_id=profile_id,
        description=payload.description,
        event_type=payload.event_type,
        amount=payload.amount.to_domain(),
        event_date=payload.date,
        recurrence=payload.recurrence,
        direction=payload.direction,
    )
    return EventResponse.from_domain(event)


@profiles_router.get("/{profile_id}/events", response_model=list[EventResponse])
def list_events(profile_id: str, session: Session = Depends(get_session)) -> list[EventResponse]:
    repo = SqlAlchemyEventRepository(session)
    events = ListByProfileUseCase(repo).execute(profile_id)
    return [EventResponse.from_domain(event) for event in events]


@events_router.put("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: str, payload: EventCreateRequest, session: Session = Depends(get_session)
) -> EventResponse:
    repo = SqlAlchemyEventRepository(session)
    event = GetUseCase(repo).execute(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")
    event.description = payload.description
    event.event_type = payload.event_type
    event.amount = payload.amount.to_domain()
    event.date = payload.date
    event.recurrence = payload.recurrence
    event.direction = payload.direction
    UpdateUseCase(repo).execute(event)
    return EventResponse.from_domain(event)


@events_router.delete("/{event_id}", status_code=204)
def delete_event(event_id: str, session: Session = Depends(get_session)) -> None:
    repo = SqlAlchemyEventRepository(session)
    DeleteUseCase(repo).execute(event_id)

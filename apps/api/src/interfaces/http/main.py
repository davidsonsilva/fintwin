# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Ponto de entrada HTTP da API — health check, onboarding (VS-02) e dashboard (VS-03)."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.interfaces.http.routers import (
    account,
    agent,
    dashboard,
    debt,
    demo,
    event,
    fragility,
    goal,
    income,
    obligation,
    recommendation,
    preventive_plan,
    profile,
    simulation,
)

app = FastAPI(title="FinTwin AI API", version="v1")

# 3000 = web servido pelo Docker; 3001 = `next dev` no host, usado pelo loop de
# validação visual (skill visual-rebuild), que precisa de HMR.
_DEFAULT_CORS_ORIGINS = "http://localhost:3000,http://localhost:3001"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("CORS_ALLOW_ORIGINS", _DEFAULT_CORS_ORIGINS).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(profile.router)
app.include_router(account.profiles_router)
app.include_router(account.accounts_router)
app.include_router(income.profiles_router)
app.include_router(income.incomes_router)
app.include_router(obligation.profiles_router)
app.include_router(obligation.obligations_router)
app.include_router(debt.profiles_router)
app.include_router(debt.debts_router)
app.include_router(goal.profiles_router)
app.include_router(goal.goals_router)
app.include_router(event.profiles_router)
app.include_router(event.events_router)
app.include_router(demo.router)
app.include_router(dashboard.router)
app.include_router(fragility.router)
app.include_router(simulation.profiles_router)
app.include_router(simulation.simulations_router)
app.include_router(preventive_plan.profiles_router)
app.include_router(preventive_plan.plans_router)
app.include_router(recommendation.profiles_router)
app.include_router(recommendation.recommendations_router)
app.include_router(agent.router)

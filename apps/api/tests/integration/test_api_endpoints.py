from decimal import Decimal

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_get_profile(client: TestClient) -> None:
    response = client.post(
        "/api/v1/profiles",
        json={"currency": "BRL", "dependents": 1, "monthly_expense_reduction_capacity": "0.2"},
    )
    assert response.status_code == 201
    profile = response.json()
    assert profile["currency"] == "BRL"

    fetched = client.get(f"/api/v1/profiles/{profile['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == profile["id"]


def test_get_profile_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/profiles/does-not-exist")
    assert response.status_code == 404


def test_account_crud_via_api(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 0}).json()

    created = client.post(
        f"/api/v1/profiles/{profile['id']}/accounts",
        json={
            "description": "Conta corrente",
            "balance": {"amount": "1500.00", "currency": "BRL"},
            "liquidity_type": "checking_account",
            "eligible_for_autonomy": False,
        },
    )
    assert created.status_code == 201
    account = created.json()

    listed = client.get(f"/api/v1/profiles/{profile['id']}/accounts")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = client.put(
        f"/api/v1/accounts/{account['id']}",
        json={
            "description": "Conta corrente renomeada",
            "balance": {"amount": "1600.00", "currency": "BRL"},
            "liquidity_type": "checking_account",
            "eligible_for_autonomy": True,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "Conta corrente renomeada"

    deleted = client.delete(f"/api/v1/accounts/{account['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/profiles/{profile['id']}/accounts").json() == []


def test_load_demo_profile_via_api(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 2}).json()

    response = client.post(f"/api/v1/profiles/{profile['id']}/demo")
    assert response.status_code == 204

    accounts = client.get(f"/api/v1/profiles/{profile['id']}/accounts").json()
    incomes = client.get(f"/api/v1/profiles/{profile['id']}/incomes").json()
    obligations = client.get(f"/api/v1/profiles/{profile['id']}/obligations").json()
    debts = client.get(f"/api/v1/profiles/{profile['id']}/debts").json()
    goals = client.get(f"/api/v1/profiles/{profile['id']}/goals").json()
    events = client.get(f"/api/v1/profiles/{profile['id']}/events").json()

    assert len(accounts) == 2
    assert len(incomes) == 1
    assert len(obligations) == 3
    assert len(debts) == 1
    assert len(goals) == 1
    assert len(events) == 3


def test_load_demo_profile_missing_profile_returns_404(client: TestClient) -> None:
    response = client.post("/api/v1/profiles/does-not-exist/demo")
    assert response.status_code == 404


def test_dashboard_summary_missing_profile_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/profiles/does-not-exist/dashboard")
    assert response.status_code == 404


def test_dashboard_summary_after_loading_demo_profile(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 2}).json()
    client.post(f"/api/v1/profiles/{profile['id']}/demo")

    response = client.get(f"/api/v1/profiles/{profile['id']}/dashboard")
    assert response.status_code == 200
    summary = response.json()

    assert summary["net_balance"]["amount"] == "12500.00"
    assert summary["monthly_obligations_total"]["amount"] == "4950.00"
    assert summary["income_commitment_pct"] is not None
    assert summary["main_goal"]["description"] == "Entrada de imóvel próprio"
    assert len(summary["upcoming_events"]) <= 5


def test_obligations_by_category_after_loading_demo_profile(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 2}).json()
    client.post(f"/api/v1/profiles/{profile['id']}/demo")

    response = client.get(f"/api/v1/profiles/{profile['id']}/obligations/by-category")
    assert response.status_code == 200
    breakdown = response.json()

    assert len(breakdown) > 0
    total_pct = sum(Decimal(item["percentage"]) for item in breakdown)
    assert abs(total_pct - Decimal("1")) < Decimal("0.0001")


def test_obligations_by_category_missing_profile_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/profiles/does-not-exist/obligations/by-category")
    assert response.status_code == 404


def test_obligations_by_category_rejects_mismatched_currency_via_http(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 0}).json()
    client.post(
        f"/api/v1/profiles/{profile['id']}/obligations",
        json={
            "description": "Assinatura internacional",
            "amount": {"amount": "100.00", "currency": "USD"},
            "category": "assinaturas",
            "frequency": "monthly",
            "due_day": 15,
            "start_date": "2024-01-01",
            "essential": False,
            "debt_related": False,
        },
    )

    response = client.get(f"/api/v1/profiles/{profile['id']}/obligations/by-category")

    assert response.status_code == 409


def test_dashboard_summary_empty_profile_has_no_goal_or_commitment(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 0}).json()

    response = client.get(f"/api/v1/profiles/{profile['id']}/dashboard")
    assert response.status_code == 200
    summary = response.json()

    assert summary["net_balance"]["amount"] == "0.00"
    assert summary["income_commitment_pct"] is None
    assert summary["main_goal"] is None
    assert summary["upcoming_events"] == []


def test_balance_history_after_loading_demo_profile(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 2}).json()
    client.post(f"/api/v1/profiles/{profile['id']}/demo")

    client.get(f"/api/v1/profiles/{profile['id']}/dashboard")
    response = client.get(f"/api/v1/profiles/{profile['id']}/balance-history")

    assert response.status_code == 200
    history = response.json()
    assert len(history) == 6
    assert history[-1]["net_balance"]["amount"] == "12500.00"
    periods = [item["period"] for item in history]
    assert periods == sorted(periods)


def test_balance_history_missing_profile_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/profiles/does-not-exist/balance-history")
    assert response.status_code == 404


def test_balance_history_rejects_out_of_bounds_months(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 2}).json()

    response = client.get(f"/api/v1/profiles/{profile['id']}/balance-history?months=-1")

    assert response.status_code == 422


def test_projection_missing_profile_returns_404(client: TestClient) -> None:
    response = client.post("/api/v1/profiles/does-not-exist/projections", json={"months": 12, "scenario": "probable"})
    assert response.status_code == 404


def test_projection_default_uses_probable_scenario_and_twelve_months(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 2}).json()
    client.post(f"/api/v1/profiles/{profile['id']}/demo")

    response = client.post(f"/api/v1/profiles/{profile['id']}/projections", json={})
    assert response.status_code == 200
    body = response.json()

    assert body["scenario"] == "probable"
    assert len(body["periods"]) == 12
    assert "assumptions" in body and len(body["assumptions"]) > 0


def test_projection_adverse_scenario_with_shorter_horizon(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 2}).json()
    client.post(f"/api/v1/profiles/{profile['id']}/demo")

    response = client.post(
        f"/api/v1/profiles/{profile['id']}/projections", json={"months": 3, "scenario": "adverse"}
    )
    assert response.status_code == 200
    body = response.json()

    assert body["scenario"] == "adverse"
    assert len(body["periods"]) == 3


def test_projection_rejects_invalid_months(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 0}).json()

    response = client.post(f"/api/v1/profiles/{profile['id']}/projections", json={"months": 5})
    assert response.status_code == 422


def test_autonomy_missing_profile_returns_404(client: TestClient) -> None:
    response = client.post("/api/v1/profiles/does-not-exist/autonomy")
    assert response.status_code == 404


def test_autonomy_after_loading_demo_profile(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 2}).json()
    client.post(f"/api/v1/profiles/{profile['id']}/demo")

    response = client.post(f"/api/v1/profiles/{profile['id']}/autonomy")
    assert response.status_code == 200
    body = response.json()

    assert body["eligible_assets"]["amount"] == "9000.00"
    assert body["basic_autonomy_months"] is not None
    assert len(body["eligible_accounts"]) == 1
    assert len(body["essential_obligations"]) == 3
    assert len(body["assumptions"]) > 0


def test_autonomy_empty_profile_has_no_basic_autonomy(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 0}).json()

    response = client.post(f"/api/v1/profiles/{profile['id']}/autonomy")
    assert response.status_code == 200
    body = response.json()

    assert body["eligible_assets"]["amount"] == "0.00"
    assert body["basic_autonomy_months"] is None


def test_fragilities_detect_missing_profile_returns_404(client: TestClient) -> None:
    response = client.post("/api/v1/profiles/does-not-exist/fragilities/detect")
    assert response.status_code == 404


def test_fragilities_list_missing_profile_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/profiles/does-not-exist/fragilities")
    assert response.status_code == 404


def test_fragilities_detect_and_list_demo_profile(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 2}).json()
    client.post(f"/api/v1/profiles/{profile['id']}/demo")

    detect_response = client.post(f"/api/v1/profiles/{profile['id']}/fragilities/detect")
    assert detect_response.status_code == 200
    detected = detect_response.json()
    assert len(detected) > 0
    codes = {item["code"] for item in detected}
    assert "UNPROVISIONED_ANNUAL_EXPENSE" in codes
    for item in detected:
        assert item["evidence"]
        assert item["title"]
        assert item["formula"]

    list_response = client.get(f"/api/v1/profiles/{profile['id']}/fragilities")
    assert list_response.status_code == 200
    assert len(list_response.json()) == len(detected)


def test_fragilities_list_filters_by_severity(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 2}).json()
    client.post(f"/api/v1/profiles/{profile['id']}/demo")
    client.post(f"/api/v1/profiles/{profile['id']}/fragilities/detect")

    response = client.get(f"/api/v1/profiles/{profile['id']}/fragilities", params={"severity": "high"})
    assert response.status_code == 200
    for item in response.json():
        assert item["severity"] == "high"


def test_fragilities_detect_is_idempotent_snapshot(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 2}).json()
    client.post(f"/api/v1/profiles/{profile['id']}/demo")

    first = client.post(f"/api/v1/profiles/{profile['id']}/fragilities/detect").json()
    second = client.post(f"/api/v1/profiles/{profile['id']}/fragilities/detect").json()

    assert len(first) == len(second)
    listed = client.get(f"/api/v1/profiles/{profile['id']}/fragilities").json()
    assert len(listed) == len(second)


def test_simulate_missing_profile_returns_404(client: TestClient) -> None:
    response = client.post(
        "/api/v1/profiles/does-not-exist/simulations",
        json={"decision_type": "CASH_PURCHASE", "parameters": {"amount": "100.00", "description": "x"}},
    )
    assert response.status_code == 404


def test_simulate_rejects_out_of_range_expense_reduction_capacity(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 0}).json()
    client.post(f"/api/v1/profiles/{profile['id']}/demo")

    response = client.post(
        f"/api/v1/profiles/{profile['id']}/simulations",
        json={
            "decision_type": "CASH_PURCHASE",
            "parameters": {"amount": "100.00", "description": "x"},
            "scenario_override": {"expense_reduction_capacity": "2"},
        },
    )
    assert response.status_code == 422


def test_simulate_cash_purchase_via_api(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 0}).json()
    client.post(f"/api/v1/profiles/{profile['id']}/demo")

    response = client.post(
        f"/api/v1/profiles/{profile['id']}/simulations",
        json={
            "decision_type": "CASH_PURCHASE",
            "parameters": {"amount": "1500.00", "description": "Geladeira nova"},
            "horizon_months": 3,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "CASH_PURCHASE"
    assert body["baseline_result"]["final_balance"]
    assert body["simulated_result"]["impact"]["closing_balance_delta"] == "-1500.00"

    listed = client.get(f"/api/v1/profiles/{profile['id']}/simulations")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    detail = client.get(f"/api/v1/simulations/{body['id']}")
    assert detail.status_code == 200
    assert detail.json()["id"] == body["id"]

    deleted = client.delete(f"/api/v1/simulations/{body['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/profiles/{profile['id']}/simulations").json() == []


def test_simulate_financing_with_custom_scenario_via_api(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 0}).json()
    client.post(f"/api/v1/profiles/{profile['id']}/demo")

    response = client.post(
        f"/api/v1/profiles/{profile['id']}/simulations",
        json={
            "decision_type": "FINANCING",
            "parameters": {
                "total_amount": "60000.00",
                "down_payment": "10000.00",
                "installments": 48,
                "description": "Carro novo",
                "recurring_costs": [{"description": "Seguro", "amount": "180.00"}],
            },
            "scenario_override": {"essential_expense_multiplier": "1.05"},
            "horizon_months": 12,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["simulated_result"]["scenario"] == "custom"
    assert body["simulated_result"]["total_cost"]["total_cost"]["amount"]


def test_simulate_income_loss_via_api(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 0}).json()
    client.post(f"/api/v1/profiles/{profile['id']}/demo")

    incomes = client.get(f"/api/v1/profiles/{profile['id']}/incomes").json()
    income_id = incomes[0]["id"]

    response = client.post(
        f"/api/v1/profiles/{profile['id']}/simulations",
        json={
            "decision_type": "INCOME_LOSS",
            "parameters": {"income_source_id": income_id, "months": 3},
            "horizon_months": 3,
        },
    )
    assert response.status_code == 201


def test_simulate_new_goal_via_api(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 0}).json()
    client.post(f"/api/v1/profiles/{profile['id']}/demo")

    response = client.post(
        f"/api/v1/profiles/{profile['id']}/simulations",
        json={
            "decision_type": "NEW_GOAL",
            "parameters": {
                "description": "Fundo de estudos",
                "target_amount": "12000.00",
                "monthly_contribution": "400.00",
                "priority": 3,
            },
        },
    )
    assert response.status_code == 201
    assert response.json()["type"] == "NEW_GOAL"


def test_generate_plans_missing_profile_returns_404(client: TestClient) -> None:
    response = client.post("/api/v1/profiles/does-not-exist/plans/generate")
    assert response.status_code == 404


def test_plans_list_missing_profile_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/profiles/does-not-exist/plans")
    assert response.status_code == 404


def test_generate_and_list_plans_for_demo_profile(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 2}).json()
    client.post(f"/api/v1/profiles/{profile['id']}/demo")
    client.post(f"/api/v1/profiles/{profile['id']}/fragilities/detect")

    generate_response = client.post(f"/api/v1/profiles/{profile['id']}/plans/generate")
    assert generate_response.status_code == 201
    generated = generate_response.json()
    assert len(generated) > 0
    codes = {item["risk_code"] for item in generated}
    assert "UNPROVISIONED_ANNUAL_EXPENSE" in codes
    for item in generated:
        assert item["status"] == "proposed"
        assert item["actions"]
        assert "deficit_avoided" in item["expected_result"]

    list_response = client.get(f"/api/v1/profiles/{profile['id']}/plans")
    assert list_response.status_code == 200
    assert len(list_response.json()) == len(generated)


def test_generate_plans_does_not_duplicate_non_terminal_plans(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 2}).json()
    client.post(f"/api/v1/profiles/{profile['id']}/demo")
    client.post(f"/api/v1/profiles/{profile['id']}/fragilities/detect")

    first = client.post(f"/api/v1/profiles/{profile['id']}/plans/generate").json()
    second = client.post(f"/api/v1/profiles/{profile['id']}/plans/generate").json()

    assert len(second) == 0
    listed = client.get(f"/api/v1/profiles/{profile['id']}/plans").json()
    assert len(listed) == len(first)


def test_plans_list_rejects_invalid_status_filter(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 2}).json()
    response = client.get(f"/api/v1/profiles/{profile['id']}/plans", params={"status": "not-a-status"})
    assert response.status_code == 422


def test_plans_list_filters_by_status(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 2}).json()
    client.post(f"/api/v1/profiles/{profile['id']}/demo")
    client.post(f"/api/v1/profiles/{profile['id']}/fragilities/detect")
    client.post(f"/api/v1/profiles/{profile['id']}/plans/generate")

    response = client.get(f"/api/v1/profiles/{profile['id']}/plans", params={"status": "approved"})
    assert response.status_code == 200
    assert response.json() == []


def test_approve_and_reject_plan_status_transitions(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 2}).json()
    client.post(f"/api/v1/profiles/{profile['id']}/demo")
    client.post(f"/api/v1/profiles/{profile['id']}/fragilities/detect")
    plans = client.post(f"/api/v1/profiles/{profile['id']}/plans/generate").json()
    assert len(plans) >= 2

    approved = client.patch(f"/api/v1/plans/{plans[0]['id']}/status", json={"status": "approved"})
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["approved_at"] is not None

    in_progress = client.patch(f"/api/v1/plans/{plans[0]['id']}/status", json={"status": "in_progress"})
    assert in_progress.status_code == 200
    assert in_progress.json()["status"] == "in_progress"

    rejected = client.patch(f"/api/v1/plans/{plans[1]['id']}/status", json={"status": "rejected"})
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"


def test_reject_status_transition_invalid_returns_422(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 2}).json()
    client.post(f"/api/v1/profiles/{profile['id']}/demo")
    client.post(f"/api/v1/profiles/{profile['id']}/fragilities/detect")
    plans = client.post(f"/api/v1/profiles/{profile['id']}/plans/generate").json()

    response = client.patch(f"/api/v1/plans/{plans[0]['id']}/status", json={"status": "completed"})
    assert response.status_code == 422


def test_update_plan_status_missing_plan_returns_404(client: TestClient) -> None:
    response = client.patch("/api/v1/plans/does-not-exist/status", json={"status": "approved"})
    assert response.status_code == 404


def _override_agent_llm(fake_llm) -> None:
    from src.interfaces.http.main import app
    from src.interfaces.http.routers.agent import get_llm_client

    app.dependency_overrides[get_llm_client] = lambda: fake_llm


def _make_fake_llm_that_proposes_cash_purchase():
    from dataclasses import dataclass
    from typing import Optional

    @dataclass
    class FakeBlock:
        type: str
        text: str = ""
        name: str = ""
        input: Optional[dict] = None
        id: str = ""

    @dataclass
    class FakeResponse:
        content: list

    class FakeLLM:
        def __init__(self):
            self._responses = [
                FakeResponse(
                    content=[
                        FakeBlock(
                            type="tool_use",
                            name="propose_simulation",
                            input={"decision_type": "CASH_PURCHASE", "parameters": {"amount": "50.00", "description": "Lanche"}},
                            id="t1",
                        )
                    ]
                ),
                FakeResponse(content=[FakeBlock(type="text", text="Proposta pronta.")]),
            ]

        def create_message(self, system, messages, tools):
            return self._responses.pop(0)

    return FakeLLM()


def test_agent_message_proposes_simulation_without_persisting(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 0}).json()
    _override_agent_llm(_make_fake_llm_that_proposes_cash_purchase())

    response = client.post(
        f"/api/v1/profiles/{profile['id']}/agent/messages",
        json={"message": "Quero comprar um lanche de 50 reais à vista"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["version"] == "v1"
    assert body["data"]["pending_action"]["decision_type"] == "CASH_PURCHASE"
    assert body["data"]["pending_action"]["confirmed"] is False

    simulations = client.get(f"/api/v1/profiles/{profile['id']}/simulations").json()
    assert simulations == []


def test_agent_confirm_action_persists_simulation_and_is_idempotent(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 0}).json()
    _override_agent_llm(_make_fake_llm_that_proposes_cash_purchase())

    sent = client.post(
        f"/api/v1/profiles/{profile['id']}/agent/messages",
        json={"message": "Quero comprar um lanche de 50 reais à vista"},
    ).json()
    action_id = sent["data"]["pending_action"]["action_id"]

    confirmed = client.post(f"/api/v1/profiles/{profile['id']}/agent/actions/{action_id}/confirm")
    assert confirmed.status_code == 201
    assert confirmed.json()["type"] == "CASH_PURCHASE"

    simulations = client.get(f"/api/v1/profiles/{profile['id']}/simulations").json()
    assert len(simulations) == 1

    re_confirmed = client.post(f"/api/v1/profiles/{profile['id']}/agent/actions/{action_id}/confirm")
    assert re_confirmed.status_code == 409


def test_agent_confirm_unknown_action_returns_404(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 0}).json()
    response = client.post(f"/api/v1/profiles/{profile['id']}/agent/actions/does-not-exist/confirm")
    assert response.status_code == 404


def test_agent_message_history_lists_user_and_assistant_messages(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 0}).json()
    _override_agent_llm(_make_fake_llm_that_proposes_cash_purchase())

    sent = client.post(
        f"/api/v1/profiles/{profile['id']}/agent/messages",
        json={"message": "Quero comprar um lanche de 50 reais à vista"},
    ).json()
    conversation_id = sent["data"]["conversation_id"]

    history = client.get(f"/api/v1/profiles/{profile['id']}/agent/conversations/{conversation_id}/messages")
    assert history.status_code == 200
    roles = [item["role"] for item in history.json()]
    assert roles == ["user", "assistant"]


def test_agent_message_missing_profile_returns_404(client: TestClient) -> None:
    response = client.post(
        "/api/v1/profiles/does-not-exist/agent/messages", json={"message": "Olá"}
    )
    assert response.status_code == 404

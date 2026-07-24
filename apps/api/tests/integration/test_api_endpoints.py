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


def test_dashboard_summary_empty_profile_has_no_goal_or_commitment(client: TestClient) -> None:
    profile = client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 0}).json()

    response = client.get(f"/api/v1/profiles/{profile['id']}/dashboard")
    assert response.status_code == 200
    summary = response.json()

    assert summary["net_balance"]["amount"] == "0.00"
    assert summary["income_commitment_pct"] is None
    assert summary["main_goal"] is None
    assert summary["upcoming_events"] == []


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

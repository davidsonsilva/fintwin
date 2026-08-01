from fastapi.testclient import TestClient


def _profile(client: TestClient) -> str:
    return client.post("/api/v1/profiles", json={"currency": "BRL", "dependents": 0}).json()["id"]


def _profile_com_folga(client: TestClient) -> str:
    """Perfil desenhado para passar em todos os portões de segurança."""
    profile_id = _profile(client)
    client.post(
        f"/api/v1/profiles/{profile_id}/accounts",
        json={
            "description": "Reserva",
            "balance": {"amount": "20000.00", "currency": "BRL"},
            "liquidity_type": "emergency_fund",
            "eligible_for_autonomy": True,
        },
    )
    client.post(
        f"/api/v1/profiles/{profile_id}/incomes",
        json={
            "description": "Salário",
            "amount": {"amount": "9000.00", "currency": "BRL"},
            "frequency": "monthly",
            "start_date": "2024-01-01",
            "stability": "stable",
        },
    )
    client.post(
        f"/api/v1/profiles/{profile_id}/obligations",
        json={
            "description": "Aluguel",
            "amount": {"amount": "3000.00", "currency": "BRL"},
            "category": "moradia",
            "frequency": "monthly",
            "due_day": 5,
            "start_date": "2024-01-01",
            "essential": True,
            "debt_related": False,
        },
    )
    client.post(
        f"/api/v1/profiles/{profile_id}/goals",
        json={
            "description": "Entrada do apartamento",
            "target_amount": {"amount": "60000.00", "currency": "BRL"},
            "current_amount": {"amount": "12000.00", "currency": "BRL"},
            "priority": 1,
            "monthly_contribution": {"amount": "900.00", "currency": "BRL"},
        },
    )
    return profile_id


def test_analise_de_perfil_inexistente_devolve_404(client: TestClient) -> None:
    response = client.post("/api/v1/profiles/nao-existe/opportunity-analyses")
    assert response.status_code == 404


def test_perfil_vazio_devolve_dados_insuficientes(client: TestClient) -> None:
    profile_id = _profile(client)
    response = client.post(f"/api/v1/profiles/{profile_id}/opportunity-analyses")

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["status"] == "insufficient_data"
    assert body["result"]["missing_data"]
    assert body["stale"] is False


def test_gerar_analise_devolve_id_e_recomendacao(client: TestClient) -> None:
    profile_id = _profile_com_folga(client)
    body = client.post(f"/api/v1/profiles/{profile_id}/opportunity-analyses").json()

    assert body["result"]["status"] == "available"
    assert body["analysis_id"]
    assert body["decision"] == "pending"
    assert body["scenario"] == "probable"
    assert len(body["result"]["scenarios"]) == 3
    assert body["result"]["recommended"]["additional_amount"]["amount"] == "1350.00"


def test_abrir_analise_devolve_os_mesmos_numeros(client: TestClient) -> None:
    profile_id = _profile_com_folga(client)
    created = client.post(f"/api/v1/profiles/{profile_id}/opportunity-analyses").json()

    reopened = client.get(f"/api/v1/opportunity-analyses/{created['analysis_id']}").json()
    assert reopened["result"] == created["result"]
    assert reopened["stale"] is False


def test_mudar_os_dados_marca_a_analise_como_defasada(client: TestClient) -> None:
    profile_id = _profile_com_folga(client)
    created = client.post(f"/api/v1/profiles/{profile_id}/opportunity-analyses").json()

    client.post(
        f"/api/v1/profiles/{profile_id}/obligations",
        json={
            "description": "Academia",
            "amount": {"amount": "300.00", "currency": "BRL"},
            "category": "lazer",
            "frequency": "monthly",
            "due_day": 10,
            "start_date": "2024-01-01",
            "essential": False,
            "debt_related": False,
        },
    )

    reopened = client.get(f"/api/v1/opportunity-analyses/{created['analysis_id']}").json()
    assert reopened["stale"] is True
    # O snapshot não muda: são os números que o usuário viu ao decidir.
    assert reopened["result"] == created["result"]


def test_aprovar_registra_a_decisao_sem_mover_dinheiro(client: TestClient) -> None:
    profile_id = _profile_com_folga(client)
    created = client.post(f"/api/v1/profiles/{profile_id}/opportunity-analyses").json()

    saldo_antes = client.get(f"/api/v1/profiles/{profile_id}/dashboard").json()["net_balance"]

    approved = client.patch(
        f"/api/v1/opportunity-analyses/{created['analysis_id']}/decision",
        json={"decision": "approved", "selected_scenario": "recommended"},
    ).json()

    assert approved["decision"] == "approved"
    assert approved["selected_scenario"] == "recommended"
    assert approved["decided_at"] is not None

    saldo_depois = client.get(f"/api/v1/profiles/{profile_id}/dashboard").json()["net_balance"]
    assert saldo_depois == saldo_antes


def test_rejeitar_nao_guarda_cenario_selecionado(client: TestClient) -> None:
    profile_id = _profile_com_folga(client)
    created = client.post(f"/api/v1/profiles/{profile_id}/opportunity-analyses").json()

    rejected = client.patch(
        f"/api/v1/opportunity-analyses/{created['analysis_id']}/decision",
        json={"decision": "rejected", "selected_scenario": "accelerated"},
    ).json()

    assert rejected["decision"] == "rejected"
    assert rejected["selected_scenario"] is None


def test_simular_outro_valor_gera_uma_analise_com_cenario_custom(client: TestClient) -> None:
    profile_id = _profile_com_folga(client)
    body = client.post(
        f"/api/v1/profiles/{profile_id}/opportunity-analyses", json={"custom_pct": "0.03"}
    ).json()

    keys = [scenario["key"] for scenario in body["result"]["scenarios"]]
    assert "custom" in keys
    custom = next(s for s in body["result"]["scenarios"] if s["key"] == "custom")
    assert custom["additional_amount"]["amount"] == "270.00"


def test_analise_inexistente_devolve_404(client: TestClient) -> None:
    assert client.get("/api/v1/opportunity-analyses/nao-existe").status_code == 404
    assert (
        client.patch(
            "/api/v1/opportunity-analyses/nao-existe/decision", json={"decision": "approved"}
        ).status_code
        == 404
    )

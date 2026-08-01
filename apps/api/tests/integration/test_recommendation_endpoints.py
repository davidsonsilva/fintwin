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


def _add_despesa(client: TestClient, profile_id: str, amount: str = "250.00") -> None:
    client.post(
        f"/api/v1/profiles/{profile_id}/obligations",
        json={
            "description": "Streaming",
            "amount": {"amount": amount, "currency": "BRL"},
            "category": "lazer",
            "frequency": "monthly",
            "due_day": 10,
            "start_date": "2024-01-01",
            "essential": False,
            "debt_related": False,
        },
    )


def test_perfil_inexistente_devolve_404(client: TestClient) -> None:
    assert client.get("/api/v1/profiles/nao-existe/insight").status_code == 404
    assert client.post("/api/v1/profiles/nao-existe/recommendations/detect").status_code == 404


def test_insight_de_perfil_vazio_traz_diagnostico_e_nenhuma_recomendacao(client: TestClient) -> None:
    profile_id = _profile(client)
    body = client.get(f"/api/v1/profiles/{profile_id}/insight").json()

    assert body["recommendation"] is None
    assert body["diagnosis"]["status"] == "insufficient_data"
    assert body["diagnosis"]["missing_data"]
    # Ler o insight não pode criar registro.
    assert client.get(f"/api/v1/profiles/{profile_id}/recommendations").json() == []


def test_ciclo_completo_pelo_http(client: TestClient) -> None:
    profile_id = _profile_com_folga(client)

    # insight detectado -> recomendação registrada
    detected = client.post(f"/api/v1/profiles/{profile_id}/recommendations/detect").json()
    rec = detected["recommendation"]
    assert rec["status"] == "pending"
    assert rec["source"] == "engine"
    assert len(rec["payload"]["scenarios"]) == 3

    # o card mostra a pendente
    assert client.get(f"/api/v1/profiles/{profile_id}/insight").json()["recommendation"]["id"] == rec["id"]

    saldo_antes = client.get(f"/api/v1/profiles/{profile_id}/dashboard").json()["net_balance"]

    # o usuário aprova
    approved = client.patch(
        f"/api/v1/recommendations/{rec['id']}/decision",
        json={"decision": "approved", "selected_scenario": "conservative"},
    ).json()
    assert approved["status"] == "approved"
    assert approved["selected_scenario"] == "conservative"
    assert approved["plan_id"]

    # plano preventivo criado e vinculado
    planos = client.get(f"/api/v1/profiles/{profile_id}/plans").json()
    assert [p["id"] for p in planos] == [approved["plan_id"]]
    assert planos[0]["risk_code"] == "GOAL_ACCELERATION_OPPORTUNITY"

    # nenhum dinheiro se moveu
    assert client.get(f"/api/v1/profiles/{profile_id}/dashboard").json()["net_balance"] == saldo_antes

    # o card não fica exibindo o plano aprovado: procura a próxima ação
    depois = client.get(f"/api/v1/profiles/{profile_id}/insight").json()
    assert depois["recommendation"] is None
    assert depois["diagnosis"] is not None

    # e o registro guarda o desfecho
    registro = client.get(f"/api/v1/profiles/{profile_id}/recommendations").json()
    assert [r["status"] for r in registro] == ["approved"]


def test_rejeitar_libera_o_card_e_nao_cria_plano(client: TestClient) -> None:
    profile_id = _profile_com_folga(client)
    rec = client.post(f"/api/v1/profiles/{profile_id}/recommendations/detect").json()["recommendation"]

    rejected = client.patch(
        f"/api/v1/recommendations/{rec['id']}/decision", json={"decision": "rejected"}
    ).json()
    assert rejected["status"] == "rejected"
    assert rejected["selected_scenario"] is None
    assert rejected["plan_id"] is None

    assert client.get(f"/api/v1/profiles/{profile_id}/plans").json() == []
    assert client.get(f"/api/v1/profiles/{profile_id}/insight").json()["recommendation"] is None


def test_detectar_de_novo_sem_mudanca_nao_duplica(client: TestClient) -> None:
    profile_id = _profile_com_folga(client)
    primeira = client.post(f"/api/v1/profiles/{profile_id}/recommendations/detect").json()
    segunda = client.post(f"/api/v1/profiles/{profile_id}/recommendations/detect").json()

    assert primeira["recommendation"]["id"] == segunda["recommendation"]["id"]
    assert len(client.get(f"/api/v1/profiles/{profile_id}/recommendations").json()) == 1


def test_dados_novos_criam_versao_encadeada(client: TestClient) -> None:
    profile_id = _profile_com_folga(client)
    primeira = client.post(f"/api/v1/profiles/{profile_id}/recommendations/detect").json()["recommendation"]

    _add_despesa(client, profile_id)
    segunda = client.post(f"/api/v1/profiles/{profile_id}/recommendations/detect").json()["recommendation"]

    assert segunda["supersedes_id"] == primeira["id"]
    anterior = client.get(f"/api/v1/recommendations/{primeira['id']}").json()
    assert anterior["status"] == "superseded"
    assert anterior["superseded_by_id"] == segunda["id"]
    # A versão antiga não foi apagada nem reescrita.
    assert anterior["payload"] == primeira["payload"]


def test_recomendacao_defasada_nao_pode_ser_aprovada(client: TestClient) -> None:
    profile_id = _profile_com_folga(client)
    rec = client.post(f"/api/v1/profiles/{profile_id}/recommendations/detect").json()["recommendation"]

    _add_despesa(client, profile_id)
    assert client.get(f"/api/v1/profiles/{profile_id}/insight").json()["recommendation"]["stale"] is True

    response = client.patch(
        f"/api/v1/recommendations/{rec['id']}/decision",
        json={"decision": "approved", "selected_scenario": "recommended"},
    )
    assert response.status_code == 409
    assert "Recalcule" in response.json()["detail"]
    assert client.get(f"/api/v1/profiles/{profile_id}/plans").json() == []


def test_nao_se_decide_duas_vezes(client: TestClient) -> None:
    profile_id = _profile_com_folga(client)
    rec = client.post(f"/api/v1/profiles/{profile_id}/recommendations/detect").json()["recommendation"]
    client.patch(f"/api/v1/recommendations/{rec['id']}/decision", json={"decision": "rejected"})

    segunda = client.patch(
        f"/api/v1/recommendations/{rec['id']}/decision", json={"decision": "approved"}
    )
    assert segunda.status_code == 409


def test_registro_filtra_por_status(client: TestClient) -> None:
    profile_id = _profile_com_folga(client)
    primeira = client.post(f"/api/v1/profiles/{profile_id}/recommendations/detect").json()["recommendation"]
    _add_despesa(client, profile_id)
    segunda = client.post(f"/api/v1/profiles/{profile_id}/recommendations/detect").json()["recommendation"]
    client.patch(
        f"/api/v1/recommendations/{segunda['id']}/decision",
        json={"decision": "approved", "selected_scenario": "recommended"},
    )

    base = f"/api/v1/profiles/{profile_id}/recommendations"
    assert [r["id"] for r in client.get(f"{base}?status=superseded").json()] == [primeira["id"]]
    assert [r["id"] for r in client.get(f"{base}?status=approved").json()] == [segunda["id"]]
    assert client.get(f"{base}?status=pending").json() == []
    assert len(client.get(base).json()) == 2


def test_recomendacao_da_conversa_exige_gesto_explicito(client: TestClient) -> None:
    profile_id = _profile_com_folga(client)

    saved = client.post(
        f"/api/v1/profiles/{profile_id}/recommendations/from-conversation",
        json={
            "conversation_id": "conv-1",
            "message_id": "msg-9",
            "payload": {"status": "available", "summary": "Usar o 13º para antecipar a meta"},
        },
    )
    assert saved.status_code == 201
    body = saved.json()
    assert body["source"] == "conversation"
    assert body["conversation_id"] == "conv-1"
    assert body["message_id"] == "msg-9"
    assert body["status"] == "pending"

    registro = client.get(f"/api/v1/profiles/{profile_id}/recommendations").json()
    assert [r["source"] for r in registro] == ["conversation"]


def test_recomendacao_inexistente_devolve_404(client: TestClient) -> None:
    assert client.get("/api/v1/recommendations/nao-existe").status_code == 404
    assert (
        client.patch(
            "/api/v1/recommendations/nao-existe/decision", json={"decision": "approved"}
        ).status_code
        == 404
    )

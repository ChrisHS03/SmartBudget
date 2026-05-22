from pathlib import Path
import sys

from importlib import util

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "backend" / "api.py"
BACKEND_PATH = ROOT / "backend"

if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

spec = util.spec_from_file_location("api", API_PATH)
assert spec is not None
assert spec.loader is not None
api = util.module_from_spec(spec)
spec.loader.exec_module(api)


def test_upsert_month_year_row_replaces_existing_row():
    existing = pd.DataFrame([
        {"month": "January", "year": 2026, "income": 1000, "housingExpenses": 200, "foodExpenses": 100, "transportationExpenses": 50, "entertainmentExpenses": 25, "otherExpenses": 10},
        {"month": "February", "year": 2026, "income": 1100, "housingExpenses": 250, "foodExpenses": 100, "transportationExpenses": 50, "entertainmentExpenses": 25, "otherExpenses": 10},
    ])
    new_row = pd.DataFrame([
        {"month": "January", "year": 2026, "income": 1500, "housingExpenses": 300, "foodExpenses": 120, "transportationExpenses": 60, "entertainmentExpenses": 30, "otherExpenses": 15},
    ])

    result = api.upsert_month_year_row(existing, new_row)

    january = result[(result["month"] == "January") & (result["year"] == 2026)].iloc[0]

    assert len(result) == 2
    assert int(january["income"]) == 1500
    assert int(january["housingExpenses"]) == 300


def test_get_api_returns_saved_rows(monkeypatch):
    frame = pd.DataFrame([
        {"month": "March", "year": 2026, "income": 2000, "housingExpenses": 500, "foodExpenses": 200, "transportationExpenses": 100, "entertainmentExpenses": 50, "otherExpenses": 25},
    ])
    monkeypatch.setattr(api, "load_data_frame", lambda: frame)

    client = api.app.test_client()
    response = client.get("/api")

    payload = response.get_json()

    assert response.status_code == 200
    assert payload["data"][0]["month"] == "March"
    assert payload["data"][0]["income"] == 2000


def test_post_api_saves_payload(monkeypatch):
    captured = {}

    def fake_save(data_frame):
        captured["data_frame"] = data_frame.copy()

    monkeypatch.setattr(api, "load_data_frame", lambda: pd.DataFrame(columns=api.FIELDNAMES))
    monkeypatch.setattr(api, "save_data_frame", fake_save)

    client = api.app.test_client()
    payload = {
        "month": "April",
        "year": 2026,
        "income": 2500,
        "housingExpenses": 700,
        "foodExpenses": 300,
        "transportationExpenses": 150,
        "entertainmentExpenses": 75,
        "otherExpenses": 40,
    }

    response = client.post("/api", json=payload)

    assert response.status_code == 200
    assert response.get_json()["data"] == payload
    assert captured["data_frame"].iloc[0]["month"] == "April"
    assert int(captured["data_frame"].iloc[0]["income"]) == 2500


def test_chat_endpoint_returns_llm_response(monkeypatch):
    monkeypatch.setattr(api, "load_data_frame", lambda: pd.DataFrame([
        {"month": "May", "year": 2026, "income": 3000, "housingExpenses": 900, "foodExpenses": 300, "transportationExpenses": 100, "entertainmentExpenses": 75, "otherExpenses": 50},
    ]))
    monkeypatch.setattr(api, "ask_financial_question", lambda question, data_frame: f"Advice for: {question}")

    client = api.app.test_client()
    response = client.post("/api/chat", json={"question": "How can I save more?", "year": 2026})

    payload = response.get_json()

    assert response.status_code == 200
    assert payload["response"] == "Advice for: How can I save more?"
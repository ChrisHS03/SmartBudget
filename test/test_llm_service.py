import sys
from importlib import util
from pathlib import Path

import httpx
import pandas as pd
from mistralai.client.errors.sdkerror import SDKError

ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = ROOT / "backend"
LLM_PATH = BACKEND_PATH / "llmService.py"

if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

spec = util.spec_from_file_location("llmService", LLM_PATH)
assert spec is not None
assert spec.loader is not None
llm_service = util.module_from_spec(spec)
spec.loader.exec_module(llm_service)


def test_build_financial_context_summarizes_finances():
    frame = pd.DataFrame([
        {"month": "January", "year": 2026, "income": 1000, "housingExpenses": 200, "foodExpenses": 100, "transportationExpenses": 50, "entertainmentExpenses": 25, "otherExpenses": 10},
        {"month": "February", "year": 2026, "income": 1200, "housingExpenses": 250, "foodExpenses": 120, "transportationExpenses": 60, "entertainmentExpenses": 30, "otherExpenses": 15},
    ])

    context = llm_service.build_financial_context(frame)

    assert "Yearly income:" in context
    assert "Yearly expenses:" in context
    assert "January" in context
    assert "February" in context


def test_ask_financial_question_translates_sdk_error(monkeypatch):
    class FakeChat:
        def complete(self, *args, **kwargs):
            raw_response = httpx.Response(
                429,
                content=b'{"message":"Service tier capacity exceeded for this model."}',
                headers={"content-type": "application/json"},
            )
            raise SDKError(
                "API error occurred",
                raw_response,
                '{"message":"Service tier capacity exceeded for this model."}',
            )

    class FakeClient:
        chat = FakeChat()

    monkeypatch.setattr(llm_service, "get_client", lambda: FakeClient())

    frame = pd.DataFrame([
        {"month": "January", "year": 2026, "income": 1000, "housingExpenses": 200, "foodExpenses": 100, "transportationExpenses": 50, "entertainmentExpenses": 25, "otherExpenses": 10},
    ])

    try:
        llm_service.ask_financial_question("What should I do?", frame)
    except RuntimeError as exc:
        assert "temporarily unavailable" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError to be raised")

from importlib import util
from pathlib import Path
import sys

import pandas as pd

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
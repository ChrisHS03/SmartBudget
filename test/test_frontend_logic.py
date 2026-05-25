from importlib import util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONT_PATH = ROOT / "frontend" / "front.py"

spec = util.spec_from_file_location("front", FRONT_PATH)
assert spec is not None
assert spec.loader is not None
front = util.module_from_spec(spec)
spec.loader.exec_module(front)


def test_build_monthly_overview_uses_last_entry_and_calculates_totals():
    entries = [
        {"month": "January", "year": 2026, "income": "1000", "housingExpenses": "200", "foodExpenses": "100", "transportationExpenses": "50", "entertainmentExpenses": "25", "otherExpenses": "10"},
        {"month": "January", "year": 2026, "income": "1200", "housingExpenses": "300", "foodExpenses": "120", "transportationExpenses": "60", "entertainmentExpenses": "30", "otherExpenses": "15"},
        {"month": "February", "year": 2026, "income": "1300", "housingExpenses": "250", "foodExpenses": "110", "transportationExpenses": "70", "entertainmentExpenses": "35", "otherExpenses": "20"},
    ]

    display_df = front.build_monthly_overview(entries, 2026)

    january = display_df[display_df["Month"] == "January"].iloc[0]
    february = display_df[display_df["Month"] == "February"].iloc[0]

    assert list(display_df["Month"]) == front.MONTHS
    assert int(january["Income"]) == 1200
    assert int(january["Total Expenses"]) == 525
    assert int(january["Balance"]) == 675
    assert int(february["Total Expenses"]) == 485
    assert int(february["Balance"]) == 815

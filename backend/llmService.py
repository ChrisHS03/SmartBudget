import os
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from mistralai.client.errors.sdkerror import SDKError
from mistralai.client.sdk import Mistral

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "ministral-3b-2512")

NUMERIC_COLUMNS = [
    "year",
    "income",
    "housingExpenses",
    "foodExpenses",
    "transportationExpenses",
    "entertainmentExpenses",
    "otherExpenses",
]

EXPENSE_COLUMNS = [
    "housingExpenses",
    "foodExpenses",
    "transportationExpenses",
    "entertainmentExpenses",
    "otherExpenses",
]


def get_client() -> Mistral:
    return Mistral(api_key=os.environ["MISTRAL_API_KEY"])


def normalize_financial_data(data_frame: pd.DataFrame) -> pd.DataFrame:
    normalized = data_frame.copy()

    for column in NUMERIC_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = pd.NA

    for column in NUMERIC_COLUMNS:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")

    return normalized


def build_budget_metrics(data_frame: pd.DataFrame) -> tuple[pd.DataFrame, float, float, float, float, float]:
    normalized = normalize_financial_data(data_frame)

    expense_values = normalized[EXPENSE_COLUMNS].to_numpy(dtype=float)
    total_expenses = np.nansum(expense_values, axis=1)
    balance = normalized["income"].to_numpy(dtype=float) - total_expenses

    normalized["totalExpenses"] = total_expenses
    normalized["balance"] = balance

    yearly_income = float(np.nansum(normalized["income"].to_numpy(dtype=float)))
    yearly_expenses = float(np.nansum(total_expenses))
    yearly_balance = float(np.nansum(balance))
    average_monthly_expenses = float(np.nanmean(total_expenses)) if len(total_expenses) else 0.0
    savings_rate = (yearly_balance / yearly_income * 100.0) if yearly_income else 0.0

    return (
        normalized,
        yearly_income,
        yearly_expenses,
        yearly_balance,
        average_monthly_expenses,
        savings_rate,
    )


def build_financial_context(data_frame: pd.DataFrame) -> str:
    if data_frame.empty:
        return "No financial data is available yet."

    normalized, yearly_income, yearly_expenses, yearly_balance, average_monthly_expenses, savings_rate = build_budget_metrics(data_frame)

    cols = ["month", "year", "income", "totalExpenses", "balance"]
    top_rows = normalized[cols].head(6)
    top_rows_text = top_rows.to_string(index=False)

    return (
        f"Yearly income: {yearly_income:,.2f}\n"
        f"Yearly expenses: {yearly_expenses:,.2f}\n"
        f"Yearly balance: {yearly_balance:,.2f}\n"
        f"Average monthly expenses: {average_monthly_expenses:,.2f}\n"
        f"Savings rate: {savings_rate:.1f}%\n\n"
        f"Sample budget rows:\n{top_rows_text}"
    )


def ask_financial_question(question: str, data_frame: pd.DataFrame) -> str:
    context = build_financial_context(data_frame)
    try:
        response = get_client().chat.complete(
            model=MISTRAL_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a financial assistant inside a budgeting app. "
                        "Use the provided budget context to answer clearly and practically. "
                        "Do not claim certainty beyond the data. Keep advice concise and helpful."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Budget context:\n{context}\n\nUser question: {question}",
                },
            ],
        )
    except SDKError as exc:
        message = str(exc)
        if "Service tier capacity exceeded" in message:
            raise RuntimeError("LLM service is temporarily unavailable. Please try again later.") from exc
        raise RuntimeError(f"LLM request failed: {message}") from exc

    choice = response.choices[0]
    message = choice.message
    if message is None or message.content is None:
        return ""

    return str(message.content)


if __name__ == "__main__":
    sample_frame = pd.DataFrame(
        [
            {
                "month": "January",
                "year": 2026,
                "income": 2000,
                "housingExpenses": 800,
                "foodExpenses": 300,
                "transportationExpenses": 100,
                "entertainmentExpenses": 75,
                "otherExpenses": 50,
            }
        ]
    )
    print(ask_financial_question("What should I focus on to improve my finances?", sample_frame))

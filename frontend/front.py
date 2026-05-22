import os
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

try:
    import catppuccin
except ImportError:
    catppuccin = None

st.set_page_config(layout="wide")

# API base URL (containerized use should set API_URL to e.g. http://backend:3000)
API_BASE = os.environ.get("API_URL", "http://backend:3000")
api_url = f"{API_BASE}/api"

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]
EXPENSE_COLUMNS = ["housingExpenses", "foodExpenses", "transportationExpenses", "entertainmentExpenses", "otherExpenses"]


def build_monthly_overview(entries, selected_year):
    df_entries = pd.DataFrame(entries)

    if df_entries.empty:
        df_year = pd.DataFrame()
    else:
        df_entries["year"] = pd.to_numeric(
            df_entries.get("year", pd.Series()),
            errors="coerce",
        ).fillna(datetime.today().year).astype(int)
        df_year = df_entries[df_entries["year"] == int(selected_year)].copy()

    if not df_year.empty:
        df_year = df_year.drop_duplicates(subset=["month"], keep="last")

    df_months = pd.DataFrame({"Month": MONTHS})
    if df_year.empty:
        df_merged = df_months
    else:
        df_year = df_year.rename(columns={"month": "Month"})
        df_merged = df_months.merge(df_year, on="Month", how="left")

    for col in ["income"] + EXPENSE_COLUMNS:
        if col in df_merged.columns:
            df_merged[col] = pd.to_numeric(df_merged[col], errors="coerce")
        else:
            df_merged[col] = pd.NA

    df_merged["Total Expenses"] = df_merged[EXPENSE_COLUMNS].sum(axis=1)
    df_merged["Balance"] = df_merged["income"] - df_merged["Total Expenses"]

    display_cols = ["Month", "income"] + EXPENSE_COLUMNS + ["Total Expenses", "Balance"]
    return df_merged[display_cols].rename(columns={
        "income": "Income",
        "housingExpenses": "Housing",
        "foodExpenses": "Food",
        "transportationExpenses": "Transport",
        "entertainmentExpenses": "Entertainment",
        "otherExpenses": "Other",
    })

def main():
    st.title("Smart Budget")
    st.write("Welcome to Smart Budget! Get a grip over your financial situation.")

    selected_year = None

    if "status_message" not in st.session_state:
        st.session_state.status_message = None

    if st.session_state.status_message:
        st.success(st.session_state.status_message)
        st.session_state.status_message = None

    try:
        response = requests.get(f"{api_url}")
        if response.status_code == 200:
            payload = response.json()
            entries = payload.get("data", []) or []

            # build DataFrame once and vectorize computations
            df_entries = pd.DataFrame(entries)
            if df_entries.empty:
                years = [datetime.today().year]
            else:
                # coerce year to int where possible
                df_entries["year"] = pd.to_numeric(df_entries.get("year", pd.Series()), errors="coerce").fillna(datetime.today().year).astype(int)
                years = sorted(df_entries["year"].unique())

            col_year, col_spacer = st.columns([1, 5])
            with col_year:
                selected_year = st.selectbox("Year", years, index=len(years) - 1)

            if selected_year is None:
                st.error("Please select a year before continuing.")
                return

            selected_year_int = int(selected_year)

            display_df = build_monthly_overview(entries, selected_year_int)

            # style and render
            fmt_cols = [c for c in display_df.columns if c != "Month"]
            styler = display_df.style.format({c: '{:,.2f}' for c in fmt_cols}, na_rep="")

            def _balance_style(s):
                return [
                    'color: green;' if v > 0 else ('color: red;' if v < 0 else '')
                    for v in s
                ]

            totalYearIncome = display_df["Income"].sum()
            totalYearExpenses = display_df["Total Expenses"].sum()
            totalYearBalance = display_df["Balance"].sum()

            st.subheader(f"Yearly summary — {selected_year_int}")
            st.write(f"Total Income: {totalYearIncome:,.2f}")
            st.write(f"Total Expenses: {totalYearExpenses:,.2f}")
            st.write(f"Total Balance: {totalYearBalance:,.2f}")
            styler = styler.apply(_balance_style, subset=["Balance"])
            st.subheader(f"Monthly overview — {selected_year_int}")

            # Charts always render in a two-column layout
            df_plot = display_df.copy().fillna(0)
            df_plot = df_plot.set_index("Month").reindex(MONTHS).fillna(0)

            # light, clean style matching Streamlit aesthetics
            style_name = catppuccin.PALETTE.mocha.identifier if catppuccin else "default"
            theme = catppuccin.PALETTE.mocha if catppuccin else None
            palette = [
                theme.colors.blue.hex,
                theme.colors.green.hex,
                theme.colors.peach.hex,
                theme.colors.mauve.hex,
                theme.colors.pink.hex,
            ] if theme else ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
            line_colors = [theme.colors.blue.hex, theme.colors.peach.hex] if theme else ["#1f77b4", "#ff7f0e"]

            chart_col1, chart_col2 = st.columns(2)

            # Stacked bar: expenses by category per month
            expense_categories = ["Housing", "Food", "Transport", "Entertainment", "Other"]
            with chart_col1:
                with plt.style.context(style_name):
                    fig1, ax1 = plt.subplots(figsize=(5, 2.8))
                    df_plot[expense_categories].plot(kind="bar", stacked=True, ax=ax1, color=palette)
                    ax1.set_title(f"Monthly Expenses — {selected_year_int}", fontsize=11)
                    ax1.set_xlabel("")
                    ax1.set_ylabel("Amount")
                    ax1.legend(title="Category", loc="upper right", frameon=False, fontsize=8, title_fontsize=8)
                    plt.tight_layout()
                    st.pyplot(fig1)
                    plt.close(fig1)

            # Line chart: Income vs Total Expenses
            with chart_col2:
                with plt.style.context(style_name):
                    fig2, ax2 = plt.subplots(figsize=(5, 2.8))
                    df_plot[["Income", "Total Expenses"]].plot(ax=ax2, marker="o", color=line_colors)
                    ax2.set_title(f"Income vs Expenses — {selected_year_int}", fontsize=11)
                    ax2.set_xlabel("")
                    ax2.set_ylabel("Amount")
                    ax2.grid(axis="y", linestyle="--", alpha=0.6)
                    ax2.legend(frameon=False, fontsize=8)
                    plt.tight_layout()
                    st.pyplot(fig2)
                    plt.close(fig2)

            st.write(styler)
        else:
            st.warning("No financial data found. Please enter your financial data.")

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")

    if "show_inputs" not in st.session_state:
        st.session_state.show_inputs = False

    if st.button("Enter Financial Data"):
        st.session_state.show_inputs = not st.session_state.show_inputs

    if st.session_state.show_inputs:
        st.subheader("Enter your monthly financial data")
        st.write("Please fill in the following details to get insights into your financial situation.")
        st.write("If you already have data for a month, you can update it by entering new values.")

        col1, col2 = st.columns(2)
        with col1:
            month = st.selectbox("Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], index=datetime.today().month - 1)
        with col2:
            year = st.number_input("Year", value=datetime.today().year, min_value=2000, step=1)
        
        income = st.text_input("Income", value="", placeholder="0.0", key="income")
        housingExpenses = st.text_input("Housing Expenses", value="", placeholder="0.0", key="housing")
        foodExpenses = st.text_input("Food Expenses", value="", placeholder="0.0", key="food")
        transportationExpenses = st.text_input("Transportation Expenses", value="", placeholder="0.0", key="transport")
        entertainmentExpenses = st.text_input("Entertainment Expenses", value="", placeholder="0.0", key="entertainment")
        otherExpenses = st.text_input("Other Expenses", value="", placeholder="0.0", key="other")

        if st.button("Submit"):
            data = {
                "month": month,
                "year": int(year),
                "income": income,
                "housingExpenses": housingExpenses,
                "foodExpenses": foodExpenses,
                "transportationExpenses": transportationExpenses,
                "entertainmentExpenses": entertainmentExpenses,
                "otherExpenses": otherExpenses
            }
            try:
                response = requests.post(f"{api_url}", json=data)
            except requests.exceptions.RequestException as e:
                st.error(f"Error submitting financial data: {e}")
                return

            if response.status_code == 200:
                payload = response.json()
                st.session_state.show_inputs = False
                st.session_state.status_message = payload.get("message", "Data submitted successfully!")
                st.rerun()
            else:
                st.error("Error submitting financial data. Please try again.")

    st.divider()
    st.subheader("Ask about your finances")
    st.write("Ask a question about your budget and get an answer based on the saved data.")

    chat_question = st.text_area(
        "Your question",
        placeholder="For example: Where am I overspending most this year?",
        key="finance_chat_question",
    )

    if st.button("Get financial advice"):
        if not chat_question.strip():
            st.warning("Type a question first.")
        else:
            try:
                chat_response = requests.post(
                    f"{api_url}/chat",
                    json={"question": chat_question, "year": selected_year_int},
                )
            except requests.exceptions.RequestException as e:
                st.error(f"Error asking for financial advice: {e}")
                return

            if chat_response.status_code == 200:
                chat_payload = chat_response.json()
                st.success(chat_payload.get("message", "Chat response generated successfully"))
                st.write(chat_payload.get("response", ""))
            else:
                error_message = "Could not get financial advice."
                try:
                    error_message = chat_response.json().get("message", error_message)
                except ValueError:
                    response_text = chat_response.text.strip()
                    if response_text:
                        error_message = response_text

                st.error(error_message)


if __name__ == "__main__":
    main()
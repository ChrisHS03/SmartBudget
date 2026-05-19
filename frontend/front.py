import os
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# API base URL (containerized use should set API_URL to e.g. http://backend:3000)
API_BASE = os.environ.get("API_URL", "http://backend:3000")
api_url = f"{API_BASE}/api"

def main():
    st.title("Smart Budget")
    st.write("Welcome to Smart Budget! Get a grip over your financial situation.")

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

            # prepare month order and names
            months = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]

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

            # filter to selected year and keep last entry per month
            df_year = df_entries[df_entries["year"] == int(selected_year)].copy() if not df_entries.empty else pd.DataFrame()
            if not df_year.empty:
                df_year = df_year.drop_duplicates(subset=["month"], keep="last")

            # create canonical months frame and merge
            df_months = pd.DataFrame({"Month": months})
            if df_year.empty:
                df_merged = df_months
            else:
                df_year = df_year.rename(columns={"month": "Month"})
                df_merged = df_months.merge(df_year, on="Month", how="left")

            # numeric columns
            expense_cols = ["housingExpenses", "foodExpenses", "transportationExpenses", "entertainmentExpenses", "otherExpenses"]
            for col in ["income"] + expense_cols:
                if col in df_merged.columns:
                    df_merged[col] = pd.to_numeric(df_merged[col], errors="coerce")
                else:
                    df_merged[col] = pd.NA

            # compute totals
            df_merged["Total Expenses"] = df_merged[expense_cols].sum(axis=1)
            df_merged["Balance"] = df_merged["income"] - df_merged["Total Expenses"]

            # build display DataFrame
            display_cols = ["Month", "income"] + expense_cols + ["Total Expenses", "Balance"]
            display_df = df_merged[display_cols].rename(columns={
                "income": "Income",
                "housingExpenses": "Housing",
                "foodExpenses": "Food",
                "transportationExpenses": "Transport",
                "entertainmentExpenses": "Entertainment",
                "otherExpenses": "Other",
            })

            # style and render
            fmt_cols = [c for c in display_df.columns if c != "Month"]
            styler = display_df.style.format({c: '{:,.2f}' for c in fmt_cols}, na_rep="")

            def _balance_style(s):
                return [
                    'color: green;' if v > 0 else ('color: red;' if v < 0 else '')
                    for v in s
                ]

            styler = styler.apply(_balance_style, subset=["Balance"])
            st.subheader(f"Monthly overview — {selected_year}")
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
                "year": year,
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
    

main()
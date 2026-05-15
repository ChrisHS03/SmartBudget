import streamlit as st
import requests
from datetime import datetime

api_url = "http://localhost:3000/api"

def main():
    st.title("Smart Budget")
    st.write("Welcome to Smart Budget! Get a grip over your financial situation.")

    try:
        response = requests.get(f"{api_url}/yearly-data/{datetime.today().year}")
        if response.status_code == 200:
            yearly_data = response.json()
          
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
        
        income = st.number_input("Income", min_value=0.0, step=100.0)
        housingExpenses = st.number_input("Housing Expenses", min_value=0.0, step=100.0)
        foodExpenses = st.number_input("Food Expenses", min_value=0.0, step=100.0)
        transportationExpenses = st.number_input("Transportation Expenses", min_value=0.0, step=100.0)
        entertainmentExpenses = st.number_input("Entertainment Expenses", min_value=0.0, step=100.0)
        otherExpenses = st.number_input("Other Expenses", min_value=0.0, step=100.0)

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
            response = requests.post(f"{api_url}", json=data)
            if response.status_code == 200:
                result = response.json()
            else:
                st.error("Error submitting financial data. Please try again.")
    

main()
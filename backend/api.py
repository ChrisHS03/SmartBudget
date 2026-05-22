from flask import Flask, request, jsonify
import os

import pandas as pd

from llmService import ask_financial_question

app = Flask(__name__)
DEFAULT_PORT = 3000

CSV_FILE = 'database.csv'
FIELDNAMES = [
    'month',
    'year',
    'income',
    'housingExpenses',
    'foodExpenses',
    'transportationExpenses',
    'entertainmentExpenses',
    'otherExpenses',
]

def ensure_csv_exists():
    if not os.path.exists(CSV_FILE):
        pd.DataFrame(columns=FIELDNAMES).to_csv(CSV_FILE, index=False)


def load_data_frame():
    ensure_csv_exists()
    return pd.read_csv(CSV_FILE)


def save_data_frame(data_frame):
    data_frame.to_csv(CSV_FILE, index=False)


def normalize_year_column(data_frame):
    data_frame = data_frame.copy()
    data_frame['year'] = pd.to_numeric(data_frame['year'], errors='coerce')
    return data_frame


def upsert_month_year_row(existing_data, new_row):
    existing_data = normalize_year_column(existing_data)
    new_row = normalize_year_column(new_row)

    month = new_row.iloc[0]['month']
    year = new_row.iloc[0]['year']

    same_month_and_year = (existing_data['month'] == month) & (existing_data['year'] == year)
    remaining_rows = existing_data.loc[~same_month_and_year]

    return pd.concat([remaining_rows, new_row], ignore_index=True)

@app.route('/api', methods=['POST'])
def receive_data():
    data = request.get_json()
    existing_data = load_data_frame()
    updated_data = upsert_month_year_row(existing_data, pd.DataFrame([data]))
    save_data_frame(updated_data)
    return jsonify({"message": "Data received successfully", "data": data}), 200

@app.route('/api', methods=['GET'])
def get_data():
    data = load_data_frame().to_dict('records')
    return jsonify({"message": "Data fetched successfully", "data": data}), 200


@app.route('/api/chat', methods=['POST'])
def chat_about_finances():
    payload = request.get_json() or {}
    question = str(payload.get("question", "")).strip()

    if not question:
        return jsonify({"message": "Question is required"}), 400

    data_frame = load_data_frame()

    selected_year = payload.get("year")
    if selected_year not in (None, "", 0):
        try:
            year_value = int(selected_year)
            data_frame = data_frame[pd.to_numeric(data_frame["year"], errors="coerce") == year_value]
        except (TypeError, ValueError, KeyError):
            pass

    try:
        response_text = ask_financial_question(question, data_frame)
    except RuntimeError as exc:
        return jsonify({"message": str(exc)}), 500

    return jsonify({"message": "Chat response generated successfully", "response": response_text}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=DEFAULT_PORT)

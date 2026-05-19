FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY frontend/ /app/frontend/

ENV PYTHONUNBUFFERED=1
EXPOSE 8501

# Run Streamlit on all interfaces so it's reachable from the host/container
CMD ["streamlit", "run", "frontend/front.py", "--server.port", "8501", "--server.address", "0.0.0.0"]

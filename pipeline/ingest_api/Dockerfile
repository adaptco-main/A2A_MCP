FROM python:3.11-slim

WORKDIR /app

# Copy dependencies and application code
COPY ./ingest_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./ingest_api/main.py .

# Copy shared libraries
COPY ./lib /app/lib
COPY ./schemas /app/schemas

# Create ledger directory
RUN mkdir -p /app/ledger

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

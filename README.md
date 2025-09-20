# Task Middleware

FastAPI service to synchronize tasks between Monday.com and Airtable with
verification gates.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -e .[development]
cp .env.example .env
```

## Development

Run tests and linters:

```bash
pytest
```

Start server:

```bash
uvicorn app.main:app --reload
```

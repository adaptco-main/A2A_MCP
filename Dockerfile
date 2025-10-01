# syntax=docker/dockerfile:1
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Copy application code and static artefacts required by the server.
COPY app ./app
COPY specs ./specs
COPY public ./public

EXPOSE 8080

CMD ["python", "-m", "app.server"]

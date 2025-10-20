# syntax=docker/dockerfile:1
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

COPY app ./app
COPY codex_qernel ./codex_qernel
COPY capsules ./capsules
COPY scripts ./scripts
COPY README.md ./README.md

RUN mkdir -p var/log

EXPOSE 8080

CMD ["python", "app/server.py"]

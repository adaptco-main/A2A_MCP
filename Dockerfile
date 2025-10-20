# syntax=docker/dockerfile:1
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Copy only the server implementation to keep image lean.
COPY app/server.py ./server.py

EXPOSE 8080

CMD ["python", "server.py"]

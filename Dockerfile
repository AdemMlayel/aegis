FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN python -m pip install --upgrade pip \
    && python -m pip install -e ".[dev,worker]"

# S11: run as a non-root user. The image is built with source copied in; create
# an unprivileged user and hand it ownership of the app + generated artifact
# tree so the container never runs the API/worker as root.
RUN useradd --create-home --uid 10001 aegis \
    && mkdir -p /app/generated \
    && chown -R aegis:aegis /app
USER aegis

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

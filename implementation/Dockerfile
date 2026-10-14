FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY mvp_vertical ./mvp_vertical

RUN python -m pip install --no-cache-dir ".[cockpit]" \
    && useradd --create-home --uid 10001 pantheon

USER pantheon

EXPOSE 8081

CMD ["mvp-cockpit-api"]

FROM python:3.11-slim AS builder

WORKDIR /build

COPY pyproject.toml README.md LICENSE ./
COPY comfy_headless/ comfy_headless/

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ".[ui,ai,websocket,health]"

FROM python:3.11-slim

RUN groupadd -r comfy && useradd -r -g comfy comfy

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY --chown=comfy:comfy comfy_headless/ comfy_headless/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 7861

USER comfy

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7861')" || exit 1

CMD ["python", "-m", "comfy_headless", "--port", "7861"]

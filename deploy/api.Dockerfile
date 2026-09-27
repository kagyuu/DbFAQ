# backend(FastAPI)のイメージ。docs/P005-impl-plan.md U006・U007、ADR-012
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1

WORKDIR /app/server
COPY server/pyproject.toml server/uv.lock server/.python-version server/INDEX.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY server/src ./src
RUN uv sync --frozen --no-dev

RUN useradd -u 10001 -M -s /usr/sbin/nologin dbfaq && mkdir -p /data /config && chown dbfaq /data

ENV PATH=/app/server/.venv/bin:$PATH \
    DBFAQ_CONFIG=/config/config.yaml \
    DBFAQ_SQLITE_PATH=/data/dbfaq.sqlite3

USER dbfaq
EXPOSE 8000
# refresh のロックと Oracle の接続プールがプロセス内にあるため 1 ワーカー固定(ADR-014)
CMD ["uvicorn", "--factory", "dbfaq_api.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

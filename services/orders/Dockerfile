FROM python:3.10.6-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install system deps for psycopg2
# RUN apt-get update && apt-get install -y \
#     gcc \
#     libpq-dev \
#     && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /bin/

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Clean any bad venv
RUN rm -rf /app/.venv

# Install Python deps
RUN uv sync --frozen --no-install-project

# Copy app
COPY . .

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["/app/entrypoint.sh"]

EXPOSE 5678

CMD ["python", "-m", "debugpy", "--wait-for-client", "--listen", "0.0.0.0:5678", "manage.py", "runserver", "0.0.0.0:8003", "--nothreading", "--noreload"]
# CMD ["python", "-m", "manage.py", "runserver", "0.0.0.0:8003", "--nothreading", "--noreload"]
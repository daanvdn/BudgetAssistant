FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Copy dependency files
COPY ../pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Ensure virtual environment is on PATH
ENV PATH="/app/.venv/bin:${PATH}"

# Ensure Python can import the `app` package from the copied `src/` folder
ENV PYTHONPATH="/app/src:${PYTHONPATH}"

# Copy application code
COPY ../src ./src/

# Copy alembic migration files
COPY ../alembic.ini ./
COPY ../alembic ./alembic/
COPY migrate.py ./
COPY ../auto_migrate.py ./

# Copy and setup entrypoint script
COPY docker-entrypoint.sh ./
# Convert Windows line endings (CRLF) to Unix (LF) and make executable
RUN sed -i 's/\r$//' docker-entrypoint.sh && chmod +x docker-entrypoint.sh

# Expose port
EXPOSE 8000

# Use entrypoint to run migrations before starting the app
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

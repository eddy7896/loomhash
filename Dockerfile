FROM python:3.12-slim

WORKDIR /app

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Copy project files
COPY pyproject.toml .
COPY README.md .

# Install dependencies (no test dependencies)
RUN pip install --no-cache-dir .

# Copy application source code
COPY loomhash/ ./loomhash/

EXPOSE 8000

# Start Uvicorn, proxy headers enabled for reverse proxy usage (e.g. Caddy)
CMD ["uvicorn", "loomhash.api.main_prod:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]

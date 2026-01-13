# Use a modern Python image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install uv for fast package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml .
COPY README.md .
COPY python-sdk/ python-sdk/

# Install dependencies using uv
RUN uv sync --no-dev

# Copy the rest of the application
COPY src/ src/

# Expose the port for SSE (matching the default or user-provided port)
EXPOSE 8000

# Run the MCP server in SSE mode
# We use --host 0.0.0.0 to make it accessible inside the container
CMD ["uv", "run", "python", "-m", "src.main", "--transport", "http", "--host", "0.0.0.0", "--port", "8000"]

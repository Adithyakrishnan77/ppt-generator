# Use a specific, slim Python version
FROM python:3.11-slim AS base

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# ---- Builder Stage ----
# This stage installs Python dependencies to keep the final image smaller.
FROM base AS builder

# Install build tools needed for some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends build-essential

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# ---- Production Stage ----
# This is the final, lean image for your application.
FROM base AS final
WORKDIR /app

# Install curl to download Ollama and create a non-root user
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    addgroup --system --gid 1001 python-group && \
    adduser --system --uid 1001 --ingroup python-group python-user && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Download and install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Create a non-root user
# Copy installed dependencies from the builder stage
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy your application code
# The .dockerignore file will prevent unnecessary files from being copied.
COPY . .

# Switch to the non-root user
USER python-user

# Expose the port your app runs on
EXPOSE 8501

# Command to run your Streamlit application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

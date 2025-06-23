FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        g++ \
        make \
        libc6-dev \
        libffi-dev \
        libssl-dev \
        curl \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install wheel
RUN pip install --upgrade pip setuptools wheel

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --verbose -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' botuser \
    && chown -R botuser:botuser /app

# Switch to non-root user
USER botuser

# Health check - check if bot process is running
HEALTHCHECK --interval=60s --timeout=30s --start-period=10s --retries=3 \
    CMD pgrep -f "python.*bot.py" > /dev/null || exit 1

# Run the bot
CMD ["python", "bot.py"]
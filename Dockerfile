# Use a smaller base image
FROM python:3.10-slim AS builder

WORKDIR /code

# Set environment variables for security, performance, and unbuffered output
ENV PYTHONDONTWRITEBYTECODE 1 \
    PYTHONUNBUFFERED 1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install gcc and other dependencies, then remove them after use
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /code/requirements.txt

# Install requirements and remove unnecessary files
RUN pip install --no-cache-dir -r /code/requirements.txt \
    && find /usr/local -depth \
        \( \
          \( -type d -a \( -name test -o -name tests \) \) \
          -o \
          \( -type f -a \( -name '*.pyc' -o -name '*.pyo' \) \) \
        \) -exec rm -rf '{}' +

# Multi-stage build
FROM python:3.10-slim

WORKDIR /code

# Copy the entire Python install directory from the previous stage
COPY --from=builder /usr/local /usr/local

# Upgrade packages, install tini, create a non-root user, and clean up
RUN set -ex \
    && apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y tini libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0 libharfbuzz-subset0 poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the application code
COPY /app /code/app

ENV PYTHONPATH "${PYTHONPATH}:/code"

# Set tini as the entry point
ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--workers", "1", "--timeout-keep-alive", "5", "--timeout-graceful-shutdown", "15", "--port", "4000"]

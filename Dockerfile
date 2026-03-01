# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim

# Install poppler for pdf2image (PDF → PNG conversion)
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
  && rm -rf /var/lib/apt/lists/*

LABEL maintainer="Mahendran Selvakumar"
LABEL description="AWS User Group Participation Certificate Generator"

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY app.py        ./
COPY cli.py        ./
COPY pyproject.toml ./
COPY requirements.txt ./
COPY src/          ./src/
COPY templates/    ./templates/
COPY config/       ./config/
COPY assets/       ./assets/

# Create output and fonts directories
RUN mkdir -p output/pdfs assets/fonts

# Expose port
EXPOSE 8080

# Non-root user for security
RUN useradd -m -u 1001 certuser && chown -R certuser:certuser /app
USER certuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/')" || exit 1

CMD ["python", "app.py"]

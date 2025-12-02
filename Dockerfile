# Whisper Transcription Service
# Optimized build for smaller image size

FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install only faster-whisper (smaller than openai-whisper)
# This avoids installing full PyTorch
RUN pip install --no-cache-dir \
    flask>=2.0.0 \
    faster-whisper>=0.10.0 \
    gunicorn>=21.0.0

# Copy application code
COPY app.py .

# Create temp directory for audio processing
RUN mkdir -p /app/temp

# Environment variables
ENV PORT=5000
ENV WHISPER_MODEL=base
ENV WHISPER_DEVICE=cpu
ENV PRELOAD_MODEL=true
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "300", "app:app"]

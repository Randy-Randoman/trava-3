FROM python:3.11-slim

WORKDIR /app

# Browsers go to a shared path so the non-root user can read them
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install dependencies (no dev packages) and Chromium for Booking.com scraping.
# --with-deps installs Chromium's system libraries via apt, so it runs as root.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

# Copy application code
COPY . .

# Run as non-root user
RUN useradd --create-home --uid 1001 trava
USER trava

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Start command - Railway sets PORT automatically
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]

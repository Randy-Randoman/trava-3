FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ .

# Copy skills package (lives at project root)
COPY skills/ /app/skills/

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Start command - Railway sets PORT automatically
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]

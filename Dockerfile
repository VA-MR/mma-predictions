# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Copy frontend files
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./

# Build frontend with environment variable
ARG VITE_TELEGRAM_BOT_USERNAME
ENV VITE_TELEGRAM_BOT_USERNAME=$VITE_TELEGRAM_BOT_USERNAME

RUN npm run build


# Stage 2: Python backend with frontend static files
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY api/ ./api/
COPY database/ ./database/
COPY scraper/ ./scraper/
COPY main.py ./

# Copy frontend build from previous stage
COPY --from=frontend-builder /frontend/dist ./frontend/dist

# Copy database if exists (for staging with data)
COPY mma_data.db* ./

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]


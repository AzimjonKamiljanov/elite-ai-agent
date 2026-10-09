# Use official Python lightweight image
FROM python:3.12-slim AS builder

# Set the working directory
WORKDIR /app

# Upgrade pip and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Final production stage
FROM python:3.12-slim

# Copy installed site-packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app

# Copy the rest of the app
COPY . /app

# Command to run Jarvis
CMD ["python", "start.py"]

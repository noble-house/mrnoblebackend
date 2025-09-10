#!/bin/bash

# Railway startup script for MrNoble Backend
echo "Starting MrNoble Backend..."

# Run database migrations
echo "Running database migrations..."
python migrate.py upgrade

# Start the application
echo "Starting FastAPI application..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT

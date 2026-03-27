#!/bin/bash
# Production start script for Render

# Exit on error
set -e

echo "🚀 Starting WoodCarvings API..."

# Print Python version
python --version

# Start the application with production settings
exec uvicorn main:app \
  --host 0.0.0.0 \
  --port ${PORT:-8000} \
  --workers ${WEB_CONCURRENCY:-1} \
  --log-level info \
  --no-access-log

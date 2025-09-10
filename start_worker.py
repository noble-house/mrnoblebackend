#!/usr/bin/env python3
"""
Celery worker startup script for MrNoble.

Usage:
    python start_worker.py                    # Start worker with default settings
    python start_worker.py --loglevel=info    # Start with specific log level
    python start_worker.py --concurrency=4    # Start with specific concurrency
"""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.celery_app import celery_app

if __name__ == "__main__":
    # Start the Celery worker
    celery_app.worker_main([
        "worker",
        "--loglevel=info",
        "--concurrency=2",
        "--queues=default,email,ai,analytics",
        "--hostname=worker@%h"
    ] + sys.argv[1:])

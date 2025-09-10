#!/usr/bin/env python3
"""
Test runner script for MrNoble backend tests.

This script provides a convenient way to run all tests with proper configuration.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run all backend tests."""
    # Add the app directory to Python path
    app_dir = Path(__file__).parent / "app"
    sys.path.insert(0, str(app_dir))
    
    # Set environment variables for testing
    os.environ["TESTING"] = "true"
    # Use in-memory SQLite for fast testing (no file I/O)
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"  # Use different DB for tests
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["SENDGRID_API_KEY"] = "test-sendgrid-key"
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    
    # Run pytest with coverage
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--cov=app",  # Coverage for app module
        "--cov-report=html",  # HTML coverage report
        "--cov-report=term-missing",  # Show missing lines in terminal
        "--cov-fail-under=80",  # Fail if coverage is below 80%
        "-x",  # Stop on first failure
    ]
    
    print("Running backend tests...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

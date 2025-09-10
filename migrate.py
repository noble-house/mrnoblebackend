#!/usr/bin/env python3
"""
Database migration management script for MrNoble.

Usage:
    python migrate.py init          # Initialize Alembic
    python migrate.py create "message"  # Create new migration
    python migrate.py upgrade       # Apply migrations
    python migrate.py downgrade     # Rollback last migration
    python migrate.py history       # Show migration history
    python migrate.py current       # Show current revision
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

def run_command(cmd):
    """Run a command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Exit code: {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def init_alembic():
    """Initialize Alembic for the project."""
    print("Initializing Alembic...")
    return run_command("alembic init alembic")

def create_migration(message):
    """Create a new migration."""
    print(f"Creating migration: {message}")
    return run_command(f'alembic revision --autogenerate -m "{message}"')

def upgrade_database():
    """Apply all pending migrations."""
    print("Upgrading database...")
    return run_command("alembic upgrade head")

def downgrade_database():
    """Rollback the last migration."""
    print("Downgrading database...")
    return run_command("alembic downgrade -1")

def show_history():
    """Show migration history."""
    print("Migration history:")
    return run_command("alembic history")

def show_current():
    """Show current revision."""
    print("Current revision:")
    return run_command("alembic current")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    if command == "init":
        init_alembic()
    elif command == "create":
        if len(sys.argv) < 3:
            print("Please provide a migration message: python migrate.py create 'your message'")
            return
        message = sys.argv[2]
        create_migration(message)
    elif command == "upgrade":
        upgrade_database()
    elif command == "downgrade":
        downgrade_database()
    elif command == "history":
        show_history()
    elif command == "current":
        show_current()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script to run database migrations on Railway.
This can be used to manually run migrations if the automatic process fails.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

def run_migrations():
    """Run database migrations."""
    print("🚀 Starting database migration process...")
    
    # Check if DATABASE_URL is set
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable is not set!")
        return False
    
    print(f"📊 Database URL: {database_url[:20]}...")
    
    try:
        # Run the migration
        print("🔄 Running migrations...")
        result = subprocess.run(
            ["python", "migrate.py", "upgrade"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        print("✅ Migration output:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️ Migration warnings:")
            print(result.stderr)
        
        # Check current revision
        print("\n🔍 Checking current revision...")
        result = subprocess.run(
            ["python", "migrate.py", "current"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        print("📋 Current revision:")
        print(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed with exit code {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = run_migrations()
    if success:
        print("\n🎉 Database migrations completed successfully!")
    else:
        print("\n💥 Database migrations failed!")
        sys.exit(1)

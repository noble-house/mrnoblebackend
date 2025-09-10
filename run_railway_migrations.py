#!/usr/bin/env python3
"""
Script to run migrations on Railway database from local machine.
This connects to the Railway PostgreSQL database and runs migrations.
"""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

def run_railway_migrations():
    """Run migrations on Railway database."""
    print("🚀 Running migrations on Railway database...")
    
    # Get Railway database URL
    railway_db_url = input("Enter your Railway PostgreSQL DATABASE_URL: ").strip()
    
    if not railway_db_url:
        print("❌ No database URL provided!")
        return False
    
    # Set the DATABASE_URL environment variable
    os.environ["DATABASE_URL"] = railway_db_url
    
    print(f"📊 Connecting to Railway database...")
    print(f"🔗 Database URL: {railway_db_url[:30]}...")
    
    try:
        # Test connection first
        from app.db import engine
        with engine.connect() as conn:
            print("✅ Database connection successful!")
        
        # Run migrations
        print("\n🔄 Running migrations...")
        import subprocess
        
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
        
        # List tables
        print("\n📋 Listing database tables...")
        from app.db import engine
        with engine.connect() as conn:
            result = conn.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            
            tables = [row[0] for row in result]
            
            if tables:
                print(f"✅ Found {len(tables)} tables:")
                for table in tables:
                    print(f"  - {table}")
            else:
                print("⚠️ No tables found!")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed with exit code {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Railway Database Migration Tool")
    print("=" * 50)
    
    success = run_railway_migrations()
    if success:
        print("\n🎉 Railway database migrations completed successfully!")
    else:
        print("\n💥 Railway database migrations failed!")
        sys.exit(1)

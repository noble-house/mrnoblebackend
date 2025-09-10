#!/usr/bin/env python3
"""
Simple script to run Railway migrations using environment variable.
Usage: RAILWAY_DATABASE_URL="your_url" python railway_migrate.py
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

def main():
    """Run migrations on Railway database."""
    
    # Get Railway database URL from environment variable
    railway_db_url = os.getenv("RAILWAY_DATABASE_URL")
    
    if not railway_db_url:
        print("❌ RAILWAY_DATABASE_URL environment variable not set!")
        print("💡 Usage: RAILWAY_DATABASE_URL='your_url' python railway_migrate.py")
        print("💡 Or set it in your .env file")
        return False
    
    # Set the DATABASE_URL for the migration
    os.environ["DATABASE_URL"] = railway_db_url
    
    print("🚀 Running migrations on Railway database...")
    print(f"🔗 Database: {railway_db_url[:30]}...")
    
    try:
        # Test connection
        from app.db import engine
        with engine.connect() as conn:
            print("✅ Database connection successful!")
        
        # Run migrations
        print("🔄 Running migrations...")
        result = subprocess.run(
            ["python", "migrate.py", "upgrade"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        print("✅ Migration completed!")
        if result.stdout:
            print("Output:", result.stdout)
        
        # Check current revision
        result = subprocess.run(
            ["python", "migrate.py", "current"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        print("📋 Current revision:", result.stdout.strip())
        
        # List tables
        with engine.connect() as conn:
            result = conn.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            
            tables = [row[0] for row in result]
            print(f"📋 Database has {len(tables)} tables:")
            for table in tables:
                print(f"  ✅ {table}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)

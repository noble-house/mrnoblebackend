#!/usr/bin/env python3
"""
Script to check database connection and list tables.
"""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

def check_database():
    """Check database connection and list tables."""
    print("🔍 Checking database connection...")
    
    try:
        from app.db import engine, SessionLocal
        from app.models import Base
        
        # Test connection
        with engine.connect() as conn:
            print("✅ Database connection successful!")
            
            # List all tables
            result = conn.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            
            tables = [row[0] for row in result]
            
            if tables:
                print(f"\n📋 Found {len(tables)} tables:")
                for table in tables:
                    print(f"  - {table}")
            else:
                print("\n⚠️ No tables found in the database!")
                print("💡 You may need to run migrations: python migrate.py upgrade")
            
            # Check if alembic_version table exists
            if 'alembic_version' in tables:
                result = conn.execute("SELECT version_num FROM alembic_version;")
                version = result.fetchone()
                if version:
                    print(f"\n🔄 Current migration version: {version[0]}")
                else:
                    print("\n⚠️ No migration version found!")
            else:
                print("\n⚠️ Alembic version table not found!")
                print("💡 You may need to run migrations: python migrate.py upgrade")
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = check_database()
    if not success:
        sys.exit(1)

#!/usr/bin/env python3
"""
Simple script to verify database tables were created.
"""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

def verify_tables():
    """Verify that all required tables exist."""
    print("🔍 Verifying database tables...")
    
    try:
        from app.db import engine
        
        # Test connection
        with engine.connect() as conn:
            print("✅ Database connection successful!")
            
            # List all tables
            result = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
            tables = [row[0] for row in result]
            
            print(f"\n📋 Found {len(tables)} tables:")
            for table in tables:
                print(f"  ✅ {table}")
            
            # Check for required tables
            required_tables = [
                'admins', 'candidates', 'jobs', 'applications', 
                'interview_links', 'emails', 'availability_options', 
                'interviews', 'scores', 'alembic_version'
            ]
            
            print(f"\n🔍 Checking required tables:")
            missing_tables = []
            for table in required_tables:
                if table in tables:
                    print(f"  ✅ {table}")
                else:
                    print(f"  ❌ {table} - MISSING!")
                    missing_tables.append(table)
            
            if missing_tables:
                print(f"\n⚠️ Missing tables: {missing_tables}")
                return False
            else:
                print(f"\n🎉 All required tables are present!")
                return True
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = verify_tables()
    if not success:
        sys.exit(1)

#!/usr/bin/env python3
"""Simple database test script."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

try:
    from app.db import engine
    
    with engine.connect() as conn:
        result = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
        tables = [row[0] for row in result]
        print("✅ Database tables:")
        for table in tables:
            print(f"  - {table}")
        print(f"\nTotal tables: {len(tables)}")
        
except Exception as e:
    print(f"❌ Error: {e}")

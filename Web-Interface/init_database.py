#!/usr/bin/env python3
"""
Initialize the Loki IDS database.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.models.database import init_db, engine


async def main():
    """Initialize the database."""
    print("=" * 60)
    print("    Initializing Loki IDS Database")
    print("=" * 60)
    
    try:
        # Initialize database tables
        await init_db()
        print("[✓] Database initialized successfully!")
        print(f"[*] Database location: {os.path.join(os.path.dirname(__file__), 'loki_ids.db')}")
        print("[*] Tables created: alerts, signatures, stats_cache")
        
    except Exception as e:
        print(f"[!] Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

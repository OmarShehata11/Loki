#!/usr/bin/env python3
"""
Initialize the Loki IDS database.
Creates database directory and all required tables.
"""
import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.models.database import init_db, db_path


async def main():
    print("=" * 60)
    print("  Loki IDS - Database Initialization")
    print("=" * 60)
    print()

    # Create database directory if it doesn't exist
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        print(f"[*] Creating database directory: {db_dir}")
        os.makedirs(db_dir, exist_ok=True)
        print(f"[✓] Directory created")
    else:
        print(f"[✓] Database directory exists: {db_dir}")

    print()
    print(f"[*] Database path: {db_path}")

    # Check if database already exists
    if os.path.exists(db_path):
        print(f"[!] Database file already exists")
        response = input("    Reinitialize? This will NOT delete existing data (y/N): ")
        if response.lower() != 'y':
            print("[*] Initialization cancelled")
            return

    print()
    print("[*] Initializing database tables...")

    try:
        await init_db()
        print("[✓] Database initialized successfully!")
        print()
        print("Tables created:")
        print("  - alerts (security alerts and events)")
        print("  - signatures (detection signatures)")
        print("  - stats_cache (cached statistics)")
        print("  - iot_devices (IoT device registration)")
        print("  - iot_device_states (IoT device states)")
        print()

        # Check database size
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            print(f"[✓] Database size: {size:,} bytes")
            print(f"[✓] Database ready at: {db_path}")

    except Exception as e:
        print(f"[✗] Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print()
    print("=" * 60)
    print("  Database initialization complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

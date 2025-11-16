#!/usr/bin/env python
"""
Initialize Database Schema
Creates all necessary tables and schemas
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from database.connection import DatabaseManager


def main():
    """Initialize database"""
    print("=" * 70)
    print("YTC Trading System - Database Initialization")
    print("=" * 70)
    print()

    # Create database manager
    print("📌 Connecting to database...")
    db = DatabaseManager()

    # Test connection
    print("🔍 Testing connection...")
    if not db.test_connection():
        print("❌ Failed to connect to database")
        sys.exit(1)
    print("✅ Connection successful")
    print()

    # Create tables
    print("📋 Creating database schema...")
    try:
        db.create_tables()
        print("✅ Database schema created successfully")
    except Exception as e:
        print(f"❌ Failed to create schema: {e}")
        sys.exit(1)
    print()

    print("=" * 70)
    print("✅ Database initialization complete!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

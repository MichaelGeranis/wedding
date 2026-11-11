#!/usr/bin/env python3
"""
Script to initialize PostgreSQL database.
Creates tables, seeds a sample invitation and creates the admin user
(username "admin", password hash from ADMIN_PASSWORD_HASH) when none exists.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import wedding_api modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine

from wedding_api.config import settings
from wedding_api.models.database import Base


async def init_database():
    """Initialize database tables and seed sample data."""
    print("Connecting to database...")

    engine = create_async_engine(settings.database_url, echo=True)

    try:
        print("Creating all database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("✓ Database tables created successfully")

        print("Seeding sample invitation data...")
        async with engine.begin() as conn:
            from sqlalchemy import text

            print("Checking for existing invitation data...")
            result = await conn.execute(text("SELECT COUNT(*) FROM invitations"))
            count = result.scalar()

            if count == 0:
                await conn.execute(
                    text("""
                        INSERT INTO invitations (
                            bride_name, groom_name, wedding_date, wedding_time,
                            venue_name, venue_address, venue_city, venue_state, venue_zip,
                            venue_maps_url, rsvp_deadline,
                            created_at, updated_at, church_name, church_address, church_city, church_state, church_zip, church_maps_url
                        ) VALUES (
                            :bride_name, :groom_name, :wedding_date, :wedding_time,
                            :venue_name, :venue_address, :venue_city, :venue_state, :venue_zip,
                            :venue_maps_url, :rsvp_deadline,
                            NOW(), NOW(), :church_name, :church_address, :church_city, :church_state, :church_zip, :church_maps_url
                        )
                    """),
                    {
                        "bride_name": "Alex Morgan",
                        "groom_name": "Sam Rivera",
                        "wedding_date": "2027-06-12",
                        "wedding_time": "18:00",
                        "venue_name": "The Garden Hall",
                        "venue_address": "1 Example Street",
                        "venue_city": "Athens",
                        "venue_state": "Greece",
                        "venue_zip": "10000",
                        "venue_maps_url": "",
                        "rsvp_deadline": "2027-05-12",
                        "church_name": "St. Example Chapel",
                        "church_address": "2 Sample Avenue",
                        "church_city": "Athens",
                        "church_state": "Greece",
                        "church_zip": "10000",
                        "church_maps_url": "",
                    },
                )
                print("✓ Sample invitation data created")
            else:
                print("✓ Invitation data already exists")

        print("Checking for an admin user...")
        async with engine.begin() as conn:
            from sqlalchemy import text

            result = await conn.execute(text("SELECT COUNT(*) FROM users"))
            if result.scalar() == 0:
                if settings.admin_password_hash:
                    await conn.execute(
                        text("INSERT INTO users (username, password_hash, is_active) VALUES ('admin', :password_hash, true)"),
                        {"password_hash": settings.admin_password_hash},
                    )
                    print("✓ Admin user 'admin' created from ADMIN_PASSWORD_HASH")
                else:
                    print("! ADMIN_PASSWORD_HASH is empty: no admin user created")
            else:
                print("✓ Admin user already exists")

        print("\n✅ Database initialization complete!")
        print("\nYou can now start the backend server:")
        print("  make dev-backend")

    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_database())

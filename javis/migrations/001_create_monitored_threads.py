"""Create monitored_threads table

This migration creates the table for storing monitored email threads.
"""

from datetime import datetime
import asyncpg
from javis import settings


async def migrate():
    """Create the monitored_threads table."""
    conn = await asyncpg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
    )

    try:
        # Create the table
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS monitored_threads (
                thread_id VARCHAR(255) PRIMARY KEY,
                candidate_email VARCHAR(255) NOT NULL,
                hr_telegram_id VARCHAR(255) NOT NULL,
                expiry_time TIMESTAMP NOT NULL,
                last_message_id VARCHAR(255),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create an index on expiry_time for efficient querying
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_monitored_threads_expiry 
            ON monitored_threads(expiry_time)
        """
        )

    finally:
        await conn.close()


async def rollback():
    """Drop the monitored_threads table."""
    conn = await asyncpg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
    )

    try:
        await conn.execute("DROP TABLE IF EXISTS monitored_threads")
    finally:
        await conn.close()

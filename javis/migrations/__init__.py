"""Database migrations module."""

import os
import importlib.util
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def run_migrations():
    """Run all database migrations in order."""
    migrations_dir = Path(__file__).parent
    python_files = sorted(
        [f for f in migrations_dir.glob("*.py") if f.name != "__init__.py"]
    )

    for migration_file in python_files:
        try:
            # Import the migration module
            spec = importlib.util.spec_from_file_location(
                f"javis.migrations.{migration_file.stem}", migration_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Run the migration
            logger.info(f"Running migration: {migration_file.name}")
            await module.migrate()
            logger.info(f"Successfully completed migration: {migration_file.name}")

        except Exception as e:
            logger.error(f"Error running migration {migration_file.name}: {str(e)}")
            raise

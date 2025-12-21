#!/usr/bin/env python3
"""Script to translate all database records."""

import asyncio
import sys
import os

# Add the workspace to Python path
sys.path.insert(0, '/workspace')

from app.core.utils.translation.bulk_translator import run_bulk_translation


def main():
    """Main function to run the bulk translation."""
    force_update = False
    if len(sys.argv) > 1 and sys.argv[1] in ['--force', '-f']:
        force_update = True
        print("Force update mode enabled - will update existing translations")
    
    print("Starting database translation process...")
    asyncio.run(run_bulk_translation(force_update))
    print("Database translation process completed!")


if __name__ == "__main__":
    main()
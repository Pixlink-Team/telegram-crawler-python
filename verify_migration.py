#!/usr/bin/env python3
"""
Verification script to ensure MongoDB migration is complete
"""

import sys
import os
from pathlib import Path

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def check_file_exists(path: str, should_exist: bool = True) -> bool:
    """Check if file exists (or doesn't exist)"""
    exists = Path(path).exists()
    if should_exist:
        if exists:
            print(f"{GREEN}✓{RESET} {path} exists")
            return True
        else:
            print(f"{RED}✗{RESET} {path} missing!")
            return False
    else:
        if not exists:
            print(f"{GREEN}✓{RESET} {path} removed")
            return True
        else:
            print(f"{RED}✗{RESET} {path} still exists!")
            return False

def check_file_content(path: str, keywords: list, should_contain: bool = False) -> bool:
    """Check if file contains (or doesn't contain) keywords"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        found_keywords = [kw for kw in keywords if kw in content]
        
        if should_contain:
            if found_keywords:
                print(f"{GREEN}✓{RESET} {path} contains {', '.join(found_keywords)}")
                return True
            else:
                print(f"{RED}✗{RESET} {path} missing keywords: {', '.join(keywords)}")
                return False
        else:
            if not found_keywords:
                print(f"{GREEN}✓{RESET} {path} clean (no {', '.join(keywords)})")
                return True
            else:
                print(f"{RED}✗{RESET} {path} still contains: {', '.join(found_keywords)}")
                return False
    except FileNotFoundError:
        print(f"{YELLOW}⚠{RESET} {path} not found")
        return True if not should_contain else False

def main():
    print("🔍 Verifying MongoDB Migration...\n")
    
    all_checks_passed = True
    
    # Check removed files
    print("📁 Checking removed files...")
    all_checks_passed &= check_file_exists("alembic.ini", should_exist=False)
    all_checks_passed &= check_file_exists("app/models/session.py", should_exist=False)
    all_checks_passed &= check_file_exists("app/models/__init__.py", should_exist=False)
    print()
    
    # Check added files
    print("📁 Checking added files...")
    all_checks_passed &= check_file_exists("app/services/mongodb.py", should_exist=True)
    all_checks_passed &= check_file_exists("app/utils/session_manager.py", should_exist=True)
    all_checks_passed &= check_file_exists("MONGODB_MIGRATION.md", should_exist=True)
    all_checks_passed &= check_file_exists("MIGRATION_COMPLETE.md", should_exist=True)
    all_checks_passed &= check_file_exists("CHANGES.md", should_exist=True)
    print()
    
    # Check requirements.txt
    print("📦 Checking requirements.txt...")
    all_checks_passed &= check_file_content(
        "requirements.txt",
        ["SQLAlchemy", "alembic", "aiosqlite"],
        should_contain=False
    )
    all_checks_passed &= check_file_content(
        "requirements.txt",
        ["motor", "pymongo"],
        should_contain=True
    )
    print()
    
    # Check config.py
    print("⚙️  Checking app/config.py...")
    all_checks_passed &= check_file_content(
        "app/config.py",
        ["database_url", "DATABASE_URL"],
        should_contain=False
    )
    all_checks_passed &= check_file_content(
        "app/config.py",
        ["mongodb_url", "mongodb_database"],
        should_contain=True
    )
    print()
    
    # Check .env.example
    print("⚙️  Checking .env.example...")
    all_checks_passed &= check_file_content(
        ".env.example",
        ["DATABASE_URL"],
        should_contain=False
    )
    all_checks_passed &= check_file_content(
        ".env.example",
        ["MONGODB_URL", "MONGODB_DATABASE"],
        should_contain=True
    )
    print()
    
    # Check session_manager.py for async methods
    print("🔄 Checking session_manager.py...")
    all_checks_passed &= check_file_content(
        "app/utils/session_manager.py",
        ["async def get_session_by_id", "async def create_session", "mongodb_service"],
        should_contain=True
    )
    print()
    
    # Check routes.py for await calls
    print("🛣️  Checking app/api/routes.py...")
    all_checks_passed &= check_file_content(
        "app/api/routes.py",
        ["await session_manager.get_session_by_id", "await session_manager.create_session"],
        should_contain=True
    )
    print()
    
    # Check docker-compose.yml
    print("🐳 Checking docker-compose.yml...")
    all_checks_passed &= check_file_content(
        "docker-compose.yml",
        ["mongodb:", "mongo:"],
        should_contain=True
    )
    print()
    
    # Final result
    print("=" * 50)
    if all_checks_passed:
        print(f"{GREEN}✅ All checks passed! Migration complete.{RESET}")
        print("\n📝 Documentation files:")
        print("  - MONGODB_MIGRATION.md - Detailed migration guide")
        print("  - MIGRATION_COMPLETE.md - Quick summary in Persian")
        print("  - CHANGES.md - Complete changelog")
        print("\n🚀 Ready to run:")
        print("  docker-compose up -d")
        return 0
    else:
        print(f"{RED}❌ Some checks failed. Please review above.{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

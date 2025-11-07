"""
Migration Verification Script
Verifies that database schema matches SQLAlchemy model definitions

Usage:
    python scripts/verify_migrations.py

Exit Codes:
    0 - All schemas match (success)
    1 - Schema mismatch found (failure)

Use this script:
- After running migrations in any environment
- Before deploying to production
- As part of CI/CD pipeline health checks
- When investigating database issues

Example CI/CD Integration:
    - name: Verify Database Schema
      run: python backend/scripts/verify_migrations.py
      if: success()
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.database import engine, Base
from sqlalchemy import inspect

# Import all models to register them with Base.metadata
from app.models import (
    Organization, CompanyKnowledge, Job, Candidate, Resume,
    Interview, Screening, User, Application, Feedback, AuditLog
)


def verify_schema():
    """
    Check that all SQLAlchemy model columns exist in the database.
    
    Returns:
        bool: True if all schemas match, False if any mismatches found
    """
    print("🔍 Verifying database schema against SQLAlchemy models...")
    print("=" * 70)
    
    inspector = inspect(engine)
    errors = []
    warnings = []
    success_count = 0
    
    # Get all tables from metadata
    for table_name, table in sorted(Base.metadata.tables.items()):
        print(f"\nChecking table: {table_name}")
        
        # Get columns from database
        try:
            db_columns = {col['name'] for col in inspector.get_columns(table_name)}
        except Exception as e:
            errors.append(f"{table_name}: Failed to inspect - {e}")
            print(f"  ❌ ERROR: Could not inspect table - {e}")
            continue
        
        # Get columns from model
        model_columns = {col.name for col in table.columns}
        
        # Check for missing columns (in model but not in DB)
        missing = model_columns - db_columns
        if missing:
            error_msg = f"{table_name}: Missing columns in database: {sorted(missing)}"
            errors.append(error_msg)
            print(f"  ❌ MISSING: {sorted(missing)}")
        
        # Check for extra columns (in DB but not in model)
        extra = db_columns - model_columns
        if extra:
            warning_msg = f"{table_name}: Extra columns in database: {sorted(extra)}"
            warnings.append(warning_msg)
            print(f"  ⚠️  EXTRA: {sorted(extra)}")
        
        if not missing and not extra:
            success_count += 1
            print(f"  ✅ OK ({len(model_columns)} columns)")
    
    # Print summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    total_tables = len(Base.metadata.tables)
    print(f"\nTables checked: {total_tables}")
    print(f"✅ Matching: {success_count}")
    print(f"❌ Errors: {len(errors)}")
    print(f"⚠️  Warnings: {len(warnings)}")
    
    # Print detailed errors
    if errors:
        print("\n" + "=" * 70)
        print("ERRORS FOUND:")
        print("=" * 70)
        for error in errors:
            print(f"  ❌ {error}")
        print("\nThese errors indicate missing database columns.")
        print("This usually means:")
        print("  1. A migration was not executed properly")
        print("  2. Database was restored from an old backup")
        print("  3. Manual schema changes were not reflected in models")
        print("\nAction Required:")
        print("  - Review migration history: alembic history")
        print("  - Check current version: alembic current")
        print("  - Run pending migrations: alembic upgrade head")
        print("  - If migrations are current, investigate manual fixes")
    
    # Print detailed warnings
    if warnings:
        print("\n" + "=" * 70)
        print("WARNINGS:")
        print("=" * 70)
        for warning in warnings:
            print(f"  ⚠️  {warning}")
        print("\nThese warnings indicate extra columns in database.")
        print("This usually means:")
        print("  1. Old migration was rolled back but columns remain")
        print("  2. Manual columns were added to database")
        print("  3. Model definitions were removed but migration not created")
        print("\nAction Recommended:")
        print("  - Review if columns are still needed")
        print("  - Create migration to remove unused columns")
        print("  - Update models if columns should be included")
    
    # Final result
    if errors:
        print("\n❌ VERIFICATION FAILED: Schema mismatches found")
        print("Database schema does NOT match model definitions")
        return False
    elif warnings:
        print("\n⚠️  VERIFICATION PASSED WITH WARNINGS")
        print("Database schema matches models but has extra columns")
        return True
    else:
        print("\n✅ VERIFICATION PASSED: All schemas match!")
        print("Database schema is in sync with model definitions")
        return True


def verify_migration_version():
    """
    Check current alembic migration version.
    
    Returns:
        str: Current migration version or None if not found
    """
    print("\n🔍 Checking alembic migration version...")
    print("=" * 70)
    
    try:
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            
            if version:
                print(f"✅ Current migration version: {version}")
                return version
            else:
                print("⚠️  No migration version found in database")
                return None
    except Exception as e:
        print(f"❌ Error checking migration version: {e}")
        return None


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("DATABASE SCHEMA VERIFICATION")
    print("=" * 70)
    
    # Check migration version first
    version = verify_migration_version()
    
    # Verify schema
    success = verify_schema()
    
    # Exit with appropriate code
    exit(0 if success else 1)

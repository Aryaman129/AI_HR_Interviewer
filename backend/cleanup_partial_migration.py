"""
Clean up partial migration artifacts from the database.
This script removes all multi-tenancy tables and columns.
"""
from sqlalchemy import create_engine, text
from app.core.config import settings

def cleanup_partial_migration():
    """Drop partially created tables and indexes."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # Drop company_knowledge table and index
            conn.execute(text("DROP INDEX IF EXISTS idx_company_knowledge_embedding CASCADE;"))
            print("✓ Dropped index idx_company_knowledge_embedding")
            
            conn.execute(text("DROP TABLE IF EXISTS company_knowledge CASCADE;"))
            print("✓ Dropped table company_knowledge")
            
            # Remove organization_id from users
            conn.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS organization_id CASCADE;"))
            print("✓ Removed organization_id from users")
            
            # Remove organization_id from jobs
            conn.execute(text("ALTER TABLE jobs DROP COLUMN IF EXISTS organization_id CASCADE;"))
            print("✓ Removed organization_id from jobs")
            
            # Remove organization_id from candidates
            conn.execute(text("ALTER TABLE candidates DROP COLUMN IF EXISTS organization_id CASCADE;"))
            print("✓ Removed organization_id from candidates")
            
            # Drop organizations table
            conn.execute(text("DROP TABLE IF EXISTS organizations CASCADE;"))
            print("✓ Dropped table organizations")
            
            # Commit transaction
            trans.commit()
            print("\n✅ Cleanup completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ Error during cleanup: {e}")
            raise

if __name__ == "__main__":
    cleanup_partial_migration()

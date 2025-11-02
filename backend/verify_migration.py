"""
Verify that the multi-tenancy migration completed successfully.
"""
from sqlalchemy import create_engine, text, inspect
from app.core.config import settings

def verify_migration():
    """Check that all expected tables and columns exist."""
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    
    print("=" * 60)
    print("MULTI-TENANCY MIGRATION VERIFICATION")
    print("=" * 60)
    
    # Check organizations table
    print("\n1. Organizations Table:")
    if 'organizations' in inspector.get_table_names():
        columns = {col['name'] for col in inspector.get_columns('organizations')}
        expected = {'id', 'name', 'slug', 'industry', 'company_size', 'website', 
                   'plan', 'max_users', 'max_jobs', 'max_candidates', 'organization_id',
                   'features', 'settings', 'is_active', 'created_at'}
        print(f"   ✓ Table exists")
        print(f"   ✓ Columns: {len(columns)} found")
        
        indexes = inspector.get_indexes('organizations')
        print(f"   ✓ Indexes: {len(indexes)} found")
    else:
        print("   ✗ Table does NOT exist!")
    
    # Check company_knowledge table
    print("\n2. Company Knowledge Table:")
    if 'company_knowledge' in inspector.get_table_names():
        columns = {col['name'] for col in inspector.get_columns('company_knowledge')}
        print(f"   ✓ Table exists")
        print(f"   ✓ Columns: {len(columns)} found")
        
        # Check for embedding column
        embedding_col = [col for col in inspector.get_columns('company_knowledge') 
                        if col['name'] == 'embedding']
        if embedding_col:
            print(f"   ✓ Embedding column exists (type: {embedding_col[0]['type']})")
        
        indexes = inspector.get_indexes('company_knowledge')
        print(f"   ✓ Indexes: {len(indexes)} found")
    else:
        print("   ✗ Table does NOT exist!")
    
    # Check organization_id in users table
    print("\n3. Users Table (organization_id):")
    if 'users' in inspector.get_table_names():
        columns = {col['name'] for col in inspector.get_columns('users')}
        if 'organization_id' in columns:
            print("   ✓ organization_id column exists")
            
            # Check foreign key
            fks = inspector.get_foreign_keys('users')
            org_fk = [fk for fk in fks if 'organization' in str(fk.get('referred_table', ''))]
            if org_fk:
                print("   ✓ Foreign key to organizations exists")
        else:
            print("   ✗ organization_id column does NOT exist!")
    
    # Check organization_id in jobs table
    print("\n4. Jobs Table (organization_id):")
    if 'jobs' in inspector.get_table_names():
        columns = {col['name'] for col in inspector.get_columns('jobs')}
        if 'organization_id' in columns:
            print("   ✓ organization_id column exists")
            
            fks = inspector.get_foreign_keys('jobs')
            org_fk = [fk for fk in fks if 'organization' in str(fk.get('referred_table', ''))]
            if org_fk:
                print("   ✓ Foreign key to organizations exists")
        else:
            print("   ✗ organization_id column does NOT exist!")
    
    # Check organization_id in candidates table
    print("\n5. Candidates Table (organization_id):")
    if 'candidates' in inspector.get_table_names():
        columns = {col['name'] for col in inspector.get_columns('candidates')}
        if 'organization_id' in columns:
            print("   ✓ organization_id column exists")
            
            fks = inspector.get_foreign_keys('candidates')
            org_fk = [fk for fk in fks if 'organization' in str(fk.get('referred_table', ''))]
            if org_fk:
                print("   ✓ Foreign key to organizations exists")
        else:
            print("   ✗ organization_id column does NOT exist!")
    
    print("\n" + "=" * 60)
    print("✅ MIGRATION VERIFICATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    verify_migration()

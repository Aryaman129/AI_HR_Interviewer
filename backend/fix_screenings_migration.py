"""
Fix missing session_state columns in screenings table
This manually applies the migration 9b373845d853 that wasn't properly executed
"""
from app.db.database import engine
from sqlalchemy import text

def fix_screenings_table():
    """Add missing session tracking columns to screenings table"""
    
    print("🔧 Fixing screenings table migration...")
    print("=" * 60)
    
    try:
        with engine.begin() as conn:  # Use begin() for auto-commit transaction
            # Add session_state column
            print("Adding session_state column...")
            conn.execute(text(
                "ALTER TABLE screenings ADD COLUMN IF NOT EXISTS session_state VARCHAR(50) DEFAULT 'in_progress'"
            ))
            print("✓ session_state column added")
            
            # Add paused_at column
            print("Adding paused_at column...")
            conn.execute(text(
                "ALTER TABLE screenings ADD COLUMN IF NOT EXISTS paused_at TIMESTAMP"
            ))
            print("✓ paused_at column added")
            
            # Add resumed_at column
            print("Adding resumed_at column...")
            conn.execute(text(
                "ALTER TABLE screenings ADD COLUMN IF NOT EXISTS resumed_at TIMESTAMP"
            ))
            print("✓ resumed_at column added")
            
            # Add last_activity_at column
            print("Adding last_activity_at column...")
            conn.execute(text(
                "ALTER TABLE screenings ADD COLUMN IF NOT EXISTS last_activity_at TIMESTAMP"
            ))
            print("✓ last_activity_at column added")
            
            # Add session_metadata column
            print("Adding session_metadata column...")
            conn.execute(text(
                "ALTER TABLE screenings ADD COLUMN IF NOT EXISTS session_metadata JSONB"
            ))
            print("✓ session_metadata column added")
            
            # Add scoring_breakdown column
            print("Adding scoring_breakdown column...")
            conn.execute(text(
                "ALTER TABLE screenings ADD COLUMN IF NOT EXISTS scoring_breakdown JSONB"
            ))
            print("✓ scoring_breakdown column added")
            
            # Create index
            print("Creating index on session_state...")
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_screenings_session_state ON screenings(session_state)"
            ))
            print("✓ Index created")
            
            print("=" * 60)
            print("✅ All columns added successfully!")
            
        # Verify columns exist (separate connection for read-only query)
        with engine.connect() as conn:
            print("\n🔍 Verifying columns...")
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'screenings' 
                AND column_name IN ('session_state', 'paused_at', 'resumed_at', 
                                   'last_activity_at', 'session_metadata', 'scoring_breakdown')
                ORDER BY column_name
            """))
            
            columns = [row[0] for row in result.fetchall()]
            print(f"Found {len(columns)} new columns:")
            for col in columns:
                print(f"  ✓ {col}")
            
            if len(columns) == 6:
                print("\n✅ SUCCESS: All 6 columns verified!")
                return True
            else:
                print(f"\n⚠️  WARNING: Expected 6 columns, found {len(columns)}")
                return False
                
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_screenings_table()
    exit(0 if success else 1)

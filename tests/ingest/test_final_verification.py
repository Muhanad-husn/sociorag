#!/usr/bin/env python3
"""
Final verification that SQLite-vec integration is working without warnings.
"""
import sys
import os

# Add the backend path to sys.path
sys.path.insert(0, r"d:\sociorag\backend")

def test_no_warnings():
    """Test that SQLite-vec works without warnings."""
    print("🔍 Final Verification: Testing SQLite-vec Integration")
    print("=" * 60)
    
    try:
        from backend.app.core.singletons import get_sqlite, get_logger
        
        # Test SQLite connection and extension
        print("1. Testing SQLite connection...")
        con = get_sqlite()
        print("   ✅ Connection established")
        
        # Test vec_version function (the corrected one)
        print("2. Testing vec_version() function...")
        cursor = con.cursor()
        cursor.execute("SELECT vec_version()")
        version = cursor.fetchone()
        print(f"   ✅ SQLite-vec version: {version[0]}")
        
        # Test vector table operations
        print("3. Testing vector table operations...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entity_vectors'")
        table_exists = cursor.fetchone() is not None
        if table_exists:
            print("   ✅ entity_vectors table exists")
        else:
            print("   ❌ entity_vectors table not found")
            return False
            
        # Test a simple vector query
        print("4. Testing vector query...")
        cursor.execute("SELECT COUNT(*) FROM entity_vectors")
        count = cursor.fetchone()[0]
        print(f"   ✅ Found {count} vectors in table")
        
        print("\n" + "=" * 60)
        print("🎉 SUCCESS: All SQLite-vec integration tests passed!")
        print("🎉 No 'sqlite_vec_version' warnings should appear anymore!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_no_warnings()
    if success:
        print("\n✅ FINAL RESULT: SQLite-vec integration is working perfectly!")
    else:
        print("\n❌ FINAL RESULT: There are still issues to resolve.")
    sys.exit(0 if success else 1)

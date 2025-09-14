#!/usr/bin/env python3
"""
Test integration with your existing setup (seed.py, setup scripts, etc.)
"""

import os
import sys

def test_env_loading():
    """Test if environment variables load correctly."""
    print("=" * 60)
    print("1. Testing Environment Loading")
    print("=" * 60)
    
    # Method 1: Direct check
    print("\nDirect environment check:")
    vars_to_check = ['SECRET_KEY', 'DATABASE_URL', 'ADMIN_PASSWORD', 'ADMIN_EMAIL']
    
    for var in vars_to_check:
        value = os.environ.get(var)
        if value:
            display = f"{value[:5]}..." if len(value) > 5 and var != 'ADMIN_EMAIL' else value
            print(f"  ✅ {var}: {display}")
        else:
            print(f"  ❌ {var}: NOT SET")
    
    # Method 2: Load through dotenv
    print("\nLoading through python-dotenv:")
    from dotenv import load_dotenv
    
    # Try project root
    if os.path.exists('.env'):
        load_dotenv('.env', override=True)
        print("  ✅ Loaded from project root .env")
    # Try app folder
    elif os.path.exists('app/.env'):
        load_dotenv('app/.env', override=True)
        print("  ✅ Loaded from app/.env")
    else:
        print("  ❌ No .env file found")
        return False
    
    # Check again after loading
    print("\nAfter dotenv loading:")
    for var in vars_to_check:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: Loaded")
        else:
            print(f"  ❌ {var}: Still not loaded")
    
    return True

def test_config_import():
    """Test if config.py loads without errors."""
    print("\n" + "=" * 60)
    print("2. Testing Config Import")
    print("=" * 60)
    
    try:
        from app.config import Config
        config = Config()
        
        print(f"  ✅ Config imported successfully")
        print(f"  - SECRET_KEY: {'Set' if config.SECRET_KEY != 'your-secret-key-here' else 'Using default'}")
        print(f"  - DATABASE_URL: {config.SQLALCHEMY_DATABASE_URI[:30]}...")
        print(f"  - ADMIN_EMAIL: {config.ADMIN_EMAIL}")
        print(f"  - WEDDING_DATE: {config.WEDDING_DATE}")
        
        return True
    except Exception as e:
        print(f"  ❌ Config import failed: {str(e)}")
        return False

def test_app_creation():
    """Test if Flask app can be created."""
    print("\n" + "=" * 60)
    print("3. Testing App Creation")
    print("=" * 60)
    
    try:
        from app import create_app
        app = create_app()
        print(f"  ✅ Flask app created")
        
        with app.app_context():
            print(f"  - Database URL: {app.config['SQLALCHEMY_DATABASE_URI'][:30]}...")
            print(f"  - Admin configured: {'Yes' if app.config.get('ADMIN_PASSWORD') else 'No'}")
        
        return True
    except Exception as e:
        print(f"  ❌ App creation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """Test database connection."""
    print("\n" + "=" * 60)
    print("4. Testing Database Connection")
    print("=" * 60)
    
    try:
        from app import create_app, db
        app = create_app()
        
        with app.app_context():
            # Test connection
            db.engine.connect()
            print(f"  ✅ Database connection successful")
            
            # Check tables
            from app.models.guest import Guest
            from app.models.allergen import Allergen
            
            guest_count = Guest.query.count()
            allergen_count = Allergen.query.count()
            
            print(f"  - Guests in database: {guest_count}")
            print(f"  - Allergens in database: {allergen_count}")
            
            return True
    except Exception as e:
        print(f"  ❌ Database connection failed: {str(e)}")
        return False

def test_admin_auth():
    """Test admin authentication."""
    print("\n" + "=" * 60)
    print("5. Testing Admin Authentication")
    print("=" * 60)
    
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from app.admin_auth import verify_admin_password
            
            # Get the password from environment
            admin_password = os.getenv('ADMIN_PASSWORD', 'your-secure-password')
            
            if verify_admin_password(admin_password):
                print(f"  ✅ Admin authentication working")
            else:
                print(f"  ❌ Admin authentication failed")
                print(f"     (Password from env: {admin_password[:3]}...)")
            
            # Test wrong password
            if not verify_admin_password("definitely-wrong-password"):
                print(f"  ✅ Wrong password correctly rejected")
            else:
                print(f"  ❌ Security issue: wrong password accepted!")
            
            return True
    except Exception as e:
        print(f"  ❌ Admin auth test failed: {str(e)}")
        return False

def check_existing_files():
    """Check if your existing setup files are present."""
    print("\n" + "=" * 60)
    print("6. Checking Existing Setup Files")
    print("=" * 60)
    
    files_to_check = [
        'seed.py',
        'setup_app.sh',
        'setup_update_db.sh',
        'requirements.txt',
        '.env',
        'app/config.py',
        'app/admin_auth.py'
    ]
    
    all_present = True
    for file in files_to_check:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - NOT FOUND")
            all_present = False
    
    return all_present

def main():
    """Run all integration tests."""
    print("\n🔍 INTEGRATION TEST FOR YOUR WEDDING WEBSITE\n")
    
    # Run tests
    results = {
        "Environment": test_env_loading(),
        "Config": test_config_import(),
        "App Creation": test_app_creation(),
        "Database": test_database_connection(),
        "Admin Auth": test_admin_auth(),
        "Files": check_existing_files()
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test}: {status}")
    
    if all(results.values()):
        print("\n✅ ALL TESTS PASSED!")
        print("\nYou can now run:")
        print("  python run.py")
        print("    or")
        print("  python run_simple.py")
        print("    or")
        print("  ./setup_app.sh  (if you prefer your shell script)")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("\nSuggested fixes:")
        
        if not results["Environment"]:
            print("\n1. Environment issues:")
            print("   - Move .env to project root: mv app/.env .")
            print("   - Or copy to app folder: cp .env app/.env")
        
        if not results["Config"]:
            print("\n2. Config issues:")
            print("   - Use the fixed config.py from the artifact above")
        
        if not results["Database"]:
            print("\n3. Database issues:")
            print("   - Check PostgreSQL is running: pg_ctl status")
            print("   - Check DATABASE_URL in .env")
            print("   - Run: ./setup_update_db.sh 'initial setup'")

if __name__ == "__main__":
    main()
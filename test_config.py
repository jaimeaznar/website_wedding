#!/usr/bin/env python3
"""
Test script to verify environment configuration is working correctly.
Run this after setting up your .env file.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment():
    """Test environment variables are loaded correctly."""
    print("=" * 60)
    print("TESTING ENVIRONMENT CONFIGURATION")
    print("=" * 60)
    
    # Test required variables
    required_vars = {
        'SECRET_KEY': '🔐 Secret Key',
        'DATABASE_URL': '🗄️  Database URL',
        'ADMIN_PASSWORD': '👤 Admin Password', 
        'ADMIN_EMAIL': '📧 Admin Email',
        'ADMIN_PHONE': '📱 Admin Phone'
    }
    
    all_good = True
    
    for var, label in required_vars.items():
        value = os.getenv(var)
        if value:
            # Don't show sensitive values
            if var in ['SECRET_KEY', 'ADMIN_PASSWORD', 'DATABASE_URL']:
                display_value = f"{value[:10]}..." if len(value) > 10 else "***"
            else:
                display_value = value
            print(f"✅ {label}: {display_value}")
        else:
            print(f"❌ {label}: NOT SET")
            all_good = False
    
    print("\n" + "-" * 60)
    
    # Test optional variables
    optional_vars = {
        'MAIL_USERNAME': '📮 Email Username',
        'MAIL_PASSWORD': '🔑 Email Password',
        'WEDDING_DATE': '💍 Wedding Date',
        'RSVP_DEADLINE': '📅 RSVP Deadline'
    }
    
    print("Optional Configuration:")
    for var, label in optional_vars.items():
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var:
                display_value = "***"
            else:
                display_value = value
            print(f"✅ {label}: {display_value}")
        else:
            print(f"⚠️  {label}: Not configured")
    
    return all_good

def test_app_creation():
    """Test if the Flask app can be created with current config."""
    print("\n" + "=" * 60)
    print("TESTING FLASK APPLICATION")
    print("=" * 60)
    
    try:
        from app import create_app
        app = create_app()
        print("✅ Flask application created successfully")
        
        # Test database connection
        with app.app_context():
            from app import db
            try:
                # Try to connect to database
                db.engine.connect()
                print("✅ Database connection successful")
            except Exception as e:
                print(f"❌ Database connection failed: {str(e)}")
                return False
                
        return True
        
    except SystemExit:
        print("❌ Application failed to start due to configuration errors")
        return False
    except Exception as e:
        print(f"❌ Error creating application: {str(e)}")
        return False

def test_admin_auth():
    """Test admin authentication is working."""
    print("\n" + "=" * 60)
    print("TESTING ADMIN AUTHENTICATION")
    print("=" * 60)
    
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from app.admin_auth import verify_admin_password
            
            # Test with the configured password
            admin_password = os.getenv('ADMIN_PASSWORD')
            if admin_password:
                # Test correct password
                if verify_admin_password(admin_password):
                    print("✅ Admin password verification working")
                else:
                    print("❌ Admin password verification failed")
                    return False
                
                # Test wrong password
                if not verify_admin_password("wrong-password"):
                    print("✅ Wrong password correctly rejected")
                else:
                    print("❌ Wrong password was accepted (security issue!)")
                    return False
            else:
                print("⚠️  Admin password not set in environment")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Error testing admin auth: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("\n🔍 Running configuration tests...\n")
    
    # Test 1: Environment variables
    env_ok = test_environment()
    
    if not env_ok:
        print("\n" + "=" * 60)
        print("❌ CONFIGURATION INCOMPLETE")
        print("=" * 60)
        print("\n📝 To fix:")
        print("1. Make sure .env file exists")
        print("2. Run: python generate_secrets.py")
        print("3. Update .env with the generated values")
        print("4. Set your database URL and admin details")
        sys.exit(1)
    
    # Test 2: Flask app creation
    app_ok = test_app_creation()
    
    # Test 3: Admin authentication
    auth_ok = test_admin_auth()
    
    # Summary
    print("\n" + "=" * 60)
    if env_ok and app_ok and auth_ok:
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\n🎉 Your configuration is ready!")
        print("\nYou can now run: python run.py")
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        print("\nPlease fix the issues above before running the application.")
        sys.exit(1)

if __name__ == "__main__":
    main()
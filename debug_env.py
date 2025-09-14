#!/usr/bin/env python3
"""
Debug script to troubleshoot environment variable loading issues.
"""

import os
import sys
from pathlib import Path

def check_env_file():
    """Check if .env file exists and show its location."""
    print("=" * 60)
    print("ENVIRONMENT FILE CHECK")
    print("=" * 60)
    
    # Check current directory
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    
    # Check for .env file
    env_paths = [
        '.env',
        './.env',
        os.path.join(current_dir, '.env')
    ]
    
    env_found = False
    for path in env_paths:
        if os.path.exists(path):
            env_found = True
            full_path = os.path.abspath(path)
            print(f"✅ Found .env at: {full_path}")
            
            # Check file size
            size = os.path.getsize(path)
            print(f"   File size: {size} bytes")
            
            # Check if readable
            if os.access(path, os.R_OK):
                print(f"   File is readable: ✅")
            else:
                print(f"   File is readable: ❌")
                
            break
    
    if not env_found:
        print("❌ .env file NOT found in current directory")
        print("\nSearching in parent directories...")
        
        # Search in parent directories
        search_dir = Path(current_dir).parent
        for _ in range(3):  # Check up to 3 levels up
            env_path = search_dir / '.env'
            if env_path.exists():
                print(f"Found .env at: {env_path}")
                break
            search_dir = search_dir.parent
    
    return env_found

def check_env_content():
    """Check the content of .env file."""
    print("\n" + "=" * 60)
    print("ENVIRONMENT FILE CONTENT CHECK")
    print("=" * 60)
    
    if not os.path.exists('.env'):
        print("❌ Cannot check content - .env file not found")
        return False
    
    try:
        with open('.env', 'r') as f:
            lines = f.readlines()
            
        print(f"Total lines in .env: {len(lines)}")
        print("\nChecking for required variables:")
        
        required_vars = [
            'SECRET_KEY',
            'DATABASE_URL',
            'ADMIN_PASSWORD',
            'ADMIN_EMAIL',
            'ADMIN_PHONE'
        ]
        
        found_vars = {}
        
        for line in lines:
            # Skip comments and empty lines
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Check for each required variable
            for var in required_vars:
                if line.startswith(f"{var}="):
                    # Found the variable
                    value = line.split('=', 1)[1].strip()
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    if value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    if value:
                        found_vars[var] = "✅ Set (hidden for security)"
                    else:
                        found_vars[var] = "⚠️  Empty value"
        
        # Report findings
        for var in required_vars:
            if var in found_vars:
                print(f"  {var}: {found_vars[var]}")
            else:
                print(f"  {var}: ❌ NOT FOUND in .env")
        
        return len(found_vars) == len(required_vars)
        
    except Exception as e:
        print(f"❌ Error reading .env file: {str(e)}")
        return False

def test_manual_load():
    """Test manual loading of .env file."""
    print("\n" + "=" * 60)
    print("TESTING MANUAL ENV LOADING")
    print("=" * 60)
    
    # Method 1: Using python-dotenv
    try:
        from dotenv import load_dotenv
        
        # Try different loading methods
        methods = [
            ("load_dotenv()", lambda: load_dotenv()),
            ("load_dotenv('.env')", lambda: load_dotenv('.env')),
            ("load_dotenv(verbose=True)", lambda: load_dotenv(verbose=True)),
            ("load_dotenv(override=True)", lambda: load_dotenv(override=True))
        ]
        
        for method_name, method_func in methods:
            print(f"\nTrying: {method_name}")
            result = method_func()
            if result:
                print(f"  ✅ Loaded successfully")
            else:
                print(f"  ⚠️  Load returned False (file might not exist)")
            
            # Check if variables are now available
            test_vars = ['SECRET_KEY', 'DATABASE_URL', 'ADMIN_PASSWORD']
            found_any = False
            for var in test_vars:
                value = os.getenv(var)
                if value:
                    print(f"  ✅ {var} is now loaded")
                    found_any = True
                    break
            
            if found_any:
                print(f"  ✅ Method '{method_name}' works!")
                break
                
    except ImportError:
        print("❌ python-dotenv is not installed!")
        print("Run: pip install python-dotenv")
        return False
    
    # Final check
    print("\n" + "-" * 60)
    print("Final environment variable check:")
    vars_to_check = ['SECRET_KEY', 'DATABASE_URL', 'ADMIN_PASSWORD', 'ADMIN_EMAIL', 'ADMIN_PHONE']
    
    all_loaded = True
    for var in vars_to_check:
        value = os.getenv(var)
        if value:
            # Hide sensitive values
            if var in ['SECRET_KEY', 'DATABASE_URL', 'ADMIN_PASSWORD']:
                display = f"{value[:5]}..." if len(value) > 5 else "***"
            else:
                display = value
            print(f"  ✅ {var}: {display}")
        else:
            print(f"  ❌ {var}: NOT LOADED")
            all_loaded = False
    
    return all_loaded

def check_file_format():
    """Check for common .env file format issues."""
    print("\n" + "=" * 60)
    print("CHECKING FILE FORMAT")
    print("=" * 60)
    
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        return
    
    with open('.env', 'rb') as f:
        content = f.read()
    
    # Check for BOM (Byte Order Mark)
    if content.startswith(b'\xef\xbb\xbf'):
        print("⚠️  File has UTF-8 BOM - this might cause issues")
    
    # Check line endings
    if b'\r\n' in content:
        print("ℹ️  File uses Windows line endings (CRLF)")
    elif b'\n' in content:
        print("ℹ️  File uses Unix line endings (LF)")
    else:
        print("⚠️  No line endings detected - file might be malformed")
    
    # Check for common issues
    text_content = content.decode('utf-8', errors='ignore')
    lines = text_content.split('\n')
    
    issues = []
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        # Check for spaces around =
        if '=' in line:
            key, value = line.split('=', 1)
            if key != key.strip():
                issues.append(f"Line {i}: Key has extra spaces: '{key}'")
            if ' ' in key:
                issues.append(f"Line {i}: Key contains spaces: '{key}'")
            if not value.strip():
                issues.append(f"Line {i}: Empty value for {key}")
    
    if issues:
        print("\n⚠️  Potential issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ No format issues detected")

def suggest_fix():
    """Suggest fixes based on the diagnostics."""
    print("\n" + "=" * 60)
    print("SUGGESTED FIXES")
    print("=" * 60)
    
    print("""
1. Make sure your .env file is in the PROJECT ROOT directory
   (same directory as run.py, requirements.txt, etc.)

2. Check that your .env file has NO SPACES around the = sign:
   ✅ CORRECT:   SECRET_KEY=your-secret-key-here
   ❌ WRONG:     SECRET_KEY = your-secret-key-here

3. Don't use quotes unless they're part of the value:
   ✅ CORRECT:   ADMIN_EMAIL=admin@example.com
   ⚠️  CAREFUL:  ADMIN_EMAIL="admin@example.com"  (quotes become part of value)

4. Make sure python-dotenv is installed:
   pip install python-dotenv

5. Try creating a fresh .env file:
   cp .env.example .env.new
   # Edit .env.new with your values
   mv .env .env.backup
   mv .env.new .env

6. If on Windows, check line endings:
   Use a text editor like Notepad++ or VS Code
   Convert to Unix line endings (LF only)
""")

def main():
    """Run all diagnostics."""
    print("\n🔍 ENVIRONMENT LOADING DIAGNOSTICS\n")
    
    # Step 1: Check if file exists
    file_exists = check_env_file()
    
    if not file_exists:
        print("\n❌ PROBLEM: .env file not found!")
        print("\nCreate it with: cp .env.example .env")
        sys.exit(1)
    
    # Step 2: Check file content
    content_ok = check_env_content()
    
    # Step 3: Check file format
    check_file_format()
    
    # Step 4: Test manual loading
    loaded = test_manual_load()
    
    # Step 5: Suggest fixes if needed
    if not loaded:
        suggest_fix()
    else:
        print("\n" + "=" * 60)
        print("✅ ENVIRONMENT VARIABLES LOADED SUCCESSFULLY!")
        print("=" * 60)
        print("\nYou can now run: python run.py")

if __name__ == "__main__":
    main()
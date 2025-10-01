#!/usr/bin/env python3
"""
Quick health check for the bot code
Test if there are any syntax or import errors
"""

import sys
import os

def test_imports():
    """Test if all imports work"""
    print("🧪 Testing imports...")
    
    try:
        import telegram
        print("✅ telegram imported successfully")
    except Exception as e:
        print(f"❌ telegram import failed: {e}")
        return False
    
    try:
        from telegram.ext import Application, CommandHandler, CallbackQueryHandler
        print("✅ telegram.ext imported successfully")
    except Exception as e:
        print(f"❌ telegram.ext import failed: {e}")
        return False
    
    try:
        import flask
        print("✅ flask imported successfully")
    except Exception as e:
        print(f"❌ flask import failed: {e}")
        return False
    
    try:
        import sqlite3
        print("✅ sqlite3 imported successfully")
    except Exception as e:
        print(f"❌ sqlite3 import failed: {e}")
        return False
    
    try:
        import pandas as pd
        print("✅ pandas imported successfully")
    except Exception as e:
        print(f"❌ pandas import failed: {e}")
        return False
    
    return True

def test_environment_variables():
    """Test environment variables"""
    print("\n🔧 Testing environment variables...")
    
    required_vars = [
        'BOT_TOKEN',
        'KITE_API_KEY', 
        'KITE_API_SECRET',
        'KITE_ACCESS_TOKEN'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            print(f"❌ {var} is missing")
        else:
            print(f"✅ {var} is set")
    
    return len(missing_vars) == 0

def test_bot_token_format():
    """Test if bot token format is correct"""
    print("\n🤖 Testing bot token format...")
    
    bot_token = os.getenv('BOT_TOKEN', '')
    if not bot_token:
        print("❌ BOT_TOKEN not set")
        return False
    
    # Bot token should be in format: numbers:letters
    if ':' in bot_token and len(bot_token) > 20:
        print(f"✅ Bot token format looks correct: {bot_token[:10]}...{bot_token[-5:]}")
        return True
    else:
        print(f"❌ Bot token format incorrect: {bot_token}")
        return False

def test_syntax():
    """Test if main.py has syntax errors"""
    print("\n📝 Testing main.py syntax...")
    
    try:
        with open('main.py', 'r') as f:
            code = f.read()
        
        # Try to compile the code
        compile(code, 'main.py', 'exec')
        print("✅ main.py syntax is correct")
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error in main.py: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading main.py: {e}")
        return False

def main():
    """Run all health checks"""
    print("🔍 BigBullScalpBot Health Check\n")
    
    checks = [
        ("Imports", test_imports),
        ("Environment Variables", test_environment_variables), 
        ("Bot Token Format", test_bot_token_format),
        ("Syntax", test_syntax)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, test_func in checks:
        print(f"\n{'='*50}")
        print(f"Testing: {name}")
        print('='*50)
        
        if test_func():
            passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED")
    
    print(f"\n{'='*50}")
    print(f"HEALTH CHECK RESULTS: {passed}/{total} PASSED")
    print('='*50)
    
    if passed == total:
        print("🎉 All checks passed! Bot should be working.")
    else:
        print("⚠️  Some checks failed. Fix the issues above.")
    
    return passed == total

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test script to verify Oslo Commute Time Optimizer setup.
Run this to check if everything is configured correctly.
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_database():
    """Test database functionality."""
    print("Testing database...")
    try:
        from database import init_database, get_connection
        init_database()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()

        expected_tables = {'travel_times', 'segments', 'config', 'collection_status'}
        actual_tables = {table[0] for table in tables}

        if expected_tables.issubset(actual_tables):
            print("✅ Database: OK")
            return True
        else:
            print(f"❌ Database: Missing tables {expected_tables - actual_tables}")
            return False
    except Exception as e:
        print(f"❌ Database: Error - {e}")
        return False


def test_google_maps_config():
    """Test Google Maps configuration."""
    print("\nTesting Google Maps configuration...")
    try:
        from google_maps import API_KEY, test_api_key

        if not API_KEY:
            print("⚠️  Google Maps: API key not configured (optional)")
            return None

        if test_api_key():
            print("✅ Google Maps: API key is valid")
            return True
        else:
            print("❌ Google Maps: API key is invalid")
            return False
    except Exception as e:
        print(f"❌ Google Maps: Error - {e}")
        return False


def test_datex_config():
    """Test DATEX configuration."""
    print("\nTesting DATEX configuration...")
    try:
        from datex_client import DATEX_USERNAME, DATEX_PASSWORD, test_datex_credentials

        if not DATEX_USERNAME or not DATEX_PASSWORD:
            print("⚠️  DATEX: Credentials not configured (optional)")
            return None

        if test_datex_credentials():
            print("✅ DATEX: Credentials are valid")
            return True
        else:
            print("❌ DATEX: Credentials are invalid")
            return False
    except Exception as e:
        print(f"❌ DATEX: Error - {e}")
        return False


def test_imports():
    """Test that all modules can be imported."""
    print("\nTesting module imports...")
    modules = [
        'database',
        'google_maps',
        'datex_client',
        'datex_collector',
        'datex_analyzer',
        'main'
    ]

    all_ok = True
    for module in modules:
        try:
            __import__(module)
            print(f"✅ Import {module}: OK")
        except Exception as e:
            print(f"❌ Import {module}: Error - {e}")
            all_ok = False

    return all_ok


def test_dependencies():
    """Test that required dependencies are installed."""
    print("\nTesting dependencies...")
    deps = [
        'fastapi',
        'uvicorn',
        'requests',
        'pydantic'
    ]

    all_ok = True
    for dep in deps:
        try:
            __import__(dep)
            print(f"✅ {dep}: installed")
        except ImportError:
            print(f"❌ {dep}: not installed")
            all_ok = False

    return all_ok


def main():
    """Run all tests."""
    print("=" * 60)
    print("Oslo Commute Time Optimizer - Setup Test")
    print("=" * 60)

    results = {
        'Dependencies': test_dependencies(),
        'Imports': test_imports(),
        'Database': test_database(),
        'Google Maps': test_google_maps_config(),
        'DATEX': test_datex_config()
    }

    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)

    for name, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⚠️  NOT CONFIGURED"
        print(f"{name:20s}: {status}")

    print("\n" + "=" * 60)

    # Check if we can run
    core_ok = results['Dependencies'] and results['Imports'] and results['Database']

    if core_ok:
        print("\n✅ Core setup is complete!")

        if results['Google Maps'] is None and results['DATEX'] is None:
            print("\n⚠️  Note: No API keys configured.")
            print("   - For instant results: Add GOOGLE_MAPS_API_KEY to .env")
            print("   - For free data: Add DATEX_USERNAME and DATEX_PASSWORD to .env")
        elif results['Google Maps'] or results['DATEX']:
            print("\n🚀 You're ready to run the application!")
            print("   Run: ./run.sh or cd backend && python main.py")
    else:
        print("\n❌ Setup incomplete. Please install dependencies:")
        print("   pip install -r requirements.txt")

    print()


if __name__ == '__main__':
    main()

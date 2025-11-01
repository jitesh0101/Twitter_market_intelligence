#!/usr/bin/env python3
"""
Quick test script to verify Chrome driver setup.
Tests the scraper initialization without actually scraping.
"""

import sys
from pathlib import Path

print("=" * 70)
print("CHROME DRIVER TEST")
print("=" * 70)

# Test 1: Import check
print("\n1. Testing imports...")
try:
    from src.scraper import StealthDriver
    from src import load_config, setup_logging
    print("    Imports successful")
except Exception as e:
    print(f"    Import failed: {e}")
    sys.exit(1)

# Test 2: Config check
print("\n2. Testing configuration...")
try:
    config = load_config("config.yaml")
    print("    Configuration loaded")
except Exception as e:
    print(f"    Config failed: {e}")
    sys.exit(1)

# Test 3: Driver initialization (most critical)
print("\n3. Testing Chrome driver initialization...")
print("   (This will open Chrome briefly, then close it)")
try:
    stealth_driver = StealthDriver(
        headless=False,  # Show browser for verification
        user_agent_rotation=True,
        window_size="1920,1080"
    )
    
    driver = stealth_driver.create_driver()
    print("    Chrome driver initialized successfully!")
    
    # Test navigation
    print("\n4. Testing navigation...")
    driver.get("https://www.google.com")
    print("    Navigation successful")
    
    # Check page title
    title = driver.title
    print(f"    Page title: {title}")
    
    # Clean up
    stealth_driver.close()
    print("\n" + "=" * 70)
    print(" ALL TESTS PASSED!")
    print("=" * 70)
    print("\nYour system is ready to scrape Twitter!")
    print("\nNext steps:")
    print("  1. Run: python main.py --scrape --target 50")
    print("  2. Or run complete pipeline: python main.py --all")
    
except Exception as e:
    print(f"\n    Driver test failed!")
    print(f"\nError details:")
    print(f"   {type(e).__name__}: {e}")
    print("\n" + "=" * 70)
    print("TROUBLESHOOTING SUGGESTIONS:")
    print("=" * 70)
    print("1. Make sure Google Chrome is installed")
    print("2. Update packages:")
    print("   pip install --upgrade undetected-chromedriver selenium")
    print("3. Check TROUBLESHOOTING.md for detailed solutions")
    print("4. If still failing, try running with headless=True in config.yaml")
    sys.exit(1)


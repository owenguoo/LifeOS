#!/usr/bin/env python3
"""
Performance test with manual API key input
For testing when environment variable isn't set
"""

import os
import sys
import asyncio
from quick_performance_test import main as run_quick_test

def get_api_key():
    """Get API key from user input or environment"""
    # First check environment
    api_key = os.getenv("TWELVELABS_API_KEY")
    if api_key:
        return api_key
    
    # If not in environment, ask user
    print("🔑 TwelveLabs API Key Required")
    print("=" * 40)
    print("Your API key is not set in the environment.")
    print("You can either:")
    print("1. Set it as environment variable:")
    print("   export TWELVELABS_API_KEY='your_key_here'")
    print("2. Enter it now (will be used for this test only)")
    print()
    
    api_key = input("Enter your TwelveLabs API key (or press Enter to cancel): ").strip()
    
    if not api_key:
        print("❌ No API key provided. Exiting.")
        sys.exit(1)
    
    return api_key

async def main():
    """Main function with API key handling"""
    print("🎬 Performance Test with API Key Helper")
    print("=" * 50)
    
    # Get API key
    api_key = get_api_key()
    
    # Set it in environment for the test
    os.environ["TWELVELABS_API_KEY"] = api_key
    
    print("✅ API key set successfully")
    print("🚀 Starting performance test...\n")
    
    # Run the actual test
    await run_quick_test()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
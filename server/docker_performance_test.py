#!/usr/bin/env python3
"""
Docker-compatible Performance Test Runner
Can be run inside Docker containers to test the optimized pipeline
"""

import asyncio
import os
import sys
import json
from performance_test import PerformanceTester, VideoTestGenerator
from config import Config


async def docker_test_runner():
    """Simplified test runner for Docker environment"""
    print("🐳 Docker Performance Test Runner")
    print("=" * 50)
    
    # Check environment
    api_key = os.getenv("TWELVELABS_API_KEY")
    if not api_key:
        print("❌ TWELVELABS_API_KEY not set")
        return False
    
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    print(f"📡 Redis URL: {redis_url}")
    
    # Update config for Docker environment
    if "redis://" in redis_url:
        parts = redis_url.replace("redis://", "").split(":")
        Config.REDIS_HOST = parts[0]
        if len(parts) > 1:
            Config.REDIS_PORT = int(parts[1])
    
    # Run simplified performance test
    tester = PerformanceTester(api_key)
    
    try:
        print("🔧 Setting up test environment...")
        await tester.setup()
        
        # Create a single test video
        print("📹 Creating test video...")
        test_video = tester.video_generator.create_test_video("docker_test.mp4", duration=8)
        
        # Test new optimized method
        print("🚀 Testing optimized implementation...")
        new_result = await tester.test_single_video_processing(test_video, "new")
        
        # Test old method for comparison
        print("⏳ Testing original implementation...")
        old_result = await tester.test_single_video_processing(test_video, "old")
        
        # Results
        print("\n" + "=" * 50)
        print("DOCKER TEST RESULTS")
        print("=" * 50)
        
        if old_result.success and new_result.success:
            improvement = ((old_result.duration - new_result.duration) / old_result.duration) * 100
            print(f"Original Method:  {old_result.duration:.2f}s")
            print(f"Optimized Method: {new_result.duration:.2f}s")
            print(f"Improvement:      {improvement:.1f}% {'📈' if improvement > 0 else '📉'}")
            
            if improvement > 20:
                print("🎉 EXCELLENT: Significant performance improvement!")
            elif improvement > 10:
                print("✅ GOOD: Noticeable performance improvement!")
            elif improvement > 0:
                print("👍 OK: Slight performance improvement")
            else:
                print("⚠️  WARNING: No improvement detected")
        else:
            print("❌ Test failed:")
            if not old_result.success:
                print(f"  Original method error: {old_result.error}")
            if not new_result.success:
                print(f"  Optimized method error: {new_result.error}")
        
        await tester.cleanup()
        return old_result.success and new_result.success
        
    except Exception as e:
        print(f"❌ Docker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(docker_test_runner())
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Quick Performance Test
Simple script to test the optimized vs original video processing
"""

import asyncio
import time
import os
import sys
import tempfile
import cv2
import numpy as np
from pathlib import Path

# Import your components
from config import Config
from video_processing.worker import VideoProcessingWorker
from video_queue.queue_manager import VideoQueueManager


def create_simple_test_video(output_path: str, duration: int = 8) -> str:
    """Create a simple test video"""
    print(f"📹 Creating test video: {output_path}")
    
    fps = 10
    resolution = (640, 480)  # Smaller for faster testing
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(output_path, fourcc, fps, resolution)
    
    total_frames = duration * fps
    
    for frame_num in range(total_frames):
        # Create simple moving pattern
        frame = np.zeros((resolution[1], resolution[0], 3), dtype=np.uint8)
        
        # Moving circle
        x = int((frame_num / total_frames) * resolution[0])
        y = resolution[1] // 2
        cv2.circle(frame, (x, y), 30, (0, 255, 0), -1)
        
        # Frame counter
        cv2.putText(frame, f"Frame {frame_num}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        writer.write(frame)
    
    writer.release()
    print(f"✅ Test video created: {os.path.getsize(output_path)} bytes")
    return output_path


async def test_worker_performance(api_key: str, video_path: str):
    """Test both old and new worker performance"""
    print("🧪 Testing Worker Performance")
    print("=" * 40)
    
    # Test job
    job = {
        "video_path": video_path,
        "metadata": {
            "user_id": "test_user_123",
            "test_mode": True
        },
        "timestamp": time.time()
    }
    
    results = {}
    
    # Test optimized implementation (default now)
    print("🚀 Testing OPTIMIZED implementation...")
    worker = VideoProcessingWorker(worker_id=0, api_key=api_key)
    
    try:
        await worker.start()
        
        start_time = time.time()
        result = await worker.process_video_segment(job)
        optimized_duration = time.time() - start_time
        
        await worker.stop()
        
        results["optimized"] = {
            "duration": optimized_duration,
            "success": result is not None and "error" not in result,
            "result": result
        }
        
        print(f"   ⏱️  Duration: {optimized_duration:.2f}s")
        print(f"   ✅ Success: {results['optimized']['success']}")
        
    except Exception as e:
        results["optimized"] = {
            "duration": 0,
            "success": False,
            "error": str(e)
        }
        print(f"   ❌ Error: {e}")
    
    # Test original methods (by using the non-optimized methods)
    print("\n⏳ Testing ORIGINAL implementation...")
    worker = VideoProcessingWorker(worker_id=1, api_key=api_key)
    
    try:
        await worker.start()
        
        start_time = time.time()
        
        # Simulate original serial processing
        video_path = job["video_path"]
        metadata = job.get("metadata", {})
        
        # Generate UUID
        linking_uuid = worker.supabase_manager.generate_linking_uuid()
        
        # 1. Upload video (using original method)
        video_id = await worker.upload_video(video_path, metadata)
        if not video_id:
            raise Exception("Video upload failed")
        
        # 2. S3 upload
        loop = asyncio.get_event_loop()
        s3_url = await loop.run_in_executor(
            None, worker.s3_manager.upload_video_segment, video_path
        )
        
        # 3. Analyze video (using original method)
        analysis = await worker.analyze_video(
            video_id, job.get("timestamp", time.time()), linking_uuid
        )
        
        # 4. Store in Supabase
        analysis.update({
            "worker_id": worker.worker_id,
            "source_file": video_path,
            "s3_url": s3_url,
            "linking_uuid": linking_uuid
        })
        
        user_id = job.get("metadata", {}).get("user_id")
        supabase_uuid = await worker.supabase_manager.insert_video_analysis(
            analysis, user_id
        )
        
        original_duration = time.time() - start_time
        
        await worker.stop()
        
        results["original"] = {
            "duration": original_duration,
            "success": supabase_uuid is not None,
            "result": analysis
        }
        
        print(f"   ⏱️  Duration: {original_duration:.2f}s")
        print(f"   ✅ Success: {results['original']['success']}")
        
    except Exception as e:
        results["original"] = {
            "duration": 0,
            "success": False,
            "error": str(e)
        }
        print(f"   ❌ Error: {e}")
    
    return results


async def test_queue_responsiveness():
    """Test Redis queue responsiveness"""
    print("\n📡 Testing Queue Responsiveness")
    print("=" * 40)
    
    queue_manager = VideoQueueManager()
    
    try:
        if not await queue_manager.connect():
            print("❌ Failed to connect to Redis")
            return None
        
        # Test queue operations
        test_job = {
            "video_path": "/test/path.mp4",
            "metadata": {"test": True},
            "timestamp": time.time()
        }
        
        # Add to queue
        start_time = time.time()
        success = await queue_manager.add_video_segment("/test/path.mp4", {"test": True})
        add_duration = time.time() - start_time
        
        # Get from queue
        start_time = time.time()
        job = await queue_manager.get_video_segment(timeout=1)
        get_duration = time.time() - start_time
        
        print(f"   📤 Add to queue: {add_duration*1000:.1f}ms")
        print(f"   📥 Get from queue: {get_duration*1000:.1f}ms")
        print(f"   🎯 Queue timeout: {Config.WORKER_TIMEOUT}s")
        
        await queue_manager.disconnect()
        
        return {
            "add_duration": add_duration,
            "get_duration": get_duration,
            "success": success and job is not None
        }
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def print_performance_summary(worker_results, queue_results):
    """Print performance summary"""
    print("\n" + "=" * 60)
    print("🎯 PERFORMANCE TEST SUMMARY")
    print("=" * 60)
    
    # Worker performance
    if worker_results:
        opt = worker_results.get("optimized", {})
        orig = worker_results.get("original", {})
        
        if opt.get("success") and orig.get("success"):
            improvement = ((orig["duration"] - opt["duration"]) / orig["duration"]) * 100
            
            print("📊 WORKER PERFORMANCE:")
            print(f"   Original Method:   {orig['duration']:.2f}s")
            print(f"   Optimized Method:  {opt['duration']:.2f}s")
            print(f"   Improvement:       {improvement:.1f}%")
            
            if improvement > 30:
                print("   🏆 EXCELLENT: Major performance boost!")
            elif improvement > 15:
                print("   🎉 GREAT: Significant improvement!")
            elif improvement > 5:
                print("   ✅ GOOD: Noticeable improvement")
            elif improvement > 0:
                print("   👍 OK: Slight improvement")
            else:
                print("   ⚠️  WARNING: No improvement detected")
        else:
            print("📊 WORKER PERFORMANCE:")
            print("   ❌ Unable to compare - test failures occurred")
    
    # Queue performance
    if queue_results and queue_results.get("success"):
        print(f"\n🔄 QUEUE PERFORMANCE:")
        print(f"   Add Operation:    {queue_results['add_duration']*1000:.1f}ms")
        print(f"   Get Operation:    {queue_results['get_duration']*1000:.1f}ms")
        print(f"   Timeout Setting:  {Config.WORKER_TIMEOUT*1000:.0f}ms")
        
        if queue_results['get_duration'] < 0.001:
            print("   🚀 EXCELLENT: Very fast queue operations")
        elif queue_results['get_duration'] < 0.01:
            print("   ✅ GOOD: Fast queue operations")
        else:
            print("   ⚠️  OK: Queue operations within expected range")
    
    print("\n" + "=" * 60)


async def main():
    """Main test function"""
    print("🎬 Quick Performance Test for Video Processing Pipeline")
    print("=" * 70)
    
    # Check prerequisites
    api_key = os.getenv("TWELVELABS_API_KEY") or Config.TWELVELABS_API_KEY
    if not api_key:
        print("❌ TWELVELABS_API_KEY is required")
        print("   export TWELVELABS_API_KEY='your_api_key'")
        sys.exit(1)
    
    # Check Redis
    queue_manager = VideoQueueManager()
    if not await queue_manager.connect():
        print("❌ Redis connection failed")
        print("   Make sure Redis is running on localhost:6379")
        print("   Or use Docker: docker-compose up -d redis")
        sys.exit(1)
    await queue_manager.disconnect()
    
    print("✅ Prerequisites checked")
    
    # Create test video
    temp_dir = tempfile.mkdtemp(prefix="quick_perf_test_")
    video_path = os.path.join(temp_dir, "test_video.mp4")
    
    try:
        create_simple_test_video(video_path, duration=6)  # Short video for quick test
        
        # Run tests
        print(f"\n🧪 Running performance tests...")
        print(f"📁 Test video: {video_path}")
        
        # Test worker performance
        worker_results = await test_worker_performance(api_key, video_path)
        
        # Test queue responsiveness
        queue_results = await test_queue_responsiveness()
        
        # Print summary
        print_performance_summary(worker_results, queue_results)
        
    finally:
        # Cleanup
        if os.path.exists(video_path):
            os.remove(video_path)
        os.rmdir(temp_dir)
        print(f"\n🧹 Cleanup complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
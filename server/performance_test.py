#!/usr/bin/env python3
"""
Performance Test Suite for Video Processing Pipeline
Compares old vs new optimized implementations
"""

import asyncio
import time
import json
import os
import sys
import tempfile
import shutil
import statistics
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Import system components
from config import Config
from video_queue.queue_manager import VideoQueueManager
from video_queue.worker_manager import WorkerManager
from video_processing.worker import VideoProcessingWorker
from performance_optimizer import get_performance_optimizer

# For creating test videos
import cv2
import numpy as np


@dataclass
class TestResult:
    """Single test result"""
    test_name: str
    implementation: str  # "old" or "new"
    duration: float
    success: bool
    error: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class PerformanceComparison:
    """Performance comparison results"""
    old_results: List[TestResult]
    new_results: List[TestResult]
    improvement_percentage: float
    statistical_significance: bool


class VideoTestGenerator:
    """Generate test videos for performance testing"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def create_test_video(self, filename: str, duration: int = 10, fps: int = 10, 
                         resolution: Tuple[int, int] = (1280, 720)) -> str:
        """Create a test video file"""
        output_path = self.output_dir / filename
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(str(output_path), fourcc, fps, resolution)
        
        total_frames = duration * fps
        
        for frame_num in range(total_frames):
            # Create a simple test frame with moving pattern
            frame = np.zeros((resolution[1], resolution[0], 3), dtype=np.uint8)
            
            # Add some visual content (moving rectangle)
            x = int((frame_num / total_frames) * resolution[0])
            y = resolution[1] // 2
            cv2.rectangle(frame, (x-50, y-50), (x+50, y+50), (0, 255, 0), -1)
            
            # Add frame number text
            cv2.putText(frame, f"Frame {frame_num}", (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            writer.write(frame)
        
        writer.release()
        return str(output_path)
    
    def create_test_batch(self, count: int = 5) -> List[str]:
        """Create a batch of test videos"""
        videos = []
        for i in range(count):
            video_path = self.create_test_video(f"test_video_{i:03d}.mp4")
            videos.append(video_path)
        return videos


class PerformanceTester:
    """Main performance testing class"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.test_dir = tempfile.mkdtemp(prefix="video_performance_test_")
        self.video_generator = VideoTestGenerator(self.test_dir)
        self.queue_manager = VideoQueueManager()
        self.results: List[TestResult] = []
        
        print(f"📁 Test directory: {self.test_dir}")
    
    async def setup(self):
        """Setup test environment"""
        print("🔧 Setting up test environment...")
        
        # Connect to Redis
        if not await self.queue_manager.connect():
            raise RuntimeError("Failed to connect to Redis")
        
        # Clear any existing queue
        await self.queue_manager.clear_queue()
        
        print("✅ Test environment ready")
    
    async def cleanup(self):
        """Cleanup test environment"""
        print("🧹 Cleaning up test environment...")
        
        # Clear queue
        if self.queue_manager.redis:
            await self.queue_manager.clear_queue()
            await self.queue_manager.disconnect()
        
        # Remove test directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        
        print("✅ Cleanup complete")
    
    async def test_single_video_processing(self, video_path: str, 
                                         implementation: str = "new") -> TestResult:
        """Test processing a single video"""
        start_time = time.time()
        
        try:
            # Create worker with appropriate method
            worker = VideoProcessingWorker(worker_id=0, api_key=self.api_key)
            await worker.start()
            
            # Create job
            job = {
                "video_path": video_path,
                "metadata": {
                    "user_id": "test_user",
                    "test_mode": True
                },
                "timestamp": time.time()
            }
            
            # Process video using appropriate method
            if implementation == "old":
                # Use original methods
                result = await self._process_video_old_way(worker, job)
            else:
                # Use optimized methods
                result = await worker.process_video_segment(job)
            
            await worker.stop()
            
            duration = time.time() - start_time
            success = result is not None and "error" not in result
            
            return TestResult(
                test_name="single_video_processing",
                implementation=implementation,
                duration=duration,
                success=success,
                error=result.get("error") if result and "error" in result else None,
                metadata={
                    "video_path": video_path,
                    "result_keys": list(result.keys()) if result else []
                }
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name="single_video_processing",
                implementation=implementation,
                duration=duration,
                success=False,
                error=str(e)
            )
    
    async def _process_video_old_way(self, worker: VideoProcessingWorker, job: Dict) -> Dict:
        """Simulate old processing way (serial operations)"""
        try:
            video_path = job["video_path"]
            metadata = job.get("metadata", {})
            
            # Check if file exists
            if not os.path.exists(video_path):
                return {"error": f"Video file not found: {video_path}"}
            
            # Generate linking UUID
            linking_uuid = worker.supabase_manager.generate_linking_uuid()
            
            # Serial processing (old way)
            start_time = time.time()
            
            # 1. Upload video (blocking)
            video_id = await worker.upload_video(video_path, metadata)
            if not video_id:
                return {"error": "Failed to upload video"}
            
            # 2. S3 upload (blocking) 
            loop = asyncio.get_event_loop()
            s3_url = await loop.run_in_executor(
                None, worker.s3_manager.upload_video_segment, video_path
            )
            
            # 3. Analyze video (blocking)
            analysis = await worker.analyze_video(
                video_id, job.get("timestamp", time.time()), linking_uuid
            )
            
            # 4. Store in Supabase (blocking)
            analysis.update({
                "worker_id": worker.worker_id,
                "source_file": video_path,
                "s3_url": s3_url,
                "file_size": os.path.getsize(video_path),
                "processed_at": datetime.now().isoformat(),
                "twelvelabs_video_id": video_id,
                "linking_uuid": linking_uuid
            })
            
            user_id = job.get("metadata", {}).get("user_id")
            supabase_uuid = await worker.supabase_manager.insert_video_analysis(
                analysis, user_id
            )
            
            # 5. Process embeddings (blocking)
            if supabase_uuid:
                embedding_result = await worker.embed_and_store_video_with_retry(
                    video_path=video_path,
                    linking_uuid=linking_uuid,
                    timestamp=job.get("timestamp", time.time())
                )
                
                # 6. Run automations (blocking)
                summary = analysis.get("detailed_summary", "")
                if summary:
                    automation_metadata = {
                        "video_id": linking_uuid,
                        "user_id": user_id,
                        "timestamp": analysis.get("datetime"),
                        "source": "video_processing",
                        "worker_id": worker.worker_id,
                    }
                    
                    automation_result = await worker.run_automations_with_retry(
                        video_id=linking_uuid,
                        summary=summary,
                        metadata=automation_metadata,
                    )
            
            analysis["supabase_stored"] = supabase_uuid is not None
            analysis["processing_time"] = time.time() - start_time
            return analysis
            
        except Exception as e:
            return {"error": str(e), "video_path": job.get("video_path", "unknown")}
    
    async def test_batch_processing(self, video_paths: List[str], 
                                   implementation: str = "new",
                                   num_workers: int = 3) -> List[TestResult]:
        """Test batch processing with multiple workers"""
        print(f"🔄 Testing batch processing: {len(video_paths)} videos, {num_workers} workers ({implementation})")
        
        start_time = time.time()
        results = []
        
        try:
            # Add videos to queue
            for video_path in video_paths:
                metadata = {
                    "user_id": "test_user",
                    "test_mode": True,
                    "batch_test": True
                }
                await self.queue_manager.add_video_segment(video_path, metadata)
            
            # Create worker manager
            worker_manager = WorkerManager(api_key=self.api_key, num_workers=num_workers)
            
            # Start performance monitoring
            optimizer = get_performance_optimizer(worker_manager)
            if optimizer:
                monitoring_task = asyncio.create_task(
                    optimizer.start_monitoring(interval=5)
                )
            
            # Process videos
            processing_start = time.time()
            
            # Start workers
            worker_task = asyncio.create_task(worker_manager.start_workers())
            
            # Wait for all videos to be processed
            while True:
                queue_size = await self.queue_manager.get_queue_size()
                if queue_size == 0:
                    break
                await asyncio.sleep(1)
            
            processing_duration = time.time() - processing_start
            
            # Stop workers
            await worker_manager.stop_workers()
            worker_task.cancel()
            
            # Stop monitoring
            if optimizer:
                await optimizer.stop_monitoring()
                monitoring_task.cancel()
            
            # Create result
            total_duration = time.time() - start_time
            
            result = TestResult(
                test_name="batch_processing",
                implementation=implementation,
                duration=total_duration,
                success=True,
                metadata={
                    "num_videos": len(video_paths),
                    "num_workers": num_workers,
                    "processing_duration": processing_duration,
                    "avg_time_per_video": processing_duration / len(video_paths),
                    "performance_report": optimizer.get_performance_report() if optimizer else None
                }
            )
            
            results.append(result)
            
        except Exception as e:
            total_duration = time.time() - start_time
            result = TestResult(
                test_name="batch_processing",
                implementation=implementation,
                duration=total_duration,
                success=False,
                error=str(e)
            )
            results.append(result)
        
        return results
    
    async def test_api_polling_performance(self) -> List[TestResult]:
        """Test TwelveLabs API polling performance"""
        print("📡 Testing API polling performance...")
        
        results = []
        test_video = self.video_generator.create_test_video("polling_test.mp4", duration=5)
        
        # Test old polling vs new polling
        worker = VideoProcessingWorker(worker_id=0, api_key=self.api_key)
        await worker.start()
        
        try:
            # Create upload task
            if not worker.index_id:
                await worker.ensure_index()
            
            task = worker.client.task.create(index_id=worker.index_id, file=test_video)
            
            # Test old polling method
            start_time = time.time()
            old_result = await worker._wait_for_task_async(task, 1.0)  # 1s intervals
            old_duration = time.time() - start_time
            
            results.append(TestResult(
                test_name="api_polling",
                implementation="old",
                duration=old_duration,
                success=old_result is not None,
                metadata={"polling_interval": 1.0, "result": old_result}
            ))
            
            # Create another task for new method
            task2 = worker.client.task.create(index_id=worker.index_id, file=test_video)
            
            # Test new polling method
            start_time = time.time()
            new_result = await worker._wait_for_task_optimized(task2, 0.5)  # 0.5s intervals
            new_duration = time.time() - start_time
            
            results.append(TestResult(
                test_name="api_polling",
                implementation="new",
                duration=new_duration,
                success=new_result is not None,
                metadata={"polling_interval": 0.5, "result": new_result}
            ))
            
        except Exception as e:
            results.append(TestResult(
                test_name="api_polling",
                implementation="error",
                duration=0,
                success=False,
                error=str(e)
            ))
        
        finally:
            await worker.stop()
        
        return results
    
    def analyze_results(self, results: List[TestResult]) -> Dict:
        """Analyze test results and generate comparison"""
        old_results = [r for r in results if r.implementation == "old" and r.success]
        new_results = [r for r in results if r.implementation == "new" and r.success]
        
        if not old_results or not new_results:
            return {"error": "Insufficient data for comparison"}
        
        # Group by test name
        comparison = {}
        
        for test_name in set(r.test_name for r in results):
            old_times = [r.duration for r in old_results if r.test_name == test_name]
            new_times = [r.duration for r in new_results if r.test_name == test_name]
            
            if old_times and new_times:
                old_avg = statistics.mean(old_times)
                new_avg = statistics.mean(new_times)
                improvement = ((old_avg - new_avg) / old_avg) * 100
                
                comparison[test_name] = {
                    "old_avg_time": old_avg,
                    "new_avg_time": new_avg,
                    "improvement_percentage": improvement,
                    "old_times": old_times,
                    "new_times": new_times,
                    "sample_size": min(len(old_times), len(new_times))
                }
        
        return comparison
    
    def generate_report(self, results: List[TestResult], comparison: Dict) -> str:
        """Generate detailed performance report"""
        report = []
        report.append("=" * 80)
        report.append("VIDEO PROCESSING PERFORMANCE TEST REPORT")
        report.append("=" * 80)
        report.append(f"Test Date: {datetime.now().isoformat()}")
        report.append(f"Total Tests Run: {len(results)}")
        report.append(f"Successful Tests: {sum(1 for r in results if r.success)}")
        report.append(f"Failed Tests: {sum(1 for r in results if not r.success)}")
        report.append("")
        
        # Overall summary
        report.append("PERFORMANCE COMPARISON SUMMARY")
        report.append("-" * 40)
        
        total_improvement = 0
        test_count = 0
        
        for test_name, data in comparison.items():
            improvement = data["improvement_percentage"]
            total_improvement += improvement
            test_count += 1
            
            report.append(f"{test_name.upper()}:")
            report.append(f"  Old Average Time: {data['old_avg_time']:.2f}s")
            report.append(f"  New Average Time: {data['new_avg_time']:.2f}s")
            report.append(f"  Improvement: {improvement:.1f}% {'📈' if improvement > 0 else '📉'}")
            report.append(f"  Sample Size: {data['sample_size']}")
            report.append("")
        
        if test_count > 0:
            avg_improvement = total_improvement / test_count
            report.append(f"OVERALL AVERAGE IMPROVEMENT: {avg_improvement:.1f}%")
        
        report.append("")
        report.append("DETAILED RESULTS")
        report.append("-" * 40)
        
        for result in results:
            status = "✅" if result.success else "❌"
            report.append(f"{status} {result.test_name} ({result.implementation}): {result.duration:.2f}s")
            if result.error:
                report.append(f"    Error: {result.error}")
            if result.metadata:
                for key, value in result.metadata.items():
                    if key != "performance_report":  # Skip large nested objects
                        report.append(f"    {key}: {value}")
            report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    async def run_comprehensive_test(self) -> str:
        """Run comprehensive performance test suite"""
        print("🚀 Starting Comprehensive Performance Test Suite")
        print("=" * 60)
        
        await self.setup()
        
        try:
            all_results = []
            
            # 1. Create test videos
            print("📹 Creating test videos...")
            test_videos = self.video_generator.create_test_batch(count=3)
            
            # 2. Test single video processing
            print("🎬 Testing single video processing...")
            for i, video in enumerate(test_videos[:2]):  # Test first 2 videos
                # Test old method
                old_result = await self.test_single_video_processing(video, "old")
                all_results.append(old_result)
                print(f"  Old method video {i+1}: {old_result.duration:.2f}s {'✅' if old_result.success else '❌'}")
                
                # Test new method  
                new_result = await self.test_single_video_processing(video, "new")
                all_results.append(new_result)
                print(f"  New method video {i+1}: {new_result.duration:.2f}s {'✅' if new_result.success else '❌'}")
            
            # 3. Test API polling performance
            print("📡 Testing API polling performance...")
            polling_results = await self.test_api_polling_performance()
            all_results.extend(polling_results)
            
            # 4. Test batch processing (if we have enough videos)
            if len(test_videos) >= 2:
                print("🔄 Testing batch processing...")
                batch_results = await self.test_batch_processing(test_videos, "new", 2)
                all_results.extend(batch_results)
            
            # 5. Analyze results
            comparison = self.analyze_results(all_results)
            
            # 6. Generate report
            report = self.generate_report(all_results, comparison)
            
            # Save report to file
            report_file = f"{self.test_dir}/performance_report.txt"
            with open(report_file, 'w') as f:
                f.write(report)
            
            print(f"📄 Report saved to: {report_file}")
            return report
            
        finally:
            await self.cleanup()


async def main():
    """Main test runner"""
    # Check for API key
    api_key = os.getenv("TWELVELABS_API_KEY") or Config.TWELVELABS_API_KEY
    if not api_key:
        print("❌ Error: TWELVELABS_API_KEY is required")
        print("Please set your API key:")
        print("  export TWELVELABS_API_KEY='your_api_key_here'")
        sys.exit(1)
    
    # Check Redis connection
    queue_manager = VideoQueueManager()
    if not await queue_manager.connect():
        print("❌ Error: Redis connection failed")
        print("Please ensure Redis is running on localhost:6379")
        sys.exit(1)
    await queue_manager.disconnect()
    
    # Run tests
    tester = PerformanceTester(api_key)
    
    try:
        report = await tester.run_comprehensive_test()
        print("\n" + "=" * 80)
        print("PERFORMANCE TEST COMPLETE!")
        print("=" * 80)
        print(report)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
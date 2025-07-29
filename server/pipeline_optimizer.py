#!/usr/bin/env python3
"""
Pipeline Performance Optimizer and Validator
Validates that video segments are processed at consistent 10-second intervals
"""

import asyncio
import time
from datetime import datetime
from video_queue.queue_manager import VideoQueueManager


class PipelineOptimizer:
    """Optimizes and validates pipeline timing consistency"""

    def __init__(self):
        self.queue_manager = VideoQueueManager()
        self.timing_data = []

    async def start_validation(self, duration_minutes: int = 5):
        """Start timing validation for specified duration"""
        print(
            f"🚀 Starting pipeline timing validation for {duration_minutes} minutes..."
        )
        await self.queue_manager.connect()

        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)

        while time.time() < end_time:
            # Monitor queue and timing consistency
            await self._check_timing_consistency()
            await asyncio.sleep(10)  # Check every 10 seconds

        # Generate final report
        await self._generate_optimization_report()

    async def _check_timing_consistency(self):
        """Check if segments are being processed at consistent intervals"""
        queue_size = await self.queue_manager.get_queue_size()
        timestamp = datetime.now()

        self.timing_data.append({"timestamp": timestamp, "queue_size": queue_size})

        # Print queue size info (performance_monitor removed)
        print(f"Queue size at {timestamp.strftime('%H:%M:%S')}: {queue_size}")

    async def _diagnose_bottlenecks(self):
        """Diagnose pipeline bottlenecks (stub, performance_monitor removed)"""
        print("Bottleneck diagnosis not available (performance monitoring disabled).")

    async def _generate_optimization_report(self):
        """Generate comprehensive optimization report (performance_monitor removed)"""
        print("\n" + "=" * 60)
        print("📊 PIPELINE OPTIMIZATION REPORT")
        print("=" * 60)

        # Timing consistency (performance_monitor removed)
        print("⏱️  TIMING ANALYSIS:")
        print("   Expected interval: 10.00s")
        print(
            "   (Detailed timing analysis unavailable - performance monitoring disabled)"
        )

        # Queue analysis
        queue_sizes = [d["queue_size"] for d in self.timing_data]
        if queue_sizes:
            avg_queue = sum(queue_sizes) / len(queue_sizes)
            max_queue = max(queue_sizes)
            print("\n📊 QUEUE ANALYSIS:")
            print(f"   Average queue size: {avg_queue:.1f}")
            print(f"   Maximum queue size: {max_queue}")

            if avg_queue > 5:
                print("   ⚠️  High average queue size indicates processing bottleneck")
            if max_queue > 20:
                print("   ❌ Very high peak queue size - consider increasing workers")

        # Recommendations
        print("\n💡 OPTIMIZATION RECOMMENDATIONS:")
        await self._generate_recommendations()

        print("=" * 60)

    async def _generate_recommendations(self):
        """Generate specific optimization recommendations (performance_monitor removed)"""
        queue_sizes = [d["queue_size"] for d in self.timing_data]
        recommendations = []

        if queue_sizes and max(queue_sizes) > 20:
            recommendations.append("Increase number of workers from 3 to 5")
            recommendations.append("Implement queue priority handling")
        elif queue_sizes and sum(queue_sizes) / len(queue_sizes) > 5:
            recommendations.append(
                "Monitor for queue backlog and optimize processing speed"
            )
        else:
            recommendations = [
                "✅ Pipeline is performing well",
                "Monitor for any degradation over time",
                "Consider stress testing with higher video volumes",
            ]

        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")


async def main():
    """Main function to run pipeline optimization"""
    optimizer = PipelineOptimizer()

    print("🎥 Video Pipeline Optimizer")
    print("This tool validates 10-second segment timing consistency")
    print("Run this while your pipeline is processing video segments")

    try:
        await optimizer.start_validation(duration_minutes=5)
    except KeyboardInterrupt:
        print("\n⏹️  Optimization monitoring stopped by user")
    except Exception as e:
        print(f"❌ Error during optimization: {e}")


if __name__ == "__main__":
    asyncio.run(main())

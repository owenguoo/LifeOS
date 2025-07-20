#!/usr/bin/env python3
"""
Pipeline Performance Optimizer and Validator
Validates that video segments are processed at consistent 10-second intervals
"""

import asyncio
import time
from datetime import datetime, timedelta
from performance_monitor import performance_monitor
from video_queue.queue_manager import VideoQueueManager

class PipelineOptimizer:
    """Optimizes and validates pipeline timing consistency"""
    
    def __init__(self):
        self.queue_manager = VideoQueueManager()
        self.timing_data = []
        
    async def start_validation(self, duration_minutes: int = 5):
        """Start timing validation for specified duration"""
        print(f"🚀 Starting pipeline timing validation for {duration_minutes} minutes...")
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
        
        self.timing_data.append({
            "timestamp": timestamp,
            "queue_size": queue_size
        })
        
        # Check for timing consistency
        consistency_report = performance_monitor.check_timing_consistency()
        
        if "actual_average_interval" in consistency_report:
            avg_interval = consistency_report["actual_average_interval"]
            deviation = consistency_report["deviation_from_expected"]
            
            status = "✅ GOOD" if deviation < 2.0 else "❌ POOR"
            print(f"{status} | Queue: {queue_size:2d} | Avg Interval: {avg_interval:.2f}s | Deviation: {deviation:.2f}s")
            
            if deviation > 5.0:
                print(f"⚠️  HIGH DEVIATION DETECTED: {deviation:.2f}s - investigating bottlenecks...")
                await self._diagnose_bottlenecks()
    
    async def _diagnose_bottlenecks(self):
        """Diagnose pipeline bottlenecks"""
        report = performance_monitor.get_performance_report()
        
        if "recent_bottlenecks" in report and report["recent_bottlenecks"]:
            print("🔍 Recent bottlenecks found:")
            for bottleneck in report["recent_bottlenecks"][-3:]:
                print(f"   - {bottleneck['type']}: {bottleneck.get('duration', 'N/A')}s")
        
        # Check queue backlog
        if "queue_metrics" in report:
            avg_queue_size = report["queue_metrics"]["current_average_size"]
            if avg_queue_size > 10:
                print(f"📈 Queue backlog detected: {avg_queue_size:.1f} average segments")
    
    async def _generate_optimization_report(self):
        """Generate comprehensive optimization report"""
        print("\n" + "="*60)
        print("📊 PIPELINE OPTIMIZATION REPORT")
        print("="*60)
        
        # Timing consistency
        consistency_report = performance_monitor.check_timing_consistency()
        if "actual_average_interval" in consistency_report:
            avg_interval = consistency_report["actual_average_interval"]
            deviation = consistency_report["deviation_from_expected"]
            consistency = consistency_report["interval_consistency"]
            
            print(f"⏱️  TIMING ANALYSIS:")
            print(f"   Expected interval: 10.00s")
            print(f"   Actual average:    {avg_interval:.2f}s")
            print(f"   Deviation:         {deviation:.2f}s")
            print(f"   Consistency:       {consistency.upper()}")
            
            if consistency == "good":
                print("   ✅ Pipeline timing is within acceptable range")
            else:
                print("   ❌ Pipeline timing needs optimization")
        
        # Performance metrics
        perf_report = performance_monitor.get_performance_report()
        if "stage_performance" in perf_report:
            print(f"\n🏭 STAGE PERFORMANCE:")
            for stage, stats in perf_report["stage_performance"].items():
                avg_time = stats["average"]
                max_time = stats["max"]
                count = stats["count"]
                print(f"   {stage:20s}: {avg_time:6.2f}s avg, {max_time:6.2f}s max ({count} samples)")
        
        # Queue analysis
        queue_sizes = [d["queue_size"] for d in self.timing_data]
        if queue_sizes:
            avg_queue = sum(queue_sizes) / len(queue_sizes)
            max_queue = max(queue_sizes)
            print(f"\n📊 QUEUE ANALYSIS:")
            print(f"   Average queue size: {avg_queue:.1f}")
            print(f"   Maximum queue size: {max_queue}")
            
            if avg_queue > 5:
                print("   ⚠️  High average queue size indicates processing bottleneck")
            if max_queue > 20:
                print("   ❌ Very high peak queue size - consider increasing workers")
        
        # Recommendations
        print(f"\n💡 OPTIMIZATION RECOMMENDATIONS:")
        await self._generate_recommendations(consistency_report, perf_report)
        
        print("="*60)
    
    async def _generate_recommendations(self, consistency_report, perf_report):
        """Generate specific optimization recommendations"""
        recommendations = []
        
        # Timing recommendations
        if "deviation_from_expected" in consistency_report:
            deviation = consistency_report["deviation_from_expected"]
            if deviation > 5.0:
                recommendations.append("Reduce TwelveLabs polling interval to 0.5s")
                recommendations.append("Implement async task processing for uploads")
            elif deviation > 2.0:
                recommendations.append("Fine-tune worker timeout settings")
        
        # Performance recommendations
        if "stage_performance" in perf_report:
            for stage, stats in perf_report["stage_performance"].items():
                if stats["average"] > 30:
                    if "upload" in stage.lower():
                        recommendations.append(f"Optimize {stage} - consider connection pooling")
                    elif "embedding" in stage.lower():
                        recommendations.append(f"Parallelize {stage} processing")
        
        # Queue recommendations
        queue_sizes = [d["queue_size"] for d in self.timing_data]
        if queue_sizes and max(queue_sizes) > 20:
            recommendations.append("Increase number of workers from 3 to 5")
            recommendations.append("Implement queue priority handling")
        
        # Default recommendations if none specific
        if not recommendations:
            recommendations = [
                "✅ Pipeline is performing well",
                "Monitor for any degradation over time",
                "Consider stress testing with higher video volumes"
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
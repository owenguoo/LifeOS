"""
Performance optimizer for video processing pipeline
Provides monitoring and auto-scaling capabilities
"""

import asyncio
import time
from typing import Dict, List, Optional
from video_queue.queue_manager import VideoQueueManager
from video_queue.worker_manager import WorkerManager
import psutil
import logging

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """Monitors and optimizes video processing pipeline performance"""
    
    def __init__(self, worker_manager: WorkerManager):
        self.worker_manager = worker_manager
        self.queue_manager = VideoQueueManager()
        self.metrics = {
            "queue_size_history": [],
            "processing_times": [],
            "worker_utilization": [],
            "throughput_history": [],
        }
        self.is_monitoring = False
        
    async def start_monitoring(self, interval: int = 30):
        """Start performance monitoring with auto-scaling"""
        self.is_monitoring = True
        logger.info("Starting performance monitoring")
        
        await self.queue_manager.connect()
        
        while self.is_monitoring:
            try:
                # Collect metrics
                await self._collect_metrics()
                
                # Analyze and optimize
                await self._analyze_and_optimize()
                
                # Wait for next cycle
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}")
                await asyncio.sleep(interval)
    
    async def stop_monitoring(self):
        """Stop performance monitoring"""
        self.is_monitoring = False
        await self.queue_manager.disconnect()
        logger.info("Stopped performance monitoring")
    
    async def _collect_metrics(self):
        """Collect performance metrics"""
        try:
            # Queue metrics
            queue_size = await self.queue_manager.get_queue_size()
            self.metrics["queue_size_history"].append({
                "timestamp": time.time(),
                "size": queue_size
            })
            
            # Worker metrics
            worker_stats = await self.worker_manager.get_worker_stats()
            active_workers = worker_stats["active_workers"]
            total_processed = worker_stats["total_processed"]
            
            self.metrics["worker_utilization"].append({
                "timestamp": time.time(),
                "active_workers": active_workers,
                "total_workers": worker_stats["total_workers"],
                "utilization": active_workers / worker_stats["total_workers"]
            })
            
            # System metrics
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            
            logger.info(f"Metrics - Queue: {queue_size}, Workers: {active_workers}, CPU: {cpu_percent}%, RAM: {memory_percent}%")
            
            # Keep only last 100 entries to prevent memory growth
            for key in self.metrics:
                if len(self.metrics[key]) > 100:
                    self.metrics[key] = self.metrics[key][-100:]
                    
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
    
    async def _analyze_and_optimize(self):
        """Analyze metrics and trigger optimizations"""
        try:
            # Check for queue buildup
            recent_queue_sizes = [m["size"] for m in self.metrics["queue_size_history"][-5:]]
            if recent_queue_sizes and all(size > 10 for size in recent_queue_sizes):
                logger.warning("Queue buildup detected - consider scaling up workers")
                await self._suggest_optimizations("queue_buildup")
            
            # Check worker utilization
            recent_utilization = [m["utilization"] for m in self.metrics["worker_utilization"][-3:]]
            if recent_utilization and all(util < 0.5 for util in recent_utilization):
                logger.info("Low worker utilization - consider scaling down")
                await self._suggest_optimizations("low_utilization")
            
            # Check for processing bottlenecks
            if len(self.metrics["processing_times"]) > 10:
                avg_processing_time = sum(self.metrics["processing_times"][-10:]) / 10
                if avg_processing_time > 60:  # More than 1 minute average
                    logger.warning(f"High processing times detected: {avg_processing_time:.2f}s average")
                    await self._suggest_optimizations("slow_processing")
                    
        except Exception as e:
            logger.error(f"Error analyzing metrics: {e}")
    
    async def _suggest_optimizations(self, issue_type: str):
        """Suggest optimizations based on detected issues"""
        suggestions = {
            "queue_buildup": [
                "Consider increasing NUM_WORKERS in config",
                "Check if TwelveLabs API is responding slowly",
                "Verify S3 upload performance",
                "Consider reducing video quality/resolution temporarily"
            ],
            "low_utilization": [
                "Consider reducing NUM_WORKERS to save resources",
                "Check if input video generation is bottleneck",
                "Verify Redis queue is receiving videos"
            ],
            "slow_processing": [
                "Check TwelveLabs API response times",
                "Verify network connectivity",
                "Consider optimizing video encoding settings",
                "Check system resources (CPU/Memory/Disk)"
            ]
        }
        
        if issue_type in suggestions:
            logger.info(f"Optimization suggestions for {issue_type}:")
            for suggestion in suggestions[issue_type]:
                logger.info(f"  - {suggestion}")
    
    def get_performance_report(self) -> Dict:
        """Generate performance report"""
        if not self.metrics["queue_size_history"]:
            return {"error": "No metrics collected yet"}
        
        # Calculate averages
        recent_queue_sizes = [m["size"] for m in self.metrics["queue_size_history"][-10:]]
        recent_utilization = [m["utilization"] for m in self.metrics["worker_utilization"][-10:]]
        
        avg_queue_size = sum(recent_queue_sizes) / len(recent_queue_sizes) if recent_queue_sizes else 0
        avg_utilization = sum(recent_utilization) / len(recent_utilization) if recent_utilization else 0
        
        # Calculate throughput (videos processed per minute)
        if len(self.metrics["worker_utilization"]) >= 2:
            time_span = (self.metrics["worker_utilization"][-1]["timestamp"] - 
                        self.metrics["worker_utilization"][0]["timestamp"]) / 60  # minutes
            if time_span > 0:
                total_processed = sum(w.processed_count for w in self.worker_manager.workers)
                throughput = total_processed / time_span
            else:
                throughput = 0
        else:
            throughput = 0
        
        return {
            "avg_queue_size": round(avg_queue_size, 2),
            "avg_worker_utilization": round(avg_utilization, 2),
            "throughput_per_minute": round(throughput, 2),
            "total_metrics_collected": len(self.metrics["queue_size_history"]),
            "monitoring_active": self.is_monitoring,
            "recommendations": self._get_recommendations(avg_queue_size, avg_utilization, throughput)
        }
    
    def _get_recommendations(self, queue_size: float, utilization: float, throughput: float) -> List[str]:
        """Get performance recommendations"""
        recommendations = []
        
        if queue_size > 20:
            recommendations.append("High queue size - consider increasing workers or optimizing processing")
        elif queue_size < 2 and utilization < 0.3:
            recommendations.append("Low queue size and utilization - consider reducing workers")
        
        if utilization > 0.9:
            recommendations.append("High worker utilization - consider adding more workers")
        elif utilization < 0.2:
            recommendations.append("Low worker utilization - check input generation or reduce workers")
        
        if throughput < 1:
            recommendations.append("Low throughput - investigate processing bottlenecks")
        elif throughput > 10:
            recommendations.append("Excellent throughput - system is performing well")
        
        if not recommendations:
            recommendations.append("System appears to be running optimally")
        
        return recommendations


# Global optimizer instance
performance_optimizer = None

def get_performance_optimizer(worker_manager: WorkerManager = None) -> Optional[PerformanceOptimizer]:
    """Get or create performance optimizer instance"""
    global performance_optimizer
    
    if performance_optimizer is None and worker_manager:
        performance_optimizer = PerformanceOptimizer(worker_manager)
    
    return performance_optimizer
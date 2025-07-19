import asyncio
import cv2
import os
import time
import tempfile
from datetime import datetime
from pathlib import Path
import threading
import queue
import sys
import signal
from config import Config
from video_queue.queue_manager import VideoQueueManager

class VideoIngestionSystem:
    def __init__(self, 
                 fps=30, 
                 resolution=(1280, 720),
                 segment_duration=10,
                 user_id=None):
        
        self.fps = fps
        self.resolution = resolution
        self.segment_duration = segment_duration
        self.user_id = user_id
        
        # Video capture setup
        self.cap = None
        self.is_recording = False
        self.frame_queue = queue.Queue(maxsize=100)
        
        # Queue manager for Redis
        self.queue_manager = VideoQueueManager()
        
        # For Mac FaceTime HD camera
        self.camera_index = int(Config.CAMERA_INDEX) if Config.CAMERA_INDEX else 0
        
        # Thread management
        self.capture_thread = None
        self._shutdown_event = threading.Event()
        
    def initialize_camera(self):
        """Initialize the camera with proper settings for Mac FaceTime HD"""
        try:
            # Try AVFoundation backend first for Mac
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_AVFOUNDATION)
            
            # If AVFoundation fails, try default backend
            if not self.cap.isOpened():
                print("AVFoundation backend failed, trying default backend...")
                self.cap = cv2.VideoCapture(self.camera_index)
            
            # Verify camera opened successfully
            if not self.cap.isOpened():
                raise Exception(f"Failed to open camera at index {self.camera_index}")
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Give camera time to initialize
            time.sleep(1)
            
            # Test frame capture with retries
            for attempt in range(5):
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
                    
                    print(f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps}fps")
                    print(f"Camera index: {self.camera_index}")
                    return True
                else:
                    print(f"Frame capture attempt {attempt + 1} failed, retrying...")
                    time.sleep(0.5)
            
            raise Exception("Failed to capture test frame after multiple attempts")
                
        except Exception as e:
            print(f"Error initializing camera: {e}", file=sys.stderr)
            if self.cap:
                self.cap.release()
            return False
    
    def capture_frames(self):
        """Continuously capture frames and put them in queue"""
        while self.is_recording and not self._shutdown_event.is_set():
            try:
                ret, frame = self.cap.read()
                if ret:
                    timestamp = time.time()
                    
                    # Add frame to queue (non-blocking)
                    try:
                        self.frame_queue.put_nowait((frame, timestamp))
                    except queue.Full:
                        # Drop oldest frame if queue is full
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put_nowait((frame, timestamp))
                        except queue.Empty:
                            pass
                else:
                    print("Failed to capture frame", file=sys.stderr)
                    time.sleep(0.1)
                    
            except Exception as e:
                print(f"Error in frame capture: {e}", file=sys.stderr)
                time.sleep(0.1)
        
        print("Frame capture thread stopped")
    
    def create_video_segment(self, frames_data, segment_id):
        """Create a video segment file and return metadata"""
        if not frames_data:
            return None
            
        try:
            # Create temporary video file
            temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(temp_path, fourcc, self.fps, self.resolution)
            
            # Write frames to video file
            for frame, timestamp in frames_data:
                writer.write(frame)
            
            writer.release()
            
            # Return metadata with file path
            segment_info = {
                "segment_id": segment_id,
                "video_path": temp_path,
                "fps": self.fps,
                "resolution": self.resolution,
                "frame_count": len(frames_data),
                "timestamp": datetime.now().isoformat(),
                "user_id": self.user_id
            }
            
            print(f"Created segment {segment_id} with {len(frames_data)} frames at {temp_path}")
            return segment_info
            
        except Exception as e:
            print(f"Error creating video segment: {e}", file=sys.stderr)
            return None
    
    async def process_segments(self):
        """Async function to process video segments and add to queue"""
        segment_id = 0
        
        # Connect to queue manager
        await self.queue_manager.connect()
        
        while self.is_recording and not self._shutdown_event.is_set():
            try:
                # Collect frames for segment_duration seconds
                frames_for_segment = []
                start_time = time.time()
                
                while (time.time() - start_time) < self.segment_duration and self.is_recording and not self._shutdown_event.is_set():
                    try:
                        frame, timestamp = self.frame_queue.get(timeout=0.1)
                        frames_for_segment.append((frame, timestamp))
                    except queue.Empty:
                        await asyncio.sleep(0.01)
                        continue
                
                if frames_for_segment:
                    # Create segment data without local file storage
                    loop = asyncio.get_event_loop()
                    segment_info = await loop.run_in_executor(
                        None, 
                        self.create_video_segment, 
                        frames_for_segment, 
                        segment_id
                    )
                    
                    if segment_info:
                        # Add video file to Redis queue for processing
                        video_path = segment_info["video_path"]
                        metadata = {k: v for k, v in segment_info.items() if k != "video_path"}
                        await self.queue_manager.add_video_segment(video_path, metadata)
                        print(f"Added segment {segment_id} to processing queue")
                    
                    segment_id += 1
                
            except Exception as e:
                print(f"Error processing segment: {e}", file=sys.stderr)
                await asyncio.sleep(1)
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C signal"""
        print(f"\nReceived signal {signum}, shutting down...")
        self._shutdown_event.set()
        self.is_recording = False
    
    async def start_ingestion(self):
        """Start the video ingestion process"""
        if not self.initialize_camera():
            return False
        
        print("Starting video ingestion with Redis queue...")
        print(f"Segment duration: {self.segment_duration}s")
        print("Direct S3 upload mode - no local storage")
        print("Press Ctrl+C to stop")
        
        # Set up signal handler for Ctrl+C
        signal.signal(signal.SIGINT, self.signal_handler)
        
        self.is_recording = True
        self._shutdown_event.clear()
        
        # Start frame capture in separate thread
        self.capture_thread = threading.Thread(target=self.capture_frames)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        
        # Start async segment processing
        try:
            await self.process_segments()
        except KeyboardInterrupt:
            print("\nReceived KeyboardInterrupt, stopping ingestion...")
        finally:
            await self.stop_ingestion()
    
    async def stop_ingestion(self):
        """Stop the video ingestion process"""
        print("Stopping video ingestion...")
        self.is_recording = False
        self._shutdown_event.set()
        
        # Wait for capture thread to finish
        if self.capture_thread and self.capture_thread.is_alive():
            print("Waiting for capture thread to stop...")
            self.capture_thread.join(timeout=2.0)
            if self.capture_thread.is_alive():
                print("Warning: Capture thread did not stop gracefully")
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        await self.queue_manager.disconnect()
        print("Ingestion stopped")
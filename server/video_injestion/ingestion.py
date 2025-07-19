import asyncio
import cv2
import os
import time
from datetime import datetime
from pathlib import Path
import threading
import queue
import sys
from config import Config
from video_queue.queue_manager import VideoQueueManager

class VideoIngestionSystem:
    def __init__(self, 
                 fps=30, 
                 resolution=(1280, 720),
                 segment_duration=10,
                 output_dir="video_segments"):
        
        self.fps = fps
        self.resolution = resolution
        self.segment_duration = segment_duration
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Video capture setup
        self.cap = None
        self.is_recording = False
        self.frame_queue = queue.Queue(maxsize=100)
        
        # Queue manager for Redis
        self.queue_manager = VideoQueueManager()
        
        # For Mac FaceTime HD camera
        self.camera_index = Config.CAMERA_INDEX
        
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
        while self.is_recording:
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
    
    def save_video_segment(self, frames_data, segment_id):
        """Save a list of frames as a video segment"""
        if not frames_data:
            return None
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"segment_{timestamp}_{segment_id:04d}.mp4"
            filepath = self.output_dir / filename
            
            # Define codec and create VideoWriter
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(filepath), fourcc, self.fps, self.resolution)
            
            frames_written = 0
            for frame, _ in frames_data:
                # Ensure frame is the correct size
                if frame.shape[:2] != (self.resolution[1], self.resolution[0]):
                    frame = cv2.resize(frame, self.resolution)
                out.write(frame)
                frames_written += 1
            
            out.release()
            
            print(f"Saved segment: {filename} ({frames_written} frames)")
            return str(filepath)
            
        except Exception as e:
            print(f"Error saving video segment: {e}", file=sys.stderr)
            return None
    
    async def process_segments(self):
        """Async function to process video segments and add to queue"""
        segment_id = 0
        
        # Connect to queue manager
        await self.queue_manager.connect()
        
        while self.is_recording:
            try:
                # Collect frames for segment_duration seconds
                frames_for_segment = []
                start_time = time.time()
                
                while (time.time() - start_time) < self.segment_duration and self.is_recording:
                    try:
                        frame, timestamp = self.frame_queue.get(timeout=0.1)
                        frames_for_segment.append((frame, timestamp))
                    except queue.Empty:
                        await asyncio.sleep(0.01)
                        continue
                
                if frames_for_segment:
                    # Save segment to file
                    loop = asyncio.get_event_loop()
                    video_path = await loop.run_in_executor(
                        None, 
                        self.save_video_segment, 
                        frames_for_segment, 
                        segment_id
                    )
                    
                    if video_path:
                        # Add to Redis queue for processing
                        metadata = {
                            "segment_id": segment_id,
                            "fps": self.fps,
                            "resolution": self.resolution,
                            "frame_count": len(frames_for_segment)
                        }
                        
                        await self.queue_manager.add_video_segment(video_path, metadata)
                        print(f"Added segment {segment_id} to processing queue")
                    
                    segment_id += 1
                
            except Exception as e:
                print(f"Error processing segment: {e}", file=sys.stderr)
                await asyncio.sleep(1)
    
    async def start_ingestion(self):
        """Start the video ingestion process"""
        if not self.initialize_camera():
            return False
        
        print("Starting video ingestion with Redis queue...")
        print(f"Segment duration: {self.segment_duration}s")
        print(f"Output directory: {self.output_dir}")
        print("Press Ctrl+C to stop")
        
        self.is_recording = True
        
        # Start frame capture in separate thread
        capture_thread = threading.Thread(target=self.capture_frames)
        capture_thread.daemon = True
        capture_thread.start()
        
        # Start async segment processing
        try:
            await self.process_segments()
        except KeyboardInterrupt:
            print("\nStopping ingestion...")
        finally:
            await self.stop_ingestion()
    
    async def stop_ingestion(self):
        """Stop the video ingestion process"""
        self.is_recording = False
        
        if self.cap:
            self.cap.release()
        
        await self.queue_manager.disconnect()
        print("Ingestion stopped")
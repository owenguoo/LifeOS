import asyncio
import cv2
import os
import time
import tempfile
from datetime import datetime
import threading
import queue
import sys
import signal
import subprocess
import pyaudio
import wave
from config import Config
from video_queue.queue_manager import VideoQueueManager
# from performance_monitor import performance_monitor  # Removed


class VideoIngestionSystem:
    def __init__(
        self,
        fps=None,  # Use config FPS by default
        resolution=None,  # Use config resolution by default
        segment_duration=None,  # Use config segment duration by default
        user_id=None,
        audio_sample_rate=44100,
        audio_channels=1,
        audio_chunk_size=1024,
    ):
        # Use config values if not specified
        self.fps = fps or Config.FPS
        self.resolution = resolution or Config.RESOLUTION
        self.segment_duration = segment_duration or Config.SEGMENT_DURATION
        self.user_id = user_id

        # Audio settings
        self.audio_sample_rate = audio_sample_rate
        self.audio_channels = audio_channels
        self.audio_chunk_size = audio_chunk_size
        self.audio_format = pyaudio.paInt16

        # Video capture setup
        self.cap = None
        self.is_recording = False
        self.frame_queue = queue.Queue(maxsize=100)

        # Audio capture setup
        self.audio = None
        self.audio_stream = None
        self.audio_queue = queue.Queue(maxsize=200)

        # Queue manager for Redis
        self.queue_manager = VideoQueueManager()

        # For Mac FaceTime HD camera
        self.camera_index = int(Config.CAMERA_INDEX) if Config.CAMERA_INDEX else 0

        # Thread management
        self.capture_thread = None
        self.audio_thread = None
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
            self.cap.set(cv2.CAP_PROP_FPS, 30)  # Keep camera at 30fps, we'll subsample

            # Give camera time to initialize
            time.sleep(1)

            # Test frame capture with retries
            for attempt in range(5):
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    actual_fps = self.cap.get(cv2.CAP_PROP_FPS)

                    print(
                        f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps}fps"
                    )
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

    def initialize_audio(self):
        """Initialize audio capture"""
        try:
            self.audio = pyaudio.PyAudio()

            # Get default input device info
            default_device = self.audio.get_default_input_device_info()
            print(f"Using audio input device: {default_device['name']}")

            # Open audio stream
            self.audio_stream = self.audio.open(
                format=self.audio_format,
                channels=self.audio_channels,
                rate=self.audio_sample_rate,
                input=True,
                frames_per_buffer=self.audio_chunk_size,
                stream_callback=self._audio_callback,
            )

            print(
                f"Audio initialized: {self.audio_sample_rate}Hz, {self.audio_channels} channel(s)"
            )
            return True

        except Exception as e:
            print(f"Error initializing audio: {e}", file=sys.stderr)
            if self.audio_stream:
                self.audio_stream.close()
            if self.audio:
                self.audio.terminate()
            return False

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio stream callback"""
        if self.is_recording and not self._shutdown_event.is_set():
            timestamp = time.time()
            try:
                self.audio_queue.put_nowait((in_data, timestamp))
            except queue.Full:
                # Drop oldest audio chunk if queue is full
                try:
                    self.audio_queue.get_nowait()
                    self.audio_queue.put_nowait((in_data, timestamp))
                except queue.Empty:
                    pass
        return (in_data, pyaudio.paContinue)

    def capture_frames(self):
        """Continuously capture frames and put them in queue with proper rate limiting"""
        target_frame_interval = 1.0 / self.fps  # Seconds between frames for target FPS
        last_frame_time = 0

        while self.is_recording and not self._shutdown_event.is_set():
            try:
                ret, frame = self.cap.read()
                current_time = time.time()

                if ret:
                    # Only capture frames at our target FPS rate
                    if current_time - last_frame_time >= target_frame_interval:
                        # Add frame to queue (non-blocking)
                        try:
                            self.frame_queue.put_nowait((frame, current_time))
                            last_frame_time = current_time
                        except queue.Full:
                            # Drop oldest frame if queue is full
                            try:
                                self.frame_queue.get_nowait()
                                self.frame_queue.put_nowait((frame, current_time))
                                last_frame_time = current_time
                            except queue.Empty:
                                pass
                else:
                    print("Failed to capture frame", file=sys.stderr)
                    time.sleep(0.1)

            except Exception as e:
                print(f"Error in frame capture: {e}", file=sys.stderr)
                time.sleep(0.1)

        print("Frame capture thread stopped")

    def create_video_segment(self, frames_data, audio_data, segment_id):
        """Create a video segment file with audio and return metadata"""
        if not frames_data:
            return None

        try:
            # Create temporary files
            temp_video_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
            temp_video_path = temp_video_file.name
            temp_video_file.close()

            temp_audio_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_audio_path = temp_audio_file.name
            temp_audio_file.close()

            final_video_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
            final_video_path = final_video_file.name
            final_video_file.close()

            # Validate and pad frames to ensure proper duration
            expected_frames = self.fps * self.segment_duration
            min_frames_for_4s = int(4 * self.fps)  # TwelveLabs minimum

            print(
                f"Video segment {segment_id}: {len(frames_data)} frames (expected: {expected_frames}, minimum: {min_frames_for_4s})"
            )

            # Pad frames if we don't have enough for the target duration
            if len(frames_data) < expected_frames and frames_data:
                print(f"Padding frames: {len(frames_data)} -> {expected_frames}")
                last_frame, base_timestamp = frames_data[-1]
                original_count = len(frames_data)

                # Pad to reach expected duration
                for i in range(original_count, expected_frames):
                    timestamp = base_timestamp + (i - original_count + 1) / self.fps
                    frames_data.append((last_frame.copy(), timestamp))

                print(
                    f"Padded to {len(frames_data)} frames for {len(frames_data) / self.fps:.1f}s duration"
                )

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(temp_video_path, fourcc, self.fps, self.resolution)

            if not writer.isOpened():
                raise Exception(f"Failed to open video writer for {temp_video_path}")

            frames_written = 0
            for frame, timestamp in frames_data:
                if frame is not None and frame.size > 0:
                    writer.write(frame)
                    frames_written += 1
                else:
                    print(f"Warning: Skipping invalid frame at index {frames_written}")

            writer.release()
            print(f"Video writer: wrote {frames_written} frames to {temp_video_path}")

            # Verify the created video file
            if os.path.exists(temp_video_path):
                file_size = os.path.getsize(temp_video_path)
                print(f"Created video file: {file_size} bytes")
                if file_size < 1000:  # Less than 1KB is suspicious
                    print(f"Warning: Video file is very small ({file_size} bytes)")
            else:
                raise Exception(f"Video file was not created: {temp_video_path}")

            # Create audio file if we have audio data
            if audio_data:
                with wave.open(temp_audio_path, "wb") as wav_file:
                    wav_file.setnchannels(self.audio_channels)
                    wav_file.setsampwidth(self.audio.get_sample_size(self.audio_format))
                    wav_file.setframerate(self.audio_sample_rate)

                    # Combine all audio chunks
                    audio_bytes = b"".join([chunk for chunk, timestamp in audio_data])
                    wav_file.writeframes(audio_bytes)

                # Use FFmpeg to combine video and audio with optimized settings
                try:
                    cmd = [
                        "ffmpeg",
                        "-y",  # -y to overwrite output file
                        "-i",
                        temp_video_path,  # video input
                        "-i",
                        temp_audio_path,  # audio input
                        "-c:v",
                        "libx264",  # video codec
                        "-preset",
                        "ultrafast",  # Fastest encoding preset
                        "-crf",
                        "28",  # Slightly lower quality for speed
                        "-c:a",
                        "aac",  # audio codec
                        "-shortest",  # finish when shortest stream ends
                        "-threads",
                        "0",  # Use all available CPU cores
                        final_video_path,
                    ]

                    result = subprocess.run(
                        cmd, capture_output=True, text=True, timeout=15
                    )  # Reduced timeout

                    if result.returncode == 0:
                        # Clean up temporary files
                        os.unlink(temp_video_path)
                        os.unlink(temp_audio_path)
                        final_path = final_video_path
                    else:
                        print(f"FFmpeg failed: {result.stderr}")
                        # Fall back to video-only
                        os.unlink(temp_audio_path)
                        os.unlink(final_video_path)
                        final_path = temp_video_path

                except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                    print(f"FFmpeg error: {e}, falling back to video-only")
                    # Clean up and fall back to video-only
                    os.unlink(temp_audio_path)
                    os.unlink(final_video_path)
                    final_path = temp_video_path
            else:
                # No audio data, use video-only file
                os.unlink(temp_audio_path)
                os.unlink(final_video_path)
                final_path = temp_video_path

            # Calculate actual video duration
            actual_duration = len(frames_data) / self.fps

            # Return metadata with file path
            segment_info = {
                "segment_id": segment_id,
                "video_path": final_path,
                "fps": self.fps,
                "resolution": self.resolution,
                "frame_count": len(frames_data),
                "duration_seconds": actual_duration,
                "audio_chunks": len(audio_data) if audio_data else 0,
                "has_audio": bool(audio_data),
                "timestamp": datetime.now().isoformat(),
                "user_id": self.user_id,
            }

            audio_info = (
                f" with {len(audio_data)} audio chunks"
                if audio_data
                else " (video only)"
            )
            print(
                f"Created segment {segment_id}: {len(frames_data)} frames ({actual_duration:.1f}s duration){audio_info} at {final_path}"
            )
            return segment_info

        except Exception as e:
            print(f"Error creating video segment: {e}", file=sys.stderr)
            # Clean up any temporary files
            for path in [temp_video_path, temp_audio_path, final_video_path]:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except Exception:
                    pass
            return None

    async def process_segments(self):
        """Async function to process video segments with audio and add to queue"""
        segment_id = 0

        # Connect to queue manager
        await self.queue_manager.connect()

        while self.is_recording and not self._shutdown_event.is_set():
            try:
                # Collect frames and audio for segment_duration seconds
                frames_for_segment = []
                audio_for_segment = []
                start_time = time.time()

                # Ensure precise timing for 10-second segments
                target_frames = self.fps * self.segment_duration
                end_time = start_time + self.segment_duration
                timing_precision = 0.01  # 10ms precision for segment boundaries

                print(
                    f"Collecting segment {segment_id}: targeting {target_frames} frames for {self.segment_duration}s"
                )

                # Strict timing control - exit collection exactly at end_time
                while (
                    time.time() < (end_time - timing_precision)
                    and self.is_recording
                    and not self._shutdown_event.is_set()
                ):
                    frames_collected = 0
                    audio_collected = 0

                    # Batch collect frames (up to 10 at once)
                    for _ in range(10):
                        try:
                            frame, timestamp = self.frame_queue.get_nowait()
                            frames_for_segment.append((frame, timestamp))
                            frames_collected += 1
                        except queue.Empty:
                            break

                    # Batch collect audio (up to 5 at once)
                    for _ in range(5):
                        try:
                            audio_chunk, timestamp = self.audio_queue.get_nowait()
                            audio_for_segment.append((audio_chunk, timestamp))
                            audio_collected += 1
                        except queue.Empty:
                            break

                    # Dynamic sleep based on collection efficiency
                    if frames_collected == 0 and audio_collected == 0:
                        await asyncio.sleep(
                            0.01
                        )  # Longer sleep when idle to reduce CPU usage
                    else:
                        await asyncio.sleep(
                            0.002
                        )  # Minimal sleep when actively collecting

                print(
                    f"Collected {len(frames_for_segment)} frames and {len(audio_for_segment)} audio chunks"
                )

                if frames_for_segment:
                    # Create segment data with both video and audio (with priority ThreadPoolExecutor)
                    loop = asyncio.get_event_loop()
                    segment_info = await loop.run_in_executor(
                        None,
                        self.create_video_segment,
                        frames_for_segment,
                        audio_for_segment,
                        segment_id,
                    )

                    if segment_info:
                        # Add video file to Redis queue for processing
                        video_path = segment_info["video_path"]
                        metadata = {
                            k: v for k, v in segment_info.items() if k != "video_path"
                        }
                        await self.queue_manager.add_video_segment(video_path, metadata)

                        audio_status = (
                            "with audio"
                            if segment_info.get("has_audio")
                            else "video only"
                        )
                        print(
                            f"Added segment {segment_id} ({audio_status}) to processing queue"
                        )

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
        """Start the video and audio ingestion process"""
        if not self.initialize_camera():
            return False

        if not self.initialize_audio():
            print("Warning: Audio initialization failed, continuing with video only")

        print("Starting video+audio ingestion with Redis queue...")
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

        # Start audio stream if available
        if self.audio_stream:
            self.audio_stream.start_stream()

        # Start async segment processing
        try:
            await self.process_segments()
        except KeyboardInterrupt:
            print("\nReceived KeyboardInterrupt, stopping ingestion...")
        finally:
            await self.stop_ingestion()

    async def stop_ingestion(self):
        """Stop the video and audio ingestion process"""
        print("Stopping video+audio ingestion...")
        self.is_recording = False
        self._shutdown_event.set()

        # Stop audio stream
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
            except Exception as e:
                print(f"Error stopping audio stream: {e}")

        if self.audio:
            try:
                self.audio.terminate()
                self.audio = None
            except Exception as e:
                print(f"Error terminating audio: {e}")

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

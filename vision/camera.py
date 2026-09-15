"""
Camera management module for the AI Hookah Bar.

Wraps OpenCV VideoCapture with graceful error handling,
horizontal mirroring, frame resizing, and FPS tracking.
"""

import cv2
import time
import numpy as np


class CameraManager:
    """Manages webcam capture with error handling and performance tracking."""

    def __init__(self, camera_index=0, width=640, height=480):
        self.camera_index = camera_index
        self.target_width = width
        self.target_height = height
        self.cap = None
        self.is_running = False
        self._fps = 0.0
        self._frame_count = 0
        self._fps_start_time = time.time()
        self._last_frame = None

    def start(self):
        """Start the camera capture. Returns True on success, False on failure."""
        try:
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                # Try without DSHOW
                self.cap = cv2.VideoCapture(self.camera_index)

            if not self.cap.isOpened():
                self.cap = None
                self.is_running = False
                return False

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.is_running = True
            self._fps_start_time = time.time()
            self._frame_count = 0
            return True

        except Exception:
            self.cap = None
            self.is_running = False
            return False

    def stop(self):
        """Stop the camera and release resources."""
        self.is_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self._last_frame = None

    def read_frame(self, mirror=True):
        """
        Read a single frame from the camera.

        Args:
            mirror: If True, flip the frame horizontally.

        Returns:
            BGR numpy array or None if read failed.
        """
        if self.cap is None or not self.is_running:
            return None

        try:
            ret, frame = self.cap.read()
            if not ret or frame is None:
                return self._last_frame
            
            # Resize if needed
            h, w = frame.shape[:2]
            if w != self.target_width or h != self.target_height:
                frame = cv2.resize(frame, (self.target_width, self.target_height))

            # Mirror for natural interaction
            if mirror:
                frame = cv2.flip(frame, 1)

            # Update FPS counter
            self._frame_count += 1
            elapsed = time.time() - self._fps_start_time
            if elapsed >= 1.0:
                self._fps = self._frame_count / elapsed
                self._frame_count = 0
                self._fps_start_time = time.time()

            self._last_frame = frame
            return frame

        except Exception:
            return self._last_frame

    @property
    def fps(self):
        """Current frames per second."""
        return self._fps

    @property
    def is_available(self):
        """Check if camera is available and running."""
        return self.cap is not None and self.cap.isOpened() and self.is_running

    def get_error_message(self):
        """Return a user-friendly error message."""
        return (
            "📷 Camera unavailable.\n\n"
            "Please check:\n"
            "- Webcam permissions are granted\n"
            "- Camera is properly connected\n"
            "- No other application is using the camera\n"
            "- Try a different camera index in settings"
        )

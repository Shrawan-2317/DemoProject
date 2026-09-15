"""
High-performance MJPEG video stream server for the AI Hookah Bar.

Streams processed camera frames with zero blinking, zero page reloads,
and buttery-smooth 30 FPS directly to the browser via multipart/x-mixed-replace.
"""

import threading
import time
import socket
import cv2
import numpy as np
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler


class _MJPEGHandler(BaseHTTPRequestHandler):
    """HTTP request handler streaming MJPEG frames."""

    def do_GET(self):
        if self.path == "/video_feed":
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            server_ref = self.server.stream_server
            try:
                while server_ref.is_running:
                    frame_bytes = server_ref.get_latest_jpeg()
                    if frame_bytes:
                        self.wfile.write(
                            b"--frame\r\n"
                            b"Content-Type: image/jpeg\r\n\r\n"
                            + frame_bytes
                            + b"\r\n"
                        )
                    time.sleep(0.033)  # ~30 FPS
            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                pass
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        # Silence console access logging to keep terminal clean
        pass


class VideoStreamServer:
    """
    Background threaded MJPEG streaming server.
    Captures frames, processes smoke and gestures, and serves smooth video.
    """

    def __init__(self, host="127.0.0.1", default_port=8502):
        self.host = host
        self.port = default_port
        self.server = None
        self.server_thread = None
        self.worker_thread = None
        self.is_running = False
        self._latest_jpeg = None
        self._lock = threading.Lock()
        self.frame_processor = None
        self.camera_manager = None

    def _find_open_port(self):
        """Find an open port starting from self.port."""
        port = self.port
        for p in range(port, port + 20):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex((self.host, p)) != 0:
                    return p
        return port

    def start(self, camera_manager, frame_processor):
        """Start the MJPEG streaming server and worker thread."""
        if self.is_running:
            return self.get_stream_url()

        self.camera_manager = camera_manager
        self.frame_processor = frame_processor
        self.port = self._find_open_port()

        try:
            self.server = ThreadingHTTPServer((self.host, self.port), _MJPEGHandler)
            self.server.stream_server = self
            self.is_running = True

            # Start HTTP server thread
            self.server_thread = threading.Thread(
                target=self.server.serve_forever,
                daemon=True,
                name="MJPEG-Server"
            )
            self.server_thread.start()

            # Start Frame capture & processing thread
            self.worker_thread = threading.Thread(
                target=self._capture_and_process_loop,
                daemon=True,
                name="MJPEG-Worker"
            )
            self.worker_thread.start()

            return self.get_stream_url()
        except Exception as e:
            self.is_running = False
            return None

    def _capture_and_process_loop(self):
        """Continuous background loop processing frames at steady 30 FPS."""
        while self.is_running:
            start_t = time.time()
            if self.camera_manager and self.camera_manager.is_running:
                frame = self.camera_manager.read_frame(mirror=True)
                if frame is not None and self.frame_processor:
                    try:
                        processed = self.frame_processor(frame)
                    except Exception:
                        processed = frame

                    # Encode to high-quality JPEG
                    ret, buf = cv2.imencode(".jpg", processed, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    if ret:
                        with self._lock:
                            self._latest_jpeg = buf.tobytes()

            elapsed = time.time() - start_t
            sleep_time = max(0.005, 0.033 - elapsed)
            time.sleep(sleep_time)

    def get_latest_jpeg(self):
        """Retrieve the latest processed JPEG bytes."""
        with self._lock:
            return self._latest_jpeg

    def get_stream_url(self):
        """Return the URL for the MJPEG video stream."""
        return f"http://{self.host}:{self.port}/video_feed"

    def stop(self):
        """Stop the streaming server and cleanup threads."""
        self.is_running = False
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
            except Exception:
                pass
            self.server = None
        self._latest_jpeg = None

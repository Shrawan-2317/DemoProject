"""
Face tracking module using MediaPipe Face Mesh.

Provides face position, mouth state, and head direction
for interactive smoke direction and burst effects.
"""

try:
    import mediapipe.python.solutions.face_mesh as mp_face_mesh
except Exception:
    try:
        from mediapipe.python.solutions import face_mesh as mp_face_mesh
    except Exception:
        try:
            import mediapipe as mp
            mp_solutions = getattr(mp, "solutions", None)
            if mp_solutions:
                mp_face_mesh = mp_solutions.face_mesh
            else:
                mp_face_mesh = None
        except Exception:
            mp_face_mesh = None

import numpy as np


class FaceTracker:
    """MediaPipe Face Mesh wrapper for face interaction."""

    # Key landmark indices for Face Mesh
    NOSE_TIP = 1
    CHIN = 152
    LEFT_EYE_OUTER = 263
    RIGHT_EYE_OUTER = 33
    MOUTH_TOP = 13
    MOUTH_BOTTOM = 14
    MOUTH_LEFT = 308
    MOUTH_RIGHT = 78
    FOREHEAD = 10

    def __init__(self, max_faces=1, detection_confidence=0.5, tracking_confidence=0.5):
        self.mp_face = mp_face_mesh
        self.face_mesh = None
        if self.mp_face is not None:
            try:
                self.face_mesh = self.mp_face.FaceMesh(
                    static_image_mode=False,
                    max_num_faces=max_faces,
                    refine_landmarks=False,
                    min_detection_confidence=detection_confidence,
                    min_tracking_confidence=tracking_confidence,
                )
            except Exception:
                self.face_mesh = None

        self.face_detected = False
        self.face_center = (0, 0)
        self.mouth_open_ratio = 0.0
        self.head_direction = (0.0, 0.0)

    def detect(self, frame_rgb):
        """
        Detect face landmarks in an RGB frame.

        Returns:
            dict with face data or None if no face detected.
        """
        if self.face_mesh is None:
            return None
        try:
            results = self.face_mesh.process(frame_rgb)

            if not results.multi_face_landmarks:
                self.face_detected = False
                return None

            face = results.multi_face_landmarks[0]
            h, w = frame_rgb.shape[:2]

            # Get key positions
            nose = face.landmark[self.NOSE_TIP]
            chin = face.landmark[self.CHIN]
            forehead = face.landmark[self.FOREHEAD]
            mouth_top = face.landmark[self.MOUTH_TOP]
            mouth_bottom = face.landmark[self.MOUTH_BOTTOM]
            mouth_left = face.landmark[self.MOUTH_LEFT]
            mouth_right = face.landmark[self.MOUTH_RIGHT]

            # Face center (nose position)
            self.face_center = (int(nose.x * w), int(nose.y * h))

            # Precise mouth center in pixel coordinates
            mx = int((mouth_left.x + mouth_right.x) * 0.5 * w)
            my = int((mouth_top.y + mouth_bottom.y) * 0.5 * h)

            # Mouth open ratio (height / width)
            mouth_height = abs(mouth_bottom.y - mouth_top.y)
            mouth_width = abs(mouth_right.x - mouth_left.x)
            self.mouth_open_ratio = (mouth_height / (mouth_width + 1e-6))

            # Head direction (tilt)
            dx = nose.x - 0.5  # deviation from center
            dy = nose.y - 0.5
            self.head_direction = (dx * 2.0, dy * 2.0)

            self.face_detected = True

            return {
                "face_center": self.face_center,
                "mouth_position": (mx, my),
                "mouth_open": self.mouth_open_ratio > 0.18,
                "mouth_ratio": self.mouth_open_ratio,
                "mouth_height_px": int(mouth_height * h),
                "head_direction": self.head_direction,
                "nose_position": (int(nose.x * w), int(nose.y * h)),
                "chin_position": (int(chin.x * w), int(chin.y * h)),
            }

        except Exception:
            self.face_detected = False
            return None

    def close(self):
        """Release MediaPipe resources."""
        if self.face_mesh is not None:
            try:
                self.face_mesh.close()
            except Exception:
                pass

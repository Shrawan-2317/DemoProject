"""
Hand tracking module using MediaPipe Hands.

Provides hand landmark detection, fingertip positions,
palm center calculation, and hand state analysis.
"""

try:
    import mediapipe.python.solutions.hands as mp_hands
    import mediapipe.python.solutions.drawing_utils as mp_draw
    import mediapipe.python.solutions.drawing_styles as mp_styles
except Exception:
    try:
        from mediapipe.python.solutions import hands as mp_hands
        from mediapipe.python.solutions import drawing_utils as mp_draw
        from mediapipe.python.solutions import drawing_styles as mp_styles
    except Exception:
        try:
            import mediapipe as mp
            mp_solutions = getattr(mp, "solutions", None)
            if mp_solutions:
                mp_hands = mp_solutions.hands
                mp_draw = mp_solutions.drawing_utils
                mp_styles = mp_solutions.drawing_styles
            else:
                mp_hands = None
                mp_draw = None
                mp_styles = None
        except Exception:
            mp_hands = None
            mp_draw = None
            mp_styles = None

import numpy as np


class HandTracker:
    """MediaPipe Hands wrapper for hand landmark detection."""

    # Landmark indices
    WRIST = 0
    THUMB_TIP = 4
    INDEX_TIP = 8
    MIDDLE_TIP = 12
    RING_TIP = 16
    PINKY_TIP = 20
    THUMB_MCP = 2
    INDEX_MCP = 5
    MIDDLE_MCP = 9
    RING_MCP = 13
    PINKY_MCP = 17
    INDEX_PIP = 6
    MIDDLE_PIP = 10
    RING_PIP = 14
    PINKY_PIP = 18

    def __init__(self, max_hands=2, detection_confidence=0.6, tracking_confidence=0.5):
        self.mp_hands = mp_hands
        self.mp_draw = mp_draw
        self.mp_styles = mp_styles
        self.hands = None

        if self.mp_hands is not None:
            try:
                self.hands = self.mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=max_hands,
                    min_detection_confidence=detection_confidence,
                    min_tracking_confidence=tracking_confidence,
                )
            except Exception:
                self.hands = None

    def detect(self, frame_rgb):
        """
        Detect hand landmarks in an RGB frame.
        """
        if self.hands is None:
            return None

        Args:
            frame_rgb: RGB numpy array.

        Returns:
            MediaPipe results object (may have .multi_hand_landmarks = None).
        """
        try:
            results = self.hands.process(frame_rgb)
            return results
        except Exception:
            return None

    def get_landmark_positions(self, hand_landmarks, frame_width, frame_height):
        """
        Convert normalized landmarks to pixel coordinates.

        Returns:
            List of (x, y) tuples in pixel space, indexed by landmark ID.
        """
        positions = []
        for lm in hand_landmarks.landmark:
            x = int(lm.x * frame_width)
            y = int(lm.y * frame_height)
            positions.append((x, y))
        return positions

    def get_fingertip_positions(self, positions):
        """
        Get positions of all 5 fingertips.

        Returns:
            Dict with keys: thumb, index, middle, ring, pinky
        """
        return {
            "thumb": positions[self.THUMB_TIP],
            "index": positions[self.INDEX_TIP],
            "middle": positions[self.MIDDLE_TIP],
            "ring": positions[self.RING_TIP],
            "pinky": positions[self.PINKY_TIP],
        }

    def get_palm_center(self, positions):
        """Calculate the center of the palm from MCP joints."""
        mcp_indices = [self.INDEX_MCP, self.MIDDLE_MCP, self.RING_MCP, self.PINKY_MCP]
        xs = [positions[i][0] for i in mcp_indices]
        ys = [positions[i][1] for i in mcp_indices]
        return (int(np.mean(xs)), int(np.mean(ys)))

    def get_wrist_position(self, positions):
        """Get wrist position."""
        return positions[self.WRIST]

    def is_finger_extended(self, positions, finger_tip_idx, finger_pip_idx, finger_mcp_idx):
        """Check if a finger is extended (tip is farther from wrist than PIP)."""
        wrist = positions[self.WRIST]
        tip = positions[finger_tip_idx]
        pip = positions[finger_pip_idx]

        tip_dist = np.sqrt((tip[0] - wrist[0])**2 + (tip[1] - wrist[1])**2)
        pip_dist = np.sqrt((pip[0] - wrist[0])**2 + (pip[1] - wrist[1])**2)

        return tip_dist > pip_dist

    def count_extended_fingers(self, positions):
        """
        Count number of extended fingers.

        Returns:
            int: number of extended fingers (0-5)
        """
        count = 0

        # Thumb: compare x distance (since thumb extends sideways)
        if abs(positions[self.THUMB_TIP][0] - positions[self.WRIST][0]) > \
           abs(positions[self.THUMB_MCP][0] - positions[self.WRIST][0]):
            count += 1

        # Other fingers
        finger_pairs = [
            (self.INDEX_TIP, self.INDEX_PIP, self.INDEX_MCP),
            (self.MIDDLE_TIP, self.MIDDLE_PIP, self.MIDDLE_MCP),
            (self.RING_TIP, self.RING_PIP, self.RING_MCP),
            (self.PINKY_TIP, self.PINKY_PIP, self.PINKY_MCP),
        ]
        for tip, pip, mcp in finger_pairs:
            if self.is_finger_extended(positions, tip, pip, mcp):
                count += 1

        return count

    def get_thumb_index_distance(self, positions):
        """Get Euclidean distance between thumb tip and index tip."""
        t = positions[self.THUMB_TIP]
        i = positions[self.INDEX_TIP]
        return np.sqrt((t[0] - i[0])**2 + (t[1] - i[1])**2)

    def draw_landmarks(self, frame, results):
        """Draw hand landmarks on the frame."""
        if results and results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_styles.get_default_hand_landmarks_style(),
                    self.mp_styles.get_default_hand_connections_style(),
                )
        return frame

    def close(self):
        """Release MediaPipe resources."""
        self.hands.close()

"""
Gesture recognition module for the AI Hookah Bar.

Implements history-based gesture detection using hand landmark positions.
Supports 7 gestures: wave, open_palm, pinch, circle, move_up, move_down, two_hands.
"""

import numpy as np
import time
from collections import deque


class GestureDetector:
    """
    Detects hand gestures from landmark positions using temporal analysis.

    Maintains a ring buffer of recent hand positions to detect
    motion-based gestures (wave, circle, directional movement).
    """

    def __init__(self, history_length=20):
        self.history_length = history_length
        self.position_history = deque(maxlen=history_length)
        self.time_history = deque(maxlen=history_length)
        self.current_gesture = "none"
        self.gesture_confidence = 0.0
        self.velocity = (0.0, 0.0)
        self.direction = (0.0, 0.0)
        self._last_gesture_time = time.time()
        self._gesture_cooldown = 0.3  # seconds between gesture changes
        self._cumulative_angle = 0.0

    def update(self, hand_positions, hand_tracker, frame_width, frame_height, num_hands=1):
        """
        Update gesture detection with new hand data.

        Args:
            hand_positions: List of (x, y) tuples from hand landmarks.
            hand_tracker: HandTracker instance for finger analysis.
            frame_width: Frame width in pixels.
            frame_height: Frame height in pixels.
            num_hands: Number of hands currently detected.

        Returns:
            dict with keys: gesture, confidence, velocity, direction
        """
        if hand_positions is None or len(hand_positions) == 0:
            self.position_history.clear()
            self.time_history.clear()
            self._cumulative_angle = 0.0
            self.current_gesture = "none"
            self.gesture_confidence = 0.0
            return self._make_result()

        # Use palm center for motion tracking
        palm = hand_tracker.get_palm_center(hand_positions)
        now = time.time()

        self.position_history.append(palm)
        self.time_history.append(now)

        # Calculate velocity
        self._update_velocity()

        # Detect gesture (priority order)
        gesture, confidence = self._detect_gesture(
            hand_positions, hand_tracker, frame_width, frame_height, num_hands
        )

        # Apply cooldown to prevent flickering
        if gesture != self.current_gesture:
            if now - self._last_gesture_time > self._gesture_cooldown:
                self.current_gesture = gesture
                self.gesture_confidence = confidence
                self._last_gesture_time = now
        else:
            self.gesture_confidence = confidence

        return self._make_result()

    def _detect_gesture(self, positions, tracker, fw, fh, num_hands):
        """Run all gesture detectors and return the best match."""

        # Two hands check (highest priority)
        if num_hands >= 2:
            return "two_hands", 0.95

        # Pinch check (thumb and index finger close together)
        pinch_dist = tracker.get_thumb_index_distance(positions)
        pinch_threshold = fw * 0.08  # 8% of frame width (~50px)
        if pinch_dist < pinch_threshold:
            return "pinch", min(1.0, 1.0 - (pinch_dist / pinch_threshold))

        # Circular motion check (for smoke tornado)
        circle_score = self._detect_circular_motion()
        if circle_score > 0.45:
            return "circle", circle_score

        # Wave check (horizontal oscillation for smoke swirl)
        wave_score = self._detect_wave()
        if wave_score > 0.45:
            return "wave", wave_score

        # Directional movement (move up/down)
        if len(self.position_history) >= 4:
            recent = list(self.position_history)[-5:]
            dy = recent[-1][1] - recent[0][1]
            dx = recent[-1][0] - recent[0][0]

            # Move down (waterfall)
            if dy > fh * 0.05 and abs(dy) > abs(dx) * 0.8:
                return "move_down", min(1.0, abs(dy) / (fh * 0.12))

            # Move up (dragon / plume)
            if dy < -fh * 0.05 and abs(dy) > abs(dx) * 0.8:
                return "move_up", min(1.0, abs(dy) / (fh * 0.12))

        # Open palm check
        extended = tracker.count_extended_fingers(positions)
        if extended >= 4:
            return "open_palm", min(1.0, extended / 5.0)

        return "none", 0.0

    def _detect_wave(self):
        """
        Detect horizontal oscillation (wave gesture).

        Looks for direction changes in x-axis movement.
        """
        if len(self.position_history) < 8:
            return 0.0

        recent = list(self.position_history)[-10:]
        x_positions = [p[0] for p in recent]

        # Count direction changes
        direction_changes = 0
        for i in range(2, len(x_positions)):
            dx_prev = x_positions[i-1] - x_positions[i-2]
            dx_curr = x_positions[i] - x_positions[i-1]
            if dx_prev * dx_curr < 0 and abs(dx_prev) > 3 and abs(dx_curr) > 3:
                direction_changes += 1

        # Also check amplitude
        x_range = max(x_positions) - min(x_positions)

        if direction_changes >= 2 and x_range > 30:
            return min(1.0, direction_changes / 4.0)

        return 0.0

    def _detect_circular_motion(self):
        """
        Detect circular hand motion by tracking cumulative angle change.
        """
        if len(self.position_history) < 10:
            return 0.0

        recent = list(self.position_history)[-12:]

        # Calculate center of the trajectory
        xs = [p[0] for p in recent]
        ys = [p[1] for p in recent]
        cx, cy = np.mean(xs), np.mean(ys)

        # Accumulate angles
        total_angle = 0.0
        for i in range(1, len(recent)):
            dx1 = recent[i-1][0] - cx
            dy1 = recent[i-1][1] - cy
            dx2 = recent[i][0] - cx
            dy2 = recent[i][1] - cy

            angle1 = np.arctan2(dy1, dx1)
            angle2 = np.arctan2(dy2, dx2)

            diff = angle2 - angle1
            # Normalize to [-pi, pi]
            while diff > np.pi:
                diff -= 2 * np.pi
            while diff < -np.pi:
                diff += 2 * np.pi

            total_angle += diff

        # A full circle is 2*pi
        circle_fraction = abs(total_angle) / (2 * np.pi)

        # Also check that points spread around the center
        distances = [np.sqrt((p[0]-cx)**2 + (p[1]-cy)**2) for p in recent]
        avg_dist = np.mean(distances)
        dist_std = np.std(distances)

        # Good circle: consistent distance from center and significant angle
        if circle_fraction > 0.4 and avg_dist > 15 and (dist_std / (avg_dist + 1e-6)) < 0.6:
            return min(1.0, circle_fraction)

        return 0.0

    def _update_velocity(self):
        """Calculate current hand velocity in pixels/second."""
        if len(self.position_history) < 2:
            self.velocity = (0.0, 0.0)
            self.direction = (0.0, 0.0)
            return

        p1 = self.position_history[-2]
        p2 = self.position_history[-1]
        t1 = self.time_history[-2]
        t2 = self.time_history[-1]

        dt = t2 - t1
        if dt < 1e-6:
            return

        vx = (p2[0] - p1[0]) / dt
        vy = (p2[1] - p1[1]) / dt
        self.velocity = (vx, vy)

        speed = np.sqrt(vx**2 + vy**2)
        if speed > 1e-6:
            self.direction = (vx / speed, vy / speed)
        else:
            self.direction = (0.0, 0.0)

    def _make_result(self):
        """Construct the gesture result dict."""
        return {
            "gesture": self.current_gesture,
            "confidence": self.gesture_confidence,
            "velocity": self.velocity,
            "direction": self.direction,
            "speed": np.sqrt(self.velocity[0]**2 + self.velocity[1]**2),
        }

    def reset(self):
        """Reset all gesture state."""
        self.position_history.clear()
        self.time_history.clear()
        self.current_gesture = "none"
        self.gesture_confidence = 0.0
        self.velocity = (0.0, 0.0)
        self.direction = (0.0, 0.0)
        self._cumulative_angle = 0.0

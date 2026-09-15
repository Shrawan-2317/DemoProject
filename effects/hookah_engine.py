"""
Unified, thread-safe Hookah Bar Engine.

Manages all tracking, physics, particle simulation, and overlay rendering
independently of Streamlit session state so it can run reliably inside
high-performance streaming threads without dropping frames or crashing.
"""

import cv2
import numpy as np
import time
import math
import random

from config.flavors import FLAVORS, SMOKE_STUNTS, STUNT_KEYS
from vision.hand_tracking import HandTracker
from vision.gesture_detection import GestureDetector
from vision.face_tracking import FaceTracker
from effects.smoke_engine import SmokeEngine
from effects.overlays import draw_virtual_hookah, draw_performance_hud, draw_safety_banner
from ai.ai_engine import AIEffectEngine
from ai.ai_coach import SmokeCoach


class HookahBarEngine:
    """Thread-safe core engine running vision, particle physics, and overlays."""

    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.hand_tracker = HandTracker(max_hands=2)
        self.gesture_detector = GestureDetector()
        self.face_tracker = FaceTracker()
        self.smoke_engine = SmokeEngine(width=640, height=480, max_particles=600)
        self.ai_engine = AIEffectEngine()
        self.ai_coach = SmokeCoach()

        self.frame_count = 0
        self.fps = 0.0
        self._fps_time = time.time()
        self._fps_count = 0

        self.current_gesture = "none"
        self.gesture_confidence = 0.0
        self.current_effect = "rise"
        self.latest_decision = {}
        self.coach_message = "👋 Hold the hookah pipe, take a puff, and open your mouth to blow smoke stunts!"

        # Inhale & Exhale state machine
        self.is_inhaling = False
        self.smoke_charge = 1.0  # Initial puff loaded
        self.wand_tip_pos = None
        self.mouth_open = False
        self.mouth_pos = None
        self.locked_stunt = "rise"
        self.locked_stunt_timer = 0.0

        # Default settings
        self.settings = {
            "selected_flavor": "Blueberry",
            "is_ai_mode": True,
            "selected_stunt": "Normal Smoke",
            "intensity": 0.85,
            "density": 0.85,
            "speed": 1.4,
            "show_hookah": True,
            "ai_gesture": True,
            "show_landmarks": False,
            "performance_mode": False,
            "show_face": False,
        }

    def update_setting(self, key, value):
        """Update a runtime setting thread-safely."""
        self.settings[key] = value

    def set_flavor(self, flavor_name):
        """Change selected flavor."""
        if flavor_name in FLAVORS:
            self.settings["selected_flavor"] = flavor_name

    def set_stunt(self, stunt_name):
        """Switch to manual stunt."""
        if stunt_name in STUNT_KEYS:
            self.settings["selected_stunt"] = stunt_name
            self.settings["is_ai_mode"] = False
            self.current_effect = STUNT_KEYS[stunt_name]
            self.locked_stunt = STUNT_KEYS[stunt_name]
            self.locked_stunt_timer = time.time() + 999.0

    def set_mode(self, is_ai_mode):
        """Switch between AI Auto and Manual mode."""
        self.settings["is_ai_mode"] = is_ai_mode

    def process_frame(self, frame):
        """
        Process a single camera frame through the full AR pipeline:
        Face Tracking -> Hand Tracking -> Pipe Inhale Proximity -> Mouth Open Exhale -> Gesture Stunt -> Overlays.
        """
        self.frame_count += 1
        h, w = frame.shape[:2]

        flavor_name = self.settings.get("selected_flavor", "Blueberry")
        if flavor_name not in FLAVORS:
            flavor_name = "Blueberry"
        flavor = FLAVORS[flavor_name]

        # Calculate FPS
        self._fps_count += 1
        now = time.time()
        elapsed = now - self._fps_time
        if elapsed >= 1.0:
            self.fps = self._fps_count / elapsed
            self._fps_count = 0
            self._fps_time = now

        # Hookah bowl coordinates (top of shisha pot at bottom right)
        hookah_bowl_x = int(w * 0.82)
        hookah_bowl_y = h - 130

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # ── 1. Face & Mouth Tracking ──
        face_data = self.face_tracker.detect(rgb_frame)
        mouth_open = False
        mouth_pos = None

        if face_data:
            mouth_pos = face_data.get("mouth_position", (w // 2, h // 2))
            mouth_open = face_data.get("mouth_open", False)
            self.mouth_open = mouth_open
            self.mouth_pos = mouth_pos
        else:
            self.mouth_open = False
            self.mouth_pos = None

        # ── 2. Hand Tracking & Pipe Grip ──
        gesture_result = {"gesture": "none", "confidence": 0.0, "velocity": (0, 0), "direction": (0, 0), "speed": 0}
        hand_detected = False
        hand_grip_pos = None

        if self.settings.get("ai_gesture", True):
            hand_results = self.hand_tracker.detect(rgb_frame)
            if hand_results and hand_results.multi_hand_landmarks:
                hand_detected = True
                num_hands = len(hand_results.multi_hand_landmarks)
                first_hand = hand_results.multi_hand_landmarks[0]
                hand_positions = self.hand_tracker.get_landmark_positions(first_hand, w, h)

                if len(hand_positions) > 8:
                    hand_grip_pos = hand_positions[5]  # Index finger knuckle
                else:
                    hand_grip_pos = self.hand_tracker.get_palm_center(hand_positions)

                gesture_result = self.gesture_detector.update(
                    hand_positions, self.hand_tracker, w, h, num_hands
                )

                if self.settings.get("show_landmarks", False):
                    frame = self.hand_tracker.draw_landmarks(frame, hand_results)

        # ── 3. Hookah Inhale Proximity Check ──
        # Bringing the hand/wand close to the mouth charges the shisha puff!
        if hand_grip_pos and mouth_pos:
            dist_to_mouth = math.hypot(hand_grip_pos[0] - mouth_pos[0], hand_grip_pos[1] - mouth_pos[1])
            if dist_to_mouth < 95:
                self.is_inhaling = True
                self.smoke_charge = min(1.0, self.smoke_charge + 0.10)  # Quickly charges up!
            else:
                self.is_inhaling = False
        else:
            self.is_inhaling = False

        # ── 4. Gesture Detection & Stunt Latching ──
        GESTURE_MAP = {
            "pinch": "ring",
            "circle": "tornado",
            "open_palm": "burst",
            "move_down": "waterfall",
            "wave": "swirl",
            "move_up": "dragon",
            "two_hands": "double",
        }

        detected_gesture = gesture_result["gesture"]
        if detected_gesture in GESTURE_MAP:
            # Lock this stunt for 2.5 seconds so it doesn't get interrupted!
            self.locked_stunt = GESTURE_MAP[detected_gesture]
            self.locked_stunt_timer = now + 2.5

        if self.settings.get("is_ai_mode", True):
            if now < self.locked_stunt_timer:
                effect_key = self.locked_stunt
                effect_intensity = self.settings["intensity"]
            else:
                effect_key = "rise"
                effect_intensity = self.settings["intensity"]
        else:
            stunt_name = self.settings.get("selected_stunt", "Normal Smoke")
            effect_key = STUNT_KEYS.get(stunt_name, "rise")
            effect_intensity = self.settings["intensity"]

        self.current_effect = effect_key
        self.current_gesture = detected_gesture
        self.gesture_confidence = gesture_result["confidence"]

        # ── 5. Smoke Generation (STRICT: ONLY WHEN MOUTH IS OPEN & PUFF AVAILABLE!) ──
        # When mouth is closed or puff is depleted: ZERO smoke is generated!
        if mouth_open and mouth_pos is not None and self.smoke_charge > 0.05:
            # Dense smoke streams out directly from the user's mouth!
            self.smoke_engine.generate_smoke(
                effect_key=effect_key,
                spawn_x=mouth_pos[0],
                spawn_y=mouth_pos[1],
                flavor=flavor,
                intensity=effect_intensity * (1.2 if self.smoke_charge > 0.2 else 0.8),
                frame_width=w,
            )
            # Smoothly deplete smoke charge during exhale so it finishes realistically
            self.smoke_charge = max(0.0, self.smoke_charge - 0.020)

        # NOTE: Persistent ambient pot smoke has been completely eliminated!
        # The room is 100% clean and clear when the user is not puffing.

        # ── 6. Update & Render Smoke Particles ──
        self.smoke_engine.update()

        speed_mod = self.settings.get("speed", 1.4)
        for p in self.smoke_engine.particle_system.particles:
            p.vx *= (0.96 + speed_mod * 0.04)
            p.vy *= (0.96 + speed_mod * 0.04)

        # Render smoke with volumetric alpha blending
        frame = self.smoke_engine.render(
            frame,
            blur_passes=1 if self.settings.get("performance_mode", False) else 2,
            performance_mode=self.settings.get("performance_mode", False),
        )

        # Ambient edge glow matching flavor
        glow_color = flavor.get("glow_color", (200, 100, 255))
        frame = self.smoke_engine.add_glow(frame, glow_color, intensity=0.08)

        # ── 7. Render Virtual Hookah Pot & Hand-Held Hose Wand ──
        wand_tip = None
        if self.settings.get("show_hookah", True):
            frame, wand_tip = draw_virtual_hookah(
                frame,
                flavor_color=flavor["primary_color"],
                glow_color=glow_color,
                opacity=0.88,
                frame_count=self.frame_count,
                hand_pos=hand_grip_pos,
                mouth_pos=mouth_pos,
                is_inhaling=self.is_inhaling,
                smoke_charge=self.smoke_charge,
            )
            self.wand_tip_pos = wand_tip

        # ── 8. Overlays (Interactive HUD & Safety Banner) ──
        gesture_display = self.current_gesture if hand_detected else "NO GESTURE"
        frame = draw_performance_hud(
            frame,
            self.fps,
            self.smoke_engine.particle_count,
            gesture_display,
            self.current_effect,
            mouth_open=mouth_open,
            is_inhaling=self.is_inhaling,
            smoke_charge=self.smoke_charge,
        )
        frame = draw_safety_banner(frame)

        # Update coach advice
        if self.ai_coach:
            self.coach_message = self.ai_coach.get_message(
                self.current_gesture, self.current_effect, flavor_name
            )

        return frame

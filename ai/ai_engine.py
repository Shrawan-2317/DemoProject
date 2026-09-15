"""
AI Effect Engine for the AI Hookah Bar.

Deterministic decision logic that selects the appropriate smoke effect
based on gesture, velocity, direction, flavor, and current state.
Designed with a clean interface for future LLM integration.
"""

import numpy as np
from config.flavors import GESTURE_EFFECTS


class AIEffectEngine:
    """
    Determines the optimal smoke effect based on user interaction context.

    Current implementation uses deterministic Python logic.
    The decide() interface is designed so an LLM can be swapped in later.
    """

    def __init__(self):
        self.gesture_map = GESTURE_EFFECTS.copy()
        self._last_effect = "rise"
        self._intensity_smoothing = 0.7  # EMA factor

    def decide(self, gesture, velocity, direction, flavor, current_effect=None):
        """
        Make an AI-powered effect decision.

        Args:
            gesture: dict with 'gesture', 'confidence', 'velocity', 'direction', 'speed'.
            velocity: (vx, vy) tuple.
            direction: (dx, dy) normalized direction.
            flavor: Flavor dict from config.
            current_effect: Currently playing effect key.

        Returns:
            dict with keys: effect, intensity, direction, particle_count
        """
        gesture_name = gesture.get("gesture", "none")
        confidence = gesture.get("confidence", 0.0)
        speed = gesture.get("speed", 0.0)

        # Determine effect from gesture mapping
        effect = self.gesture_map.get(gesture_name, None)

        if effect is None or gesture_name == "none":
            # Keep current effect or default to rise
            effect = current_effect if current_effect else "rise"

        # Calculate intensity from speed and confidence
        speed_factor = min(1.0, speed / 500.0)  # Normalize speed
        base_intensity = 0.4 + confidence * 0.3 + speed_factor * 0.3
        base_intensity = max(0.3, min(1.0, base_intensity))

        # Adjust for flavor density
        density_mod = flavor.get("density", 0.8)
        intensity = base_intensity * (0.5 + density_mod * 0.5)

        # Determine particle count based on intensity and flavor
        base_count = int(flavor.get("particle_size", 16) * 5)
        particle_count = int(base_count * intensity * density_mod)
        particle_count = max(20, min(300, particle_count))

        # Determine direction
        dx, dy = direction
        if abs(dx) < 0.1 and abs(dy) < 0.1:
            smoke_direction = "up"
        elif dy < -0.5:
            smoke_direction = "up"
        elif dy > 0.5:
            smoke_direction = "down"
        elif dx < -0.5:
            smoke_direction = "left"
        elif dx > 0.5:
            smoke_direction = "right"
        else:
            smoke_direction = "up"

        self._last_effect = effect

        return {
            "effect": effect,
            "intensity": round(intensity, 2),
            "direction": smoke_direction,
            "particle_count": particle_count,
            "gesture_detected": gesture_name,
            "confidence": round(confidence, 2),
        }

    def get_status_text(self, decision):
        """Format the AI decision as display-friendly text."""
        effect_names = {
            "rise": "Normal Smoke",
            "ring": "Smoke Ring",
            "tornado": "Smoke Tornado",
            "burst": "Smoke Burst",
            "waterfall": "Smoke Waterfall",
            "spiral": "Smoke Spiral",
            "heart": "Smoke Heart",
            "dragon": "Dragon Smoke",
            "swirl": "Smoke Swirl",
            "double": "Double Smoke",
        }
        effect = decision.get("effect", "rise")
        return effect_names.get(effect, effect.title())

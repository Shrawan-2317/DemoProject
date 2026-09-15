"""
Smoke rendering engine for the AI Hookah Bar.

Renders particles onto a transparent overlay, applies Gaussian blur
and color tinting, then alpha-composites onto the camera frame.
"""

import cv2
import numpy as np
from effects.smoke_particles import ParticleSystem
from effects.smoke_stunts import STUNT_GENERATORS


class SmokeEngine:
    """Core smoke rendering pipeline."""

    def __init__(self, width=640, height=480, max_particles=500):
        self.width = width
        self.height = height
        self.particle_system = ParticleSystem(max_particles=max_particles)
        self.frame_count = 0
        self._overlay_cache = None

    def generate_smoke(self, effect_key, spawn_x, spawn_y, flavor, intensity=0.8, frame_width=640):
        """
        Generate new smoke particles for the given effect.

        Args:
            effect_key: Key from STUNT_GENERATORS (e.g. 'rise', 'ring').
            spawn_x, spawn_y: Particle spawn position.
            flavor: Flavor dict with color/size properties.
            intensity: Effect intensity (0.0 - 1.0).
            frame_width: Frame width for effects that need it.
        """
        generator = STUNT_GENERATORS.get(effect_key, STUNT_GENERATORS["rise"])

        # Build kwargs based on what the generator accepts
        kwargs = {
            "cx": spawn_x,
            "cy": spawn_y,
            "flavor": flavor,
            "intensity": intensity,
        }

        # Some generators need frame_count or frame_width
        import inspect
        sig = inspect.signature(generator)
        if "frame_count" in sig.parameters:
            kwargs["frame_count"] = self.frame_count
        if "frame_width" in sig.parameters:
            kwargs["frame_width"] = frame_width
        if "count" in sig.parameters:
            kwargs["count"] = int(10 * intensity)

        new_particles = generator(**kwargs)

        for p in new_particles:
            self.particle_system.spawn_particle(p)

    def update(self):
        """Update all particles for one frame."""
        self.particle_system.update()
        self.frame_count += 1

    def render(self, frame, blur_passes=2, performance_mode=False):
        """
        Render smoke particles onto the camera frame.

        Pipeline:
        1. Create transparent overlay (BGRA)
        2. Draw soft circles for each particle
        3. Apply Gaussian blur
        4. Alpha-blend with camera frame

        Args:
            frame: BGR camera frame (numpy array).
            blur_passes: Number of blur iterations for softness.
            performance_mode: If True, reduce quality for speed.

        Returns:
            BGR frame with smoke composited.
        """
        if self.particle_system.is_empty:
            return frame

        h, w = frame.shape[:2]

        # Create smoke overlay with alpha channel
        overlay = np.zeros((h, w, 4), dtype=np.uint8)

        # Draw particles (sorted by life ratio so older particles are behind)
        sorted_particles = sorted(
            self.particle_system.particles,
            key=lambda p: p.life_ratio,
            reverse=True
        )

        for p in sorted_particles:
            px, py = int(p.x), int(p.y)
            radius = max(1, int(p.radius))
            alpha = int(max(0, min(255, p.alpha)))

            # Skip out-of-bounds particles
            if px < -radius or px > w + radius or py < -radius or py > h + radius:
                continue

            if alpha < 3:
                continue

            # Dense volumetric particle with soft anti-aliased edge
            cv2.circle(overlay, (px, py), radius, (*p.color, min(255, int(alpha * 1.25))), -1, cv2.LINE_AA)
            cv2.circle(overlay, (px, py), int(radius * 1.35), (*p.color, int(alpha * 0.45)), -1, cv2.LINE_AA)

        # Apply gentle blur so edges soften without destroying stunt shapes
        overlay = cv2.GaussianBlur(overlay, (9, 9), 0)

        # Alpha-composite overlay onto frame
        result = self._alpha_blend(frame, overlay)

        return result

    def _alpha_blend(self, background, overlay_bgra):
        """
        Blend a BGRA overlay onto a BGR background.

        Uses the overlay's alpha channel for per-pixel blending.
        """
        # Extract channels
        overlay_bgr = overlay_bgra[:, :, :3]
        # Boost alpha contrast so smoke is thick, rich, and unmistakable
        alpha_mask = np.clip(overlay_bgra[:, :, 3].astype(np.float32) / 255.0 * 2.2, 0.0, 1.0)

        # Expand alpha to 3 channels
        alpha_3ch = np.stack([alpha_mask] * 3, axis=-1)

        # Blend
        bg_float = background.astype(np.float32)
        fg_float = overlay_bgr.astype(np.float32)

        blended = bg_float * (1.0 - alpha_3ch) + fg_float * alpha_3ch

        return blended.astype(np.uint8)

    def add_glow(self, frame, color, intensity=0.3):
        """
        Add a subtle ambient glow effect to the frame edges.

        Args:
            frame: BGR frame.
            color: BGR glow color tuple.
            intensity: Glow strength (0.0 - 1.0).

        Returns:
            Frame with edge glow.
        """
        h, w = frame.shape[:2]
        glow_layer = np.zeros_like(frame, dtype=np.uint8)

        # Create radial vignette glow at edges
        center_x, center_y = w // 2, h // 2
        Y, X = np.ogrid[:h, :w]
        dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
        max_dist = np.sqrt(center_x**2 + center_y**2)

        # Invert: glow at edges, dark at center
        glow_mask = np.clip(dist / max_dist, 0, 1)
        glow_mask = (glow_mask ** 2 * intensity * 255).astype(np.uint8)

        glow_layer[:, :, 0] = (glow_mask * color[0] / 255).astype(np.uint8)
        glow_layer[:, :, 1] = (glow_mask * color[1] / 255).astype(np.uint8)
        glow_layer[:, :, 2] = (glow_mask * color[2] / 255).astype(np.uint8)

        return cv2.add(frame, glow_layer)

    def clear(self):
        """Remove all particles."""
        self.particle_system.clear()

    @property
    def particle_count(self):
        return self.particle_system.count

    def resize(self, width, height):
        """Update engine dimensions."""
        self.width = width
        self.height = height

"""
Smoke particle system for the AI Hookah Bar.

Defines SmokeParticle dataclass and ParticleSystem manager
for spawning, updating, and culling smoke particles.
"""

import numpy as np
import random


class SmokeParticle:
    """A single smoke particle with physics and visual properties."""

    __slots__ = ['x', 'y', 'vx', 'vy', 'radius', 'alpha', 'initial_alpha', 'life',
                 'max_life', 'color', 'turbulence', 'growth_rate']

    def __init__(self, x, y, vx=0.0, vy=-1.0, radius=10.0, alpha=180,
                 life=60, color=(200, 200, 200), turbulence=0.5, growth_rate=0.3):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.radius = float(radius)
        self.alpha = float(alpha)
        self.initial_alpha = float(alpha)
        self.life = int(life)
        self.max_life = int(life)
        self.color = color
        self.turbulence = float(turbulence)
        self.growth_rate = float(growth_rate)

    @property
    def alive(self):
        return self.life > 0 and self.alpha > 3

    @property
    def life_ratio(self):
        """Remaining life as a fraction (1.0 = new, 0.0 = dead)."""
        return self.life / max(self.max_life, 1)

    def update(self):
        """Update particle position, size, and opacity for one frame."""
        # Add turbulence
        self.vx += random.gauss(0, self.turbulence)
        self.vy += random.gauss(0, self.turbulence * 0.5)

        # Apply velocity
        self.x += self.vx
        self.y += self.vy

        # Grow radius (smoke expands)
        self.radius += self.growth_rate

        # Fade out cleanly to 0 so smoke vanishes after its life
        self.life -= 1
        fade_ratio = max(0.0, self.life / max(self.max_life, 1))
        # Non-linear fade: stay visible initially, then vanish smoothly
        self.alpha = self.initial_alpha * (fade_ratio ** 1.3)

        # Slow down over time (drag)
        self.vx *= 0.97
        self.vy *= 0.97


class ParticleSystem:
    """Manages a collection of smoke particles with lifecycle control."""

    def __init__(self, max_particles=500):
        self.particles = []
        self.max_particles = max_particles

    def spawn(self, x, y, count=1, **kwargs):
        """
        Spawn new particles at position (x, y).

        Args:
            x, y: Spawn position.
            count: Number of particles to spawn.
            **kwargs: Override default SmokeParticle parameters.
        """
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break

            # Add slight randomness to spawn position
            px = x + random.gauss(0, kwargs.get('spread', 5))
            py = y + random.gauss(0, kwargs.get('spread', 5))

            particle = SmokeParticle(
                x=px,
                y=py,
                vx=kwargs.get('vx', random.gauss(0, 0.5)),
                vy=kwargs.get('vy', random.gauss(-2, 0.5)),
                radius=kwargs.get('radius', random.uniform(8, 15)),
                alpha=kwargs.get('alpha', random.uniform(120, 200)),
                life=kwargs.get('life', random.randint(40, 80)),
                color=kwargs.get('color', (200, 200, 200)),
                turbulence=kwargs.get('turbulence', 0.5),
                growth_rate=kwargs.get('growth_rate', 0.3),
            )
            self.particles.append(particle)

    def spawn_particle(self, particle):
        """Add a pre-configured particle directly."""
        if len(self.particles) < self.max_particles:
            self.particles.append(particle)

    def update(self):
        """Update all particles and remove dead ones."""
        for p in self.particles:
            p.update()

        # Remove dead particles
        self.particles = [p for p in self.particles if p.alive]

    def clear(self):
        """Remove all particles."""
        self.particles.clear()

    @property
    def count(self):
        return len(self.particles)

    @property
    def is_empty(self):
        return len(self.particles) == 0

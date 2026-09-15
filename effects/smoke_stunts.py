"""
Smoke stunt generators for the AI Hookah Bar.

Each stunt function generates particles with specific trajectories:
rise, ring, tornado, burst, waterfall, spiral, heart, dragon, swirl, double.
"""

import math
import random
from effects.smoke_particles import SmokeParticle


def generate_rise_particles(cx, cy, flavor, intensity=0.8, count=8):
    """Dense normal smoke — billowing cloud rising from mouth."""
    particles = []
    n = max(3, int(count * intensity))
    p_size = flavor.get("particle_size", 14)
    for _ in range(n):
        p = SmokeParticle(
            x=cx + random.gauss(0, 8),
            y=cy + random.gauss(0, 3),
            vx=random.gauss(0, 0.8),
            vy=random.uniform(-3.5, -2.0) * intensity,
            radius=p_size * random.uniform(0.9, 1.4),
            alpha=random.uniform(220, 255),
            life=random.randint(28, 45),  # Vanishes cleanly after ~1.2s
            color=_blend_color(flavor["primary_color"], flavor["secondary_color"], random.random()),
            turbulence=0.35,
            growth_rate=0.35,
        )
        particles.append(p)
    return particles


def generate_ring_particles(cx, cy, flavor, intensity=0.8, frame_count=0):
    """
    Smoke ring (O-Ring) stunt — tightly clustered expanding circular donut
    shooting forward/upward with crisp ring geometry.
    """
    particles = []
    num_points = int(32 * intensity)
    p_size = flavor.get("particle_size", 14) * 1.15
    base_r = 20.0
    for i in range(num_points):
        angle = (2 * math.pi * i / num_points)
        px = cx + base_r * math.cos(angle)
        py = cy + base_r * math.sin(angle) * 0.85

        radial_speed = 0.95 * intensity
        forward_vy = -3.5 * intensity

        vx = math.cos(angle) * radial_speed
        vy = math.sin(angle) * radial_speed * 0.85 + forward_vy

        p = SmokeParticle(
            x=px,
            y=py,
            vx=vx,
            vy=vy,
            radius=p_size,
            alpha=255.0,  # Maximum solid ring opacity
            life=random.randint(32, 48),  # Distinct lifespan then cleanly vanishes
            color=_blend_color(flavor["primary_color"], flavor["secondary_color"], (i / num_points)),
            turbulence=0.04,  # Minimal turbulence so circular donut stays clean
            growth_rate=0.18,
        )
        particles.append(p)
    return particles


def generate_tornado_particles(cx, cy, flavor, intensity=0.8, frame_count=0):
    """
    Smoke tornado stunt — tightly spinning helical funnel expanding as it twists upward.
    """
    particles = []
    n = max(8, int(15 * intensity))
    p_size = flavor.get("particle_size", 14)
    base_angle = frame_count * 0.40

    for i in range(n):
        t = i / max(n, 1)
        angle = base_angle + t * math.pi * 3.5
        radius = 8.0 + t * 45.0 * intensity
        height_offset = -t * 85.0 * intensity

        px = cx + radius * math.cos(angle)
        py = cy + height_offset + radius * math.sin(angle) * 0.35

        tangent_x = -math.sin(angle) * 3.0 * intensity
        tangent_y = math.cos(angle) * 0.9 * intensity

        p = SmokeParticle(
            x=px + random.gauss(0, 1.5),
            y=py + random.gauss(0, 1.5),
            vx=tangent_x,
            vy=-3.0 * intensity + tangent_y,
            radius=p_size * (0.6 + t * 0.7),
            alpha=random.uniform(210, 255),
            life=random.randint(28, 44),  # Vanishes after swirl
            color=_blend_color(flavor["primary_color"], flavor["secondary_color"], t),
            turbulence=0.25,
            growth_rate=0.25,
        )
        particles.append(p)
    return particles


def generate_burst_particles(cx, cy, flavor, intensity=0.8, count=36):
    """
    Smoke burst stunt (Palm push) — explosive 360-degree shockwave expanding outward rapidly.
    """
    particles = []
    n = max(20, int(count * intensity))
    p_size = flavor.get("particle_size", 14)
    for i in range(n):
        angle = (2 * math.pi * i / n) + random.gauss(0, 0.1)
        speed = random.uniform(6.5, 12.0) * intensity

        p = SmokeParticle(
            x=cx + math.cos(angle) * 8,
            y=cy + math.sin(angle) * 8,
            vx=math.cos(angle) * speed,
            vy=math.sin(angle) * speed,
            radius=p_size * random.uniform(1.1, 1.8),
            alpha=random.uniform(220, 255),
            life=random.randint(22, 36),  # Fast shockwave burst then vanishes!
            color=_blend_color(flavor["primary_color"], flavor["secondary_color"], random.random()),
            turbulence=0.3,
            growth_rate=0.5,
        )
        particles.append(p)
    return particles


def generate_waterfall_particles(cx, cy, flavor, intensity=0.8, count=14):
    """
    Smoke waterfall stunt (Move down) — dense, heavy cascade pouring straight down like dry ice.
    """
    particles = []
    n = max(6, int(count * intensity))
    p_size = flavor.get("particle_size", 14)
    for _ in range(n):
        p = SmokeParticle(
            x=cx + random.gauss(0, 25),
            y=cy + random.uniform(0, 6),
            vx=random.gauss(0, 0.7),
            vy=random.uniform(4.0, 7.5) * intensity,
            radius=p_size * random.uniform(1.2, 1.8),
            alpha=random.uniform(220, 255),
            life=random.randint(28, 45),  # Cascades down then vanishes
            color=_blend_color(flavor["primary_color"], flavor["secondary_color"], random.random()),
            turbulence=0.20,
            growth_rate=0.40,
        )
        particles.append(p)
    return particles


def generate_spiral_particles(cx, cy, flavor, intensity=0.8, frame_count=0):
    """Smoke spiral stunt — 3D double-helix trajectory."""
    particles = []
    n = max(6, int(10 * intensity))
    p_size = flavor.get("particle_size", 14)
    base_angle = frame_count * 0.28

    for i in range(n):
        t = i / max(n, 1)
        angle = base_angle + t * math.pi * 4.0
        radius = 18.0 + t * 35.0
        height = -t * 90.0 * intensity

        px = cx + radius * math.cos(angle)
        py = cy + height

        depth = math.sin(angle) * 0.5 + 0.5
        p = SmokeParticle(
            x=px,
            y=py,
            vx=math.cos(angle) * 2.2 * intensity,
            vy=-2.4 * intensity,
            radius=p_size * (0.8 + depth * 0.5),
            alpha=random.uniform(190, 250) * (0.6 + depth * 0.4),
            life=random.randint(28, 44),
            color=_blend_color(flavor["primary_color"], flavor["secondary_color"], depth),
            turbulence=0.25,
            growth_rate=0.28,
        )
        particles.append(p)
    return particles


def generate_heart_particles(cx, cy, flavor, intensity=0.8, frame_count=0):
    """Smoke heart stunt — distinct parametric heart curve."""
    particles = []
    num_points = int(24 * intensity)
    p_size = flavor.get("particle_size", 14)
    scale = 3.6 + math.sin(frame_count * 0.1) * 0.4

    for i in range(num_points):
        t = (2 * math.pi * i / num_points)
        hx = 16 * math.sin(t) ** 3
        hy = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))

        px = cx + hx * scale
        py = cy + hy * scale - 40

        p = SmokeParticle(
            x=px + random.gauss(0, 1.2),
            y=py + random.gauss(0, 1.2),
            vx=random.gauss(0, 0.3),
            vy=random.gauss(-0.6, 0.2),
            radius=p_size * 0.9,
            alpha=random.uniform(210, 255),
            life=random.randint(28, 45),
            color=_blend_color(flavor["primary_color"], flavor["secondary_color"], (i / num_points)),
            turbulence=0.12,
            growth_rate=0.18,
        )
        particles.append(p)
    return particles


def generate_dragon_particles(cx, cy, flavor, intensity=0.8, frame_count=0):
    """Dragon smoke stunt — dual high-speed angled streams shooting down-out."""
    particles = []
    p_size = flavor.get("particle_size", 14)
    for angle_deg in [-55, 55]:
        rad = math.radians(angle_deg)
        for _ in range(int(5 * intensity)):
            speed = random.uniform(5.5, 9.5) * intensity
            p = SmokeParticle(
                x=cx + math.sin(rad) * 12,
                y=cy + math.cos(rad) * 8,
                vx=math.sin(rad) * speed + random.gauss(0, 0.4),
                vy=math.cos(rad) * speed * 0.7 + random.gauss(0, 0.4),
                radius=p_size * random.uniform(0.9, 1.5),
                alpha=random.uniform(210, 255),
                life=random.randint(25, 40),
                color=_blend_color(flavor["primary_color"], flavor["secondary_color"], random.random()),
                turbulence=0.4,
                growth_rate=0.35,
            )
            particles.append(p)
    return particles


def generate_swirl_particles(cx, cy, flavor, intensity=0.8, frame_count=0):
    """Smoke swirl stunt (Hand wave) — dynamic sweeping vortex expanding across frame."""
    particles = []
    n = max(8, int(12 * intensity))
    p_size = flavor.get("particle_size", 14)
    swirl_angle = frame_count * 0.30

    for i in range(n):
        t = i / max(n, 1)
        angle = swirl_angle + t * math.pi * 2.5
        radius = 12.0 + t * 50.0 * intensity

        px = cx + radius * math.cos(angle)
        py = cy - t * 65.0 + radius * math.sin(angle) * 0.4

        p = SmokeParticle(
            x=px,
            y=py,
            vx=math.cos(angle + math.pi/2) * 2.4 * intensity,
            vy=-1.8 * intensity,
            radius=p_size * (0.8 + t * 0.6),
            alpha=random.uniform(200, 250),
            life=random.randint(28, 45),
            color=_blend_color(flavor["primary_color"], flavor["secondary_color"], t),
            turbulence=0.35,
            growth_rate=0.30,
        )
        particles.append(p)
    return particles


def generate_double_particles(cx, cy, flavor, intensity=0.8, frame_count=0, frame_width=640):
    """Double smoke stunt (Two hands) — two symmetrical massive rising columns."""
    particles = []
    offset = frame_width * 0.18
    p_size = flavor.get("particle_size", 14)

    for side in [-1, 1]:
        sx = cx + side * offset
        for _ in range(int(5 * intensity)):
            p = SmokeParticle(
                x=sx + random.gauss(0, 10),
                y=cy + random.gauss(0, 5),
                vx=random.gauss(side * 0.8, 0.5),
                vy=random.uniform(-4.2, -2.6) * intensity,
                radius=p_size * random.uniform(1.0, 1.6),
                alpha=random.uniform(210, 255),
                life=random.randint(28, 45),
                color=_blend_color(flavor["primary_color"], flavor["secondary_color"], random.random()),
                turbulence=0.35,
                growth_rate=0.35,
            )
            particles.append(p)
    return particles


def _blend_color(c1, c2, t):
    """Linearly interpolate between two BGR color tuples."""
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


# Registry mapping stunt key to generator function
STUNT_GENERATORS = {
    "rise": generate_rise_particles,
    "ring": generate_ring_particles,
    "tornado": generate_tornado_particles,
    "burst": generate_burst_particles,
    "waterfall": generate_waterfall_particles,
    "spiral": generate_spiral_particles,
    "heart": generate_heart_particles,
    "dragon": generate_dragon_particles,
    "swirl": generate_swirl_particles,
    "double": generate_double_particles,
}

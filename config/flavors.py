"""
Flavor configuration for the AI Hookah Bar.

Each flavor defines visual properties that affect the virtual smoke appearance:
- primary_color / secondary_color: BGR tuples for smoke tinting
- particle_size: base radius of smoke particles
- density: particle spawn rate multiplier (0.0 - 1.0)
- glow_color: BGR tuple for neon glow effects
- animation_style: movement modifier for the smoke
"""

FLAVORS = {
    "Blueberry": {
        "primary_color": (255, 80, 120),      # BGR
        "secondary_color": (255, 120, 200),
        "glow_color": (255, 100, 150),
        "particle_size": 18,
        "density": 0.8,
        "animation_style": "smooth",
        "emoji": "🫐",
        "description": "Rich berry clouds with deep purple haze"
    },
    "Mint": {
        "primary_color": (180, 255, 80),
        "secondary_color": (220, 255, 180),
        "glow_color": (200, 255, 130),
        "particle_size": 16,
        "density": 0.7,
        "animation_style": "crisp",
        "emoji": "🌿",
        "description": "Cool refreshing mist with icy undertones"
    },
    "Mango": {
        "primary_color": (50, 180, 255),
        "secondary_color": (120, 220, 255),
        "glow_color": (80, 200, 255),
        "particle_size": 20,
        "density": 0.9,
        "animation_style": "warm",
        "emoji": "🥭",
        "description": "Tropical golden waves of sweetness"
    },
    "Watermelon": {
        "primary_color": (120, 80, 255),
        "secondary_color": (150, 130, 255),
        "glow_color": (140, 100, 255),
        "particle_size": 19,
        "density": 0.85,
        "animation_style": "juicy",
        "emoji": "🍉",
        "description": "Sweet summer vibes with pink clouds"
    },
    "Grape": {
        "primary_color": (220, 70, 150),
        "secondary_color": (255, 130, 220),
        "glow_color": (240, 100, 180),
        "particle_size": 18,
        "density": 0.85,
        "animation_style": "rich",
        "emoji": "🍇",
        "description": "Deep violet plumes of luxury"
    },
    "Rose": {
        "primary_color": (180, 130, 255),
        "secondary_color": (200, 170, 255),
        "glow_color": (190, 150, 255),
        "particle_size": 17,
        "density": 0.75,
        "animation_style": "elegant",
        "emoji": "🌹",
        "description": "Delicate floral wisps of romance"
    },
    "Coconut": {
        "primary_color": (220, 230, 240),
        "secondary_color": (235, 240, 250),
        "glow_color": (230, 235, 245),
        "particle_size": 22,
        "density": 0.65,
        "animation_style": "tropical",
        "emoji": "🥥",
        "description": "Creamy white clouds of paradise"
    },
    "Lemon": {
        "primary_color": (80, 240, 255),
        "secondary_color": (140, 250, 255),
        "glow_color": (110, 245, 255),
        "particle_size": 15,
        "density": 0.75,
        "animation_style": "zesty",
        "emoji": "🍋",
        "description": "Bright citrus bursts of energy"
    },
}

# Gesture → Smoke Effect mapping
GESTURE_EFFECTS = {
    "wave": "swirl",
    "open_palm": "burst",
    "pinch": "ring",
    "circle": "tornado",
    "move_up": "rise",
    "move_down": "waterfall",
    "two_hands": "double",
}

# Available smoke stunts for manual selection
SMOKE_STUNTS = [
    "Normal Smoke",
    "Smoke Ring",
    "Smoke Tornado",
    "Smoke Burst",
    "Smoke Waterfall",
    "Smoke Spiral",
    "Smoke Heart",
    "Dragon Smoke",
]

# Stunt name → internal key mapping
STUNT_KEYS = {
    "Normal Smoke": "rise",
    "Smoke Ring": "ring",
    "Smoke Tornado": "tornado",
    "Smoke Burst": "burst",
    "Smoke Waterfall": "waterfall",
    "Smoke Spiral": "spiral",
    "Smoke Heart": "heart",
    "Dragon Smoke": "dragon",
}

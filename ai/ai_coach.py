"""
AI Smoke Coach for the AI Hookah Bar.

Provides contextual suggestions and encouragement
based on detected gestures and current state.
"""

import random
import time


class SmokeCoach:
    """
    Generates contextual coaching messages that react to user gestures.

    Messages cycle to avoid repetition and provide variety.
    """

    def __init__(self):
        self._last_message = ""
        self._last_update_time = 0
        self._message_cooldown = 3.0  # seconds between message changes
        self._gesture_history = []

        # Tips for when no gesture is detected
        self.idle_tips = [
            "👋 Try waving your hand to create a Smoke Swirl!",
            "✋ Show an open palm for a Smoke Burst!",
            "🤏 Pinch your fingers to make a Smoke Ring!",
            "🔄 Move your hand in a circle for a Tornado!",
            "⬆️ Move your hand upward for Rising Smoke!",
            "⬇️ Move your hand downward for a Waterfall!",
            "🙌 Use both hands for Double Smoke!",
            "💡 Switch flavors to change the smoke color!",
            "🎨 Each flavor has unique particle effects!",
        ]

        # Responses per gesture
        self.gesture_responses = {
            "wave": [
                "🌀 Nice wave! Creating a beautiful Smoke Swirl!",
                "🌊 Great movement! The swirl looks amazing!",
                "👋 Perfect wave! Try varying your speed!",
            ],
            "open_palm": [
                "💥 Boom! Smoke Burst activated!",
                "✋ Great palm! The burst is looking powerful!",
                "🎆 Nice! Try holding your palm steady for maximum effect!",
            ],
            "pinch": [
                "⭕ Perfect pinch! Smoke Ring forming!",
                "🤏 Nice precision! The ring is expanding beautifully!",
                "💨 Great form! Try a slower pinch for bigger rings!",
            ],
            "circle": [
                "🌪️ Tornado detected! Incredible spiral effect!",
                "🔄 Amazing circular motion! The tornado is fierce!",
                "🌀 Keep the circle going for an epic tornado!",
            ],
            "move_up": [
                "⬆️ Rising Smoke! Elegant upward flow!",
                "☁️ Beautiful lift! The smoke is soaring!",
                "🆙 Great movement! Try faster for more intensity!",
            ],
            "move_down": [
                "⬇️ Waterfall activated! Mesmerizing cascade!",
                "🌊 Gorgeous downward flow! Like a smoke waterfall!",
                "💧 Perfect! The cascade effect is stunning!",
            ],
            "two_hands": [
                "🙌 Both hands detected! Double Smoke unleashed!",
                "✨ Dual power! The smoke is twice as magnificent!",
                "🎭 Amazing! Two streams of smoke flowing!",
            ],
        }

        self._tip_index = 0

    def get_message(self, gesture_name, effect_name=None, flavor_name=None):
        """
        Get a contextual coaching message.

        Args:
            gesture_name: Current detected gesture.
            effect_name: Current smoke effect.
            flavor_name: Current flavor name.

        Returns:
            str: Coaching message.
        """
        now = time.time()

        # Rate-limit message updates
        if now - self._last_update_time < self._message_cooldown and self._last_message:
            return self._last_message

        self._last_update_time = now

        if gesture_name == "none" or gesture_name is None:
            # Cycle through idle tips
            msg = self.idle_tips[self._tip_index % len(self.idle_tips)]
            self._tip_index += 1
        else:
            responses = self.gesture_responses.get(gesture_name, self.idle_tips)
            msg = random.choice(responses)

        self._last_message = msg
        return msg

    def get_flavor_tip(self, flavor_name):
        """Get a flavor-specific tip."""
        tips = {
            "Blueberry": "🫐 Blueberry creates deep purple clouds — try a Smoke Ring!",
            "Mint": "🌿 Mint gives a cool, crisp smoke — perfect for Rising Smoke!",
            "Mango": "🥭 Mango's golden waves look amazing in a Tornado!",
            "Watermelon": "🍉 Watermelon's pink smoke is beautiful in a Heart shape!",
            "Grape": "🍇 Grape's deep violet is stunning with Dragon Smoke!",
            "Rose": "🌹 Rose creates the most elegant Spirals!",
            "Coconut": "🥥 Coconut's white clouds are perfect for a Burst!",
            "Lemon": "🍋 Lemon's bright citrus looks great in a Waterfall!",
        }
        return tips.get(flavor_name, f"✨ {flavor_name} flavor selected — try different stunts!")

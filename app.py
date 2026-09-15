"""
AI Hookah Bar — Virtual AR Smoke Experience

Main Streamlit application entry point.

This is a VISUAL SIMULATION / AR-STYLE ENTERTAINMENT APPLICATION ONLY.
No physical smoking equipment is controlled by this application.
"""

import streamlit as st
import cv2
import numpy as np
import time
import os
import base64

# ── Page Config (must be first Streamlit call) ──
st.set_page_config(
    page_title="AI Hookah Bar — Virtual Smoke Experience",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Imports (after page config) ──
from config.flavors import FLAVORS, SMOKE_STUNTS, STUNT_KEYS
from vision.camera import CameraManager
from vision.hand_tracking import HandTracker
from vision.gesture_detection import GestureDetector
from vision.face_tracking import FaceTracker
from effects.smoke_engine import SmokeEngine
from effects.overlays import draw_virtual_hookah, draw_performance_hud, draw_safety_banner
from ai.ai_engine import AIEffectEngine
from ai.ai_coach import SmokeCoach
from effects.hookah_engine import HookahBarEngine
from ui.styles import (
    get_custom_css, get_landing_html, status_metric_html,
    coach_panel_html, intensity_bar_html, safety_notice_html,
)
from ui.sidebar import render_sidebar


# ═══════════════════════════════════════════════
#  Session State Initialization
# ═══════════════════════════════════════════════

def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        "entered": False,
        "camera_active": False,
        "camera_manager": None,
        "stream_server": None,
        "hand_tracker": None,
        "gesture_detector": None,
        "face_tracker": None,
        "smoke_engine": None,
        "ai_engine": None,
        "ai_coach": None,
        "selected_flavor": "Blueberry",
        "current_effect": "rise",
        "current_gesture": "none",
        "gesture_confidence": 0.0,
        "fps": 0.0,
        "particle_count": 0,
        "ai_decision": {},
        "coach_message": "",
        "frame_count": 0,
        "last_capture": None,
        "intensity_pct": 70,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session_state()


# ═══════════════════════════════════════════════
#  Helper Functions
# ═══════════════════════════════════════════════

def start_camera():
    """Initialize camera, tracking modules, and start the zero-flicker streaming server with HookahBarEngine."""
    if st.session_state.get("camera_manager") is None:
        st.session_state.camera_manager = CameraManager(camera_index=0, width=640, height=480)

    success = st.session_state.camera_manager.start()
    if not success:
        return False

    engine = HookahBarEngine.get_instance()
    engine.set_flavor(st.session_state.get("selected_flavor", "Blueberry"))
    engine.update_setting("intensity", st.session_state.get("intensity_slider", 0.85))
    engine.update_setting("density", st.session_state.get("density_slider", 0.85))
    engine.update_setting("speed", st.session_state.get("speed_slider", 1.4))
    engine.update_setting("show_hookah", st.session_state.get("show_hookah", True))
    engine.update_setting("ai_gesture", st.session_state.get("ai_gesture", True))
    engine.update_setting("show_landmarks", st.session_state.get("show_landmarks", False))
    engine.update_setting("performance_mode", st.session_state.get("performance_mode", False))
    engine.update_setting("show_face", st.session_state.get("show_face", False))

    # Initialize & Start smooth MJPEG stream server (completely eliminates blinking)
    if st.session_state.get("stream_server") is None:
        from vision.stream_server import VideoStreamServer
        st.session_state.stream_server = VideoStreamServer(default_port=8502)

    st.session_state.stream_server.start(
        camera_manager=st.session_state.camera_manager,
        frame_processor=lambda f: engine.process_frame(f),
    )

    st.session_state.camera_active = True
    return True


def stop_camera():
    """Stop camera and streaming server."""
    if st.session_state.get("stream_server"):
        st.session_state.stream_server.stop()
    if st.session_state.get("camera_manager"):
        st.session_state.camera_manager.stop()
    st.session_state.camera_active = False


def process_stream_frame(frame):
    """Process each frame through smoke and gesture engine for the background streaming server."""
    flavor_name = st.session_state.get("selected_flavor", "Blueberry")
    settings = {
        "selected_flavor": flavor_name,
        "is_ai_mode": "AI Auto" in st.session_state.get("smoke_mode", "🤖 AI Auto"),
        "selected_stunt": st.session_state.get("stunt_select", "Normal Smoke"),
        "intensity": st.session_state.get("intensity_slider", 0.7),
        "density": st.session_state.get("density_slider", 0.6),
        "speed": st.session_state.get("speed_slider", 1.5),
        "show_hookah": st.session_state.get("show_hookah", True),
        "ai_gesture": st.session_state.get("ai_gesture", True),
        "show_landmarks": st.session_state.get("show_landmarks", False),
        "performance_mode": st.session_state.get("performance_mode", False),
        "show_face": st.session_state.get("show_face", False),
    }
    return process_frame(frame, settings)


def process_frame(frame, settings):
    """
    Process a single camera frame through the full pipeline.

    Pipeline:
    1. MediaPipe hand detection
    2. Gesture recognition
    3. AI effect decision
    4. Smoke particle generation
    5. Smoke rendering
    6. Overlays (hookah, HUD, safety)

    Returns:
        Processed BGR frame.
    """
    h, w = frame.shape[:2]
    flavor_name = settings["selected_flavor"]
    flavor = FLAVORS[flavor_name]

    # ── 1. Hand Tracking ──
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    hand_results = None
    gesture_result = {"gesture": "none", "confidence": 0.0, "velocity": (0, 0), "direction": (0, 0), "speed": 0}
    num_hands = 0
    hand_positions = None
    spawn_x, spawn_y = w // 2, int(h * 0.45)

    skip_detection = settings["performance_mode"] and (st.session_state.frame_count % 2 != 0)

    if settings["ai_gesture"] and not skip_detection:
        hand_tracker = st.session_state.hand_tracker
        gesture_detector = st.session_state.gesture_detector

        hand_results = hand_tracker.detect(rgb_frame)

        if hand_results and hand_results.multi_hand_landmarks:
            num_hands = len(hand_results.multi_hand_landmarks)

            # Use first hand for gesture detection
            first_hand = hand_results.multi_hand_landmarks[0]
            hand_positions = hand_tracker.get_landmark_positions(first_hand, w, h)

            # Spawn smoke near the palm
            palm = hand_tracker.get_palm_center(hand_positions)
            spawn_x, spawn_y = palm

            # Detect gesture
            gesture_result = gesture_detector.update(
                hand_positions, hand_tracker, w, h, num_hands
            )

            # Draw landmarks if enabled
            if settings["show_landmarks"]:
                frame = hand_tracker.draw_landmarks(frame, hand_results)

    # ── 2. Face Tracking (optional) ──
    face_data = None
    if settings["show_face"] and not skip_detection:
        face_tracker = st.session_state.face_tracker
        face_data = face_tracker.detect(rgb_frame)

        if face_data and face_data.get("mouth_open"):
            # Mouth open → trigger burst from face position
            if gesture_result["gesture"] == "none":
                gesture_result["gesture"] = "open_palm"
                gesture_result["confidence"] = 0.6
                spawn_x = face_data["nose_position"][0]
                spawn_y = face_data["chin_position"][1]

    # ── 3. AI Effect Decision ──
    smoke_engine = st.session_state.smoke_engine
    ai_engine = st.session_state.ai_engine

    if settings["is_ai_mode"]:
        decision = ai_engine.decide(
            gesture=gesture_result,
            velocity=gesture_result.get("velocity", (0, 0)),
            direction=gesture_result.get("direction", (0, 0)),
            flavor=flavor,
            current_effect=st.session_state.current_effect,
        )
        effect_key = decision["effect"]
        effect_intensity = decision["intensity"] * settings["intensity"]
        st.session_state.ai_decision = decision
    else:
        # Manual mode
        stunt = settings["selected_stunt"] or "Normal Smoke"
        effect_key = STUNT_KEYS.get(stunt, "rise")
        effect_intensity = settings["intensity"]
        st.session_state.ai_decision = {
            "effect": effect_key,
            "intensity": effect_intensity,
            "direction": "up",
            "particle_count": 100,
            "gesture_detected": gesture_result["gesture"],
            "confidence": gesture_result["confidence"],
        }

    st.session_state.current_effect = effect_key
    st.session_state.current_gesture = gesture_result["gesture"]
    st.session_state.gesture_confidence = gesture_result["confidence"]

    # ── 4. Generate Smoke Particles ──
    # Spawn rate modulated by density slider
    spawn_rate = max(1, int(3 * settings["density"]))
    if st.session_state.frame_count % max(1, 4 - spawn_rate) == 0:
        smoke_engine.generate_smoke(
            effect_key=effect_key,
            spawn_x=spawn_x,
            spawn_y=spawn_y,
            flavor=flavor,
            intensity=effect_intensity,
            frame_width=w,
        )

    # ── 5. Update & Render Smoke ──
    smoke_engine.update()

    # Apply speed modifier to particle velocities
    speed_mod = settings["speed"]
    for p in smoke_engine.particle_system.particles:
        p.vx *= (0.95 + speed_mod * 0.05)
        p.vy *= (0.95 + speed_mod * 0.05)

    frame = smoke_engine.render(
        frame,
        blur_passes=1 if settings["performance_mode"] else 2,
        performance_mode=settings["performance_mode"],
    )

    # ── 6. Add ambient glow ──
    glow_color = flavor.get("glow_color", (200, 100, 255))
    frame = smoke_engine.add_glow(frame, glow_color, intensity=0.08)

    # ── 7. Virtual Hookah Overlay ──
    if settings["show_hookah"]:
        frame = draw_virtual_hookah(
            frame,
            flavor_color=flavor["primary_color"],
            glow_color=glow_color,
        )

    # ── 8. Performance HUD ──
    fps_val = st.session_state.camera_manager.fps if st.session_state.camera_manager else 0
    st.session_state.fps = fps_val
    st.session_state.particle_count = smoke_engine.particle_count

    frame = draw_performance_hud(
        frame, fps_val, smoke_engine.particle_count,
        gesture_result["gesture"], effect_key,
    )

    # ── 9. Safety Banner ──
    frame = draw_safety_banner(frame)

    st.session_state.frame_count += 1

    return frame


# ═══════════════════════════════════════════════
#  Main Application
# ═══════════════════════════════════════════════

def main():
    """Main application entry point."""

    # Inject custom CSS
    st.markdown(get_custom_css(), unsafe_allow_html=True)

    # ── Landing Page ──
    if not st.session_state.entered:
        render_landing_page()
        return

    # ── Main Experience ──
    render_main_experience()


def render_landing_page():
    """Render the futuristic landing page."""

    st.markdown("# 🌬️ AI HOOKAH BAR")
    st.markdown(get_landing_html(), unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="enter-btn">', unsafe_allow_html=True)
        if st.button("⚡ ENTER AI HOOKAH BAR ⚡", key="enter_bar", use_container_width=True):
            st.session_state.entered = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(safety_notice_html(), unsafe_allow_html=True)

    # Feature descriptions
    st.markdown("---")
    cols = st.columns(3)
    features = [
        ("🎯 Gesture Recognition", "Wave, pinch, swirl — your hands control the smoke"),
        ("🎨 8 Unique Flavors", "Each flavor creates distinctly colored smoke clouds"),
        ("🌀 8 Smoke Stunts", "Rings, tornados, hearts, dragons and more"),
    ]
    for col, (title, desc) in zip(cols, features):
        with col:
            st.markdown(f"""
            <div class="glass-card" style="text-align: center; min-height: 120px;">
                <h3 style="font-size: 1rem; margin-bottom: 0.5rem;">{title}</h3>
                <p style="color: #8b9dc0; font-size: 0.85rem;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)


def render_main_experience():
    """Render the main experience with selectable layout modes including a dedicated Camera Streaming Studio."""

    # ── Sidebar Controls ──
    settings = render_sidebar()

    # Sync settings with live engine
    engine = HookahBarEngine.get_instance()
    engine.set_flavor(settings["selected_flavor"])
    engine.update_setting("intensity", settings["intensity"])
    engine.update_setting("density", settings["density"])
    engine.update_setting("speed", settings["speed"])
    engine.update_setting("show_hookah", settings["show_hookah"])
    engine.update_setting("ai_gesture", settings["ai_gesture"])
    engine.update_setting("show_landmarks", settings["show_landmarks"])
    engine.update_setting("performance_mode", settings["performance_mode"])
    engine.update_setting("show_face", settings["show_face"])
    if not settings["is_ai_mode"] and settings.get("selected_stunt"):
        engine.set_stunt(settings["selected_stunt"])
    else:
        engine.set_mode(settings["is_ai_mode"])

    # Handle camera start/stop from sidebar or main screen
    if settings.get("start_camera"):
        success = start_camera()
        if not success:
            st.error(st.session_state.camera_manager.get_error_message() if st.session_state.camera_manager else "Camera failed to start")
        else:
            st.rerun()

    if settings.get("stop_camera"):
        stop_camera()
        st.rerun()

    # ── Header ──
    st.markdown("# 🌬️ AI HOOKAH BAR")

    # ── Layout Mode Selector ──
    layout_options = [
        "🎥 Camera Streaming Studio",
        "🎛️ Split Studio (Side-by-Side)",
        "🎨 Full Lounge Deck",
    ]
    selected_layout = st.segmented_control(
        "Layout Mode",
        layout_options,
        default="🎥 Camera Streaming Studio",
        label_visibility="collapsed",
    )
    if not selected_layout:
        selected_layout = "🎥 Camera Streaming Studio"

    # ── Render Chosen Layout ──
    if selected_layout == "🎥 Camera Streaming Studio":
        render_camera_streaming_studio(settings)
    elif selected_layout == "🎛️ Split Studio (Side-by-Side)":
        render_split_studio(settings)
    else:
        render_full_deck_layout(settings)

    # ── Safety Notice ──
    st.markdown(safety_notice_html(), unsafe_allow_html=True)


def render_camera_streaming_studio(settings):
    """
    Dedicated layout exclusively for camera streaming.
    Focuses entirely on the live camera stream with sleek, minimalist quick controls.
    """
    if st.session_state.camera_active and st.session_state.camera_manager and st.session_state.camera_manager.is_available:
        # Top status and action bar
        col_status, col_snap, col_stop = st.columns([3, 1, 1])
        with col_status:
            flavor = settings["selected_flavor"]
            emoji = FLAVORS[flavor]["emoji"]
            st.markdown(
                f'<div style="display:flex; align-items:center; gap:12px; margin: 0.2rem 0;">'
                f'<span style="background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4); '
                f'border-radius: 20px; padding: 4px 12px; font-size: 0.8rem; font-weight: 700; letter-spacing: 0.5px;">● LIVE STREAMING</span>'
                f'<span style="color: #c4b5fd; font-size: 0.85rem;">Active Flavor: <strong>{emoji} {flavor}</strong></span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col_snap:
            if st.button("📸 Screenshot", key="stream_cam_snap", use_container_width=True):
                settings["capture"] = True
        with col_stop:
            if st.button("⏹ Stop Camera", key="stream_cam_stop", use_container_width=True):
                stop_camera()
                st.rerun()

        # The Live Camera Stream (Centerpiece)
        render_camera_feed(settings)

        # Quick Flavor Selector directly under camera
        st.markdown('<div style="font-size: 0.75rem; color: #8b9dc0; font-weight: 600; letter-spacing: 1px; margin: 0.8rem 0 0.3rem 0; text-transform: uppercase;">🎨 Quick Flavor Switch</div>', unsafe_allow_html=True)
        flavor_cols = st.columns(8)
        for i, name in enumerate(FLAVORS.keys()):
            with flavor_cols[i]:
                is_active = settings["selected_flavor"] == name
                css_class = "flavor-active" if is_active else "flavor-btn"
                st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
                if st.button(f"{FLAVORS[name]['emoji']}", key=f"stream_flav_{name}", help=f"Switch to {name}", use_container_width=True):
                    st.session_state.selected_flavor = name
                    st.session_state["selected_flavor_name"] = name
                    st.session_state["pending_flavor"] = name
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        # Quick Stunt Selector directly under flavors
        st.markdown('<div style="font-size: 0.75rem; color: #8b9dc0; font-weight: 600; letter-spacing: 1px; margin: 0.6rem 0 0.3rem 0; text-transform: uppercase;">🌀 Quick Smoke Stunts</div>', unsafe_allow_html=True)
        stunt_emojis = {
            "Normal Smoke": "💨", "Smoke Ring": "⭕", "Smoke Tornado": "🌪️",
            "Smoke Burst": "💥", "Smoke Waterfall": "🌊", "Smoke Spiral": "🌀",
            "Smoke Heart": "💜", "Dragon Smoke": "🐉",
        }
        stunt_cols = st.columns(8)
        for i, stunt in enumerate(SMOKE_STUNTS):
            with stunt_cols[i]:
                current_key = STUNT_KEYS.get(stunt, "")
                is_active = st.session_state.current_effect == current_key
                css_class = "stunt-active" if is_active else "stunt-btn"
                st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
                short_name = stunt.replace("Smoke ", "")
                if st.button(f"{stunt_emojis.get(stunt, '💨')} {short_name}", key=f"stream_stunt_{stunt}", help=f"Trigger {stunt}", use_container_width=True):
                    st.session_state.current_effect = current_key
                    st.session_state["pending_mode"] = "🎮 Manual"
                    st.session_state["pending_stunt"] = stunt
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        # Live AI Smoke Coach Banner
        if st.session_state.ai_coach:
            coach = st.session_state.ai_coach
            msg = coach.get_message(
                st.session_state.current_gesture,
                st.session_state.current_effect,
                settings["selected_flavor"],
            )
            st.session_state.coach_message = msg
            st.markdown(
                f'<div style="margin-top: 0.8rem;">' + coach_panel_html("AI SMOKE COACH", msg) + '</div>',
                unsafe_allow_html=True,
            )

        # Interactive AR Hookah Guide
        st.markdown("""
        <div style="margin-top: 0.8rem; background: linear-gradient(135deg, rgba(30, 20, 50, 0.7), rgba(20, 30, 60, 0.7)); 
                    border: 1px solid rgba(196, 181, 253, 0.25); border-radius: 12px; padding: 14px 18px;">
            <div style="font-size: 0.85rem; font-weight: 700; color: #a78bfa; margin-bottom: 8px; letter-spacing: 0.5px;">
                💨 HOW TO INHALE, EXHALE & PERFORM GESTURE STUNTS
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; font-size: 0.78rem; color: #e2e8f0;">
                <div><strong>1. ✋ Hold Pipe:</strong> Raise hand to grip the flexible hookah hose and metallic wand.</div>
                <div><strong>2. 🔥 Take a Puff:</strong> Bring the pipe to your mouth to inhale! Water boils & coals flare.</div>
                <div><strong>3. 👄 Exhale on Open Mouth:</strong> Pull pipe away. <em>Smoke ONLY exhales when mouth is open!</em></div>
                <div><strong>4. ✨ Gestures for Stunts:</strong> Pinch = Rings ⭕ | Circle = Tornado 🌪️ | Palm = Burst 💥 | Down = Waterfall 🌊 | Wave = Swirl 🌀</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        render_camera_placeholder()


def render_split_studio(settings):
    """Side-by-side studio layout: camera on left, interactive controls on right."""
    col_cam, col_ctrl = st.columns([6, 5])

    with col_cam:
        if st.session_state.camera_active and st.session_state.camera_manager and st.session_state.camera_manager.is_available:
            col_t, col_s = st.columns([2, 1])
            with col_t:
                st.markdown('<div class="section-title" style="margin: 0.2rem 0;">📹 LIVE STREAM</div>', unsafe_allow_html=True)
            with col_s:
                if st.button("⏹ Stop", key="split_stop_cam", use_container_width=True):
                    stop_camera()
                    st.rerun()
            render_camera_feed(settings)
        else:
            render_camera_placeholder()

    with col_ctrl:
        tab_f, tab_s, tab_c = st.tabs(["🎨 Flavors", "🌀 Stunts", "⚙️ Options"])
        with tab_f:
            render_flavor_grid(settings)
        with tab_s:
            render_stunt_grid(settings)
        with tab_c:
            render_quick_controls(settings)
            render_status_dashboard(settings)


def render_full_deck_layout(settings):
    """Comprehensive deck layout with camera on top and full tabbed options below."""
    if st.session_state.camera_active and st.session_state.camera_manager and st.session_state.camera_manager.is_available:
        col_title, col_snap, col_stop = st.columns([3, 1, 1])
        with col_title:
            st.markdown('<div class="section-title" style="margin: 0.2rem 0;">📹 LIVE CAMERA <span style="color:#10b981; font-size:0.85rem; font-weight:600;">● LIVE STREAMING</span></div>', unsafe_allow_html=True)
        with col_snap:
            if st.button("📸 Screenshot", key="deck_cam_snap", use_container_width=True):
                settings["capture"] = True
        with col_stop:
            if st.button("⏹ Stop Camera", key="deck_cam_stop", use_container_width=True):
                stop_camera()
                st.rerun()

        render_camera_feed(settings)
    else:
        render_camera_placeholder()

    st.markdown("<hr style='border-color: rgba(139, 92, 246, 0.2); margin: 1.5rem 0 1rem 0;'>", unsafe_allow_html=True)

    tab_flavors, tab_stunts, tab_ai, tab_controls = st.tabs([
        "🎨 Flavors (Smoke Colors)",
        "🌀 Smoke Stunts",
        "🤖 AI Gestures & Coach",
        "⚙️ Adjustments & Options",
    ])

    with tab_flavors:
        render_flavor_grid(settings)

    with tab_stunts:
        render_stunt_grid(settings)

    with tab_ai:
        render_status_dashboard(settings)

    with tab_controls:
        render_quick_controls(settings)


def render_camera_feed(settings):
    """Render the smooth, zero-flicker native video stream via MJPEG."""
    stream_server = st.session_state.get("stream_server")
    if not stream_server or not stream_server.is_running:
        # Auto-start stream server if camera is active
        if st.session_state.get("camera_active") and st.session_state.get("camera_manager"):
            from vision.stream_server import VideoStreamServer
            if st.session_state.stream_server is None:
                st.session_state.stream_server = VideoStreamServer(default_port=8502)
            st.session_state.stream_server.start(
                camera_manager=st.session_state.camera_manager,
                frame_processor=lambda f: process_stream_frame(f),
            )
            time.sleep(0.15)

    stream_server = st.session_state.get("stream_server")
    stream_url = stream_server.get_stream_url() if stream_server and stream_server.is_running else None
    if not stream_url:
        render_camera_placeholder()
        return

    # Handle screenshot capture
    if settings.get("capture") and stream_server:
        jpeg_data = stream_server.get_latest_jpeg()
        if jpeg_data:
            capture_path = os.path.join(os.path.dirname(__file__), "assets", "capture.png")
            os.makedirs(os.path.dirname(capture_path), exist_ok=True)
            with open(capture_path, "wb") as f:
                f.write(jpeg_data)
            st.session_state.last_capture = capture_path
            st.toast("📸 Screenshot captured!", icon="✅")

    # Render hardware-accelerated MJPEG stream inside a clean iframe (100% zero-blink)
    import streamlit.components.v1 as components
    components.html(
        f"""
        <div style="display:flex; justify-content:center; align-items:center; width:100%; height:100%; margin:0; padding:0; background:transparent;">
            <img src="{stream_url}" 
                 style="width:100%; max-width:700px; height:auto; aspect-ratio: 4/3;
                        border-radius:18px; border: 2px solid rgba(139, 92, 246, 0.5); 
                        box-shadow: 0 10px 40px rgba(139, 92, 246, 0.35), 0 0 25px rgba(6, 182, 212, 0.2); 
                        display:block; margin: 0 auto; object-fit: cover; background: #07070d;" 
                 alt="AI Hookah Stream" />
        </div>
        """,
        height=525,
    )


def render_camera_placeholder():
    """Show prominent start camera card when camera is not active."""
    st.markdown('<div class="section-title">📹 LIVE CAMERA</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="glass-card" style="text-align: center; padding: 3rem 1.5rem; margin-bottom: 1rem;">
        <div style="font-size: 3.5rem; margin-bottom: 0.8rem;">📷</div>
        <h2 style="color: #c4b5fd; font-weight: 700; font-size: 1.5rem; margin-bottom: 0.5rem;">Camera Ready</h2>
        <p style="color: #94a3b8; font-size: 0.95rem; max-width: 500px; margin: 0 auto 1.5rem auto;">
            Turn on your camera to start interacting with virtual smoke, gesture recognition, and AR hookah effects.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("▶ START CAMERA NOW", key="center_start_cam", use_container_width=True):
            if start_camera():
                st.rerun()
            else:
                msg = st.session_state.camera_manager.get_error_message() if st.session_state.camera_manager else "Unable to open webcam."
                st.error(msg)


def render_quick_controls(settings):
    """Render in-page quick sliders and toggles."""
    st.markdown('<div class="section-title">⚙️ QUICK SETTINGS</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Current Flavor:** {settings['selected_flavor']}")
        st.markdown(f"**Smoke Mode:** {'🤖 AI Auto' if settings['is_ai_mode'] else '🎮 Manual'}")
        st.markdown(f"**Virtual Hookah Overlay:** {'Enabled' if settings['show_hookah'] else 'Disabled'}")
    with c2:
        st.markdown(f"**Smoke Intensity:** {int(settings['intensity'] * 100)}%")
        st.markdown(f"**Particle Density:** {int(settings['density'] * 100)}%")
        st.markdown(f"**Hand Tracking:** {'Active' if settings['ai_gesture'] else 'Off'}")
    st.info("💡 You can fine-tune all sliders, toggles, and performance modes anytime in the left sidebar.")


def render_flavor_grid(settings):
    """Render the flavor selection cards."""
    st.markdown('<div class="section-title">🎨 FLAVORS</div>', unsafe_allow_html=True)

    flavor_names = list(FLAVORS.keys())
    cols = st.columns(4)

    for i, name in enumerate(flavor_names):
        flavor = FLAVORS[name]
        col = cols[i % 4]
        with col:
            is_active = settings["selected_flavor"] == name
            css_class = "flavor-active" if is_active else "flavor-btn"
            st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
            if st.button(
                f"{flavor['emoji']} {name}",
                key=f"flav_{name}",
                use_container_width=True,
            ):
                st.session_state.selected_flavor = name
                st.session_state["selected_flavor_name"] = name
                st.session_state["pending_flavor"] = name
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)


def render_stunt_grid(settings):
    """Render the smoke stunt selection buttons."""
    st.markdown('<div class="section-title">🌀 SMOKE STUNTS</div>', unsafe_allow_html=True)

    stunt_emojis = {
        "Normal Smoke": "💨",
        "Smoke Ring": "⭕",
        "Smoke Tornado": "🌪️",
        "Smoke Burst": "💥",
        "Smoke Waterfall": "🌊",
        "Smoke Spiral": "🌀",
        "Smoke Heart": "💜",
        "Dragon Smoke": "🐉",
    }

    cols = st.columns(4)
    for i, stunt in enumerate(SMOKE_STUNTS):
        col = cols[i % 4]
        with col:
            current_key = STUNT_KEYS.get(stunt, "")
            is_active = st.session_state.current_effect == current_key
            css_class = "stunt-active" if is_active else "stunt-btn"
            emoji = stunt_emojis.get(stunt, "💨")
            st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
            if st.button(
                f"{emoji} {stunt}",
                key=f"stunt_{stunt}",
                use_container_width=True,
            ):
                st.session_state.current_effect = STUNT_KEYS.get(stunt, "rise")
                st.session_state["pending_mode"] = "🎮 Manual"
                st.session_state["pending_stunt"] = stunt
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)


def render_status_dashboard(settings):
    """Render the gesture/effect status dashboard."""
    st.markdown('<div class="section-title">📊 STATUS</div>', unsafe_allow_html=True)

    engine = HookahBarEngine.get_instance()
    cols = st.columns(4)

    # Gesture
    with cols[0]:
        gesture = engine.current_gesture.upper()
        if gesture == "NONE":
            gesture = "POT SMOKE (IDLE)"
        st.markdown(
            status_metric_html("Detected Gesture", gesture),
            unsafe_allow_html=True,
        )

    # Effect
    with cols[1]:
        effect_names = {
            "rise": "NORMAL SMOKE", "ring": "SMOKE RING", "tornado": "TORNADO",
            "burst": "BURST", "waterfall": "WATERFALL", "spiral": "SPIRAL",
            "heart": "HEART", "dragon": "DRAGON", "swirl": "SWIRL", "double": "DOUBLE",
        }
        effect = effect_names.get(engine.current_effect, "NORMAL SMOKE")
        st.markdown(
            status_metric_html("AI Effect", effect),
            unsafe_allow_html=True,
        )

    # Flavor
    with cols[2]:
        flavor = settings["selected_flavor"]
        emoji = FLAVORS[flavor]["emoji"]
        st.markdown(
            status_metric_html("Flavor", f"{emoji} {flavor}"),
            unsafe_allow_html=True,
        )

    # Intensity
    with cols[3]:
        decision = st.session_state.ai_decision
        intensity = decision.get("intensity", settings["intensity"])
        pct = int(intensity * 100)
        st.session_state.intensity_pct = pct
        st.markdown(
            status_metric_html("Intensity", f"{pct}%"),
            unsafe_allow_html=True,
        )

    # Intensity bar
    st.markdown(
        intensity_bar_html(st.session_state.intensity_pct),
        unsafe_allow_html=True,
    )

    # AI Coach
    if st.session_state.ai_coach:
        coach = st.session_state.ai_coach
        msg = coach.get_message(
            st.session_state.current_gesture,
            st.session_state.current_effect,
            settings["selected_flavor"],
        )
        st.session_state.coach_message = msg
        st.markdown(
            coach_panel_html("AI SMOKE COACH", msg),
            unsafe_allow_html=True,
        )

    # Show last capture
    if st.session_state.last_capture and os.path.exists(st.session_state.last_capture):
        with st.expander("📸 Last Screenshot"):
            capture_img = cv2.imread(st.session_state.last_capture)
            if capture_img is not None:
                st.image(cv2.cvtColor(capture_img, cv2.COLOR_BGR2RGB), use_container_width=True)


# ── Run ──
if __name__ == "__main__":
    main()
else:
    main()

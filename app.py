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
    is_cam_ready = st.session_state.camera_active and (
        st.session_state.get("use_browser_camera")
        or (st.session_state.camera_manager and st.session_state.camera_manager.is_available)
    )
    if is_cam_ready:
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
        is_cam_ready = st.session_state.camera_active and (
            st.session_state.get("use_browser_camera")
            or (st.session_state.camera_manager and st.session_state.camera_manager.is_available)
        )
        if is_cam_ready:
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
    is_cam_ready = st.session_state.camera_active and (
        st.session_state.get("use_browser_camera")
        or (st.session_state.camera_manager and st.session_state.camera_manager.is_available)
    )
    if is_cam_ready:
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
    # If browser camera mode is active, render the client-side Web Camera Studio
    if st.session_state.get("use_browser_camera"):
        render_browser_webrtc_camera(settings)
        return

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


def render_browser_webrtc_camera(settings):
    """
    Client-side Web Camera Studio that directly requests browser camera permissions
    via navigator.mediaDevices.getUserMedia for Streamlit Community Cloud and web browsers.
    """
    flavor_name = settings.get("selected_flavor", "Blueberry")
    flavor_info = FLAVORS.get(flavor_name, FLAVORS["Blueberry"])
    p_color = flavor_info["primary_color"]
    # Convert BGR to RGB hex
    hex_color = f"#{p_color[2]:02x}{p_color[1]:02x}{p_color[0]:02x}"
    stunt_key = STUNT_KEYS.get(settings.get("selected_stunt", "Normal Smoke"), "rise")

    import streamlit.components.v1 as components
    components.html(
        f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    background: transparent;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    overflow: hidden;
                    color: white;
                }}
                .video-container {{
                    position: relative;
                    width: 640px;
                    max-width: 95vw;
                    height: 480px;
                    max-height: 80vh;
                    border-radius: 18px;
                    overflow: hidden;
                    border: 2px solid rgba(139, 92, 246, 0.6);
                    box-shadow: 0 10px 40px rgba(139, 92, 246, 0.35), 0 0 25px rgba(6, 182, 212, 0.2);
                    background: #080812;
                }}
                video {{
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    transform: scaleX(-1);
                    display: block;
                }}
                canvas {{
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    pointer-events: none;
                }}
                .overlay-prompt {{
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(10, 10, 20, 0.88);
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    padding: 20px;
                    box-sizing: border-box;
                    text-align: center;
                    z-index: 10;
                }}
                .btn-request {{
                    background: linear-gradient(135deg, #8b5cf6, #3b82f6);
                    color: white;
                    border: none;
                    padding: 14px 28px;
                    font-size: 1rem;
                    font-weight: 700;
                    border-radius: 30px;
                    cursor: pointer;
                    box-shadow: 0 4px 20px rgba(139, 92, 246, 0.5);
                    transition: all 0.2s;
                    margin-top: 15px;
                }}
                .btn-request:hover {{
                    transform: scale(1.05);
                    box-shadow: 0 6px 25px rgba(139, 92, 246, 0.7);
                }}
                .hud-badge {{
                    position: absolute;
                    top: 12px;
                    left: 12px;
                    background: rgba(15, 15, 25, 0.75);
                    border: 1px solid rgba(139, 92, 246, 0.4);
                    border-radius: 8px;
                    padding: 6px 12px;
                    font-size: 0.78rem;
                    color: #00ffcc;
                    font-family: monospace;
                    z-index: 5;
                }}
                .hud-action {{
                    position: absolute;
                    top: 12px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: rgba(16, 185, 129, 0.85);
                    border: 1px solid #10b981;
                    border-radius: 20px;
                    padding: 5px 16px;
                    font-size: 0.78rem;
                    font-weight: 700;
                    color: white;
                    letter-spacing: 0.5px;
                    z-index: 5;
                }}
                .controls-bar {{
                    position: absolute;
                    bottom: 12px;
                    left: 50%;
                    transform: translateX(-50%);
                    display: flex;
                    gap: 10px;
                    z-index: 5;
                }}
                .ctrl-btn {{
                    background: rgba(20, 20, 35, 0.85);
                    color: #c4b5fd;
                    border: 1px solid rgba(139, 92, 246, 0.4);
                    padding: 8px 16px;
                    font-size: 0.8rem;
                    font-weight: 600;
                    border-radius: 20px;
                    cursor: pointer;
                    transition: all 0.2s;
                    backdrop-filter: blur(4px);
                }}
                .ctrl-btn:hover {{
                    background: rgba(139, 92, 246, 0.4);
                    color: white;
                }}
            </style>
        </head>
        <body>
            <div class="video-container">
                <div class="hud-badge" id="hud-status">FPS: 30 | FLAVOR: {flavor_name.upper()}</div>
                <div class="hud-action" id="action-banner">💨 TAP 'TAKE PUFF' TO INHALE & BLOW SMOKE</div>

                <div class="overlay-prompt" id="permission-card">
                    <div style="font-size: 3rem; margin-bottom: 10px;">📹</div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: #c4b5fd; margin-bottom: 6px;">
                        Allow Camera in Browser
                    </div>
                    <div style="font-size: 0.85rem; color: #94a3b8; max-width: 380px; line-height: 1.4;">
                        Your browser will ask for camera permission to stream your live video and render the interactive AR Hookah experience.
                    </div>
                    <button class="btn-request" onclick="startWebcam()">
                        ▶ ALLOW CAMERA & START
                    </button>
                    <div style="font-size: 0.72rem; color: #64748b; margin-top: 15px;">
                        🔒 Click the Padlock icon in your URL bar anytime to check permissions.
                    </div>
                </div>

                <video id="webcam-video" autoplay playsinline muted></video>
                <canvas id="ar-canvas" width="640" height="480"></canvas>

                <div class="controls-bar">
                    <button class="ctrl-btn" onclick="triggerPuff()">🔥 Take Puff</button>
                    <button class="ctrl-btn" onclick="triggerExhale()">💨 Exhale Smoke</button>
                    <button class="ctrl-btn" onclick="nextStunt()">🌀 Change Stunt</button>
                </div>
            </div>

            <script>
                const video = document.getElementById('webcam-video');
                const canvas = document.getElementById('ar-canvas');
                const ctx = canvas.getContext('2d');
                const permCard = document.getElementById('permission-card');
                const actionBanner = document.getElementById('action-banner');
                const hudStatus = document.getElementById('hud-status');

                let streamActive = false;
                let frameCount = 0;
                let particles = [];
                let isPuffing = false;
                let smokeCharge = 1.0;
                let currentStunt = "{stunt_key}";
                const stunts = ["ring", "tornado", "burst", "waterfall", "swirl"];
                let stuntIdx = stunts.indexOf(currentStunt);
                if (stuntIdx === -1) stuntIdx = 0;

                const flavorHex = "{hex_color}";

                function startWebcam() {{
                    navigator.mediaDevices.getUserMedia({{
                        video: {{ width: 640, height: 480, facingMode: 'user' }}
                    }})
                    .then(stream => {{
                        video.srcObject = stream;
                        streamActive = true;
                        permCard.style.display = 'none';
                        requestAnimationFrame(renderLoop);
                    }})
                    .catch(err => {{
                        console.error(err);
                        permCard.innerHTML = `
                            <div style="font-size: 3rem; margin-bottom: 10px;">🔒</div>
                            <div style="font-size: 1.15rem; font-weight: 700; color: #f87171; margin-bottom: 8px;">
                                Camera Permission Blocked
                            </div>
                            <div style="font-size: 0.82rem; color: #cbd5e1; max-width: 420px; line-height: 1.5;">
                                1. Click the <strong>Padlock / Tune icon 🔒</strong> on the left side of your browser URL bar.<br>
                                2. Change <strong>Camera</strong> permission to <strong>Allow</strong>.<br>
                                3. Refresh this page to start the experience!
                            </div>
                            <button class="btn-request" onclick="startWebcam()" style="background: #3b82f6; margin-top: 15px;">
                                🔄 Try Again
                            </button>
                        `;
                    }});
                }}

                function triggerPuff() {{
                    isPuffing = true;
                    smokeCharge = 1.0;
                    actionBanner.innerText = "🔥 INHALING... CHARGING SMOKE (100%)";
                    actionBanner.style.background = "rgba(239, 68, 68, 0.85)";
                    setTimeout(() => {{
                        isPuffing = false;
                        actionBanner.innerText = "👄 PUFF READY! CLICK 'EXHALE SMOKE' TO BLOW STUNTS!";
                        actionBanner.style.background = "rgba(139, 92, 246, 0.85)";
                    }}, 1200);
                }}

                function triggerExhale() {{
                    if (smokeCharge <= 0.1) smokeCharge = 1.0;
                    actionBanner.innerText = "💨 EXHALING! STUNT: " + stunts[stuntIdx].toUpperCase();
                    actionBanner.style.background = "rgba(16, 185, 129, 0.85)";

                    const mouthX = 320;
                    const mouthY = 240;
                    spawnStuntParticles(stunts[stuntIdx], mouthX, mouthY);
                }}

                function nextStunt() {{
                    stuntIdx = (stuntIdx + 1) % stunts.length;
                    currentStunt = stunts[stuntIdx];
                    actionBanner.innerText = "🎯 ACTIVE STUNT: " + currentStunt.toUpperCase();
                    actionBanner.style.background = "rgba(59, 130, 246, 0.85)";
                    triggerExhale();
                }}

                function spawnStuntParticles(stunt, cx, cy) {{
                    const count = stunt === "ring" ? 32 : (stunt === "burst" ? 36 : 24);
                    for (let i = 0; i < count; i++) {{
                        let vx = (Math.random() - 0.5) * 1.5;
                        let vy = -(Math.random() * 2.5 + 2.0);
                        let px = cx;
                        let py = cy;
                        let r = 12;

                        if (stunt === "ring") {{
                            const angle = (2 * Math.PI * i) / count;
                            px = cx + Math.cos(angle) * 18;
                            py = cy + Math.sin(angle) * 15;
                            vx = Math.cos(angle) * 1.0;
                            vy = Math.sin(angle) * 0.8 - 3.2;
                        }} else if (stunt === "tornado") {{
                            const angle = (2 * Math.PI * i) / count;
                            vx = -Math.sin(angle) * 3.0;
                            vy = -2.8;
                        }} else if (stunt === "burst") {{
                            const angle = (2 * Math.PI * i) / count;
                            const speed = Math.random() * 4.0 + 5.0;
                            vx = Math.cos(angle) * speed;
                            vy = Math.sin(angle) * speed;
                        }} else if (stunt === "waterfall") {{
                            px = cx + (Math.random() - 0.5) * 50;
                            vy = Math.random() * 3.5 + 3.0;
                        }} else if (stunt === "swirl") {{
                            const angle = (2 * Math.PI * i) / count;
                            vx = Math.cos(angle + Math.PI/2) * 2.8;
                            vy = -2.0;
                        }}

                        particles.push({{
                            x: px, y: py, vx: vx, vy: vy,
                            radius: r,
                            alpha: 1.0,
                            life: 40,
                            maxLife: 40,
                            color: flavorHex
                        }});
                    }}
                }}

                function renderLoop() {{
                    frameCount++;
                    ctx.clearRect(0, 0, 640, 480);

                    // 1. Draw Virtual Hookah Pot at Bottom Right
                    const potX = 520;
                    const potY = 460;
                    drawHookahPot(ctx, potX, potY, frameCount, isPuffing, flavorHex);

                    // 2. Update & Render Smoke Particles
                    for (let i = particles.length - 1; i >= 0; i--) {{
                        const p = particles[i];
                        p.x += p.vx;
                        p.y += p.vy;
                        p.radius += 0.35;
                        p.life--;
                        p.alpha = Math.max(0, p.life / p.maxLife);

                        if (p.life <= 0) {{
                            particles.splice(i, 1);
                            continue;
                        }}

                        ctx.save();
                        ctx.beginPath();
                        ctx.arc(p.x, p.y, p.radius, 0, 2 * Math.PI);
                        ctx.fillStyle = p.color;
                        ctx.globalAlpha = p.alpha * 0.85;
                        ctx.shadowColor = p.color;
                        ctx.shadowBlur = 15;
                        ctx.fill();
                        ctx.restore();
                    }}

                    requestAnimationFrame(renderLoop);
                }}

                function drawHookahPot(ctx, cx, cy, fc, puffing, color) {{
                    // Glass Base
                    ctx.save();
                    ctx.beginPath();
                    ctx.ellipse(cx, cy - 35, 50, 36, 0, 0, 2 * Math.PI);
                    ctx.fillStyle = color;
                    ctx.globalAlpha = puffing ? 0.85 : 0.55;
                    ctx.shadowColor = color;
                    ctx.shadowBlur = puffing ? 25 : 12;
                    ctx.fill();
                    ctx.restore();

                    // Dynamic Bubbles inside water
                    const bCount = puffing ? 12 : 5;
                    for (let b = 0; b < bCount; b++) {{
                        const by = cy - 10 - ((fc * (puffing ? 4 : 1.5) + b * 16) % 36);
                        const bx = cx + Math.sin(fc * 0.15 + b) * 22;
                        ctx.beginPath();
                        ctx.arc(bx, by, 3, 0, 2 * Math.PI);
                        ctx.fillStyle = "rgba(255, 255, 255, 0.9)";
                        ctx.fill();
                    }}

                    // Chrome Stem
                    ctx.fillStyle = "#cbd5e1";
                    ctx.fillRect(cx - 5, cy - 110, 10, 75);
                    ctx.fillStyle = "#f8fafc";
                    ctx.fillRect(cx - 2, cy - 110, 4, 75);

                    // Ash Tray
                    ctx.beginPath();
                    ctx.ellipse(cx, cy - 110, 32, 8, 0, 0, 2 * Math.PI);
                    ctx.fillStyle = "#94a3b8";
                    ctx.fill();

                    // Ceramic Bowl & Hot Coals
                    ctx.beginPath();
                    ctx.ellipse(cx, cy - 120, 18, 9, 0, 0, 2 * Math.PI);
                    ctx.fillStyle = color;
                    ctx.fill();

                    // Glowing Coals
                    ctx.beginPath();
                    ctx.arc(cx, cy - 126, 6, 0, 2 * Math.PI);
                    ctx.fillStyle = puffing ? "#ffdd00" : "#ff5500";
                    ctx.shadowColor = "#ff3300";
                    ctx.shadowBlur = puffing ? 25 : 10;
                    ctx.fill();
                }}

                // Automatically try requesting camera if allowed
                if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {{
                    navigator.permissions && navigator.permissions.query({{ name: 'camera' }}).then(res => {{
                        if (res.state === 'granted') {{
                            startWebcam();
                        }}
                    }}).catch(() => {{}});
                }}
            </script>
        </body>
        </html>
        """,
        height=525,
    )


def render_camera_placeholder():
    """Show prominent start camera card with browser permission guidance and native camera input."""
    st.markdown('<div class="section-title">📹 LIVE CAMERA STUDIO</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="glass-card" style="text-align: center; padding: 2rem 1.5rem; margin-bottom: 1rem;">
        <div style="font-size: 3.2rem; margin-bottom: 0.6rem;">📹</div>
        <h2 style="color: #c4b5fd; font-weight: 700; font-size: 1.4rem; margin-bottom: 0.4rem;">Camera Access & Controls</h2>
        <p style="color: #94a3b8; font-size: 0.92rem; max-width: 540px; margin: 0 auto 1rem auto;">
            Connect your camera to experience the interactive virtual hookah, mouth exhale simulation, and gesture stunts.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Browser Permission Help Card
    st.markdown("""
    <div style="background: rgba(139, 92, 246, 0.12); border: 1px solid rgba(139, 92, 246, 0.4); border-radius: 12px; padding: 16px 20px; margin-bottom: 1.2rem;">
        <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; color: #c4b5fd; font-size: 0.95rem; margin-bottom: 8px;">
            <span>🔒</span> HOW TO GRANT CAMERA PERMISSION IN YOUR BROWSER
        </div>
        <div style="font-size: 0.85rem; color: #e2e8f0; line-height: 1.6;">
            <strong>Step 1:</strong> Look at your browser's address bar (where the URL <code>https://hookahlounge.streamlit.app</code> is).<br>
            <strong>Step 2:</strong> Click the <strong>Padlock / Site Settings icon (🔒 or ⚙️)</strong> located just to the <strong>left</strong> of the URL.<br>
            <strong>Step 3:</strong> In the popup menu, locate <strong>Camera</strong> and toggle it from <em>Block</em> to <strong>Allow</strong>.<br>
            <strong>Step 4:</strong> Click the <strong>Reload / Refresh 🔄</strong> button in your browser.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🌐 START BROWSER WEBCAM STUDIO", key="start_webcam_btn", use_container_width=True):
            st.session_state.camera_active = True
            st.session_state.use_browser_camera = True
            st.rerun()

    with col2:
        if st.button("💻 START LOCAL CAMERA (OpenCV)", key="center_start_cam", use_container_width=True):
            if start_camera():
                st.session_state.use_browser_camera = False
                st.rerun()
            else:
                st.session_state.camera_active = True
                st.session_state.use_browser_camera = True
                st.info("💡 Cloud environment detected. Switching to Browser Web Camera mode.")
                st.rerun()

    # Direct Native Camera Capture (Bypasses iframe security and forces browser permission prompt!)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 📸 Quick Cloud Camera Snap (Direct Browser Prompt)")
    st.caption("Takes a photo using your device camera and renders it directly with AR hookah, smoke, and flavor.")
    cam_img = st.camera_input("Take a photo with AR Smoke", key="native_webcam_prompt")
    if cam_img is not None:
        try:
            bytes_data = cam_img.getvalue()
            cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
            if cv2_img is not None:
                engine = HookahBarEngine.get_instance()
                processed_frame, info = engine.process_frame(cv2_img)
                rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                st.image(rgb_frame, caption=f"💨 Live Hookah Smoke AR: {st.session_state.selected_flavor}", use_container_width=True)
                st.toast("💨 Live AR Smoke applied to your photo!", icon="✨")
        except Exception as e:
            st.error(f"Error processing image: {e}")


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

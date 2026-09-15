"""
Sidebar controls for the AI Hookah Bar Streamlit application.

Renders all sidebar controls: camera, flavor selection,
smoke settings, intensity sliders, and toggle options.
"""

import streamlit as st
from config.flavors import FLAVORS, SMOKE_STUNTS


def render_sidebar():
    """
    Render the complete sidebar with all controls.

    Returns:
        dict with all current settings.
    """
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 0.5rem 0 1rem 0;">
            <span style="font-size: 1.8rem;">🌬️</span>
            <h3 style="background: linear-gradient(135deg, #a855f7, #06b6d4);
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                       margin: 0.3rem 0 0 0; font-size: 1.2rem;">
                AI HOOKAH CONTROL
            </h3>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-title">📷 CAMERA</div>', unsafe_allow_html=True)

        # Camera control
        col1, col2 = st.columns(2)
        with col1:
            start_cam = st.button("▶ Start", key="start_cam", use_container_width=True)
        with col2:
            stop_cam = st.button("⏹ Stop", key="stop_cam", use_container_width=True)

        # ── Flavor Selection ──
        st.markdown('<div class="section-title">🎨 FLAVOR</div>', unsafe_allow_html=True)
        flavor_names = list(FLAVORS.keys())
        flavor_display = [f"{FLAVORS[f]['emoji']} {f}" for f in flavor_names]

        # Handle pending flavor updates from the main page grid before widget creation
        if "pending_flavor" in st.session_state:
            pending_f = st.session_state.pop("pending_flavor")
            if pending_f in flavor_names:
                st.session_state["flavor_select"] = flavor_names.index(pending_f)

        default_idx = st.session_state.get("flavor_select", 0)
        if default_idx >= len(flavor_names):
            default_idx = 0

        selected_idx = st.selectbox(
            "Select Flavor",
            range(len(flavor_names)),
            index=default_idx,
            format_func=lambda i: flavor_display[i],
            key="flavor_select",
            label_visibility="collapsed",
        )
        selected_flavor = flavor_names[selected_idx]
        st.session_state["selected_flavor_name"] = selected_flavor
        st.session_state["selected_flavor"] = selected_flavor

        # ── Smoke Mode ──
        st.markdown('<div class="section-title">💨 SMOKE MODE</div>', unsafe_allow_html=True)
        mode_options = ["🤖 AI Auto", "🎮 Manual"]
        if "pending_mode" in st.session_state:
            st.session_state["smoke_mode"] = st.session_state.pop("pending_mode")

        default_mode_idx = 0
        if st.session_state.get("smoke_mode") in mode_options:
            default_mode_idx = mode_options.index(st.session_state["smoke_mode"])

        smoke_mode = st.radio(
            "Mode",
            mode_options,
            index=default_mode_idx,
            key="smoke_mode",
            label_visibility="collapsed",
            horizontal=True,
        )
        is_ai_mode = "AI Auto" in smoke_mode

        # Manual effect selection
        selected_stunt = None
        if not is_ai_mode:
            if "pending_stunt" in st.session_state:
                st.session_state["stunt_select"] = st.session_state.pop("pending_stunt")

            default_stunt_idx = 0
            curr_stunt = st.session_state.get("stunt_select")
            if curr_stunt in SMOKE_STUNTS:
                default_stunt_idx = SMOKE_STUNTS.index(curr_stunt)

            selected_stunt = st.selectbox(
                "Smoke Effect",
                SMOKE_STUNTS,
                index=default_stunt_idx,
                key="stunt_select",
                label_visibility="collapsed",
            )

        # ── Intensity Controls ──
        st.markdown('<div class="section-title">⚡ CONTROLS</div>', unsafe_allow_html=True)

        intensity = st.slider(
            "Smoke Intensity",
            0.1, 1.0, 0.7,
            step=0.05,
            key="intensity_slider",
        )

        density = st.slider(
            "Particle Density",
            0.1, 1.0, 0.6,
            step=0.05,
            key="density_slider",
        )

        speed = st.slider(
            "Smoke Speed",
            0.5, 3.0, 1.5,
            step=0.1,
            key="speed_slider",
        )

        # ── Toggles ──
        st.markdown('<div class="section-title">⚙️ OPTIONS</div>', unsafe_allow_html=True)

        show_hookah = st.checkbox("🏺 Show Virtual Hookah", value=True, key="show_hookah")
        ai_gesture = st.checkbox("🤖 AI Gesture Mode", value=True, key="ai_gesture")
        show_landmarks = st.checkbox("📍 Show Landmarks", value=False, key="show_landmarks")
        performance_mode = st.checkbox("⚡ Performance Mode", value=False, key="performance_mode")
        show_face = st.checkbox("😊 Face Tracking", value=False, key="show_face")

        # ── Screenshot ──
        st.markdown('<div class="section-title">📸 CAPTURE</div>', unsafe_allow_html=True)
        capture = st.button("📸 Capture Screenshot", key="capture_btn", use_container_width=True)

        # ── Safety ──
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0 0.5rem 0; 
                    border-top: 1px solid rgba(139, 92, 246, 0.15);
                    margin-top: 1rem;">
            <p style="color: #5a5a70; font-size: 0.65rem; line-height: 1.4;">
                🔒 Virtual Experience Only<br>
                No physical equipment controlled
            </p>
        </div>
        """, unsafe_allow_html=True)

    return {
        "start_camera": start_cam,
        "stop_camera": stop_cam,
        "selected_flavor": selected_flavor,
        "is_ai_mode": is_ai_mode,
        "selected_stunt": selected_stunt,
        "intensity": intensity,
        "density": density,
        "speed": speed,
        "show_hookah": show_hookah,
        "ai_gesture": ai_gesture,
        "show_landmarks": show_landmarks,
        "performance_mode": performance_mode,
        "show_face": show_face,
        "capture": capture,
    }

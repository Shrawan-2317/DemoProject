"""
Custom CSS styles for the AI Hookah Bar Streamlit application.

Provides a premium futuristic lounge aesthetic with:
- Dark background
- Neon purple/blue/cyan accents
- Glassmorphism cards
- Smooth animations
- Modern typography
"""


def get_custom_css():
    """Return the complete custom CSS for the application."""
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap');

    /* ── Global Reset & Theme ── */
    .stApp {
        background: linear-gradient(135deg, #0a0a0f 0%, #0d0818 30%, #0a0f1a 60%, #0a0a0f 100%) !important;
        color: #e0e0f0 !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Hide Streamlit defaults */
    #MainMenu { visibility: hidden; }
    header { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }

    /* ── Main Container ── */
    .block-container {
        max-width: 1100px !important;
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }

    /* ── Typography ── */
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
    }

    h1 {
        background: linear-gradient(135deg, #a855f7 0%, #06b6d4 50%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center !important;
        font-size: 2.8rem !important;
        letter-spacing: -0.5px;
        margin-bottom: 0 !important;
        animation: titleGlow 3s ease-in-out infinite;
    }

    @keyframes titleGlow {
        0%, 100% { filter: brightness(1); }
        50% { filter: brightness(1.2); }
    }

    /* ── Glassmorphism Cards ── */
    .glass-card {
        background: rgba(15, 15, 30, 0.6) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(139, 92, 246, 0.2) !important;
        border-radius: 16px !important;
        padding: 1.2rem !important;
        margin: 0.5rem 0 !important;
        box-shadow: 0 8px 32px rgba(139, 92, 246, 0.1),
                    inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
        transition: all 0.3s ease !important;
    }

    .glass-card:hover {
        border-color: rgba(139, 92, 246, 0.4) !important;
        box-shadow: 0 8px 40px rgba(139, 92, 246, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(6, 182, 212, 0.3)) !important;
        color: #e0e0f0 !important;
        border: 1px solid rgba(139, 92, 246, 0.4) !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.5rem !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        backdrop-filter: blur(10px) !important;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.6), rgba(6, 182, 212, 0.6)) !important;
        border-color: rgba(168, 85, 247, 0.8) !important;
        box-shadow: 0 0 25px rgba(139, 92, 246, 0.4),
                    0 0 50px rgba(6, 182, 212, 0.2) !important;
        transform: translateY(-2px) !important;
    }

    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* ── Enter Button (Landing) ── */
    .enter-btn > button {
        background: linear-gradient(135deg, #8b5cf6 0%, #06b6d4 100%) !important;
        color: white !important;
        font-size: 1.3rem !important;
        padding: 1rem 3rem !important;
        border-radius: 16px !important;
        border: none !important;
        font-weight: 800 !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        box-shadow: 0 0 30px rgba(139, 92, 246, 0.5),
                    0 0 60px rgba(6, 182, 212, 0.3) !important;
        animation: enterPulse 2s ease-in-out infinite !important;
    }

    @keyframes enterPulse {
        0%, 100% { 
            box-shadow: 0 0 30px rgba(139, 92, 246, 0.5), 0 0 60px rgba(6, 182, 212, 0.3);
        }
        50% { 
            box-shadow: 0 0 50px rgba(139, 92, 246, 0.7), 0 0 80px rgba(6, 182, 212, 0.5);
        }
    }

    .enter-btn > button:hover {
        transform: translateY(-3px) scale(1.03) !important;
        box-shadow: 0 0 50px rgba(139, 92, 246, 0.8),
                    0 0 100px rgba(6, 182, 212, 0.5) !important;
    }

    /* ── Flavor Cards ── */
    .flavor-btn > button {
        background: rgba(20, 15, 40, 0.5) !important;
        border: 1px solid rgba(139, 92, 246, 0.25) !important;
        border-radius: 14px !important;
        padding: 0.7rem 1.2rem !important;
        font-size: 0.85rem !important;
        width: 100% !important;
        min-height: 55px !important;
        transition: all 0.3s ease !important;
    }

    .flavor-btn > button:hover {
        background: rgba(139, 92, 246, 0.2) !important;
        border-color: rgba(168, 85, 247, 0.6) !important;
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.3) !important;
    }

    .flavor-active > button {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.4), rgba(6, 182, 212, 0.3)) !important;
        border-color: rgba(168, 85, 247, 0.8) !important;
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.4) !important;
    }

    /* ── Stunt Buttons ── */
    .stunt-btn > button {
        background: rgba(15, 20, 40, 0.5) !important;
        border: 1px solid rgba(6, 182, 212, 0.25) !important;
        border-radius: 12px !important;
        font-size: 0.8rem !important;
        padding: 0.5rem 1rem !important;
        width: 100% !important;
    }

    .stunt-btn > button:hover {
        background: rgba(6, 182, 212, 0.2) !important;
        border-color: rgba(6, 182, 212, 0.6) !important;
    }

    .stunt-active > button {
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.35), rgba(139, 92, 246, 0.25)) !important;
        border-color: rgba(6, 182, 212, 0.8) !important;
        box-shadow: 0 0 15px rgba(6, 182, 212, 0.3) !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d0818 0%, #0a0a0f 100%) !important;
        border-right: 1px solid rgba(139, 92, 246, 0.15) !important;
    }

    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stCheckbox label {
        color: #c0b0e0 !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 500 !important;
    }

    /* ── Sliders ── */
    .stSlider > div > div > div {
        background: linear-gradient(90deg, #8b5cf6, #06b6d4) !important;
    }

    .stSlider > div > div > div > div {
        background: #8b5cf6 !important;
        box-shadow: 0 0 10px rgba(139, 92, 246, 0.5) !important;
    }

    /* ── Select boxes ── */
    .stSelectbox > div > div {
        background: rgba(15, 15, 30, 0.8) !important;
        border: 1px solid rgba(139, 92, 246, 0.3) !important;
        border-radius: 10px !important;
        color: #e0e0f0 !important;
    }

    /* ── Camera Feed Container ── */
    .camera-container {
        border: 2px solid rgba(139, 92, 246, 0.3);
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 0 40px rgba(139, 92, 246, 0.15),
                    0 0 80px rgba(6, 182, 212, 0.08);
        position: relative;
    }

    .camera-container img {
        border-radius: 18px;
    }

    /* ── Status Cards ── */
    .status-metric {
        background: rgba(15, 15, 30, 0.5);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 12px;
        padding: 0.8rem 1rem;
        text-align: center;
    }

    .status-metric h4 {
        color: #8b9dc0 !important;
        font-size: 0.7rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        margin-bottom: 4px !important;
    }

    .status-metric p {
        color: #a855f7 !important;
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        font-family: 'Outfit', sans-serif !important;
        margin: 0 !important;
    }

    /* ── Coach Panel ── */
    .coach-panel {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(6, 182, 212, 0.08));
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-radius: 14px;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
    }

    .coach-panel h4 {
        color: #06b6d4 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1.5px !important;
        margin-bottom: 8px !important;
    }

    .coach-panel p {
        color: #c8d0e0 !important;
        font-size: 0.95rem !important;
        line-height: 1.5 !important;
    }

    /* ── Intensity Bar ── */
    .intensity-bar {
        height: 8px;
        border-radius: 4px;
        background: rgba(30, 30, 60, 0.5);
        overflow: hidden;
        margin-top: 4px;
    }

    .intensity-fill {
        height: 100%;
        border-radius: 4px;
        background: linear-gradient(90deg, #8b5cf6, #06b6d4);
        transition: width 0.3s ease;
    }

    /* ── Section Dividers ── */
    .section-title {
        color: #8b9dc0;
        font-family: 'Outfit', sans-serif;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 2px;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(139, 92, 246, 0.15);
        margin: 1rem 0 0.5rem 0;
    }

    /* ── Safety Disclaimer ── */
    .safety-notice {
        background: rgba(15, 15, 30, 0.4);
        border: 1px solid rgba(100, 100, 140, 0.2);
        border-radius: 10px;
        padding: 0.6rem 1rem;
        text-align: center;
        font-size: 0.75rem;
        color: #6b7080;
        margin-top: 1rem;
    }

    /* ── Expander styling ── */
    .streamlit-expanderHeader {
        background: rgba(15, 15, 30, 0.5) !important;
        border: 1px solid rgba(139, 92, 246, 0.2) !important;
        border-radius: 10px !important;
        color: #c0b0e0 !important;
        font-family: 'Outfit', sans-serif !important;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #0a0a0f;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(139, 92, 246, 0.3);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(139, 92, 246, 0.5);
    }

    /* ── Animations ── */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }

    /* ── Landing Page ── */
    .landing-subtitle {
        text-align: center;
        color: #8b9dc0;
        font-family: 'Outfit', sans-serif;
        font-size: 1.15rem;
        font-weight: 300;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin-top: -10px;
        margin-bottom: 2rem;
    }

    .landing-features {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin: 2rem 0;
        flex-wrap: wrap;
    }

    .feature-item {
        text-align: center;
        padding: 1rem;
        min-width: 120px;
    }

    .feature-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }

    .feature-text {
        color: #8b9dc0;
        font-size: 0.85rem;
        font-family: 'Outfit', sans-serif;
    }

    /* Image styling */
    [data-testid="stImage"] img {
        border-radius: 16px;
    }
    </style>
    """


def get_landing_html():
    """Return the landing page HTML content."""
    return """
    <div style="text-align: center; padding: 2rem 0;">
        <div style="font-size: 4rem; margin-bottom: 1rem;">🌬️</div>
        <div class="landing-subtitle">Virtual Smoke Experience</div>
        
        <div class="landing-features">
            <div class="feature-item">
                <div class="feature-icon">📷</div>
                <div class="feature-text">Live Camera</div>
            </div>
            <div class="feature-item">
                <div class="feature-icon">🤖</div>
                <div class="feature-text">AI Gesture</div>
            </div>
            <div class="feature-item">
                <div class="feature-icon">💨</div>
                <div class="feature-text">Virtual Smoke</div>
            </div>
            <div class="feature-item">
                <div class="feature-icon">🎨</div>
                <div class="feature-text">8 Flavors</div>
            </div>
            <div class="feature-item">
                <div class="feature-icon">🌀</div>
                <div class="feature-text">8 Stunts</div>
            </div>
            <div class="feature-item">
                <div class="feature-icon">✨</div>
                <div class="feature-text">Real-time FX</div>
            </div>
        </div>
    </div>
    """


def status_metric_html(label, value):
    """Create a styled status metric card."""
    return f"""
    <div class="status-metric">
        <h4>{label}</h4>
        <p>{value}</p>
    </div>
    """


def coach_panel_html(title, message):
    """Create a styled AI coach panel."""
    return f"""
    <div class="coach-panel">
        <h4>🤖 {title}</h4>
        <p>{message}</p>
    </div>
    """


def intensity_bar_html(percentage):
    """Create an animated intensity bar."""
    return f"""
    <div class="intensity-bar">
        <div class="intensity-fill" style="width: {percentage}%;"></div>
    </div>
    """


def safety_notice_html():
    """Return the safety disclaimer HTML."""
    return """
    <div class="safety-notice">
        🔒 <strong>Virtual Experience Only</strong> — No physical smoking equipment is controlled by this application.
    </div>
    """

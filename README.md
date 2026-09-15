# 🌬️ AI Hookah Bar — Virtual AR Smoke Experience

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

A futuristic, **AI-powered virtual Hookah Bar experience** built with Python, Streamlit, OpenCV, and MediaPipe. 

Experience realistic augmented-reality shisha smoking right in your web browser — hold the virtual hookah pipe in your hands, take a puff, pull the pipe away, and **blow rich, billowing smoke stunts directly from your mouth** using intuitive hand gestures!

> **⚠️ Virtual Entertainment Only**  
> *No physical smoking equipment, tobacco, nicotine, or combustion is involved. This application is an AR visual simulation and entertainment experience designed for fun, creativity, and visual art.*

---

## ✨ Features & Mechanics

| Feature | Description |
|---|---|
| ✋ **Interactive Hookah Pipe** | Flexible braided hose dynamically links from the vase to your hand with a sleek metallic wand. |
| 🔥 **Realistic Inhale / Puff** | Bring the pipe to your mouth to inhale — watch the vase water bubble violently and coals flare glowing red-hot! |
| 👄 **Mouth-Triggered Exhale** | *Zero smoke when mouth is closed!* Smoke pours directly from your lips the instant you open your mouth. |
| 💨 **Quick Smoke Dissipation** | Smoke expands, performs its stunt, and cleanly fades to 0 alpha — leaving the room 100% clean and clear. |
| 🌀 **8 Gesture Smoke Stunts** | Pinch for Rings ⭕, Circle for Tornado 🌪️, Palm for Burst 💥, Move Down for Waterfall 🌊, Wave for Swirl 🌀! |
| 🎨 **8 Curated Shisha Flavors** | Blueberry, Mint, Mango, Watermelon, Grape, Rose, Coconut, and Lemon with custom glow colors. |
| 🤖 **AI Auto Mode & Coach** | Adaptive effect selection and real-time interactive smoke coaching. |
| 🎥 **Clean Camera Studio Layout** | 3 dedicated layouts (Camera Studio, Split Studio, Full Lounge Deck) with screenshot capture. |

---

## 🎮 How to Smoke & Perform Stunts

```
  [ ✋ Grip Pipe ]  ──>  [ 🔥 Take a Puff ]  ──>  [ 👄 Open Mouth ]  ──>  [ ✨ Gesture Stunt ]
   Raise hand to          Bring pipe to           Pull pipe away &        Pinch, Circle, Wave,
   hold the wand.         mouth to inhale.        open mouth to exhale!   or Palm for stunts!
```

### Supported Hand Gestures & Stunts:
- 🤏 **Pinch (👌)** → **Smoke Rings (O-Rings)**: Shoots crisp, expanding circular donut rings forward.
- 🔄 **Circular Motion (🔄)** → **Smoke Tornado**: Spinning conical helical vortex twisting upward.
- ✋ **Open Palm / Push (✋)** → **Smoke Burst**: 360-degree explosive shockwave blast.
- ⬇️ **Hand Down (👇)** → **Smoke Waterfall**: Heavy, dense cascade pouring straight down like dry ice fog.
- 👋 **Hand Wave (👋)** → **Smoke Swirl**: Sweeping orbital wave vortex.
- ⬆️ **Hand Up (☝️)** → **Dragon Smoke**: Dual high-speed angled exhaust jets.
- 🙌 **Both Hands (🙌)** → **Double Smoke**: Twin towering smoke columns.

---

## 🚀 Local Installation

### Prerequisites
- Python 3.9+ 
- Webcam (built-in or USB)

### Quick Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Shrawan-2317/DemoProject.git
   cd DemoProject
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\activate

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the application**:
   ```bash
   streamlit run app.py
   ```

5. **Open in browser**: Navigate to `http://localhost:8501`.

---

## ☁️ Deploying to Streamlit Community Cloud

You can deploy this project for free on [Streamlit Community Cloud](https://share.streamlit.io/):

1. **Push this code to your GitHub repository** (`main` branch).
2. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with GitHub.
3. Click **"New app"**.
4. Configure your repository:
   - **Repository:** `Shrawan-2317/DemoProject`
   - **Branch:** `main`
   - **Main file path:** `app.py`
5. Click **"Deploy!"**
   - The included `packages.txt` automatically configures headless camera & graphics libraries (`libgl1`, `libglib2.0-0`).
   - The included `requirements.txt` installs `opencv-python-headless` and `mediapipe` cleanly.

---

## 📁 Project Architecture

```
ai-hookah-bar/
├── app.py                     # Main Streamlit application & layout engine
├── requirements.txt           # Python dependencies (headless-compatible)
├── packages.txt               # Linux system dependencies for Streamlit Cloud
├── .gitignore                 # Standard Python/Streamlit exclusions
├── LICENSE                    # MIT License
├── README.md                  # Project overview & documentation
│
├── config/
│   └── flavors.py             # Shisha flavors, stunt keys & color palettes
│
├── vision/
│   ├── camera.py              # OpenCV camera capture & stream management
│   ├── stream_server.py       # MJPEG threaded video streaming server
│   ├── hand_tracking.py       # MediaPipe hand landmarks & finger counting
│   ├── gesture_detection.py   # Temporal gesture classifier & motion tracker
│   └── face_tracking.py       # MediaPipe face mesh & mouth opening detector
│
├── effects/
│   ├── hookah_engine.py       # Thread-safe unified AR pipeline & state machine
│   ├── smoke_engine.py        # Volumetric particle renderer & alpha blending
│   ├── smoke_particles.py     # Smoke particle physics & lifecycle system
│   ├── smoke_stunts.py        # 8 distinct mathematical stunt generators
│   └── overlays.py            # Hookah vase, coals, dynamic hose & HUD graphics
│
├── ai/
│   ├── ai_engine.py           # Intelligent gesture-to-stunt decision engine
│   └── ai_coach.py            # Interactive hookah trick coach
│
└── ui/
    └── styles.py              # Custom glassmorphic CSS design system
```

---

## 📄 License

This project is open-source and licensed under the [MIT License](LICENSE).

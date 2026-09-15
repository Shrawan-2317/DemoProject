"""
Visual overlay module for the AI Hookah Bar.

Draws a virtual hookah graphic and HUD elements on the camera frame
using OpenCV primitives with glow effects.
"""

import cv2
import numpy as np
import math


def draw_virtual_hookah(frame, flavor_color=(200, 100, 255), glow_color=(255, 120, 200),
                        opacity=0.85, frame_count=0, hand_pos=None, mouth_pos=None,
                        is_inhaling=False, smoke_charge=0.0):
    """
    Draw realistic virtual hookah pot anchored at bottom-right with dynamic bubbling water,
    pulsing hot coals, and a flexible braided hose connecting to the user's hand with a metallic wand!
    """
    h, w = frame.shape[:2]
    overlay = frame.copy()

    # Anchor hookah base neatly on the bottom right so user's face & chest remain center-stage
    cx = int(w * 0.82)
    base_y = h - 15

    # ── 1. Water base (Curved Glass Vase) ──
    base_w = 58
    base_h = 42
    base_center = (cx, base_y - base_h)

    # Outer glass reflection
    for i in range(4):
        alpha_mod = 1.0 - i * 0.15
        bw = base_w + i * 3
        bh = base_h + i * 2
        tint = tuple(int(c * alpha_mod * 0.45) for c in flavor_color)
        cv2.ellipse(overlay, (cx, base_y - base_h), (bw, bh), 0, 0, 360, tint, -1, cv2.LINE_AA)

    # Internal liquid glow
    liquid_color = tuple(min(255, int(c * 0.7 + (60 if is_inhaling else 30))) for c in flavor_color)
    cv2.ellipse(overlay, base_center, (base_w - 6, base_h - 6), 0, 0, 360, liquid_color, -1, cv2.LINE_AA)

    # Water line (waving water surface)
    wave_offset = int(3 * math.sin(frame_count * (0.35 if is_inhaling else 0.15)))
    water_y = base_y - base_h + 4 + wave_offset
    cv2.ellipse(overlay, (cx, water_y), (base_w - 8, 10), 0, 0, 360, (230, 210, 120), 2, cv2.LINE_AA)

    # Dynamic Rising Water Bubbles inside the vase (bubbles boil violently when inhaling!)
    bubble_count = 14 if is_inhaling else 6
    bubble_speed_mult = 3.2 if is_inhaling else 1.0
    for b_idx in range(bubble_count):
        b_speed = (1.5 + (b_idx % 3) * 0.6) * bubble_speed_mult
        b_y_progress = (frame_count * b_speed + b_idx * 14) % (base_h - 6)
        by = base_y - 6 - int(b_y_progress)
        bx = cx + int(math.sin(frame_count * 0.15 + b_idx * 1.3) * (base_w * 0.42))
        b_radius = 2 + (b_idx % 3) + (1 if is_inhaling else 0)
        cv2.circle(overlay, (bx, by), b_radius, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.circle(overlay, (bx - 1, by - 1), 1, (255, 255, 255), -1, cv2.LINE_AA)

    # ── 2. Downstem inside the water ──
    cv2.rectangle(overlay, (cx - 3, base_y - base_h - 15), (cx + 3, base_y - 12), (160, 160, 180), -1, cv2.LINE_AA)

    # ── 3. Metallic Stem (Vertical Chrome Tube with Ornamental Spheres) ──
    stem_top = base_y - base_h - 75
    stem_bottom = base_y - base_h - 10

    cv2.rectangle(overlay, (cx - 7, stem_top), (cx + 7, stem_bottom), (170, 175, 190), -1, cv2.LINE_AA)
    cv2.rectangle(overlay, (cx - 2, stem_top), (cx + 3, stem_bottom), (235, 240, 255), -1, cv2.LINE_AA)

    # Ornamental metallic spheres on the stem
    sphere_y1 = stem_bottom - 20
    sphere_y2 = stem_top + 25
    for sy in [sphere_y1, sphere_y2]:
        cv2.circle(overlay, (cx, sy), 11, (160, 165, 180), -1, cv2.LINE_AA)
        cv2.circle(overlay, (cx - 2, sy - 2), 4, (240, 245, 255), -1, cv2.LINE_AA)
        cv2.circle(overlay, (cx, sy), 11, flavor_color, 1, cv2.LINE_AA)

    # ── 4. Ash Tray (Wide Chrome Plate beneath the bowl) ──
    tray_y = stem_top + 4
    cv2.ellipse(overlay, (cx, tray_y), (36, 9), 0, 0, 360, (140, 145, 160), -1, cv2.LINE_AA)
    cv2.ellipse(overlay, (cx, tray_y), (36, 9), 0, 0, 360, (220, 225, 240), 2, cv2.LINE_AA)
    cv2.ellipse(overlay, (cx, tray_y), (30, 6), 0, 0, 360, (90, 95, 110), -1, cv2.LINE_AA)

    # ── 5. Ceramic Hookah Bowl (Top) ──
    bowl_center = (cx, stem_top - 6)
    cv2.ellipse(overlay, bowl_center, (22, 12), 0, 0, 360, (130, 125, 145), -1, cv2.LINE_AA)
    cv2.ellipse(overlay, bowl_center, (18, 9), 0, 0, 360, flavor_color, -1, cv2.LINE_AA)

    # ── 6. Pulsing Hot Coals (Bright orange-red flare when inhaling) ──
    coal_pulse = math.sin(frame_count * (0.35 if is_inhaling else 0.18))
    coal_heat = 250 if is_inhaling else int(180 + 70 * coal_pulse)
    coal_glow_color = (30, int(coal_heat * 0.7), coal_heat)  # BGR: Orange-red heat
    coal_center = (cx, stem_top - 12)

    for offset_x in [-6, 0, 6]:
        c_pt = (cx + offset_x, stem_top - 10 + abs(offset_x) // 3)
        cv2.circle(overlay, c_pt, 6 if is_inhaling else 5, (40, 40, 50), -1, cv2.LINE_AA)
        cv2.circle(overlay, c_pt, 4 if is_inhaling else 3, coal_glow_color, -1, cv2.LINE_AA)
        cv2.circle(overlay, (c_pt[0] - 1, c_pt[1] - 1), 2 if is_inhaling else 1, (220, 245, 255), -1, cv2.LINE_AA)

    # Sparks flying from coals
    spark_count = 6 if is_inhaling else 3
    for spark_i in range(spark_count):
        spark_y = stem_top - 14 - ((frame_count * 3 + spark_i * 9) % 35)
        spark_x = cx + int(math.sin(frame_count * 0.25 + spark_i * 1.8) * 12)
        cv2.circle(overlay, (spark_x, spark_y), 1, (0, 210, 255), -1, cv2.LINE_AA)

    # ── 7. Hookah Hose Port & Flexible Braided Hose ──
    port_pt = (cx - 30, base_y - base_h + 2)
    # Hose port connector on vase
    cv2.circle(overlay, port_pt, 7, (180, 185, 195), -1, cv2.LINE_AA)
    cv2.circle(overlay, port_pt, 4, (60, 60, 70), -1, cv2.LINE_AA)

    wand_tip_pos = None

    if hand_pos is not None:
        hx, hy = hand_pos
        # Wand orientation towards mouth (if mouth is known) or angled up
        if mouth_pos is not None:
            dx = mouth_pos[0] - hx
            dy = mouth_pos[1] - hy
            wand_angle = math.atan2(dy, dx)
        else:
            wand_angle = -math.pi * 0.4  # Angled upwards-left

        wand_length = 65
        # The grip point is in the hand, tip is pointing out towards mouth
        wand_tip_x = int(hx + math.cos(wand_angle) * wand_length)
        wand_tip_y = int(hy + math.sin(wand_angle) * wand_length)
        wand_base_x = int(hx - math.cos(wand_angle) * 15)
        wand_base_y = int(hy - math.sin(wand_angle) * 15)
        wand_tip_pos = (wand_tip_x, wand_tip_y)

        # Generate Cubic Bezier Curve from port to wand base
        p0 = port_pt
        # Natural sag with gravity down towards bottom
        p1 = (int(p0[0] - 60), int(min(h - 5, max(p0[1] + 35, base_y + 10))))
        p2 = (int(wand_base_x + 30), int(min(h - 5, max(wand_base_y + 80, base_y))))
        p3 = (wand_base_x, wand_base_y)

        hose_points = []
        for t_step in range(25):
            tt = t_step / 24.0
            bx = int((1-tt)**3 * p0[0] + 3*(1-tt)**2 * tt * p1[0] + 3*(1-tt)*tt**2 * p2[0] + tt**3 * p3[0])
            by = int((1-tt)**3 * p0[1] + 3*(1-tt)**2 * tt * p1[1] + 3*(1-tt)*tt**2 * p2[1] + tt**3 * p3[1])
            hose_points.append([bx, by])

        pts = np.array(hose_points, dtype=np.int32)
        # 1. Dark outer drop shadow
        cv2.polylines(overlay, [pts], False, (20, 20, 25), 9, cv2.LINE_AA)
        # 2. Rich velvet/braided body with flavor accent
        cv2.polylines(overlay, [pts], False, (75, 70, 95), 6, cv2.LINE_AA)
        cv2.polylines(overlay, [pts], False, flavor_color, 2, cv2.LINE_AA)

        # Suction pulse light along hose when inhaling!
        if is_inhaling:
            pulse_idx = int((frame_count * 2) % len(hose_points))
            px, py = hose_points[pulse_idx]
            cv2.circle(overlay, (px, py), 6, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(overlay, (px, py), 10, (100, 230, 255), 2, cv2.LINE_AA)

        # ── 8. Draw Metallic Hookah Wand / Mouthpiece in Hand ──
        # Draw cylindrical chrome grip
        cv2.line(overlay, (wand_base_x, wand_base_y), (wand_tip_x, wand_tip_y),
                 (190, 195, 210), 7, cv2.LINE_AA)
        cv2.line(overlay, (wand_base_x, wand_base_y), (wand_tip_x, wand_tip_y),
                 (240, 245, 255), 2, cv2.LINE_AA)

        # Decorative grip bands (gold rings)
        for g_step in [0.25, 0.45, 0.65]:
            gx = int(wand_base_x + (wand_tip_x - wand_base_x) * g_step)
            gy = int(wand_base_y + (wand_tip_y - wand_base_y) * g_step)
            cv2.circle(overlay, (gx, gy), 5, (60, 200, 245), -1, cv2.LINE_AA)

        # Tapered mouthpiece tip
        cv2.circle(overlay, (wand_tip_x, wand_tip_y), 5, (230, 235, 250), -1, cv2.LINE_AA)
        cv2.circle(overlay, (wand_tip_x, wand_tip_y), 3, (60, 180, 255), -1, cv2.LINE_AA)

        # If user is inhaling (tip is right at mouth): render active suction flare!
        if is_inhaling:
            # Pulsing suction aura
            cv2.circle(overlay, (wand_tip_x, wand_tip_y), 12, (0, 200, 255), 2, cv2.LINE_AA)
            cv2.circle(overlay, (wand_tip_x, wand_tip_y), 7, (255, 255, 255), -1, cv2.LINE_AA)

    else:
        # No hand detected: hose rests coiled on table
        rest_pts = []
        for t in range(24):
            tt = t / 23.0
            hx = port_pt[0] - int(45 * tt + 18 * math.sin(tt * math.pi))
            hy = port_pt[1] + int(30 * tt)
            rest_pts.append([hx, hy])

        pts = np.array(rest_pts, dtype=np.int32)
        cv2.polylines(overlay, [pts], False, (25, 25, 30), 8, cv2.LINE_AA)
        cv2.polylines(overlay, [pts], False, (80, 75, 100), 5, cv2.LINE_AA)
        cv2.polylines(overlay, [pts], False, flavor_color, 2, cv2.LINE_AA)
        # Tip on stand
        tip = tuple(rest_pts[-1])
        cv2.circle(overlay, tip, 5, (200, 205, 220), -1, cv2.LINE_AA)
        cv2.circle(overlay, tip, 3, flavor_color, -1, cv2.LINE_AA)

    # ── 9. Blend Overlay onto Frame ──
    result = cv2.addWeighted(overlay, opacity, frame, 1.0 - opacity, 0)

    # ── 10. Radial Coal & Flavor Glow ──
    glow_overlay = np.zeros_like(frame, dtype=np.uint8)
    for r in range(32, 6, -6):
        a = max(8, int((32 - r) * (1.4 if is_inhaling else (0.8 + 0.3 * coal_pulse))))
        cv2.circle(glow_overlay, coal_center, r,
                   tuple(int(c * a / 35) for c in glow_color), -1, cv2.LINE_AA)
    result = cv2.add(result, glow_overlay)

    return result, wand_tip_pos


def draw_performance_hud(frame, fps, particle_count, gesture_name, effect_name,
                         mouth_open=False, is_inhaling=False, smoke_charge=0.0):
    """
    Draw interactive Hookah Studio HUD with real-time inhale/exhale status,
    mouth tracking indicator, and smoke gauge.
    """
    h, w = frame.shape[:2]

    # Semi-transparent top HUD bar
    hud_h = 75
    hud_w = 260
    hud_overlay = frame.copy()
    cv2.rectangle(hud_overlay, (0, 0), (hud_w, hud_h), (12, 14, 20), -1)
    frame = cv2.addWeighted(hud_overlay, 0.65, frame, 0.35, 0)

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.42
    color = (0, 255, 200)

    # Stats
    cv2.putText(frame, f"FPS: {fps:.0f} | Particles: {particle_count}", (10, 18),
                font, font_scale, color, 1, cv2.LINE_AA)

    # Mouth Status Pill
    mouth_color = (0, 255, 120) if mouth_open else (90, 140, 230)
    mouth_str = "MOUTH: OPEN [EXHALING]" if (mouth_open and smoke_charge > 0.05) else ("MOUTH: OPEN [EMPTY]" if mouth_open else "MOUTH: CLOSED")
    cv2.putText(frame, mouth_str, (10, 36),
                font, font_scale, mouth_color, 1, cv2.LINE_AA)

    # Gesture & Stunt
    cv2.putText(frame, f"Gesture: {gesture_name.upper()}", (10, 52),
                font, font_scale, (240, 220, 100), 1, cv2.LINE_AA)
    cv2.putText(frame, f"Stunt: {effect_name.upper()} | Puff: {int(smoke_charge * 100)}%", (10, 68),
                font, font_scale, (255, 140, 200), 1, cv2.LINE_AA)

    # ── Top Center Action Guidance Banner ──
    banner_w = 480
    banner_h = 32
    bx1 = (w - banner_w) // 2
    by1 = 8
    banner_overlay = frame.copy()

    if is_inhaling:
        bg_color = (20, 80, 180)  # Amber-red pulsing
        msg = f">> INHALING... CHARGING SMOKE ({int(smoke_charge*100)}%) - PULL AWAY & OPEN MOUTH!"
        txt_color = (0, 255, 255)
    elif mouth_open and smoke_charge > 0.05:
        bg_color = (15, 110, 35)   # Green exhaling
        msg = f">> EXHALING SMOKE! ACTIVE STUNT: {effect_name.upper()} <<"
        txt_color = (255, 255, 255)
    elif smoke_charge > 0.05:
        bg_color = (30, 40, 90)
        msg = f">> PUFF READY ({int(smoke_charge*100)}%)! OPEN MOUTH TO BLOW SMOKE & DO GESTURES <<"
        txt_color = (120, 230, 255)
    else:
        bg_color = (25, 25, 35)
        msg = ">> AIR CLEAN: BRING HOOKAH PIPE TO MOUTH TO TAKE A PUFF! <<"
        txt_color = (200, 200, 220)

    cv2.rectangle(banner_overlay, (bx1, by1), (bx1 + banner_w, by1 + banner_h), bg_color, -1)
    frame = cv2.addWeighted(banner_overlay, 0.75, frame, 0.25, 0)
    cv2.rectangle(frame, (bx1, by1), (bx1 + banner_w, by1 + banner_h), (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, msg, (bx1 + 10, by1 + 21), font, 0.38, txt_color, 1, cv2.LINE_AA)

    return frame


def draw_safety_banner(frame):
    """Draw the safety disclaimer at the bottom of the frame."""
    h, w = frame.shape[:2]

    banner_h = 22
    banner_overlay = frame.copy()
    cv2.rectangle(banner_overlay, (0, h - banner_h), (w, h), (0, 0, 0), -1)
    frame = cv2.addWeighted(banner_overlay, 0.6, frame, 0.4, 0)

    text = "Virtual AR Experience Only - No physical smoking equipment is controlled"
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, text, (10, h - 6),
                font, 0.35, (150, 150, 150), 1, cv2.LINE_AA)

    return frame


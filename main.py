import numpy as np
import cv2
import json
from flask import Flask, request, jsonify

# 1. Import your 4 separate module files
import stump_finder
import pitch_finder
import tracker
import smoother
import physics
import decision
import os
import shutil

app = Flask(__name__)
FRAME_WIDTH = 3840
STUMP_WIDTH_OFFSET = 7

def flip_x(x_coord, adjust=0):
    return (FRAME_WIDTH - x_coord) - adjust

def run_mobile_backend(video, corners, is_lhb=False):
    print(f"🚀 Booting Modular DRS System... | LHB Mode: {is_lhb}")

    cap = cv2.VideoCapture(video)
    ret, frame_img = cap.read()
    cap.release()

    # Stage 1: Detector finds the stumps
    OFF_STUMP_X, LEG_STUMP_X, STUMP_HEIGHT, STUMP_BASE = stump_finder.find_stumps_overlay(frame_img, corners)

    # --- THE FIX: OFFSET THE FINISHED STUMP COORDS ---
    if is_lhb:
        print(f"🔄 LHB detected: Offsetting Off-Stump {OFF_STUMP_X} by -7px")
        OFF_STUMP_X = OFF_STUMP_X - STUMP_WIDTH_OFFSET

    pitch_width = corners[1, 0] - corners[0, 0]
    stump_x_dist = 0.075 * pitch_width
    LEG_STUMP_X = int(OFF_STUMP_X + stump_x_dist + ((27 - stump_x_dist) / 2.8))

    print(f"📊 CORRECTED COORDS: Off={OFF_STUMP_X}, Leg={LEG_STUMP_X}")

    # Stage 2-5: Core Processing
    BOUNCE_X, BOUNCE_Y, BOUNCE_FRAME = pitch_finder.find_pitch(video, corners, OFF_STUMP_X, LEG_STUMP_X, STUMP_HEIGHT, STUMP_BASE)
    path_data = tracker.track_ball(video, OFF_STUMP_X, LEG_STUMP_X, STUMP_HEIGHT, STUMP_BASE, BOUNCE_X, BOUNCE_Y, BOUNCE_FRAME)
    smoothed_list = smoother.apply_dual_threshold_smoothing(path_data, same_dir_limit=10, opposing_limit=0)
    IMPACT_X, IMPACT_Y = smoothed_list[-1]
    WICKET_X, WICKET_Y, future_points = physics.ballPhysics(video, smoothed_list, OFF_STUMP_X, LEG_STUMP_X, STUMP_HEIGHT, STUMP_BASE)

    # Stage 6: Decision
    BOUNCE_VERDICT, BOUNCE_OUTCHANCE, IMPACT_VERDICT, IMPACT_OUTCHANCE, WICKETS_VERDICT, WICKETS_OUTCHANCE = decision.MakeDecision(
        OFF_STUMP_X, LEG_STUMP_X, STUMP_HEIGHT, BOUNCE_X, WICKET_X, WICKET_Y, 48, 52, smoothed_list
    )

    # --- VERDICT LOGIC ---
    f_verdict = "OUT"
    if int(WICKETS_OUTCHANCE) < 40:
        f_verdict = "NOT OUT (Missing Stumps)"
    elif int(BOUNCE_OUTCHANCE) < 40:
        f_verdict = "NOT OUT (Pitched Outside Leg)"
    elif int(IMPACT_OUTCHANCE) < 40:
        f_verdict = "NOT OUT (Impact Outside Off)"
    elif 40 < int(WICKETS_OUTCHANCE) < 60:
        f_verdict = "UMPIRE'S CALL (Wickets)"
    elif 40 < int(IMPACT_OUTCHANCE) < 60:
        f_verdict = "UMPIRE'S CALL (Impact)"
    elif 40 < int(BOUNCE_OUTCHANCE) < 60:
        f_verdict = "UMPIRE'S CALL (Pitching)"

    result_data = {
        "final_DRS_verdict": f_verdict,
        "metadata": {"off_x": float(OFF_STUMP_X), "leg_x": float(LEG_STUMP_X), "stump_base": float(STUMP_BASE), "stump_height": float(STUMP_HEIGHT)},
        "path_data": {"tracked_points": [[float(x), float(y)] for x, y in smoothed_list], "future_points": [[float(x), float(y)] for x, y in future_points]},
        "stages": {
            "pitching": {"verdict": str(BOUNCE_VERDICT), "confidence": float(BOUNCE_OUTCHANCE), "x": float(BOUNCE_X), "y": float(BOUNCE_Y)},
            "impact": {"verdict": str(IMPACT_VERDICT), "confidence": float(IMPACT_OUTCHANCE), "x": float(IMPACT_X), "y": float(IMPACT_Y)},
            "wickets": {"verdict": str(WICKETS_VERDICT), "confidence": float(WICKETS_OUTCHANCE), "x": float(WICKET_X), "y": float(WICKET_Y)}
        }
    }
    return result_data


@app.route('/analyze', methods=['POST'])
def analyze():
    # --- 1. NUCLEAR PRE-FLIGHT SANITATION ---
    # Wipe /tmp clean to ensure 1077 vs 1096 "ghosting" isn't happening
    print("--- STARTING PRE-FLIGHT SANITATION ---", flush=True)
    tmp_path = "/tmp"
    for filename in os.listdir(tmp_path):
        file_path = os.path.join(tmp_path, filename)
        try:
            print(f"CLEANING STALE FILE: {filename}", flush=True)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Could not delete {file_path}: {e}", flush=True)
    print("--- MEMORY CLEARED: PROCEEDING ---", flush=True)

    # --- 2. RECEIVE VIDEO FILE ---
    if 'video' not in request.files:
        return jsonify({"error": "No video file"}), 400

    video_file = request.files['video']
    # Save to /tmp for Cloud Run persistence
    video_path = os.path.join(tmp_path, "temp_video.mov")
    video_file.save(video_path)

    # --- 3. EXTRACT DATA SAFELY ---
    # Swift sends this in the multipart 'data' field
    raw_data = request.form.get('data')
    if not raw_data:
        print("❌ Error: No JSON metadata found in 'data' field")
        return jsonify({"error": "Missing metadata"}), 401

    try:
        data = json.loads(raw_data)

        # Log parsed coordinates for Cloud Debugging
        print(f"CLOUD_DEBUG: Sanitized Coords: {data.get('coordinates')}", flush=True)

        is_lhb_val = data.get('isLHB', False)
        coords_list = data.get('coordinates', [])

        if len(coords_list) != 4:
            print(f"❌ Error: Expected 4 points, got {len(coords_list)}")
            return jsonify({"error": "Need 4 points"}), 402

        raw_corners = np.array([[p['x'], p['y']] for p in coords_list], dtype=np.float32)

        # Snap to the nearest 5px increment
        # Example: 102.4 -> 100.0, 103.6 -> 105.0
        corners = np.round(raw_corners / 5) * 5

        # --- 4. RUN BACKEND ---
        # Ensure your backend also outputs to /tmp if it generates a JSON file
        result = run_mobile_backend(video_path, corners, is_lhb_val)

        return jsonify(result)

    except Exception as e:
        print(f"❌ JSON Parse/Logic Error: {e}")
        return jsonify({"error": str(e)}), 403
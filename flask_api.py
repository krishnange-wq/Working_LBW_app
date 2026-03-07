import os
import json
import numpy as np
from flask import Flask, request, jsonify
import main

app = Flask(__name__)

# --- AUTOMATIC PATH SETUP ---
# This finds the folder where api.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Creates an 'uploads' folder inside your project directory
VIDEO_DIR = os.path.join(BASE_DIR, "uploads")

# Create the directory if it doesn't exist
if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)
    print(f"📁 Created upload directory at: {VIDEO_DIR}")


@app.route('/analyze', methods=['POST'])
def analyze_delivery():
    video_path = None
    try:
        # 1. RECEIVE THE VIDEO FILE
        if 'video' not in request.files:
            return jsonify({"error": "No video file uploaded"}), 400

        file = request.files['video']
        # Enforce project standard: lowercase .mov
        filename = file.filename.lower().replace(".mov", "") + ".mov"
        video_path = os.path.join(VIDEO_DIR, filename)

        # Save the incoming file from the iPhone
        file.save(video_path)
        print(f"📥 Received and saved: {filename}")

        # 2. RECEIVE THE COORDINATES
        coords_json = request.form.get('coordinates')
        if not coords_json:
            return jsonify({"error": "No coordinates provided"}), 400

        raw_coords = json.loads(coords_json)
        coords = np.array([[p['x'], p['y']] for p in raw_coords], dtype=np.float32)

        # 3. 🚀 EXECUTE BACKEND
        # Still applies Leg Side = UC and Stump Gap rules
        backend_results = main.run_mobile_backend(video_path, coords)

        # 4. 🛡️ PRIVACY CLEANUP
        if os.path.exists(video_path):
            os.remove(video_path)
            print(f"🗑️ Video deleted for privacy: {filename}")

        return jsonify(backend_results)

    except Exception as e:
        if video_path and os.path.exists(video_path):
            os.remove(video_path)
        print(f"❌ Server Error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("-" * 50)
    print(f"📡 LBW SERVER ACTIVE")
    print(f"📂 Saving temp files to: {VIDEO_DIR}")
    print(f"🚀 URL: http://0.0.0.0:5000/analyze")
    print("-" * 50)
    app.run(host='0.0.0.0', port=5000)
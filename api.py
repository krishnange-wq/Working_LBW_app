import os
import time
import json
import numpy as np
import main  # Your backend logic

# --- CONFIGURATION ---
HOME = os.path.expanduser("~")
# Absolute path to your specific Simulator Device
SIM_ROOT = os.path.join(HOME,
                        "Library/Developer/CoreSimulator/Devices/771B2C29-40ED-4C12-9F41-F885417F56D3/data/Containers/Data/Application")
VIDEO_DIR = "/Users/home/PycharmProjects/LBW_app"


def find_pitch_data():
    """Scans all subfolders in the Simulator root for pitch_data.json"""
    for root, dirs, files in os.walk(SIM_ROOT):
        if "pitch_data.json" in files:
            return os.path.join(root, "pitch_data.json")
    return None


def write_full_result(target_dir, result_dict):
    """Writes the complete backend dictionary back to the Simulator."""
    result_path = os.path.join(target_dir, "result.json")
    with open(result_path, 'w') as f:
        json.dump(result_dict, f, indent=4)
    print(f"📡 Full Results Sent to iPad: {result_dict.get('final_DRS_verdict', 'N/A')}")


print("-" * 50)
print(f"📡 LBW BIDIRECTIONAL API (FULL DATA MODE)")
print(f"📂 Scanning: {SIM_ROOT}")
print("-" * 50)

try:
    while True:
        json_path = find_pitch_data()

        if json_path:
            print(f"\n🔔 NEW DATA DETECTED")
            try:
                with open(json_path, 'r') as f:
                    input_data = json.load(f)

                # Setup inputs for main.py
                # Note: .mov is lowercase per your project standards
                video_name = input_data.get('video_file', 'IMG_6963.mov')
                video_path = os.path.join(VIDEO_DIR, video_name)
                coords = np.array([[p['x'], p['y']] for p in input_data['coordinates']], dtype=np.float32)

                # 🚀 EXECUTE BACKEND
                # Expecting a dict like: {"decision": "OUT", "pitching": "Outside Leg", "ball_path": [...]}
                backend_results = main.run_mobile_backend(video_path, coords)

                # Ensure we are sending a dictionary
                if not isinstance(backend_results, dict):
                    backend_results = {"decision": str(backend_results)}

                # 📤 SEND EVERYTHING BACK
                write_full_result(os.path.dirname(json_path), backend_results)

                # 🧹 CLEANUP INPUT
                os.remove(json_path)
                print("✅ Cycle Complete. Ready for next ball.")

            except Exception as e:
                print(f"❌ Error during processing: {e}")

        time.sleep(1)
except KeyboardInterrupt:
    print("\n🛑 Stopped.")
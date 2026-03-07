import json
import os

# 1. The deep Simulator path (The Source)
SIM_PATH = "/Users/home/Library/Developer/CoreSimulator/Devices/771B2C29-40ED-4C12-9F41-F885417F56D3/data/Containers/Data/Application/B7F1F02C-E68B-4F23-96D9-9227408D371A/Documents/pitch_data.json"

# 2. Your iMac Project path (The Destination)
# We use the absolute path to your PyCharm project folder
PROJECT_DIR = "/Users/home/PycharmProjects/LBW_app"
LOCAL_TRIGGER = os.path.join(PROJECT_DIR, "api_trigger.json")


def run_trigger():
    if not os.path.exists(SIM_PATH):
        print(f"❌ Simulator JSON not found at: {SIM_PATH}")
        return

    with open(SIM_PATH, 'r') as f:
        data = json.load(f)

    # Correct the filename casing as we discussed
    data['video_file'] = "IMG_6963.MOV"

    # Write the file to the PyCharm folder
    with open(LOCAL_TRIGGER, 'w') as f:
        json.dump(data, f)

    print(f"🚀 Data pushed to: {LOCAL_TRIGGER}")
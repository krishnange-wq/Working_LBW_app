# main.py
import numpy as np
import cv2


# 1. Import your 4 separate module files
import stump_finder
import pitch_finder
import tracker
import smoother
import physics
import decision
f_verdict=""
def run_mobile_backend(video,corners):
    print("🚀 Booting Modular DRS System...")

    # --- INPUTS ---
    # Ensure this stays lowercase .mov


    # --- THE BUCKET BRIGADE ---

    # Stage 1: Detector finds the stumps
    print("⚙️ Stage 1: Detecting Stumps...")
    # ==========================================
    # THE FIX: Grab the actual image first
    # ==========================================
    cap = cv2.VideoCapture(video)
    ret, frame_img = cap.read()
    cap.release()
    OFF_STUMP_X, LEG_STUMP_X, STUMP_HEIGHT, STUMP_BASE = stump_finder.find_stumps_overlay(frame_img, corners)
    LEG_STUMP_X = 1114
    print(str(OFF_STUMP_X),str(LEG_STUMP_X))
    # Stage 2: Pitch_finder uses the stumps to find the pitch of the ball
    BOUNCE_X, BOUNCE_Y, BOUNCE_FRAME = pitch_finder.find_pitch(video,corners, OFF_STUMP_X,LEG_STUMP_X,STUMP_HEIGHT,STUMP_BASE)
    # Stage 3: Tracker finds the ball's path
    path_data  = tracker.track_ball(video,OFF_STUMP_X,LEG_STUMP_X,STUMP_HEIGHT,STUMP_BASE,BOUNCE_X,BOUNCE_Y,BOUNCE_FRAME)
    # Stage 4: Smoother smooths the tracker to make it more accurate
    smoothed_list = smoother.apply_dual_threshold_smoothing(path_data, same_dir_limit=10, opposing_limit=0)
    IMPACT_X, IMPACT_Y = smoothed_list[-1]
    print(IMPACT_X,IMPACT_Y)
    # Stage 3: Physics takes the raw coordinates and outputs the full parabola
    WICKET_X, WICKET_Y, future_points = physics.ballPhysics(video,smoothed_list,OFF_STUMP_X, LEG_STUMP_X, STUMP_HEIGHT, STUMP_BASE)
    print(future_points)
    # Stage 4: Decision takes the parabola, stumps, and corners to make a ruling
    BOUNCE_VERDICT, BOUNCE_OUTCHANCE, IMPACT_VERDICT, IMPACT_OUTCHANCE, WICKETS_VERDICT, WICKETS_OUTCHANCE = decision.MakeDecision(OFF_STUMP_X,LEG_STUMP_X,STUMP_HEIGHT,BOUNCE_X,WICKET_X,WICKET_Y,48,52,smoothed_list)
    print(BOUNCE_VERDICT,IMPACT_VERDICT,WICKETS_VERDICT)
    print(BOUNCE_OUTCHANCE, IMPACT_OUTCHANCE, WICKETS_OUTCHANCE)
    print(STUMP_BASE)

    # Clean strings to be safe
    B_V = str(BOUNCE_VERDICT).upper()
    I_V = str(IMPACT_VERDICT).upper()
    W_V = str(WICKETS_VERDICT).upper()

    # DEBUG: If this prints, we know the code is running
    print("Checking Verdict Logic...")
    f_verdict = "OUT"
    if int(WICKETS_OUTCHANCE)<40:
        f_verdict = "NOT OUT (Missing Stumps)"
        print("5")
    elif int(BOUNCE_OUTCHANCE)<40:
        f_verdict = "NOT OUT (Pitched Outside Leg)"
        print("1")
    elif int(IMPACT_OUTCHANCE)<40:
        f_verdict = "NOT OUT (Impact Outside Off)"
        print("3")
    elif 40<int(WICKETS_OUTCHANCE)<60:
        f_verdict = "UMPIRE'S CALL (Wickets)"
        print("6")
    elif 40<int(WICKETS_OUTCHANCE)<60:
        f_verdict = "UMPIRE'S CALL (Impact)"
        print("4")
    elif 40<int(BOUNCE_OUTCHANCE)<60:
        # Per your instruction: Pitching UC only on leg side
        f_verdict = "UMPIRE'S CALL (Pitching)"
        print("2")


    print(f"VERDICT: {f_verdict}")

    # --- 3. The Gigantic Dictionary ---
    result_data = {
        "final_DRS_verdict": f_verdict,

        "metadata": {
            "status": "success",
            "stump_geometry": {
                "off_x": float(OFF_STUMP_X),
                "leg_x": float(LEG_STUMP_X),
                "stump_base": float(STUMP_BASE),
                "stump_height": float(STUMP_HEIGHT)
            }
        },

        "path_data": {
            "tracked_points": [[float(x), float(y)] for x, y in smoothed_list],
            "future_points": [[float(x), float(y)] for x, y in future_points]
        },

        "stages": {
            "pitching": {
                "verdict": BOUNCE_VERDICT,
                "confidence": float(BOUNCE_OUTCHANCE),
                "x": float(BOUNCE_X), "y": float(BOUNCE_Y)
            },
            "impact": {
                "verdict": IMPACT_VERDICT,
                "confidence": float(IMPACT_OUTCHANCE),
                "x": float(IMPACT_X), "y": float(IMPACT_Y)
            },
            "wickets": {
                "verdict": WICKETS_VERDICT,
                "confidence": float(WICKETS_OUTCHANCE),
                "x": float(WICKET_X), "y": float(WICKET_Y)
            }
        }
    }
    final_verdict = f_verdict
    for key, value in result_data.items():
        print(f"Key: {key} | Type: {type(value)}")
    print(result_data)
    return result_data

# if __name__ == "__main__":
#     run_mobile_backend("/Users/home/PycharmProjects/LBW_app/IMG_6193.mov",np.float32([[906, 1577], [1267, 1572], [2112, 2374], [85, 2406]]))

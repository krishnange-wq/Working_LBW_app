import cv2
import numpy as np
def find_first_frame(VIDEO_PATH):
    # 1. RELOAD THE ACTUAL VIDEO FRAME
    # Replace 'video_path' with your actual file name if different
    cap = cv2.VideoCapture(VIDEO_PATH)
    ret, real_frame = cap.read()
    cap.release()

    if not ret:
        print("❌ Error: Could not read video. Please check 'video_path'.")
    else:
        print("✅ Video Frame Loaded Successfully.")

# 2. DEFINE THE CLEAN MARKER FUNCTION
def find_stumps_overlay(frame_img, pitch_corners, hand="RH"):
    # A. GEOMETRIC ANCHOR (Bowling Crease)
    res =5

    tl = np.round(pitch_corners[0]/res) *res
    tr = np.round(pitch_corners[1]/res) *res
    print(str(tl),str(tr))

    crease_mid_x = int((tl[0] + tr[0]) / 2)
    crease_y = int((tl[1] + tr[1]) / 2)
    pitch_width_px = np.linalg.norm(tl - tr)

    # B. SEARCH BOX (25% Width, 40% Height Upwards)
    box_w = int(pitch_width_px * 0.25)
    box_h = int(pitch_width_px * 0.28)

    x1 = max(0, crease_mid_x - box_w // 2)
    x2 = min(frame_img.shape[1], crease_mid_x + box_w // 2)
    y1 = max(0, crease_y - box_h)
    y2 = crease_y



    roi = frame_img[y1:y2, x1:x2]

    # C. DETECT STUMPS (Vertical Sobel)
    if roi.size == 0: return x1, x2, y1, y2

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    sobel = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    col_sums = np.sum(np.absolute(sobel), axis=0)

    threshold = np.max(col_sums) * 0.8
    valid_cols = np.where(col_sums > threshold)[0]

    if len(valid_cols) == 0:
        # Fallback Center
        stump_l = x1 + int(box_w * 0.45)
        stump_r = x1 + int(box_w * 0.55)
        stump_t = y1
    else:
        stump_l = x1 + valid_cols[0]
        stump_r = x1 + valid_cols[-1]

        # Scan Rows for Top
        row_sums = np.sum(np.absolute(sobel[:, valid_cols[0]:valid_cols[-1]]), axis=1)
        valid_rows = np.where(row_sums > (np.max(row_sums) * 0.2))[0]
        stump_t = y1 + valid_rows[0] if len(valid_rows) > 0 else y1

    stump_b = y2

    # D. DRAW MARKERS ON COPY OF REAL FRAME
    preview = frame_img.copy()

    if hand == "RH":
        pt_top_off = (int(stump_l), int(stump_t))
        pt_bot_leg = (int(stump_r), int(stump_b))
    else:
        pt_top_off = (int(stump_r), int(stump_t))
        pt_bot_leg = (int(stump_l), int(stump_b))

    # Red Cross (Top Off)
    #cv2.drawMarker(preview, pt_top_off, (0, 0, 255), cv2.MARKER_CROSS, 25, 2)
    # Blue Cross (Bottom Leg)
    #cv2.drawMarker(preview, pt_bot_leg, (255, 0, 0), cv2.MARKER_TILTED_CROSS, 25, 2)

    print(stump_l, stump_r, stump_t, stump_b)
    return stump_l, stump_r, stump_t, stump_b

# 3. RUN ON THE REAL FRAME
# if ret:
#     s_l, s_r, s_t, s_b = find_stumps_overlay(real_frame, PITCH_CORNERS, hand="RH")
#
#     # Update Globals
#     OFF_STUMP_X = s_l
#     LEG_STUMP_X = 1114
#     STUMP_HEIGHT = s_t
#     STUMP_BASE = PITCH_CORNERS[0][1]
#     STUMP_X_DIST = LEG_STUMP_X-OFF_STUMP_X
#     STUMP_Y_DIST = STUMP_BASE-STUMP_HEIGHT
#     print(str(OFF_STUMP_X))
#     print(str(LEG_STUMP_X))
#     print(str(STUMP_X_DIST))
#     print(str(STUMP_Y_DIST))

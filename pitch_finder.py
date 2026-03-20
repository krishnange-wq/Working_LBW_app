import cv2
import numpy as np

def find_pitch(VIDEO_PATH, PITCH_CORNERS,OFF_STUMP_X,LEG_STUMP_X,STUMP_HEIGHT,STUMP_BASE):
    # --- 1. PASTE YOUR TUNER VALUES HERE ---
    BOX_CENTER_X = 0.43
    BOX_CENTER_Y = 0.02
    BOX_WIDTH = 0.43
    BOX_HEIGHT = 0.06
    # --- 2. CONFIGURATION ---
    VIDEO_PATH = VIDEO_PATH
    PITCH_CORNERS = PITCH_CORNERS
    print(PITCH_CORNERS)


    OFF_STUMP_X = OFF_STUMP_X
    STUMP_HEIGHT = STUMP_HEIGHT

    LEG_STUMP_X = LEG_STUMP_X
    STUMP_BASE = STUMP_BASE

    PITCH_END_Y = PITCH_CORNERS[0][1]
    STUMP_X_DIST=LEG_STUMP_X-OFF_STUMP_X
    STUMP_Y_DIST=STUMP_BASE-STUMP_HEIGHT
    # Ball Filters
    MIN_BALL_AREA = 10/(38*103)*(STUMP_X_DIST*STUMP_Y_DIST)
    MAX_BALL_AREA = 600/(38*103)*(STUMP_X_DIST*STUMP_Y_DIST)

    # --- 3. CALCULATE THE BOX PIXEL COORDINATES ---
    # Origin = Top Left
    origin = PITCH_CORNERS[0]
    origin_x, origin_y = origin

    # Master Dimensions (Distance to TR and BL)
    master_w = np.linalg.norm(PITCH_CORNERS[1] - PITCH_CORNERS[0])
    master_h = np.linalg.norm(PITCH_CORNERS[3] - PITCH_CORNERS[0])

    # Calculate Box in Pixels
    center_x_px = origin_x + (master_w * BOX_CENTER_X)
    center_y_px = origin_y + (master_h * BOX_CENTER_Y)
    width_px    = master_w * BOX_WIDTH
    height_px   = master_h * BOX_HEIGHT

    # Coordinates for OpenCV (Top-Left of the box)
    box_x1 = int(center_x_px - (width_px / 2))
    box_y1 = int(center_y_px - (height_px / 2))
    box_x2 = int(center_x_px + (width_px / 2))
    box_y2 = int(center_y_px + (height_px / 2))

    print(f"📦 SEARCH BOX CALCULATED:")
    print(f"   X: {box_x1} to {box_x2}")
    print(f"   Y: {box_y1} to {box_y2}")

    # --- 4. THE SCANNER ---
    try:
        cap = cv2.VideoCapture(VIDEO_PATH)
        fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)

        record_y = 0
        best_pitch_coords = None
        best_frame_data = None

        print(f"🔎 SCANNING: Searching strictly inside your Cyan Box...")

        frame_count = 0

        while True:
            ret, frame = cap.read()
            frame_count+=1
            if not ret: break

            # A. PRE-PROCESS
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            l_white = np.array([0, 0, 100])
            u_white = np.array([180, 55, 255])
            mask_white = cv2.inRange(hsv, l_white, u_white)
            motion_mask = fgbg.apply(frame)
            combined = cv2.bitwise_and(motion_mask, mask_white)

            # B. DEFINE MASK (The Simple Rectangle)
            # We create a black image and draw a white rectangle on it
            search_mask = np.zeros(frame.shape[:2], dtype=np.uint8)
            cv2.rectangle(search_mask, (box_x1, box_y1), (box_x2, box_y2), 255, -1)

            # C. APPLY MASK
            final_mask = cv2.bitwise_and(combined, combined, mask=search_mask)

            # D. FIND BALL
            contours, _ = cv2.findContours(final_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)


            for c in contours:
                area = cv2.contourArea(c)
                x, y, w, h = cv2.boundingRect(c)
                aspect = float(w) / h

                if MIN_BALL_AREA < area < MAX_BALL_AREA and 0.5 < aspect < 1.6:
                    center_y = y + h
                    center_x = int(x + w/2)

                    # Track Lowest Point (Bounce)
                    if center_y > record_y:
                        record_y = center_y
                        best_pitch_coords = (center_x, center_y)
                        best_frame_data = frame.copy()
                        BOUNCE_FRAME = frame_count-1


        cap.release()

        # --- 5. VISUALIZATION ---
        if best_frame_data is not None:
            # Draw Pink Pitch (Reference)
            cv2.polylines(best_frame_data, [PITCH_CORNERS.astype(np.int32)], True, (255, 0, 255), 2)


            # Draw Your Cyan Box
            cv2.rectangle(best_frame_data, (box_x1, box_y1), (box_x2, box_y2), (255, 255, 0), 2)

            # Draw Pitch Point
            px, py = best_pitch_coords
            cv2.drawMarker(best_frame_data, (px, py), (0, 0, 255), cv2.MARKER_CROSS, 40, 4)

            # Display
            height, width = best_frame_data.shape[:2]
            disp_h = 500
            scale = disp_h / height
            disp_w = int(width * scale)
            final_img = cv2.resize(best_frame_data, (disp_w, disp_h))


            print(f"\n✅ FOUND PITCH POINT: {best_pitch_coords}")
            print(f"   COPY THIS: PITCH_POINT = {best_pitch_coords}")
            print("bounce frame: "+str(BOUNCE_FRAME))
            BOUNCE_X,BOUNCE_Y = best_pitch_coords
            return BOUNCE_X, BOUNCE_Y, BOUNCE_FRAME
        else:
            print("❌ No ball found inside the Box.")

    except Exception as e:
        print(f"Error: {e}")
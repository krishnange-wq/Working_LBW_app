import cv2
import numpy as np

def ballPhysics(VIDEO_PATH,smoothed_list,OFF_STUMP_X, LEG_STUMP_X, STUMP_HEIGHT, STUMP_BASE):
    # ==========================================
    # 🏏 PURE PHYSICS PREDICTOR: NO MULTIPLIERS
    # ==========================================

    # 1. RELOAD
    filename = VIDEO_PATH
    cap = cv2.VideoCapture(filename)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 5)
    ret, frame = cap.read()

    if not ret:
        print(f"❌ Error: Could not load {filename}")
    else:
        # 2. CONFIGURATION
        STUMP_Y_TOP = STUMP_HEIGHT
        PITCH_END_Y = STUMP_BASE
        STUMP_Y_BASE = STUMP_BASE
        OFF_STUMP_X = OFF_STUMP_X
        LEG_STUMP_X = LEG_STUMP_X
        STUMP_Y_DIST = STUMP_BASE-STUMP_HEIGHT
        print(LEG_STUMP_X)
        GRAVITY_PIXELS = 1.2/105*STUMP_Y_DIST
        print(GRAVITY_PIXELS)
        DRAG_FACTOR = 0.985
        TILT_FACTOR = 0.05

        # 1. ALWAYS start from the original clean_list to ensure changes like 'divisor' apply
        # 2. Chain them so the output of one is the input of the next
        smoothed_list = smoothed_list
        clean_list = smoothed_list


        # 3. Explicitly update path_data so the rest of the script sees the NEW values
        path_data = smoothed_list
        pts = np.array(path_data)

        # 3. MAPPING
        h, w = frame.shape[:2]
        src_pts = np.float32([[0, STUMP_Y_TOP], [w, STUMP_Y_TOP], [w, h], [0, h]])
        dst_pts = np.float32([[0, 20.12], [3.05, 20.12], [3.05, 0.0], [0, 0.0]])
        H_matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
        num_points=len(clean_list)
        if  num_points >= 3:
            print(path_data)
            pts = np.array(path_data)

            # 4. CALCULATE PURE PHYSICS FROM TRACKING
            # Velocity (v = p_n - p_n-1)
            v2_x = float(pts[-1][0] - pts[-2][0])
            v1_x = float(pts[-2][0] - pts[-3][0])

            # Acceleration (a = v2 - v1)
            # This is the "Swing" found in your data
            acc_x = v2_x - v1_x

            # Vertical state
            curr_dy = float(pts[-1][1] - pts[-2][1])
            if curr_dy >= 0: curr_dy = -abs(curr_dy) if curr_dy != 0 else -10

            curr_dx = v2_x
            curr_x, curr_y = float(pts[-1][0]), float(pts[-1][1])
            future_points = [(int(curr_x), int(curr_y))]

            # 5. PREDICTION LOOP
            for _ in range(150):
                # Apply Horizontal Physics (Swing)
                curr_dx += acc_x
                curr_dx *= DRAG_FACTOR
                curr_x += curr_dx

                # Apply Vertical Physics (Gravity)
                curr_dy *= DRAG_FACTOR
                curr_dy += GRAVITY_PIXELS
                curr_y += curr_dy

                # Perspective Check
                p_in = np.array([[[curr_x, curr_y]]], dtype=np.float32)
                p_out = cv2.perspectiveTransform(p_in, H_matrix)
                dist_from_bowler = p_out[0][0][1]

                future_points.append((int(curr_x), int(curr_y)))

                # Tilt-Adjusted Stop
                height_px = max(0, PITCH_END_Y - curr_y)
                adjusted_target = 20.12 - ((height_px / 10.0) * TILT_FACTOR)

                if dist_from_bowler >= adjusted_target:
                    break

            # 6. DRAWING
            for i in range(1, len(path_data)):
                cv2.line(frame, (int(pts[i-1][0]), int(pts[i-1][1])),
                                (int(pts[i][0]), int(pts[i][1])), (0, 255, 255), 3)

            if len(future_points) > 1:
                for i in range(len(future_points) - 1):
                    cv2.line(frame, future_points[i], future_points[i+1], (0, 0, 255), 4)

                impact_pt = future_points[-1]
                WICKET_X,WICKET_Y=impact_pt
                print(impact_pt)
                print(LEG_STUMP_X)
                pink_col = (180, 105, 255)
                cv2.line(frame, (int(OFF_STUMP_X), int(STUMP_Y_TOP)), (int(OFF_STUMP_X), int(STUMP_Y_BASE)), pink_col, 1)
                cv2.line(frame, (int(LEG_STUMP_X), int(STUMP_Y_TOP)), (int(LEG_STUMP_X), int(STUMP_Y_BASE)), pink_col, 1)
                cv2.line(frame, (int(OFF_STUMP_X), int(STUMP_Y_TOP)), (int(LEG_STUMP_X), int(STUMP_Y_TOP)), (255, 255, 255), 2)


                is_high = impact_pt[1] < STUMP_Y_TOP
                label, col = ("MISSING (HIGH)", (0, 255, 0)) if is_high else ("HITTING", (0, 0, 255))

                cv2.circle(frame, impact_pt, 6, col, -1)
                cv2.putText(frame, label, (impact_pt[0]+20, impact_pt[1]),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, col, 3)
                return WICKET_X, WICKET_Y, future_points
        elif num_points == 2:
            # --- NEW: 1st-degree Linear Logic ---
            print("📏 Using 1st-degree (Linear) estimation")
            x_coords = np.array([p[0] for p in clean_list])
            y_coords = np.array([p[1] for p in clean_list])

            model = np.polyfit(x_coords, y_coords, 1)
            predict_func = np.poly1d(model)

            WICKET_X = int(x_coords[-1])
            WICKET_Y = int(predict_func(WICKET_X))
            future_points = [(WICKET_X, WICKET_Y)]
            return WICKET_X, WICKET_Y, future_points

        elif num_points == 1:
            # --- NEW: Static Point Logic ---
            print("📍 Using 0-degree (Static) estimation")
            WICKET_X = int(clean_list[0][0])
            WICKET_Y = STUMP_BASE
            future_points = [(WICKET_X,WICKET_Y)]
            return WICKET_X, WICKET_Y, future_points

        else:
            # Still fail if 0 points
            print("❌ 0 points found: Cannot calculate trajectory.")
            return None
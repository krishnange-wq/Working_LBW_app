import cv2
import numpy as np

def MakeDecision(OFF_STUMP_X,LEG_STUMP_X,STUMP_HEIGHT,BOUNCE_X,WICKET_X,WICKET_Y,UCMin,UCMax,smoothed_list):
    # ==========================================
    # 1. ROBUST DATA FETCHING
    # ==========================================
    # We define a helper to safely get the X-coordinate
    def get_x(val):
        if isinstance(val, (tuple, list, np.ndarray)):
            return int(val[0]) # It's a tuple (x, y), take x
        else:
            return int(val)    # It's already just x

    try:
        # Safely extract X values regardless of format
        ball_x = BOUNCE_X
        off_x  = OFF_STUMP_X
        leg_x  = LEG_STUMP_X

        print(leg_x)

        print(f"✅ DATA LOADED:")
        print(f"   Ball X: {ball_x}")
        print(f"   Off X:  {off_x}")
        print(f"   Leg X:  {leg_x}")

    except NameError:
        print("❌ ERROR: Data missing. Please run the Tracker/Calibrator first.")
        raise SystemExit

    # User Settings
    BATSMAN_HAND = "RH"  # "RH" or "LH"
    MARGIN_PX = 40       # Uncertainty Width

    # ==========================================
    # 2. THE LOGIC
    # ==========================================
    def get_pitch_verdict(ball_x, stump_off_x, stump_leg_x, hand="RH"):
        """
        Determines if the ball pitched In Line, Outside Off, or Outside Leg.

        RULES:
        1. Outside Leg = Invalid (Green)
        2. Leg Line Edge = Umpire's Call (Orange)
        3. In Line OR Outside Off = Valid (Red)
        """

        MARGIN_PX = 10 # Width of the "Umpire's Call" zone (approx half ball width)

        # 1. IDENTIFY STUMP COORDINATES
        # Assuming screen coordinates: 0 is Left, Width is Right.
        left_stump_x = min(stump_off_x, stump_leg_x)
        right_stump_x = max(stump_off_x, stump_leg_x)

        # 2. SETUP LIMITS BASED ON HAND
        if hand == "RH":
            # RH Batsman: Leg Stump is RIGHT, Off Stump is LEFT
            leg_limit = right_stump_x
            off_limit = left_stump_x

            # Calculate signed distance from Leg Stump
            # Positive = Moving towards Off Side (Valid)
            # Negative = Moving outside Leg (Invalid)
            dist_from_leg = leg_limit - ball_x

            # Check for textual label (for display purposes only)
            is_outside_off = (ball_x < off_limit)

        else: # LH Batsman
            # LH Batsman: Leg Stump is LEFT, Off Stump is RIGHT
            leg_limit = left_stump_x
            off_limit = right_stump_x

            # Positive = Moving towards Off Side (Valid)
            # Negative = Moving outside Leg (Invalid)
            dist_from_leg = ball_x - leg_limit

            # Check for textual label
            is_outside_off = (ball_x > off_limit)

        # 3. CALCULATE PROBABILITY (0 to 100 scale)
        # 0%   = Deep Outside Leg
        # 50%  = Exactly on Leg Stump Line
        # 100% = Deep In Line (or Outside Off)

        # Map the distance to a 0-100 probability
        # If dist is -MARGIN, prob becomes 0. If dist is 0, prob is 50.
        prob = 50 + (dist_from_leg / MARGIN_PX) * 50

        # Clamp to 0-100 range
        prob = max(0, min(100, prob))

        # 4. GENERATE VERDICT LABEL & COLOR
        # Note: Logic uses 48-52 buffer for UC.

        if prob < 48:
            # Clearly Outside Leg
            return "OUTSIDE LEG", prob, (0, 200, 0) # Green

        elif prob > 52:
            # Clearly Valid (In Line OR Outside Off)
            if is_outside_off:
                return "OUTSIDE OFF", prob, (255, 255, 0) # Red (Valid)
            else:
                return "IN LINE", prob, (255, 255, 0) # Red (Valid)

        else:
            # In the "Zone of Uncertainty" (48% - 52%) around Leg Stump
            return "UMPIRE'S CALL", prob, (0, 140, 255) # Orange
    # ==========================================
    # 3. VISUALIZATION
    # ==========================================

    # Run Logic
    zone, conf, color = get_pitch_verdict(ball_x, off_x, leg_x, BATSMAN_HAND)

    # Draw Dashboard
    h, w = 300, 600
    dashboard = np.zeros((h, w, 3), dtype=np.uint8)
    center = w // 2
    scale = 3.0 # High zoom to see details

    # Map Real X to Screen X
    def map_x(val_x):
        mid = (off_x + leg_x) / 2
        return int(center + (val_x - mid) * scale)

    s_off_scr = map_x(off_x)
    s_leg_scr = map_x(leg_x)
    b_x_scr   = map_x(ball_x)

    # Draw Danger Zone (Leg Side)
    if BATSMAN_HAND == "RH":
        cv2.rectangle(dashboard, (s_leg_scr, 0), (w, h), (20, 20, 50), -1)
    else:
        cv2.rectangle(dashboard, (0, 0), (s_leg_scr, h), (20, 20, 50), -1)

    # Draw Stumps
    cv2.line(dashboard, (s_off_scr, 0), (s_off_scr, h), (255,255,255), 2)
    cv2.line(dashboard, (s_leg_scr, 0), (s_leg_scr, h), (255,255,255), 2)
    cv2.putText(dashboard, "OFF", (s_off_scr-15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)
    cv2.putText(dashboard, "LEG", (s_leg_scr-15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)

    # Draw Ball
    cv2.circle(dashboard, (b_x_scr, 150), 10, color, -1)
    cv2.circle(dashboard, (b_x_scr, 150), 12, (255,255,255), 1)

    # Text Stats
    cv2.putText(dashboard, f"{zone}", (20, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.putText(dashboard, f"CONFIDENCE: {conf:.1f}%", (20, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)

    BOUNCE_VERDICT = zone
    BOUNCE_OUTCHANCE= conf

    # Umpire's Call Label logic
    if 48 <= conf <= 52 and "LEG" in zone:
        cv2.putText(dashboard, "UMPIRE'S CALL", (w-200, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)



    # ==========================================
    # 1. PASTE YOUR PAD IMPACT X
    # ==========================================
    # Where did the ball hit the pad? (X-coordinate)
    IMPACT_PAD_X  = smoothed_list[-1][0]


    # Reuse your calibrated stump positions (or paste them)
    try:
        s_off = OFF_STUMP_X
        s_leg = LEG_STUMP_X
        print(LEG_STUMP_X)
    except:
        # Fallback if you restarted the kernel
        s_off = 1083
        s_leg = 1118

    # Settings
    MARGIN_PX = 40  # Uncertainty zone width
    BATSMAN_HAND = "RH"

    # ==========================================
    # 2. IMPACT LINE LOGIC
    # ==========================================

    def analyze_impact_line(ball_x, off_x, leg_x, margin):
        # Define the "Corridor"
        left_boundary = min(off_x, leg_x)
        right_boundary = max(off_x, leg_x)

        # 1. Check strict position
        if left_boundary <= ball_x <= right_boundary:
            # INSIDE (In Line)
            # Distance to nearest edge
            dist = min(ball_x - left_boundary, right_boundary - ball_x)

            # 50% (On Line) -> 100% (Center)
            conf = min(100, 50 + (dist / margin) * 50)
            verdict = "IN LINE"
            color = (0, 255, 0) # Green

        else:
            # OUTSIDE
            dist = min(abs(ball_x - left_boundary), abs(ball_x - right_boundary))

            # 50% (On Line) -> 0% (Far Outside)
            conf = max(0, 50 - (dist / margin) * 50)

            # Verdict depends on side
            if ball_x < left_boundary:
                # Left side
                verdict = "OUTSIDE OFF" if BATSMAN_HAND == "RH" else "OUTSIDE LEG"
            else:
                # Right side
                verdict = "OUTSIDE LEG" if BATSMAN_HAND == "RH" else "OUTSIDE OFF"

            color = (0, 0, 255) # Red

        # Umpire's Call Logic (40% - 60%)
        if UCMin <= conf <= UCMax:
            verdict += " (Umpire's Call)"
            color = (0, 165, 255) # Orange

        return verdict, conf, color, left_boundary, right_boundary

    # ==========================================
    # 3. VISUALIZATION
    # ==========================================

    verdict, conf, col, l_bound, r_bound = analyze_impact_line(IMPACT_PAD_X, s_off, s_leg, MARGIN_PX)

    # Draw
    h, w = 300, 600
    dash = np.zeros((h, w, 3), dtype=np.uint8)
    center = w // 2
    scale = 3.0

    def map_x(val):
        mid = (l_bound + r_bound) / 2
        return int(center + (val - mid) * scale)

    xl = map_x(l_bound)
    xr = map_x(r_bound)
    xb = map_x(IMPACT_PAD_X)

    # Draw Zones
    cv2.rectangle(dash, (xl, 0), (xr, h), (30, 60, 30), -1) # In Line (Green tint)
    cv2.rectangle(dash, (0, 0), (xl, h), (30, 30, 50), -1)  # Left (Red tint)
    cv2.rectangle(dash, (xr, 0), (w, h), (30, 30, 50), -1)  # Right (Red tint)

    # Lines
    cv2.line(dash, (xl, 0), (xl, h), (255,255,255), 2)
    cv2.line(dash, (xr, 0), (xr, h), (255,255,255), 2)

    # Labels
    lab_l = "OFF" if BATSMAN_HAND == "RH" else "LEG"
    lab_r = "LEG" if BATSMAN_HAND == "RH" else "OFF"
    cv2.putText(dash, lab_l, (xl-40, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)
    cv2.putText(dash, lab_r, (xr+10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)

    # Ball
    cv2.circle(dash, (xb, 150), 12, col, -1)
    cv2.circle(dash, (xb, 150), 14, (255,255,255), 1)

    # Stats
    cv2.putText(dash, f"IMPACT: {verdict}", (20, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.8, col, 2)
    cv2.putText(dash, f"Confidence: {conf:.1f}%", (20, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)
    IMPACT_VERDICT=verdict
    IMPACT_OUTCHANCE = conf


    # 50% Marker
    if UCMin <= conf <= UCMax:
        cv2.putText(dash, "!!! CRITICAL EDGE !!!", (w-200, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)



    # ==========================================
    # 1. DATA INPUT (Wicket Impact)
    # ==========================================
    # These should come from your predictor loop
    WICKET_X = WICKET_X
    WICKET_Y = WICKET_Y

    # Stump Coordinates
    s_off = OFF_STUMP_X
    s_leg = LEG_STUMP_X
    s_top = STUMP_HEIGHT

    # Tuning
    MARGIN_PX = 30  # "Uncertainty" zone

    # ==========================================
    # 2. WICKET PROBABILITY LOGIC
    # ==========================================

    def analyze_wicket_hit(val, low_bound, high_bound, margin, inverse=False):
        """Calculates linear confidence for hitting a target range."""
        # If inverse is true, 'hitting' means being BELOW the bound (for Y-axis)
        if not inverse:
            # Horizontal Logic (Between Off and Leg)
            center = (low_bound + high_bound) / 2
            dist = abs(val - center)
            max_dist = abs(high_bound - low_bound) / 2

            if low_bound <= val <= high_bound:
                # Inside: 50% at edge -> 100% at center
                conf = min(100, 50 + ((max_dist - dist) / margin) * 50)
            else:
                # Outside: 50% at edge -> 0% far away
                ext_dist = min(abs(val - low_bound), abs(val - high_bound))
                conf = max(0, 50 - (ext_dist / margin) * 50)
        else:
            # Vertical Logic (Must be BELOW s_top)
            # On screen, Y increases as you go DOWN
            if val >= low_bound: # Hitting (Below bails)
                dist = val - low_bound
                conf = min(100, 50 + (dist / margin) * 50)
            else: # Missing (Above bails)
                dist = low_bound - val
                conf = max(0, 50 - (dist / margin) * 50)

        return conf

    # Calculate Line and Height confidence
    conf_x = analyze_wicket_hit(WICKET_X, s_off, s_leg, MARGIN_PX)
    conf_y = analyze_wicket_hit(WICKET_Y, s_top, None, MARGIN_PX, inverse=True)

    # Final Hitting Probability
    # If either is 0%, the total hit is 0%
    hit_prob = (conf_x / 100.0) * (conf_y / 100.0) * 100

    # ==========================================
    # 3. VERDICT & COLOR
    # ==========================================
    if hit_prob > 60:
        verdict, col = "HITTING", (0, 0, 255) # Red
    elif hit_prob > 40:
        verdict, col = "UMPIRE'S CALL", (0, 165, 255) # Orange
    else:
        # Determine why it missed
        if conf_x <= 40:
            verdict = "MISSING (LINE)"
        else:
            verdict = "MISSING (HIGH)"
        col = (0, 255, 0) # Green

    # ==========================================
    # 4. VISUALIZATION (Dashboard)
    # ==========================================
    dash = np.zeros((300, 600, 3), dtype=np.uint8)

    # Text Info
    cv2.putText(dash, f"WICKET VERDICT: {verdict}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, col, 2)
    cv2.putText(dash, f"Overall Probability: {hit_prob:.1f}%", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)
    WICKETS_VERDICT=verdict
    WICKETS_OUTCHANCE = hit_prob


    # Progress Bars for Line and Height
    def draw_bar(img, y, label, val):
        cv2.putText(img, label, (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
        cv2.rectangle(img, (150, y-15), (450, y+5), (50,50,50), -1)
        bar_w = int(300 * (val/100))
        bar_col = (0, 255, 0) if val > 50 else (0, 0, 255)
        cv2.rectangle(img, (150, y-15), (150 + bar_w, y+5), bar_col, -1)

        cv2.putText(img, f"{val:.1f}%", (460, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

    draw_bar(dash, 150, "LINE (X)", conf_x)
    draw_bar(dash, 200, "HEIGHT (Y)", conf_y)
    return BOUNCE_VERDICT, BOUNCE_OUTCHANCE, IMPACT_VERDICT, IMPACT_OUTCHANCE, WICKETS_VERDICT,WICKETS_OUTCHANCE




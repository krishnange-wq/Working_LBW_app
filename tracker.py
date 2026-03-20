

from re import I
import cv2
import numpy as np
import os
from moviepy.video.io.VideoFileClip import VideoFileClip
from scipy.io import wavfile


def track_ball(video_path, OFF_STUMP_X,LEG_STUMP_X,STUMP_HEIGHT,STUMP_BASE,BOUNCE_X,BOUNCE_Y,BOUNCE_FRAME):
    # --- 1. SETTINGS ---
    VIDEO_PATH = video_path
    START_FRAME = BOUNCE_FRAME
    PITCH_X, PITCH_Y = BOUNCE_X,BOUNCE_Y

    STUMP_X_DIST=LEG_STUMP_X-OFF_STUMP_X
    STUMP_X_DIST = STUMP_X_DIST
    STUMP_Y_DIST=STUMP_BASE-STUMP_HEIGHT
    STUMP_Y_DIST= STUMP_Y_DIST

    # AUDIO SYNC SETTINGS
    # -2 corrects for the speed of sound delay (Sound arrives ~2 frames after impact)
    AUDIO_OFFSET_FRAMES = -2
    AUDIO_THRESHOLD = 0.05   # Sensitivity (0.0 to 1.0)

    # STUMP COORDINATES
    old_off_x = OFF_STUMP_X
    print(OFF_STUMP_X)
    old_leg_x = LEG_STUMP_X
    print(LEG_STUMP_X)
    STUMP_HEIGHT = STUMP_HEIGHT
    print(STUMP_HEIGHT)

    # SEARCH LIMITS
    SEARCH_UP   = int(75/105 * STUMP_Y_DIST)
    print(SEARCH_UP)
    SEARCH_DOWN = int(5/105 *STUMP_Y_DIST)
    MAX_RIGHT, MIN_RIGHT = int(13/29*STUMP_X_DIST),int(2/29*STUMP_X_DIST)
    MIN_LEFT, MAX_LEFT   = int(2/29*STUMP_X_DIST), int(13/29*STUMP_X_DIST)



    IMPACT_FRAME=0
    # --- 2. AUDIO LOCK FUNCTION ---
    def get_audio_lock_frame(video_path):
        print("🎧 Scanning Audio for Impact...")
        try:
            # Get FPS
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            cap.release()

            # Extract Audio
            clip = VideoFileClip(video_path)
            clip.audio.write_audiofile("temp_audio.wav")

            # Analyze
            # 1. Load the audio
            # Note: scipy returns the sample rate (sr) first, then the audio data (y)
            sr, y = wavfile.read("temp_audio.wav")

            # Handle stereo audio (if the .mov file has left/right channels, we combine them)
            y = y.astype(np.float32)
            if len(y.shape) > 1:
                y = np.mean(y, axis=1)

            # 2. Normalize volume (Exactly like your Colab code)
            y_norm = y / np.max(np.abs(y))

            # 3. Calculate RMS Volume Spikes (The Numpy Way)
            frame_length = 1024
            hop_length = 256

            # We slide a window over the audio and calculate the volume for each chunk
            num_frames = 1 + (len(y_norm) - frame_length) // hop_length
            rms = np.array([
                np.sqrt(np.mean(y_norm[i * hop_length: i * hop_length + frame_length] ** 2))
                for i in range(num_frames)
            ])

            # 4. Convert frames to time (Exactly like your Colab code)
            times = np.arange(len(rms)) * hop_length / sr

            # Scan Backwards to find the "Snick"
            for i in range(len(rms) - 1, -1, -1):
                if rms[i] > AUDIO_THRESHOLD:
                    peak_time = times[i]
                    abs_frame = int(peak_time * fps)
                    lock_frame = abs_frame + AUDIO_OFFSET_FRAMES
                    print(f"🔒 AUDIO LOCK FOUND: Frame {lock_frame} (Time: {peak_time:.2f}s)")
                    return lock_frame
                    IMPACT_FRAME = lock_frame

            print("⚠️ No loud sound found. Tracking will run to end.")
            return 99999
        except Exception as e:
            print(f"❌ Audio Error: {e}")
            return 99999

    # --- 3. INITIALIZATION ---
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print("❌ Error: Could not open video file.")
    else:
        # A. Get the Stop Frame
        LOCK_FRAME_ABS = get_audio_lock_frame(VIDEO_PATH)

        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps    = cap.get(cv2.CAP_PROP_FPS)

        # Preview
        cap.set(cv2.CAP_PROP_POS_FRAMES, START_FRAME)
        ret, preview_img = cap.read()
        if ret:
            cv2.line(preview_img, (OFF_STUMP_X, 0), (OFF_STUMP_X, height), (255, 0, 255), 5)
            cv2.line(preview_img, (LEG_STUMP_X, 0), (LEG_STUMP_X, height), (255, 0, 255), 5)
            print("📸 Preview displayed. Starting render...")

        # Output Setup
        # OUTPUT_FILE = "hawkeye_audio_locked.avi"
        # fourcc = cv2.VideoWriter_fourcc(*'MJPG')  # Line 119 stays exactly the same
        # out = cv2.VideoWriter("tracked_output.avi", fourcc, fps,
        #                       (width, height))  # Line 120 gets the new hardcoded name

        last_x, last_y = np.float64(PITCH_X), np.float64(PITCH_Y)
        path_data = [(last_x, last_y)]
        frame_count = 0

        try:
            cap.set(cv2.CAP_PROP_POS_FRAMES, START_FRAME)

            while True:
                ret, frame = cap.read()
                if not ret or frame_count > 150:
                    break

                # Calculate Absolute Frame Number
                current_abs_frame = START_FRAME + frame_count
                frame_count += 1
                if frame_count % 10 == 0:
                    print(f"DEBUG: Processing frame {frame_count} at 4K...", flush=True)
                display_frame = frame.copy()

                # --- THE MAGIC LOCK ---
                # Check if we have hit the audio frame yet
                is_before_impact = current_abs_frame <= LOCK_FRAME_ABS

                if is_before_impact:
                    # === TRACKING ACTIVE ===
                    # Dynamic Horizontal Search
                    SR = int(np.interp(last_x, [OFF_STUMP_X-10, LEG_STUMP_X], [MAX_RIGHT, MIN_RIGHT]))
                    SL = int(np.interp(last_x, [OFF_STUMP_X+0, LEG_STUMP_X-0], [MIN_LEFT, MAX_LEFT]))

                    x1, x2 = max(0, int(last_x) - SL), min(width, int(last_x) + SR)
                    y1, y2 = max(0, int(last_y) - (SEARCH_UP)), min(height, int(last_y) + SEARCH_DOWN)
                    # Calculate the raw value
                    if BOUNCE_X < OFF_STUMP_X+(STUMP_X_DIST/100000):
                        raw_k = (7 / 29) * STUMP_X_DIST
                        p_two = (10/29)*STUMP_X_DIST
                    else:
                        raw_k = (5 / 29) * STUMP_X_DIST
                        print("raw k"+str(raw_k))
                        p_two  = (8.1/29)*STUMP_X_DIST


                    # Round it to the nearest ODD integer
                    k_size = int(raw_k)
                    if k_size % 2 == 0:  # If the result is even
                        k_size += 1  # Add 1 to make it odd

                    # Final safety check: ensure k_size is at least 3
                    k_size = max(3, k_size)
                    print(k_size,p_two)
                    roi = frame[y1:y2, x1:x2]
                    if roi.size > 0:
                        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                        gray = cv2.medianBlur(gray, k_size)
                        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1.2, 25,
                                                   param1=50, param2=p_two, minRadius=10, maxRadius=45)

                        if circles is not None:
                            best_c = None
                            min_score = float('inf')
                            for c in circles[0, :]:
                                gx, gy = c[0] + x1, c[1] + y1
                                dx = gx - last_x
                                score = abs(gy - last_y)
                                if last_x > LEG_STUMP_X and dx > 5: score += 100
                                elif last_x < OFF_STUMP_X and dx < -5: score += 100
                                else: score += abs(dx - 10)

                                if score < min_score:
                                    min_score = score
                                    best_c = (gx, gy)

                            if best_c:
                                last_x, last_y = best_c
                                if last_y >= STUMP_HEIGHT+10:
                                  path_data.append((last_x, last_y))
                                print(last_y)

                # --- DRAWING ---
                # 1. Stumps & Box
                cv2.line(display_frame, (OFF_STUMP_X, 0), (OFF_STUMP_X, height), (255, 0, 255), 3)
                cv2.line(display_frame, (LEG_STUMP_X, 0), (LEG_STUMP_X, height), (255, 0, 255), 3)

                # Only draw search box if still tracking
                if is_before_impact:
                    # Recalculate box for display (since we might have skipped it above)
                    # (Re-using variables from above or calculating if needed, keeping it simple here)
                     cv2.rectangle(display_frame, (int(last_x)-10, int(last_y)-10), (int(last_x)+10, int(last_y)+10), (255,0,0), 1)

                # 2. Green Line
                if len(path_data) > 1:
                    pts = np.array(path_data, np.int32)
                    cv2.polylines(display_frame, [pts], False, (0, 255, 0), 4)
                    print(pts)

                # 3. IMPACT MARKER (If we passed the lock frame)
                if not is_before_impact:
                    # Use the LAST KNOWN coordinates
                    ix, iy = path_data[-1]
                    IMPACT_X = int(ix)
                    IMPACT_Y = int(iy)
                    cv2.circle(display_frame, (int(ix), int(iy)), 12, (0, 0, 255), -1) # Red Dot
                    cv2.circle(display_frame, (int(ix), int(iy)), 25, (0, 0, 255), 3)  # Ring
                    cv2.putText(display_frame, "IMPACT", (int(ix)+30, int(iy)),
                               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

                # out.write(display_frame)
                if frame_count % 10 == 0:
                    print(f"Processing Frame {frame_count}... (Abs: {current_abs_frame})", end='\r')

        except Exception as e:
            print(f"\n⚠️ Error: {e}")
        finally:
            # out.release()
            cap.release()
            print(f"\n✅ Video Processing Complete.")
            OFF_STUMP_X = old_off_x
            print("off:"+str(OFF_STUMP_X))
            LEG_STUMP_X = old_leg_x
            print("leg:"+str(LEG_STUMP_X))
            return path_data
            # if os.path.exists(OUTPUT_FILE):
            #     files.download(OUTPUT_FILE)
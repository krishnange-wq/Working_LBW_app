import numpy as np

def apply_dual_threshold_smoothing(path_data, same_dir_limit=30, opposing_limit=10):
    """
    Applies asymmetric damping based on direction of movement.

    Args:
        path_data: List of (x, y) coordinates.
        same_dir_limit: Max allowed acceleration in the direction of travel.
        opposing_limit: Max allowed acceleration against the direction of travel.
    """
    if not path_data or len(path_data) < 3:
        return path_data

    # Start with first two points fixed to establish initial velocity
    smoothed_path = [path_data[0], path_data[1]]

    # Initial Velocity (X only)
    prev_dx = path_data[1][0] - path_data[0][0]

    for i in range(2, len(path_data)):
        raw_pt = path_data[i]

        # 1. Calc Velocity relative to the last smoothed point
        raw_dx = raw_pt[0] - smoothed_path[-1][0]
        raw_y = raw_pt[1]

        # 2. Calc Acceleration (The Jerk)
        accel_x = raw_dx - prev_dx

        final_dx = raw_dx

        # 3. SELECT THRESHOLD BASED ON DIRECTION
        # Check if acceleration is in the same direction as current velocity
        is_same_direction = (accel_x * prev_dx) >= 0
        active_limit = same_dir_limit if is_same_direction else opposing_limit
        dampened_accel = 0.5 if is_same_direction else 0.2

        # 4. APPLY DAMPING
        if abs(accel_x) > active_limit:
            # We halve the jerk (the acceleration component)
            #dampened_accel = accel_x * 0.5
            print(dampened_accel)
            final_dx = prev_dx + dampened_accel

        # 5. UPDATE
        # Create new coordinate (Keeping X as float, preserving Raw Y)
        new_x = smoothed_path[-1][0] + final_dx
        new_y = raw_y

        smoothed_path.append((new_x, new_y))

        # Update state for next loop
        prev_dx = final_dx

    return smoothed_path
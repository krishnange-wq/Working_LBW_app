import numpy as np

def calculate_linear_safety_anchors(points):
    """
    Takes in a numpy array of points (post-bounce segment).
    Calculates:
    B: The first point (Bounce).
    K: The midpoint of all points after B (Trend).
    L: A corrected boundary point where L.x is the last tracked X,
       but L.y is calculated based on the slope of B -> K.

    Returns: A numpy array (float32) of [B, K, L].
    """
    # 1. B (Bounce Point) - Origin of the rail
    B = points[0]

    # 2. K (Trend Point) - Centroid of the flight cluster
    K = np.mean(points[1:], axis=0)

    # Calculate the Slope (m) from B to K
    dx = K[0] - B[0]
    dy = K[1] - B[1]

    # Handle vertical/static edge cases with a tiny epsilon
    m = dy / dx if abs(dx) > 1e-6 else 0.0

    # 3. L (Corrected Boundary)
    # Use the actual last X-coordinate (L.x)
    L_x = points[-1][0]

    # Force L.y to sit exactly on the B -> K line at L.x
    # Formula: y = y1 + m * (x - x1)
    L_y = B[1] + m * (L_x - B[0])

    L = np.array([L_x, L_y], dtype=np.float32)

    # Return unified float32 array [[Bx, By], [Kx, Ky], [Lx, Ly]]
    return np.array([B, K, L], dtype=np.float32)


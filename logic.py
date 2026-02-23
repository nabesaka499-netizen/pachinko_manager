
def get_table_revenue(spins):
    """
    Returns the Total Revenue (Yen) at specific spins to Ceiling, 
    derived from the user's 'Base 20 / 27 Exchange' table.
    
    Data Points (Derived from EV + Cost):
    S=200: EV=5853,  Cost=9250,  Rev=15103
    S=300: EV=4483,  Cost=13875, Rev=18358
    S=400: EV=3482,  Cost=18500, Rev=21982
    S=500: EV=2750,  Cost=23125, Rev=25875
    S=600: EV=2215,  Cost=27750, Rev=29965
    """
    # Sorted points (Spins, Revenue)
    points = [
        (200, 15103),
        (300, 18358),
        (400, 21982),
        (500, 25875),
        (600, 29965)
    ]
    
    # Extrapolation / Interpolation
    s = spins
    
    # If below 200, assume linear trend from 200-300 (or steeper?)
    # Yuutime logic suggests revenue hits a floor (Jackpot value). 
    # But closer to ceiling = higher probability of hitting ceiling outcome.
    # We will use linear extrapolation from nearest segment.
    
    if s <= 200:
        p1, p2 = points[0], points[1]
    elif s >= 600:
        p1, p2 = points[-2], points[-1]
    else:
        # Find segment
        for i in range(len(points) - 1):
            if points[i][0] <= s <= points[i+1][0]:
                p1, p2 = points[i], points[i+1]
                break
    
    # Linear Interpolation
    # y = y1 + (x - x1) * (y2 - y1) / (x2 - x1)
    slope = (p2[1] - p1[1]) / (p2[0] - p1[0])
    val = p1[1] + (s - p1[0]) * slope
    
    return val
def calculate_expectation(base, remaining_spins, exchange_rate=27.0, actual_10r_out=1400.0, model_type="大海4SP"):
    """
    Calculates EV using model-specific anchor points.
    model_type: "大海4SP" or "大海5SP"
    """
    s = float(remaining_spins)
    if s <= 0: return 0
    if base <= 0: base = 1.0
    
    # 1. Machine Specific Parameters
    if model_type == "大海5SP":
        p = 1.0 / 319.6  # Sea Story 5 SP
        std_out = 1400.0
        border_points = [
            (100, 6.09),
            (200, 9.91),
            (300, 12.41),
            (400, 14.12),
            (500, 15.30),
            (600, 16.15)
        ]
    else:
        # Default: 大海4SP
        p = 1.0 / 319.7
        std_out = 1400.0
        border_points = [
            (100, 6.64),
            (200, 10.64),
            (300, 13.20),
            (400, 14.91),
            (500, 16.09),
            (600, 16.90)
        ]
    
    # Interpolate Border at std_out
    if s <= 100:
        p1, p2 = border_points[0], border_points[1]
    elif s >= 600:
        p1, p2 = border_points[-2], border_points[-1]
    else:
        p1, p2 = border_points[0], border_points[1]
        for i in range(len(border_points) - 1):
            if border_points[i][0] <= s <= border_points[i+1][0]:
                p1, p2 = border_points[i], border_points[i+1]
                break
    
    slope = (p2[1] - p1[1]) / (p2[0] - p1[0])
    border_std = p1[1] + (s - p1[0]) * slope
    border_std = max(2.0, min(19.0, border_std))
    
    # 2. Adjust Border for User's actual_10r_out
    border_adj = border_std * (std_out / actual_10r_out)
    
    # 3. Expected Spins (accounts for hitting before S)
    prob_no_hit = (1.0 - p) ** s
    expected_spins = (1.0 - prob_no_hit) / p
    
    # 4. EV Calculation
    rev_balls = (expected_spins / border_adj) * 250.0
    inv_balls = (expected_spins / base) * 250.0
    
    profit_balls = rev_balls - inv_balls
    
    # 5. Convert to Yen
    yen_per_ball = 100.0 / exchange_rate
    ev_yen = profit_balls * yen_per_ball

    # 6. Exploit: Add provided gain in Yen for 大海5SP
    if model_type == "大海5SP":
        # --- A. Remaining Ball Gain (from previous instructions) ---
        # Data points provided by user (remaining_spins, gain_yen)
        gain_points = [
            (100, 77.5),
            (200, 70.5),
            (300, 65.5),
            (400, 61.8),
            (500, 59.1),
            (600, 57.1)
        ]
        
        target_s = s
        if target_s <= 100:
            g_yen = gain_points[0][1]
        elif target_s >= 600:
            g_yen = gain_points[-1][1]
        else:
            # Linear Interpolation
            p1, p2 = gain_points[0], gain_points[1]
            for i in range(len(gain_points) - 1):
                if gain_points[i][0] <= target_s <= gain_points[i+1][0]:
                    p1, p2 = gain_points[i], gain_points[i+1]
                    break
            g_slope = (p2[1] - p1[1]) / (p2[0] - p1[0])
            g_yen = p1[1] + (target_s - p1[0]) * g_slope
            
        ev_yen += g_yen

        # --- B. Electric Support Support (D) and Yu-Time Gain ---
        # Theoretical Attacker Payout = 1389.0
        # Avg Support Spins per hit = 85.0
        # D = (Actual - Theoretical) / 85.0
        d_rate = (actual_10r_out - 1389.0) / 85.0
        
        # Yu-Time duration = 350 spins
        yu_gain_balls = 350.0 * d_rate
        
        # Probability of reaching Yu-Time = prob_no_hit (calculated at step 3)
        ev_yu_yen = (prob_no_hit * yu_gain_balls) * yen_per_ball
        
        ev_yen += ev_yu_yen
    
    return int(ev_yen)

def get_estimated_time(remaining_spins, model_type="大海4SP"):
    """
    Returns estimated total time (minutes) to finish the session, 
    based on user-provided simulation data.
    """
    if model_type == "大海5SP":
        # Refined measured data for Sea Story 5 SP
        points = [
            (100, 35.0),
            (200, 45.0),
            (300, 53.0),
            (400, 59.0),
            (450, 61.0),
            (500, 63.0)
        ]
    else:
        # Default: 大海4SP
        points = [
            (100, 46.0),
            (200, 57.0),
            (300, 64.0),
            (400, 70.0),
            (500, 74.0)
        ]
    
    s = float(remaining_spins)
    
    if s <= 100:
        p1, p2 = points[0], points[1]
    elif s >= 500:
        p1, p2 = points[-2], points[-1]
    else:
        p1, p2 = points[0], points[1]
        for i in range(len(points) - 1):
            if points[i][0] <= s <= points[i+1][0]:
                p1, p2 = points[i], points[i+1]
                break
    
    slope = (p2[1] - p1[1]) / (p2[0] - p1[0])
    est_min = p1[1] + (s - p1[0]) * slope
    
    # Floor at 30 mins (avg loop duration if s=0)
    return max(30.0, est_min)

def get_expected_hits(remaining_spins, model_type="大海4SP"):
    """
    Returns estimated total hit count (Ren-chan) for the session,
    based on user-provided simulation data.
    """
    if model_type == "大海5SP":
        # Refined points from provided reference images
        points = [
            (100, 2.50),
            (200, 2.70),
            (300, 2.80),
            (400, 2.90),
            (450, 2.90),
            (500, 2.90)
        ]
        s = float(remaining_spins)
        if s <= 100:
            p1, p2 = points[0], points[1]
        elif s >= 500:
            p1, p2 = points[-2], points[-1]
        else:
            p1, p2 = points[0], points[1]
            for i in range(len(points) - 1):
                if points[i][0] <= s <= points[i+1][0]:
                    p1, p2 = points[i], points[i+1]
                    break
        slope = (p2[1] - p1[1]) / (p2[0] - p1[0])
        return p1[1] + (s - p1[0]) * slope
    else:
        # Probabilistic model for other models (e.g. 大海4SP)
        p = 1.0 / 319.7
        avg_ren = 2.85
        yu_duration = 1200
        
        s = float(remaining_spins)
        p_hit_before = 1.0 - (1.0 - p)**s
        p_reach_yu = (1.0 - p)**s
        p_hit_during_yu = 1.0 - (1.0 - p)**yu_duration
        p_total_hit = p_hit_before + (p_reach_yu * p_hit_during_yu)
        return p_total_hit * avg_ren

def get_base_curve(base, exchange_rate, machine_out, model_type="大海4SP"):
    points = []
    for b in [x * 0.5 for x in range(30, 51)]: # 15 to 25
        val = calculate_expectation(b, 400, exchange_rate, machine_out, model_type)
        points.append((b, val))
    return points

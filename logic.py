
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

def calculate_expectation(base, remaining_spins, exchange_rate=27.0, actual_10r_out=1400.0, is_tech_intervened=False):
    """
    Calculates EV using a reliable model derived from '大海4SP' data points.
    Anchor Points (Remaining Spins S, Border B @ 1400 out):
    S=600, B=16.90
    S=500, B=16.09
    S=400, B=14.91
    S=300, B=13.20
    S=200, B=10.64
    S=100, B=6.64
    """
    s = float(remaining_spins)
    if s <= 0: return 0
    if base <= 0: base = 1.0
    
    # 1. Machine Constant (Sea Story 4 SP / 大海4SP Middle)
    p = 1.0 / 319.7
    
    # 2. Anchor Points for Border (at 1400 balls)
    border_points = [
        (100, 6.64),
        (200, 10.64),
        (300, 13.20),
        (400, 14.91),
        (500, 16.09),
        (600, 16.90)
    ]
    
    # Interpolate Border at 1400
    if s <= 100:
        # Extrapolate downwards (riskier, but 0 spins = 0 border is not right)
        # Use slope from 100-200
        p1, p2 = border_points[0], border_points[1]
    elif s >= 600:
        # Extrapolate upwards (should hit flat border ~18-19)
        p1, p2 = border_points[-2], border_points[-1]
    else:
        # Find segment
        p1, p2 = border_points[0], border_points[1] # fallback
        for i in range(len(border_points) - 1):
            if border_points[i][0] <= s <= border_points[i+1][0]:
                p1, p2 = border_points[i], border_points[i+1]
                break
    
    slope = (p2[1] - p1[1]) / (p2[0] - p1[0])
    border_1400 = p1[1] + (s - p1[0]) * slope
    
    # Border 1400 can't go below effectively 4-5 or above 20.0 (flat border for this machine)
    border_1400 = max(2.0, min(19.0, border_1400))
    
    # 3. Adjust Border for User's actual_10r_out
    # Border is inversely proportional to output
    # B_adj = B_std * (1400 / actual_out)
    border_adj = border_1400 * (1400.0 / actual_10r_out)
    
    # 4. Calculate Expected Spins (Actual spins you will perform on average)
    # E_spins = (1 - (1-p)^S) / p
    # This accounts for hitting BEFORE the remaining spins are up.
    # Use approx (1 - exp(-p*S)) / p if S is large, but exact is fine.
    prob_no_hit = (1.0 - p) ** s
    expected_spins = (1.0 - prob_no_hit) / p
    
    # 5. EV Calculation
    # Revenue (Balls) = (Expected Spins / Border) * 250
    # Investment (Balls) = (Expected Spins / User Base) * 250
    
    rev_balls = (expected_spins / border_adj) * 250.0
    inv_balls = (expected_spins / base) * 250.0
    
    profit_balls = rev_balls - inv_balls
    
    # 6. Convert to Yen
    yen_per_ball = 100.0 / exchange_rate
    ev_yen = profit_balls * yen_per_ball
    
    return int(ev_yen)

def get_base_curve(base, exchange_rate, machine_out, steps=10):
    points = []
    # Plot Exp vs Base for fixed 400 spins
    for b in [x * 0.5 for x in range(30, 51)]: # 15 to 25
        val = calculate_expectation(b, 400, exchange_rate, machine_out, False)
        points.append((b, val))
    return points

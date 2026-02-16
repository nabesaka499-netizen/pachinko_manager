
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
    Calculate EV based on calibrated Table Data.
    Standard: Base 20.0, Exch 27.0, Out 1400.0.
    """
    
    # 1. Get Base Revenue (Standard)
    # This represents the Total Yen Revenue for Base 20/Rate 27/Out 1400 context.
    base_rev_yen = get_table_revenue(remaining_spins)
    
    # 2. Adjust Revenue for actual Exchange Rate and Output
    # Rate Adjustment: Scaling from 27.0 (3.70 yen)
    if exchange_rate <= 0: exchange_rate = 27.0
    
    std_yen_ball = 3.7037 # 100/27
    cur_yen_ball = 100.0 / exchange_rate
    
    # Output Adjustment: Proportional to Out/1400
    out_ratio = actual_10r_out / 1400.0
    
    # Rate Ratio
    rate_ratio = cur_yen_ball / std_yen_ball
    
    # Final Revenue
    final_revenue = base_rev_yen * out_ratio * rate_ratio
    
    # 3. Calculate Cost
    # Cost = (Spins / Base) * 250 balls * Current Yen Rate
    # Note: User table derivation used 3.70 for cost (Savings Investment).
    if base <= 0: base = 1.0
    
    cost_balls = (remaining_spins / base) * 250.0
    cost_yen = cost_balls * cur_yen_ball
    
    # 4. EV
    ev = final_revenue - cost_yen
    
    return int(ev)

def get_base_curve(base, exchange_rate, machine_out, steps=10):
    points = []
    # Plot Exp vs Base for fixed 400 spins
    for b in range(15, 27):
        val = calculate_expectation(b, 400, exchange_rate, machine_out, False)
        points.append((b, val))
    return points

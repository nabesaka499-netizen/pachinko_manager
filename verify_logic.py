
import logic

def verify():
    model = "大海5SP"
    base = 20.0
    exchange_rate = 27.5
    actual_10r_out = 1389.0
    
    print(f"--- {model} 期待値検証 (ベース:{base}, 交換率:{exchange_rate}) ---")
    print("残り回転数 | 出玉 1389 | 出玉 1420 | 出玉 1380")
    print("-------------------------------------------------")
    for spins in [600, 500, 400, 300, 200, 100]:
        ev_std = logic.calculate_expectation(base, spins, exchange_rate, 1389.0, model)
        ev_plus = logic.calculate_expectation(base, spins, exchange_rate, 1420.0, model)
        ev_minus = logic.calculate_expectation(base, spins, exchange_rate, 1380.0, model)
        print(f"{spins:10d} | {ev_std:8,d} | {ev_plus:8,d} | {ev_minus:8,d}")

if __name__ == "__main__":
    verify()

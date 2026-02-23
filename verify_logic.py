
import logic

def verify():
    model = "大海5SP"
    base = 20.0
    exchange_rate = 27.5
    actual_10r_out = 1389.0
    
    print(f"--- {model} 期待値検証 (ベース:{base}, 交換率:{exchange_rate}) ---")
    print("残り回転数 | 期待値(円)")
    print("-------------------------")
    for spins in [600, 500, 400, 300, 200, 100]:
        ev = logic.calculate_expectation(base, spins, exchange_rate, actual_10r_out, model)
        print(f"{spins:10d} | {ev:7,d}")

if __name__ == "__main__":
    verify()

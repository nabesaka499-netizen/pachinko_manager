
import streamlit as st
import pandas as pd
import logic
import database as db
import matplotlib.pyplot as plt
import importlib

# Force reload logic module to pick up changes
importlib.reload(logic)
importlib.reload(db)

st.set_page_config(page_title="Pachinko Manager (Sea Story 4 SP)", layout="wide")

# Init DB
db.init_db()

st.title("🌊 Sea Story 4 SP Expectation Manager")

# Store Configuration
STORE_CONFIG = {
    "ラフェスタ 5": list(range(987, 1005)),
    "999": list(range(81, 85)) + list(range(86, 88)) + list(range(93, 101)) + list(range(141, 149))
}

# Sidebar: Inputs and Machine Selection
st.sidebar.header("台データ入力")

# 1. Rename "Default Store" if exists
db.rename_store("Default Store", "ラフェスタ 5")

# 2. Ensure "999" exists
db.add_store("999", 28.0) # Assuming rate, user can update if needed.

# 3. Store Selection
stores = db.get_stores()
if stores.empty:
    db.add_store("ラフェスタ 5", 27.0)
    stores = db.get_stores()

store_names = stores['name'].tolist()
# Filter only configured stores or show all? Let's show all in DB but config applies to known ones.
selected_store_name = st.sidebar.selectbox("店舗", store_names, index=store_names.index("ラフェスタ 5") if "ラフェスタ 5" in store_names else 0)

store_row = stores[stores['name'] == selected_store_name].iloc[0]
store_id = int(store_row['id'])
rate = float(store_row['exchange_rate'])

# Machine Selection
st.sidebar.subheader("台選択")

# Ensure machines for selected store
if selected_store_name in STORE_CONFIG:
    target_machines = STORE_CONFIG[selected_store_name]
    db.ensure_machines(store_id, target_machines)
    machine_list = sorted(target_machines)
else:
    # Fallback or other stores
    machine_list = db.get_all_machine_numbers(store_id)
    if not machine_list:
        machine_list = [1] # Dummy

m_num = st.sidebar.selectbox("台番号", machine_list)

# Get Machine Stats & Weighted Averages
mid, _ = db.get_or_create_machine(store_id, m_num)
# Now returns 7 values including record_count
w_base, w_out, t_spins, t_inv, t_out, t_hits, rec_count = db.get_machine_weighted_stats(store_id, m_num)

if rec_count > 0:
    # Calculate investment units (1 unit = 250 balls)
    inv_units = t_inv / 250.0
    st.sidebar.info(f"""
    **過去{rec_count}回の実戦データ平均**
    - **平均ベース**: {w_base:.1f}
      └ ({t_spins:,}回転 / {inv_units:,.1f}単位)
    - **平均出玉**: {w_out:.0f}
      └ ({t_out:,}玉 / {t_hits}回)
    """)

# Remarks Input
current_remarks = db.get_machine_remarks(store_id, m_num)
new_remarks = st.sidebar.text_area("備考", current_remarks)
if st.sidebar.button("備考を保存"):
    db.update_machine_remarks(store_id, m_num, new_remarks)
    st.success("備考を保存しました。")
    st.rerun()

# Result Input
st.sidebar.markdown("---")
st.sidebar.subheader("実戦データ入力")
# Investment in 1k yen units (1 unit = 250 balls)
inv_k = st.sidebar.number_input("投資 (千円)", min_value=0, max_value=200, value=None, step=1, placeholder="0")
spins = st.sidebar.number_input("総回転数", min_value=0, max_value=3000, value=None, step=1, placeholder="0")
# Using "Total Hits" to calc avg out 
total_hits = st.sidebar.number_input("総当たり回数 (10R)", min_value=0, max_value=50, value=None, step=1, placeholder="0") 
# User said "Total Out Balls (10R)". 
# Usually we input: "Total Won Balls".
total_out = st.sidebar.number_input("総出玉", min_value=0, max_value=50000, value=None, step=1, placeholder="0")


col_btn1, col_btn2 = st.sidebar.columns(2)
with col_btn1:
    if st.sidebar.button("記録"):
        # Handle None input (treat as 0)
        v_inv = inv_k if inv_k is not None else 0
        v_spins = spins if spins is not None else 0
        v_hits = total_hits if total_hits is not None else 0
        v_out = total_out if total_out is not None else 0

        if v_spins > 0:
            # Convert 1k yen to balls (1k = 250 balls)
            inv_balls = v_inv * 250
            db.add_record(store_id, m_num, inv_balls, v_spins, v_hits, v_out)
            st.success("保存しました。")
            st.rerun()
        else:
            st.error("回転数を入力してください。")
with col_btn2:
    if st.button("1件削除", type="primary"):
        db.delete_last_record(store_id, m_num)
        st.warning("最新のデータを1件削除しました。")
        st.rerun()

if st.sidebar.button("直前の削除を取り消す"):
    if db.restore_last_record(store_id, m_num):
        st.success("データを復活させました。")
        st.rerun()
    else:
        st.error("復活できるデータがありません。")

# Main Area: Calculator (Only for Lafesta 5)
if selected_store_name == "ラフェスタ 5":
    st.subheader("期待値計算")

    # Calculator Inputs - Using Number Input (Tab-like precision)
    col_input1, col_input2, col_input3, col_input4 = st.columns(4)
    with col_input1:
        cur_spins = st.number_input("残り回転数", 0, 1500, 450, step=10)
    with col_input2:
        # Default base is "Weighted Base" if available, else 20
        default_base = float(w_base) if w_base > 10 else 20.0
        cur_base = st.number_input("現在のベース", 10.0, 30.0, default_base, step=0.1, format="%.1f")
    with col_input3:
        cur_rate = st.number_input("換金率 (玉/100円)", 20.0, 50.0, float(rate), step=0.1, format="%.1f")
    with col_input4:
        # Default average from weighted stats
        default_out = int(w_out) if w_out > 1000 else 1400
        # Clamp default value to be within valid range
        default_out = max(1300, min(1500, default_out))
        
        cur_avg_out = st.number_input("平均出玉 (R)", 1300, 1500, default_out, step=5) 

    # Validation inputs
    exp_val = logic.calculate_expectation(cur_base, cur_spins, cur_rate, cur_avg_out, False)

    # Display Results
    c1 = st.container()
    c1.metric("期待値", f"¥{exp_val:,}")

    st.divider()

# Machine Statistics Section (Bottom)
st.divider()

# Machine Statistics Section (Bottom) - Full List
st.subheader("📊 全台データ一覧")
all_stats = db.get_all_machines_status(store_id)

if all_stats:
    df = pd.DataFrame(all_stats)
    # Ensure column order
    df = df[["番号", "回転率(詳細)", "出玉(詳細)", "備考"]]
    
    # Display as a clean table/dataframe
    # height argument controls how much vertical space it takes. 
    # use_container_width expands it to fill width.
    st.dataframe(
        df, 
        hide_index=True, 
        use_container_width=True,
        height=(len(df) + 1) * 35 + 3 # approx height adjustment
    )
else:
    st.info("データがありません。")


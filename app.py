
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

# Sidebar: Inputs and Machine Selection
st.sidebar.header("台データ入力")

# Auto-select or create default store
stores = db.get_stores()
if stores.empty:
    db.add_store("Default Store", 27.0)
    stores = db.get_stores()

store_row = stores.iloc[0]
store_id = int(store_row['id'])
rate = float(store_row['exchange_rate'])
selected_store_name = store_row['name']

# Machine Selection
st.sidebar.subheader("台選択")

# Ensure default machines (987-1004) exist
db.ensure_default_machines(store_id)

# Force machine list to 987-1004
machine_list = list(range(987, 1005))
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
inv_k = st.sidebar.number_input("投資 (千円)", 0, 200, 10, step=1)
spins = st.sidebar.number_input("総回転数", 0, 3000, 0)
# Using "Total Hits" to calc avg out 
total_hits = st.sidebar.number_input("総当たり回数 (10R)", 0, 50, 0) 
# User said "Total Out Balls (10R)". 
# Usually we input: "Total Won Balls".
total_out = st.sidebar.number_input("総出玉", 0, 50000, 0)


col_btn1, col_btn2 = st.sidebar.columns(2)
with col_btn1:
    if st.sidebar.button("記録"):
        if spins > 0:
            # Convert 1k yen to balls (1k = 250 balls)
            inv_balls = inv_k * 250
            db.add_record(store_id, m_num, inv_balls, spins, total_hits, total_out)
            st.success("保存しました。")
            st.rerun()
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

# Main Area: Calculator
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


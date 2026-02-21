
import streamlit as st
import pandas as pd
import logic
import database as db
import matplotlib.pyplot as plt
import importlib

# Force reload logic module to pick up changes
importlib.reload(logic)
importlib.reload(db)

st.set_page_config(page_title="ホール別　実践データ管理表", layout="wide")

# Init DB
db.init_db()

st.title("🌊 ホール別　実践データ管理表")

# Store Configuration
# Define ranges with exclusion logic (4 and 9)
def generate_range_exclude_49(start, end):
    return [i for i in range(start, end + 1) if i % 10 not in (4, 9)]

sh_alta = generate_range_exclude_49(1551, 1561) + generate_range_exclude_49(1650, 1660)
sh_agnes = list(range(1837, 1839))
sh_shinkai = list(range(1850, 1852))

STORE_CONFIG = {
    "ラフェスタ 5": list(range(987, 1005)),
    "999": list(range(81, 85)) + list(range(86, 88)) + list(range(93, 101)) + list(range(141, 149)),
    "スーパーハリウッド1000": sh_alta + sh_agnes + sh_shinkai
}

# Sidebar: Inputs and Machine Selection
st.sidebar.header("台データ入力")

# 1. Rename "Default Store" if exists
db.rename_store("Default Store", "ラフェスタ 5")

# 2. Ensure stores exist
db.add_store("999", 28.0)
db.add_store("スーパーハリウッド1000", 28.0)

# 3. Store Selection
# ... (existing code) ...

# ... (inside STORE_MODEL_CONFIG) ...
STORE_MODEL_CONFIG = {
    "999": {
        "P大海物語5スペシャル ALTA": list(range(93, 101)) + list(range(141, 149)),
        "PA大海物語5 With アグネス･ラム ARBC": list(range(81, 85)),
        "PA大海物語4スペシャル RBA": list(range(86, 88))
    },
    "スーパーハリウッド1000": {
        "P大海物語5スペシャル ALTA": sh_alta,
        "PA大海物語5 With アグネス･ラム ARBC": sh_agnes,
        "PA新海物語 ARBB": sh_shinkai
    }
}


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

# 1. Determine Model (Island) for the selected machine
current_model_name = "不明"
current_model_machines = []

# Move model config definition up or refer to a consolidated one
# Let's use the one at the bottom, or just define it here.
# Actually, the one at the bottom is for display grouping. I should unify them.
MODEL_GROUPS = {
    "999": {
        "P大海物語5スペシャル ALTA": list(range(93, 101)) + list(range(141, 149)),
        "PA大海物語5 With アグネス･ラム ARBC": list(range(81, 85)),
        "PA大海物語4スペシャル RBA": list(range(86, 88))
    },
    "スーパーハリウッド1000": {
        "P大海物語5スペシャル ALTA": sh_alta,
        "PA大海物語5 With アグネス･ラム ARBC": sh_agnes,
        "PA新海物語 ARBB": sh_shinkai
    },
    "ラフェスタ 5": {
        "大海4SP": STORE_CONFIG["ラフェスタ 5"]
    }
}

if selected_store_name in MODEL_GROUPS:
    for mname, mnums in MODEL_GROUPS[selected_store_name].items():
        if m_num in mnums:
            current_model_name = mname
            current_model_machines = mnums
            break

# 2. Get Island Stats
i_base, i_out, i_rec_count = db.get_model_weighted_stats(store_id, current_model_machines)

# 3. Sidebar Display: Stats
if rec_count > 0:
    inv_units = t_inv / 250.0
    st.sidebar.info(f"""
    **台#{m_num} 実戦平均** ({rec_count}回)
    - **ベース**: {w_base:.1f} ({t_spins:,} / {inv_units:,.1f})
    - **出玉**: {w_out:.0f} ({t_out:,} / {t_hits})
    """)

if i_rec_count > 0:
    st.sidebar.success(f"""
    **シマ平均 [{current_model_name}]** ({i_rec_count}回)
    - **ベース**: {i_base:.1f}
    - **出玉**: {i_out:.0f}
    """)

# 4. Remarks Input
current_remarks = db.get_machine_remarks(store_id, m_num)
# Use key for remarks to allow resetting
new_remarks_val = st.sidebar.text_area("備考", current_remarks, key="input_remarks")

if st.sidebar.button("備考を保存"):
    db.update_machine_remarks(store_id, m_num, new_remarks_val)
    st.success("備考を保存しました。")
    st.rerun()

# 5. History Management: Delete Specific Records
st.sidebar.markdown("---")
st.sidebar.subheader("履歴管理 (最新5件)")
history_df = db.get_machine_history(store_id, m_num, limit=5)
if not history_df.empty:
    for idx, row in history_df.iterrows():
        rid = row['id']
        date_str = row['date']
        # Display: 02-22: 21.5 / 1420
        label = f"{date_str[5:]}: {row['base_calculated']:.1f} / {int(row['out_10r_calculated'])}"
        if st.sidebar.button(f"削除 {label}", key=f"del_{rid}"):
            if db.delete_record_by_id(rid):
                st.sidebar.success(f"{label} を削除しました。")
                st.rerun()
else:
    st.sidebar.caption("履歴がありません。")

if st.sidebar.button("直前の削除を元に戻す"):
    if db.restore_last_record(store_id, m_num):
        st.success("データを復活させました。")
        st.rerun()
    else:
        st.error("復活できるデータがありません。")

# 6. Result Input
st.sidebar.markdown("---")
st.sidebar.subheader("実戦データ入力")

# Use keys for easy resetting
inv_k_raw = st.sidebar.text_input("投資 (千円)", value="", placeholder="0", key="input_inv")
spins_raw = st.sidebar.text_input("総回転数", value="", placeholder="0", key="input_spins")
total_hits_raw = st.sidebar.text_input("総当たり回数 (10R)", value="", placeholder="0", key="input_hits") 
total_out_raw = st.sidebar.text_input("総出玉", value="", placeholder="0", key="input_out")

# Helper to safely convert text to numeric
def safe_to_num(val, is_int=True):
    try:
        if not val: return 0
        return int(val) if is_int else float(val)
    except ValueError:
        return 0

col_btn1, col_btn2 = st.sidebar.columns(2)
with col_btn1:
    if st.sidebar.button("記録"):
        v_inv = safe_to_num(inv_k_raw)
        v_spins = safe_to_num(spins_raw)
        v_hits = safe_to_num(total_hits_raw)
        v_out = safe_to_num(total_out_raw)

        if v_spins > 0:
            inv_balls = v_inv * 250
            db.add_record(store_id, m_num, inv_balls, v_spins, v_hits, v_out)
            
            # Clear remarks in DB as well since user wants it emptied
            db.update_machine_remarks(store_id, m_num, "")
            
            # Clear inputs in session state
            for k in ["input_inv", "input_spins", "input_hits", "input_out", "input_remarks"]:
                st.session_state[k] = ""
                
            st.success("保存しました。入力内容と備考をリセットしました。")
            st.rerun()
        else:
            st.error("回転数を入力してください。")
with col_btn2:
    if st.button("1件削除", type="primary"):
        db.delete_last_record(store_id, m_num)
        st.warning("最新のデータを1件削除しました。")
        st.rerun()

# Main Area: Calculator
# Dynamic Settings based on Store
if selected_store_name == "ラフェスタ 5":
    calc_title = "大海4SP 期待値計算"
    calc_model = "大海4SP"
    default_rate = float(rate) # Typically 27.0
    default_out_std = 1400
else:
    calc_title = f"{current_model_name} 期待値計算"
    calc_model = "大海5SP"
    default_rate = 27.5
    default_out_std = 1390

st.subheader(calc_title)

# Calculator Inputs
col_input1, col_input2, col_input3, col_input4 = st.columns(4)
with col_input1:
    cur_spins = st.number_input("残り回転数", 0, 1500, 450, step=10)
with col_input2:
    # Default priority: Island Average > Weighted Base > 20.0
    if i_rec_count > 0:
        default_base = float(i_base)
    elif w_base > 10:
        default_base = float(w_base)
    else:
        default_base = 20.0
    
    # Clamp to prevent StreamlitValueOutOfBoundsError
    default_base = max(10.0, min(30.0, default_base))
    cur_base = st.number_input("現在のベース", 10.0, 30.0, default_base, step=0.1, format="%.1f")
with col_input3:
    cur_rate = st.number_input("換金率 (玉/100円)", 20.0, 50.0, default_rate, step=0.1, format="%.1f")
with col_input4:
    # Default priority: Island Average > Weighted Avg Out > model default
    if i_rec_count > 0:
        default_out = int(i_out)
    elif w_out > 1000:
        default_out = int(w_out)
    else:
        default_out = default_out_std
    
    default_out = max(1300, min(1550, default_out))
    cur_avg_out = st.number_input("平均出玉 (R)", 1300, 1550, default_out, step=5) 

# Calculate using the selected model
exp_val = logic.calculate_expectation(cur_base, cur_spins, cur_rate, cur_avg_out, calc_model)

# Display Results
c1 = st.container()
c1.metric("期待値", f"¥{exp_val:,}")

st.divider()

# Result Input
# ... (omitted parts) ...

# Machine Statistics Section (Bottom)
st.divider()

# Machine Statistics Section (Bottom) - Full List
st.subheader("📊 全台データ一覧")
all_stats = db.get_all_machines_status(store_id)

# Model Configuration for display grouping (Using MODEL_GROUPS defined above)
if all_stats:
    df_all = pd.DataFrame(all_stats)
    
    # Check if we have specific model grouping for this store
    if selected_store_name in MODEL_GROUPS:
        model_map = MODEL_GROUPS[selected_store_name]
        
        for model_name, machine_nums in model_map.items():
            # Filter df for these machines
            df_model = df_all[df_all["番号"].isin(machine_nums)].copy()
            
            if not df_model.empty:
                st.markdown(f"**{model_name}**")
                
                # Calculate Model Summary (Island Stats)
                m_base, m_out, m_count = db.get_model_weighted_stats(store_id, machine_nums)
                if m_count > 0:
                    summary_df = pd.DataFrame([{
                        "番号": "【平均】",
                        "回転率(詳細)": f"{m_base:.1f} ({m_count}件)",
                        "出玉(詳細)": f"{int(m_out):,}",
                        "備考": "シマ加重平均"
                    }])
                    df_model = pd.concat([df_model, summary_df], ignore_index=True)
                
                # Ensure column order
                df_model = df_model[["番号", "回転率(詳細)", "出玉(詳細)", "備考"]]
                
                st.dataframe(
                    df_model, 
                    hide_index=True, 
                    use_container_width=True,
                    height=(len(df_model) + 1) * 35 + 3
                )
    else:
        # Default display (No grouping defined)
        df_all = df_all[["番号", "回転率(詳細)", "出玉(詳細)", "備考"]]
        st.dataframe(
            df_all, 
            hide_index=True, 
            use_container_width=True,
            height=(len(df_all) + 1) * 35 + 3
        )
else:
    st.info("データがありません。")


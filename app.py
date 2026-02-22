
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
i_base, i_out, _, _, _, _, i_rec_count = db.get_model_weighted_stats(store_id, current_model_machines)

# Helper to safely convert text to numeric
def safe_to_num(val, is_int=True):
    try:
        if not val: return 0
        return int(val) if is_int else float(val)
    except ValueError:
        return 0

# Callbacks for safe session state updates
def save_record_callback(st_id, machine_num):
    v_inv = safe_to_num(st.session_state.get("input_inv", ""), is_int=False)
    v_spins = safe_to_num(st.session_state.get("input_spins", ""), is_int=True)
    v_hits = safe_to_num(st.session_state.get("input_hits", ""), is_int=True)
    v_out = safe_to_num(st.session_state.get("input_out", ""), is_int=True)

    if v_spins > 0:
        inv_balls = v_inv * 250
        db.add_record(st_id, machine_num, inv_balls, v_spins, v_hits, v_out)
        db.update_machine_remarks(st_id, machine_num, "")
        # Reset inputs
        for k in ["input_inv", "input_spins", "input_hits", "input_out", "input_remarks"]:
            st.session_state[k] = ""
        st.session_state["record_success"] = True
    else:
        st.session_state["record_error"] = "回転数を入力してください。"

def save_remarks_callback(st_id, machine_num):
    remarks_text = st.session_state.get("input_remarks", "")
    db.update_machine_remarks(st_id, machine_num, remarks_text)
    st.session_state["remarks_success"] = True

def delete_record_callback(r_id, label_text):
    if db.delete_record_by_id(r_id):
        st.session_state["del_msg"] = f"{label_text} を削除しました。"

# 3. Sidebar Display: Stats
if rec_count > 0:
    st.sidebar.info(f"""
    **台#{m_num} 実践平均** ({rec_count}回)
    - **ベース**: {w_base:.1f} ({t_spins:.0f} / {t_inv/250:.1f})
    - **出玉**: {w_out:.0f} ({t_out:.0f} / {t_hits:.1f})
    """)

if i_rec_count > 0:
    st.sidebar.success(f"""
    **シマ平均 [{current_model_name}]** ({i_rec_count}回)
    - **ベース**: {i_base:.1f}
    - **出玉**: {i_out:.0f}
    """)

# 4. Remarks Input
current_remarks = db.get_machine_remarks(store_id, m_num)
st.sidebar.text_area("備考", current_remarks, key="input_remarks")
st.sidebar.button("備考を保存", on_click=save_remarks_callback, args=(store_id, m_num))
if st.session_state.get("remarks_success"):
    st.sidebar.success("備考を保存しました。")
    del st.session_state["remarks_success"]

# 5. History Management
st.sidebar.markdown("---")
st.sidebar.subheader("履歴管理 (最新5件)")
history_df = db.get_machine_history(store_id, m_num, limit=5)
if not history_df.empty:
    for idx, row in history_df.iterrows():
        rid = row['id']
        date_str = row['date']
        label = f"{date_str[5:]}: {row['base_calculated']:.1f} / {int(row['out_10r_calculated'])}"
        st.sidebar.button(f"削除 {label}", key=f"del_{rid}", on_click=delete_record_callback, args=(rid, label))

if st.session_state.get("del_msg"):
    st.sidebar.success(st.session_state["del_msg"])
    del st.session_state["del_msg"]
else: st.sidebar.caption("履歴がありません。")

st.sidebar.markdown("---")
st.sidebar.subheader("実戦データ入力")

# Data Entry Widgets
col_in1, _ = st.sidebar.columns([1, 2])
with col_in1:
    st.text_input("投資 (千円)", value="", placeholder="0", key="input_inv")
    st.text_input("総回転数", value="", placeholder="0", key="input_spins")
    st.text_input("総当たり回数", value="", placeholder="0", key="input_hits") 
    st.text_input("総出玉", value="", placeholder="0", key="input_out")

st.sidebar.button("記録", use_container_width=True, on_click=save_record_callback, args=(store_id, m_num))

if st.session_state.get("record_success"):
    st.sidebar.success("保存しました。入力内容と備考をリセットしました。")
    del st.session_state["record_success"]
if st.session_state.get("record_error"):
    st.sidebar.error(st.session_state["record_error"])
    del st.session_state["record_error"]

# Main Area: Calculator
# Dynamic Settings based on Store
if selected_store_name == "ラフェスタ 5":
    calc_title = "大海4SP 期待値計算"
    calc_model = "大海4SP"
    default_rate = float(rate) # Typically 27.0
    default_out_std = 1400
else:
    # Fixed title for non-Lafesta stores as requested
    calc_title = "P大海物語5スペシャル ALTA 期待値計算"
    calc_model = "大海5SP"
    default_rate = 27.5
    default_out_std = 1400

st.subheader(calc_title)

# Calculator Inputs
col_input1, col_input2, col_input3, col_input4 = st.columns(4)
with col_input1:
    cur_spins = st.number_input("残り回転数", 0, 1500, 450, step=10)
with col_input2:
    # Default priority: Island Average > Weighted Base > 20.0
    val_base = 20.0
    if float(i_rec_count) > 0:
        val_base = float(i_base)
    elif float(rec_count) > 0 and float(w_base) > 10:
        val_base = float(w_base)
    
    # Clamp to prevent StreamlitValueOutOfBoundsError
    default_base = max(10.0, min(30.0, val_base))
    cur_base = st.number_input("現在のベース", 10.0, 30.0, default_base, step=0.1, format="%.1f")
with col_input3:
    cur_rate = st.number_input("換金率", 20.0, 50.0, float(default_rate), step=0.1, format="%.1f")
with col_input4:
    # Default priority: Island Average > Weighted Avg Out > model default
    val_out = float(default_out_std)
    if float(i_rec_count) > 0:
        val_out = float(i_out)
    elif float(rec_count) > 0 and float(w_out) > 1000:
        val_out = float(w_out)
    
    default_out_final = max(1300.0, min(1550.0, val_out))
    cur_avg_out = st.number_input("平均出玉", 1300, 1550, int(default_out_final), step=5) 

# Calculate using the selected model
exp_val = logic.calculate_expectation(cur_base, cur_spins, cur_rate, cur_avg_out, calc_model)
est_time = logic.get_estimated_time(cur_spins, calc_model)
avg_hits = logic.get_expected_hits(cur_spins, calc_model)
hourly_wage = int((exp_val / est_time) * 60)

# Display Results - 2x2 grid for mobile compatibility
col_res1, col_res2 = st.columns(2)
with col_res1:
    st.metric("期待値", f"¥{exp_val:,}")
    st.metric("消化時間", f"約{int(est_time)}分")
with col_res2:
    st.metric("時給 (見込)", f"¥{hourly_wage:,}")
    st.metric("平均連荘", f"{avg_hits:.2f}回")

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
                m_base, m_out, m_spins, m_inv, m_out_balls, m_hits, m_count = db.get_model_weighted_stats(store_id, machine_nums)
                if m_count > 0:
                    m_inv_units = m_inv / 250.0
                    summary_df = pd.DataFrame([{
                        "番号": "【平均】",
                        "回転率(詳細)": f"{m_base:.1f} ({m_spins:,}/{m_inv_units:,.1f})",
                        "出玉(詳細)": f"{int(m_out):,} ({m_out_balls:,}/{m_hits})",
                        "備考": f"シマ加重平均 ({m_count}件)"
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



import sqlite3
import pandas as pd
import datetime

DB_PATH = 'pachinko.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Stores: name, exchange_rate
    c.execute('''CREATE TABLE IF NOT EXISTS stores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        exchange_rate REAL DEFAULT 27.0
    )''')
    
    # Machines: store_id, machine_number, accumulated stats
    c.execute('''CREATE TABLE IF NOT EXISTS machines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_id INTEGER,
        machine_number INTEGER,
        total_spins INTEGER DEFAULT 0,
        total_out_balls INTEGER DEFAULT 0,
        avg_out_balls REAL DEFAULT 1400.0,
        avg_base REAL DEFAULT 20.0,
        FOREIGN KEY(store_id) REFERENCES stores(id),
        UNIQUE(store_id, machine_number)
    )''')
    
    # Records: history
    c.execute('''CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        machine_id INTEGER,
        date TEXT,
        investment_balls INTEGER,
        spins INTEGER,
        hits INTEGER DEFAULT 0,
        out_balls INTEGER,
        base_calculated REAL,
        out_10r_calculated REAL,
        FOREIGN KEY(machine_id) REFERENCES machines(id)
    )''')
    
    # Migration: Ensure new columns exist if table already exists
    try:
        c.execute("ALTER TABLE machines ADD COLUMN avg_base REAL DEFAULT 20.0")
    except sqlite3.OperationalError:
        pass # Column likely exists
    
    try:
        c.execute("ALTER TABLE records ADD COLUMN base_calculated REAL")
    except sqlite3.OperationalError:
        pass
        
    try:
        c.execute("ALTER TABLE records ADD COLUMN out_10r_calculated REAL")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()

def get_stores():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM stores", conn)
    except:
        return pd.DataFrame()
    conn.close()
    return df

def add_store(name, rate):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO stores (name, exchange_rate) VALUES (?, ?)", (name, rate))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_or_create_machine(store_id, machine_number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, avg_out_balls FROM machines WHERE store_id=? AND machine_number=?", (store_id, machine_number))
    res = c.fetchone()
    if res:
        conn.close()
        return res[0], res[1]
    else:
        c.execute("INSERT INTO machines (store_id, machine_number) VALUES (?, ?)", (store_id, machine_number))
        mid = c.lastrowid
        conn.commit()
        conn.close()
        # Default 1400
        return mid, 1400.0

def add_record(store_id, machine_number, investment, spins, hits, out_balls, date=None):
    if date is None:
        date = datetime.date.today().strftime('%Y-%m-%d')
    
    mid, _ = get_or_create_machine(store_id, machine_number)
    
    # Calculate performance metrics for this specific record
    # Base = Spins / (Investment / 250)
    inv_units = investment / 250.0
    base_cal = spins / inv_units if inv_units > 0 else 0.0
    
    # 10R Out = Out / Hits
    out_10r_cal = out_balls / hits if hits > 0 else 0.0
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO records (machine_id, date, investment_balls, spins, hits, out_balls, base_calculated, out_10r_calculated) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (mid, date, investment, spins, hits, out_balls, base_cal, out_10r_cal))
    
    # Update machine stats: Weighted Average
    c.execute("SELECT SUM(hits), SUM(out_balls), SUM(spins), SUM(investment_balls) FROM records WHERE machine_id=?", (mid,))
    row = c.fetchone()
    if row:
        t_hits = row[0] or 0
        t_out = row[1] or 0
        t_spins = row[2] or 0
        t_inv = row[3] or 0
        
        # Weighted Avg Out
        new_avg_out = t_out / t_hits if t_hits > 0 else 1400.0
        
        # Weighted Base
        t_inv_units = t_inv / 250.0
        new_avg_base = t_spins / t_inv_units if t_inv_units > 0 else 20.0
        
        # Update summary
        c.execute("UPDATE machines SET avg_out_balls = ?, avg_base = ?, total_spins = ?, total_out_balls = ? WHERE id = ?", 
                  (new_avg_out, new_avg_base, t_spins, t_out, mid))
    
    conn.commit()
    conn.close()

def get_machine_weighted_stats(store_id, machine_number):
    """
    Returns (weighted_base, weighted_avg_out, total_spins, total_hits, record_count)
    """
    mid, _ = get_or_create_machine(store_id, machine_number)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT SUM(spins), SUM(investment_balls), SUM(hits), SUM(out_balls), COUNT(id) FROM records WHERE machine_id=?", (mid,))
    row = c.fetchone()
    conn.close()
    
    if not row or not row[0]:
        return 0, 1400.0, 0, 0, 0, 0, 0
        
    t_spins = row[0]
    t_inv_balls = row[1]
    t_hits = row[2]
    t_out_balls = row[3]
    record_count = row[4]
    
    # Weighted Base
    inv_k_yen = t_inv_balls / 250.0
    weighted_base = t_spins / inv_k_yen if inv_k_yen > 0 else 0
    
    # Weighted Avg Out
    weighted_out = t_out_balls / t_hits if t_hits > 0 else 1400.0
    
    return weighted_base, weighted_out, t_spins, t_inv_balls, t_out_balls, t_hits, record_count

def delete_last_record(store_id, machine_number):
    mid, _ = get_or_create_machine(store_id, machine_number)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Find the last record ID
    c.execute("SELECT id FROM records WHERE machine_id=? ORDER BY id DESC LIMIT 1", (mid,))
    row = c.fetchone()
    
    if row:
        last_id = row[0]
        c.execute("DELETE FROM records WHERE id=?", (last_id,))
        
        # Recalculate and update machine stats after deletion
        c.execute("SELECT SUM(hits), SUM(out_balls), SUM(spins), SUM(investment_balls) FROM records WHERE machine_id=?", (mid,))
        stat_row = c.fetchone()
        
        if stat_row and stat_row[2]: # If there are still records
            t_hits = stat_row[0] or 0
            t_out = stat_row[1] or 0
            t_spins = stat_row[2] or 0
            t_inv = stat_row[3] or 0
            
            # Weighted Avg Out
            new_avg_out = t_out / t_hits if t_hits > 0 else 1400.0
            
            # Weighted Base
            t_inv_units = t_inv / 250.0
            new_avg_base = t_spins / t_inv_units if t_inv_units > 0 else 20.0
            
            c.execute("UPDATE machines SET avg_out_balls = ?, avg_base = ?, total_spins = ?, total_out_balls = ? WHERE id = ?", 
                      (new_avg_out, new_avg_base, t_spins, t_out, mid))
        else:
            # No records left, reset to default
            c.execute("UPDATE machines SET avg_out_balls=1400.0, avg_base=20.0, total_spins=0, total_out_balls=0 WHERE id=?", (mid,))
            
    conn.commit()
    conn.close()

def clear_machine_records(store_id, machine_number):
    mid, _ = get_or_create_machine(store_id, machine_number)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM records WHERE machine_id=?", (mid,))
    # Reset machine stats
    c.execute("UPDATE machines SET avg_out_balls=1400.0, avg_base=20.0, total_spins=0, total_out_balls=0 WHERE id=?", (mid,))
    conn.commit()
    conn.close()

def get_all_machine_numbers(store_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT machine_number FROM machines WHERE store_id=? ORDER BY machine_number ASC", (store_id,))
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def ensure_default_machines(store_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Cleanup
    c.execute("SELECT id FROM machines WHERE store_id=? AND (machine_number < 987 OR machine_number > 1004)", (store_id,))
    rows = c.fetchall()
    ids_to_remove = [r[0] for r in rows]
    
    if ids_to_remove:
        c.executemany("DELETE FROM records WHERE machine_id=?", [(mid,) for mid in ids_to_remove])
        c.executemany("DELETE FROM machines WHERE id=?", [(mid,) for mid in ids_to_remove])
    
    # 2. Defaults 987-1004
    defaults = range(987, 1005)
    for num in defaults:
        c.execute("INSERT OR IGNORE INTO machines (store_id, machine_number, avg_out_balls, avg_base, total_spins, total_out_balls) VALUES (?, ?, 1400.0, 20.0, 0, 0)", (store_id, num))
        
    conn.commit()
    conn.close()

def get_all_machines_status(store_id):
    m_nums = get_all_machine_numbers(store_id)
    data = []
    for m in m_nums:
        # returns 7 values
        wb, wo, t_spins, _, _, _, _ = get_machine_weighted_stats(store_id, m)
        
        rate_disp = f"{wb:.1f}" if t_spins > 0 else "-"
        out_disp = f"{int(wo)}" if t_spins > 0 else "-"
        
        data.append({
            "番号": m,
            "回転率": rate_disp,
            "出玉": out_disp
        })
    return data

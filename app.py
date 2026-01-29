import streamlit as st
import pandas as pd
import db_manager as db
import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Garment ERP", 
    page_icon="🧵", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. OPTIMIZED CSS (SINGLE LINE NAV) ---
st.markdown("""
<style>
    /* APP THEME */
    .stApp { background-color: #F8FAFC; font-family: 'Inter', sans-serif; }
    
    /* HIDE DEFAULT HEADER */
    header[data-testid="stHeader"] { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }

    /* --- HORIZONTAL NAVIGATION BAR --- */
    div[role="radiogroup"] {
        display: flex;
        flex-direction: row;
        flex-wrap: nowrap; /* Forces single line */
        justify-content: space-between;
        width: 100%;
        background: white;
        padding: 4px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        margin-bottom: 15px;
        gap: 4px;
        border: 1px solid #E2E8F0;
    }
    
    div[role="radiogroup"] label {
        flex: 1; /* Equal width for all buttons */
        text-align: center;
        background: transparent;
        border: 1px solid transparent !important;
        border-radius: 8px !important;
        transition: all 0.2s;
        margin: 0 !important;
        
        /* RESPONSIVE FONT & PADDING */
        padding: 8px 2px !important;
        font-size: clamp(10px, 3.5vw, 14px) !important; /* Auto-scales text */
        white-space: nowrap; /* Prevents text wrapping */
    }
    
    div[role="radiogroup"] label:hover {
        background-color: #F1F5F9;
    }
    
    /* ACTIVE TAB STYLE */
    div[role="radiogroup"] label[data-checked="true"] {
        background-color: #EEF2FF !important;
        color: #4F46E5 !important;
        font-weight: 700 !important;
        border: 1px solid #C7D2FE !important;
    }
    
    /* Hide the tiny circle from radio buttons */
    div[role="radiogroup"] label div:first-child { display: none; }
    div[role="radiogroup"] label div:last-child { margin-left: 0 !important; }

    /* --- INPUT FIELDS & BUTTONS --- */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox div[data-baseweb="select"] div {
        min-height: 45px !important;
        border-radius: 8px !important;
        border: 1px solid #E2E8F0 !important;
        font-size: 15px !important;
        background-color: white !important;
        color: #1E293B !important;
    }
    
    .stButton button {
        width: 100%;
        min-height: 45px;
        border-radius: 8px;
        font-weight: 600;
        background-color: #4F46E5;
        color: white;
        border: none;
    }

    /* --- MOBILE CARDS --- */
    .mobile-card {
        background: white; border-radius: 10px; padding: 12px;
        margin-bottom: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        border: 1px solid #F1F5F9;
    }
    .card-row { display: flex; justify-content: space-between; align-items: center; }
    
    /* --- STAT TILES --- */
    .stat-tile {
        background: white; padding: 10px; border-radius: 10px; text-align: center;
        border: 1px solid #E2E8F0; margin-bottom: 5px;
    }
    .stat-num { font-size: 18px; font-weight: 800; color: #1E293B; }
    .stat-desc { font-size: 10px; color: #64748B; font-weight: 600; text-transform: uppercase; }

</style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def render_mobile_card(title, subtitle, metric_label, metric_value):
    st.markdown(f"""
    <div class="mobile-card">
        <div style="font-weight:700; font-size:14px; color:#111827;">{title}</div>
        <div style="font-size:11px; color:#6B7280; margin-bottom:6px;">{subtitle}</div>
        <div class="card-row">
            <span style="font-size:11px; color:#9CA3AF;">{metric_label}</span>
            <span style="font-size:12px; font-weight:700; color:#4F46E5; background:#EEF2FF; padding:2px 8px; border-radius:12px;">{metric_value}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_stat_tile(label, value, color_border="#4F46E5"):
    st.markdown(f"""
    <div class="stat-tile" style="border-bottom: 3px solid {color_border};">
        <div class="stat-num">{value}</div>
        <div class="stat-desc">{label}</div>
    </div>
    """, unsafe_allow_html=True)

def render_df(df, file_name="data"):
    if df.empty: st.info("No data."); return
    # Mobile download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(f"⬇️ CSV", csv, f"{file_name}.csv", "text/csv", key=f"dl_{file_name}")
    st.dataframe(df, use_container_width=True, hide_index=True)

# --- 4. NAVIGATION (OPTIMIZED) ---
# Short labels with Icons to fit in one line
nav_items = {
    "Home": "🏠 Dash",
    "Workers": "👷 Staff",
    "Masters": "⚙️ Config",
    "Pay": "💰 Pay"
}

# The Magic: Radio Button disguised as a horizontal tab bar
selected_label = st.radio("Nav", list(nav_items.values()), horizontal=True, label_visibility="collapsed")

# Map label back to key
selected_nav = next(key for key, value in nav_items.items() if value == selected_label)

# --- 5. PAGE: DASHBOARD ---
if selected_nav == "Home":
    st.markdown("##### 👋 Dashboard")
    
    pcs, earn, pending, active = db.get_dashboard_stats()
    
    c1, c2 = st.columns(2)
    with c1: render_stat_tile("Today Pcs", f"{pcs:,.0f}", "#10B981")
    with c2: render_stat_tile("Prod. Value", f"₹{earn:,.0f}", "#F59E0B")
    
    st.markdown("<div style='height:5px'></div>", unsafe_allow_html=True)
    
    c3, c4 = st.columns(2)
    with c3: render_stat_tile("Pending", f"₹{pending:,.0f}", "#EF4444")
    with c4: render_stat_tile("Active", str(active), "#6366F1")

    st.markdown("---")
    st.caption("⚡ **Quick Entry**")
    
    with st.container(border=True):
        p_date = st.date_input("Date", datetime.date.today())
        
        c_staff, c_item = st.columns(2)
        p_staff = c_staff.selectbox("Worker", [""] + db.get_staff_list())
        p_item = c_item.selectbox("Item", [""] + db.get_items_list())
        
        c_proc, c_qty = st.columns(2)
        p_process = c_proc.selectbox("Process", [""] + db.get_processes_list())
        p_qty = c_qty.number_input("Qty", min_value=1, step=1)
        
        # Auto-Rate
        rate_val = db.get_rate(p_item, p_process) if p_item and p_process else 0.0
        p_rate = st.number_input("Rate (₹)", value=rate_val)
        
        if st.button("SAVE ENTRY"):
            if p_staff and p_item and p_process:
                db.save_production(str(p_date), p_staff, p_item, p_process, p_qty, p_rate)
                st.success("Done!")
            else: st.error("Missing Data")

# --- 6. PAGE: WORKERS ---
elif selected_nav == "Workers":
    st.markdown("##### 👷 Worker Stats")
    
    search = st.selectbox("Search Worker", [""] + db.get_staff_list())
    
    if search:
        details = db.get_staff_details(search)
        role = details.get('role', '-')
        
        e, p, bal, hist_df = db.get_worker_history(search)
        
        # Compact Balance Card
        st.markdown(f"""
        <div style="background:#EEF2FF; border:1px solid #C7D2FE; padding:12px; border-radius:10px; margin-bottom:15px; text-align:center;">
            <div style="font-size:12px; color:#4338CA; font-weight:600; margin-bottom:4px;">PENDING BALANCE</div>
            <div style="font-size:24px; font-weight:800; color:{'#EF4444' if bal > 0 else '#10B981'};">₹ {bal:,.0f}</div>
            <div style="font-size:10px; color:#6B7280; margin-top:4px;">Earned: ₹{e:,.0f} • Paid: ₹{p:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.caption("📜 History")
        if not hist_df.empty:
            for _, row in hist_df.head(8).iterrows():
                d_str = pd.to_datetime(row['date']).strftime('%d/%m')
                render_mobile_card(
                    f"{row['item']} ({row['process']})", 
                    f"{d_str} • Rate: ₹{row['rate']}",
                    "Total",
                    f"₹ {row['amount']:,.0f}"
                )
        else: st.info("No History")

# --- 7. PAGE: MASTERS ---
elif selected_nav == "Masters":
    st.markdown("##### ⚙️ Setup")
    
    t_list = ["Staff", "Item", "Proc", "Rate", "Other"]
    sub_nav = st.segmented_control("Type", t_list, default="Staff") # Streamlit 1.40+ feature, else use selectbox
    if not sub_nav: sub_nav = "Staff" # Fallback

    if sub_nav == "Staff":
        with st.form("f_st"):
            n = st.text_input("Name")
            p = st.text_input("Phone")
            r = st.selectbox("Role", ["Stitching", "Helper", "Cutting"])
            s_type = st.radio("Pay Type", ["Piece Rate", "Salaried"], horizontal=True)
            m_sal = st.number_input("Monthly ₹", step=500.0) if s_type == "Salaried" else 0.0
            
            if st.form_submit_button("Save"):
                db.save_staff(n, p, r, s_type, m_sal)
                st.success("Saved")
        render_df(db.get_df("masters_staff")[['name','role']])

    elif sub_nav == "Item":
        with st.form("f_it"):
            n = st.text_input("Name")
            if st.form_submit_button("Save"):
                db.save_master("masters_items", {"name":n})
                st.success("Saved")
        render_df(db.get_df("masters_items"))

    elif sub_nav == "Rate":
        with st.form("f_rt"):
            i = st.selectbox("Item", db.get_items_list())
            pr = st.selectbox("Proc", db.get_processes_list())
            rt = st.number_input("Rate", 0.0)
            if st.form_submit_button("Update"):
                db.save_rate(i, pr, rt)
                st.success("Updated")
        render_df(db.get_rates_df())
    
    elif sub_nav == "Proc":
        with st.form("f_pr"):
            n = st.text_input("Process")
            if st.form_submit_button("Save"):
                db.save_master("masters_processes", {"name":n})
                st.success("Saved")
        render_df(db.get_df("masters_processes"))
        
    elif sub_nav == "Other":
        c1, c2 = st.columns(2)
        with c1:
            n = st.text_input("Color")
            if st.button("Add Col"): db.save_master("masters_colors", {"name":n}); st.rerun()
        with c2:
            s = st.text_input("Size")
            if st.button("Add Sz"): db.save_master("masters_sizes", {"name":s}); st.rerun()

# --- 8. PAGE: PAYMENTS ---
elif selected_nav == "Pay":
    st.markdown("##### 💸 Payments")
    
    mode = st.radio("Type", ["Salary", "Advance"], horizontal=True)
    
    with st.container(border=True):
        pd_ = st.date_input("Date")
        ps = st.selectbox("Worker", [""] + db.get_staff_list())
        
        if ps:
            e, p, bal, _ = db.get_worker_history(ps)
            st.caption(f"Due: **₹ {bal:,.0f}**")
        
        amt = st.number_input("₹ Amount", min_value=1)
        rem = st.text_input("Note", mode)
        
        if st.button("CONFIRM PAYMENT"):
            if ps and amt > 0:
                db.save_payment(str(pd_), ps, amt, mode, rem)
                st.success("Recorded")
            else: st.error("Invalid")
    
    st.caption("Recent")
    df = db.get_df("payments")
    if not df.empty:
        df = df.sort_values(by="created_at", ascending=False).head(5)
        for _, r in df.iterrows():
            render_mobile_card(r['staff_name'], r['type'], "Paid", f"₹{r['amount']:,.0f}")

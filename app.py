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

# --- 2. MOBILE-FIRST CSS (BIGGER ICONS) ---
st.markdown("""
<style>
    /* APP THEME */
    .stApp { background-color: #F8FAFC; font-family: 'Inter', sans-serif; }
    
    /* HIDE DEFAULT HEADER */
    header[data-testid="stHeader"] { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }

    /* --- BIGGER NAVIGATION BAR --- */
    div[role="radiogroup"] {
        display: flex;
        flex-direction: row;
        flex-wrap: nowrap;
        justify-content: space-between;
        width: 100%;
        background: white;
        padding: 8px; /* Increased padding */
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        gap: 8px;
        border: 1px solid #E2E8F0;
    }
    
    div[role="radiogroup"] label {
        flex: 1;
        text-align: center;
        background: transparent;
        border: 1px solid transparent !important;
        border-radius: 12px !important;
        transition: all 0.2s;
        margin: 0 !important;
        
        /* BIGGER FONT & ICONS */
        padding: 12px 4px !important;
        font-size: 16px !important; /* Fixed readable size */
        font-weight: 600 !important;
        white-space: nowrap;
        color: #64748B !important;
        cursor: pointer;
    }
    
    div[role="radiogroup"] label:hover {
        background-color: #F1F5F9;
        color: #1E293B !important;
    }
    
    /* ACTIVE TAB STYLE */
    div[role="radiogroup"] label[data-checked="true"] {
        background-color: #EEF2FF !important;
        color: #4F46E5 !important;
        font-weight: 800 !important;
        border: 1px solid #C7D2FE !important;
        box-shadow: 0 2px 4px rgba(79, 70, 229, 0.1);
    }
    
    div[role="radiogroup"] label div:first-child { display: none; }
    div[role="radiogroup"] label div:last-child { margin-left: 0 !important; }

    /* --- INPUT FIELDS & BUTTONS --- */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox div[data-baseweb="select"] div {
        min-height: 50px !important;
        border-radius: 12px !important;
        border: 1px solid #E2E8F0 !important;
        font-size: 16px !important;
        background-color: white !important;
        color: #1E293B !important;
    }
    
    .stButton button {
        width: 100%;
        min-height: 50px;
        border-radius: 12px;
        font-weight: 700;
        background-color: #4F46E5;
        color: white;
        border: none;
        font-size: 16px;
    }

    /* --- MOBILE CARDS --- */
    .mobile-card {
        background: white; border-radius: 12px; padding: 16px;
        margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        border: 1px solid #F1F5F9;
    }
    .card-row { display: flex; justify-content: space-between; align-items: center; }
    
    /* --- STAT TILES --- */
    .stat-tile {
        background: white; padding: 12px; border-radius: 12px; text-align: center;
        border: 1px solid #E2E8F0; margin-bottom: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .stat-num { font-size: 20px; font-weight: 800; color: #1E293B; }
    .stat-desc { font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }

</style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def render_mobile_card(title, subtitle, metric_label, metric_value):
    st.markdown(f"""
    <div class="mobile-card">
        <div style="font-weight:700; font-size:15px; color:#111827; margin-bottom:4px;">{title}</div>
        <div style="font-size:13px; color:#6B7280; margin-bottom:8px;">{subtitle}</div>
        <div class="card-row">
            <span style="font-size:12px; font-weight:500; color:#9CA3AF;">{metric_label}</span>
            <span style="font-size:14px; font-weight:700; color:#4F46E5; background:#EEF2FF; padding:4px 10px; border-radius:8px;">{metric_value}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_stat_tile(label, value, color_border="#4F46E5"):
    st.markdown(f"""
    <div class="stat-tile" style="border-bottom: 4px solid {color_border};">
        <div class="stat-num">{value}</div>
        <div class="stat-desc">{label}</div>
    </div>
    """, unsafe_allow_html=True)

def render_df(df, file_name="data"):
    if df.empty: st.info("No data."); return
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(f"⬇️ CSV", csv, f"{file_name}.csv", "text/csv", key=f"dl_{file_name}")
    st.dataframe(df, use_container_width=True, hide_index=True)

# --- 4. NAVIGATION (BIGGER ICONS) ---
nav_items = {
    "Home": "🏠 Home",
    "Workers": "👷 Staff",
    "Masters": "⚙️ Setup",
    "Pay": "💰 Pay"
}
selected_label = st.radio("Nav", list(nav_items.values()), horizontal=True, label_visibility="collapsed")
selected_nav = next(key for key, value in nav_items.items() if value == selected_label)

# --- 5. PAGE: DASHBOARD ---
if selected_nav == "Home":
    st.markdown("##### 👋 Dashboard")
    
    pcs, earn, pending, active = db.get_dashboard_stats()
    
    c1, c2 = st.columns(2)
    with c1: render_stat_tile("Today Pcs", f"{pcs:,.0f}", "#10B981")
    with c2: render_stat_tile("Prod. Value", f"₹{earn:,.0f}", "#F59E0B")
    
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    
    c3, c4 = st.columns(2)
    with c3: render_stat_tile("Pending", f"₹{pending:,.0f}", "#EF4444")
    with c4: render_stat_tile("Active", str(active), "#6366F1")

    st.markdown("---")
    st.markdown("##### ⚡ Quick Entry")
    
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
        
        # Color Logic
        if bal < 0:
            bal_color = "#EF4444"
            status_text = "ADVANCE / OVERPAID"
        else:
            bal_color = "#10B981"
            status_text = "PENDING PAYABLE"
        
        # Balance Card
        st.markdown(f"""
        <div style="background:white; border:1px solid #E5E7EB; padding:20px; border-radius:16px; margin-bottom:20px; text-align:center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
            <div style="font-size:12px; color:#6B7280; font-weight:600; letter-spacing:1px;">CURRENT BALANCE</div>
            <div style="font-size:32px; font-weight:800; color:{bal_color}; margin: 5px 0;">₹ {abs(bal):,.0f}</div>
            <div style="font-size:11px; font-weight:700; color:{bal_color}; background-color:#F3F4F6; padding:4px 8px; border-radius:6px; display:inline-block;">{status_text}</div>
            <div style="margin-top:15px; border-top:1px solid #F3F4F6; padding-top:10px; display:flex; justify-content:space-around;">
                <div><div style="font-size:10px; color:#9CA3AF;">EARNED</div><div style="font-weight:700; color:#1F2937;">₹{e:,.0f}</div></div>
                <div><div style="font-size:10px; color:#9CA3AF;">PAID</div><div style="font-weight:700; color:#1F2937;">₹{p:,.0f}</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("##### 📜 Recent Work")
        if not hist_df.empty:
            for _, row in hist_df.head(10).iterrows():
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
    sub_nav = st.segmented_control("Type", t_list, default="Staff") 
    if not sub_nav: sub_nav = "Staff" 

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
            
            # Show simplified balance info
            color = "#EF4444" if bal < 0 else "#10B981"
            lbl = "Advance" if bal < 0 else "Due"
            st.markdown(f"<div style='background:#F3F4F6; padding:10px; border-radius:8px; text-align:center; font-weight:bold; color:{color}; margin-bottom:10px;'>Current: ₹ {abs(bal):,.0f} ({lbl})</div>", unsafe_allow_html=True)
        
        amt = st.number_input("₹ Amount", min_value=1)
        rem = st.text_input("Note", mode)
        
        if st.button("CONFIRM PAYMENT"):
            if ps and amt > 0:
                db.save_payment(str(pd_), ps, amt, mode, rem)
                st.success("Recorded")
            else: st.error("Invalid")
    
    st.markdown("##### 🕒 Recent")
    df = db.get_df("payments")
    if not df.empty:
        df = df.sort_values(by="created_at", ascending=False).head(5)
        for _, r in df.iterrows():
            render_mobile_card(r['staff_name'], r['type'], "Paid", f"₹{r['amount']:,.0f}")

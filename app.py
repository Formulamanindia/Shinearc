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

# --- 2. MOBILE-FIRST CSS ---
st.markdown("""
<style>
    /* APP THEME */
    .stApp { background-color: #F8FAFC; font-family: 'Inter', sans-serif; }
    
    /* HIDE DEFAULT HEADER */
    header[data-testid="stHeader"] { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }

    /* --- STICKY NAVIGATION BAR --- */
    div.stSegmentedControl {
        position: sticky;
        top: 0;
        z-index: 9999;
        background-color: #F8FAFC;
        padding-top: 10px;
        padding-bottom: 10px;
        margin-bottom: 10px;
    }

    /* --- DASHBOARD GRID (MOBILE 2x2, DESKTOP 4x1) --- */
    .dashboard-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr); /* Force 2 columns on Mobile */
        gap: 10px;
        margin-bottom: 20px;
    }
    
    /* Desktop Adjustment: 4 Columns */
    @media (min-width: 768px) {
        .dashboard-grid {
            grid-template-columns: repeat(4, 1fr);
        }
    }

    /* --- STAT TILES STYLE --- */
    .stat-tile-html {
        background: white; 
        padding: 15px 5px; 
        border-radius: 12px; 
        text-align: center;
        border: 1px solid #E2E8F0; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    .stat-num-html { font-size: 18px; font-weight: 800; color: #1E293B; margin-bottom: 4px; }
    .stat-desc-html { font-size: 11px; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }

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
    
    /* --- SEGMENTED CONTROL STYLING --- */
    div[data-baseweb="segmented-control"] {
        width: 100%;
        overflow-x: auto;
        background-color: white;
        border-radius: 12px;
        padding: 4px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }
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

def render_df(df, file_name="data"):
    if df.empty: st.info("No data."); return
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(f"⬇️ CSV", csv, f"{file_name}.csv", "text/csv", key=f"dl_{file_name}")
    st.dataframe(df, use_container_width=True, hide_index=True)

# --- 4. NAVIGATION (STICKY TOP) ---
nav_options = ["🏠 Home", "👷 Workers", "⚙️ Masters", "💰 Pay"]
selected_nav = st.segmented_control("Main Menu", nav_options, default="🏠 Home", label_visibility="collapsed")

if not selected_nav: selected_nav = "🏠 Home"

# --- 5. PAGE: DASHBOARD ---
if "Home" in selected_nav:
    st.markdown("##### 👋 Dashboard")
    
    pcs, earn, pending, active = db.get_dashboard_stats()
    
    # --- CUSTOM HTML GRID FOR 2x2 MOBILE VIEW ---
    st.markdown(f"""
    <div class="dashboard-grid">
        <div class="stat-tile-html" style="border-bottom: 4px solid #10B981;">
            <div class="stat-num-html">{pcs:,.0f}</div>
            <div class="stat-desc-html">Today Pcs</div>
        </div>
        <div class="stat-tile-html" style="border-bottom: 4px solid #F59E0B;">
            <div class="stat-num-html">₹{earn:,.0f}</div>
            <div class="stat-desc-html">Prod. Value</div>
        </div>
        <div class="stat-tile-html" style="border-bottom: 4px solid #EF4444;">
            <div class="stat-num-html">₹{pending:,.0f}</div>
            <div class="stat-desc-html">Pending Pay</div>
        </div>
        <div class="stat-tile-html" style="border-bottom: 4px solid #6366F1;">
            <div class="stat-num-html">{active}</div>
            <div class="stat-desc-html">Active Staff</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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
elif "Workers" in selected_nav:
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
        <div style="background:white; border:1px solid #E5E7EB; padding:15px; border-radius:12px; margin-bottom:15px; text-align:center; box-shadow: 0 2px 4px -1px rgba(0,0,0,0.05);">
            <div style="font-size:11px; color:#6B7280; font-weight:600; letter-spacing:1px;">CURRENT BALANCE</div>
            <div style="font-size:28px; font-weight:800; color:{bal_color}; margin: 4px 0;">₹ {abs(bal):,.0f}</div>
            <div style="font-size:10px; font-weight:700; color:{bal_color}; background-color:#F8FAFC; padding:4px 8px; border-radius:6px; display:inline-block;">{status_text}</div>
            <div style="margin-top:12px; border-top:1px solid #F1F5F9; padding-top:8px; display:flex; justify-content:space-around;">
                <div><div style="font-size:9px; color:#9CA3AF;">EARNED</div><div style="font-weight:700; color:#1F2937;">₹{e:,.0f}</div></div>
                <div><div style="font-size:9px; color:#9CA3AF;">PAID</div><div style="font-weight:700; color:#1F2937;">₹{p:,.0f}</div></div>
            </div>
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
elif "Masters" in selected_nav:
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
elif "Pay" in selected_nav:
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
            st.markdown(f"<div style='background:#F8FAFC; padding:8px; border-radius:8px; text-align:center; font-size:12px; border:1px solid #E2E8F0;'>Current: <span style='color:{color}; font-weight:bold;'>₹ {abs(bal):,.0f} ({lbl})</span></div>", unsafe_allow_html=True)
        
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

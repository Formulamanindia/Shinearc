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

# --- 2. CUSTOM CSS (ICON NAVIGATION) ---
st.markdown("""
<style>
    /* APP THEME */
    .stApp { background-color: #F8FAFC; font-family: 'Inter', sans-serif; }
    
    /* HIDE STREAMLIT ELEMENTS */
    header[data-testid="stHeader"] { visibility: hidden; }
    
    /* --- CUSTOM TOP NAVIGATION BAR --- */
    .nav-container {
        display: flex;
        justify-content: space-around;
        align-items: center;
        background-color: white;
        padding: 10px 5px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border: 1px solid #E2E8F0;
    }
    
    /* Hide the actual radio inputs */
    div[role="radiogroup"] {
        display: none;
    }

    /* Style for the custom buttons we will create */
    .nav-button {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 100%;
        padding: 8px;
        border-radius: 8px;
        cursor: pointer;
        color: #64748B;
        transition: all 0.2s ease;
        text-decoration: none;
        border: none;
        background: none;
    }
    
    .nav-button:hover {
        background-color: #F1F5F9;
        color: #1E293B;
    }
    
    .nav-button.active {
        color: #4F46E5;
        background-color: #EEF2FF;
    }
    
    .nav-icon {
        font-size: 20px;
        margin-bottom: 4px;
    }
    
    .nav-label {
        font-size: 11px;
        font-weight: 600;
    }

    /* --- MOBILE INPUTS --- */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox div[data-baseweb="select"] div {
        min-height: 48px !important;
        border-radius: 10px !important;
        border: 1px solid #E5E7EB !important;
        font-size: 16px !important;
        background-color: white !important;
    }
    
    .stButton button {
        width: 100%; min-height: 48px; border-radius: 10px; font-weight: 600;
        background-color: #4F46E5; color: white; border: none;
    }

    /* --- CARDS & STATS --- */
    .mobile-card {
        background: white; border-radius: 12px; padding: 15px;
        margin-bottom: 10px; border: 1px solid #F1F5F9; box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    .stat-tile {
        background: white; padding: 15px; border-radius: 12px; text-align: center;
        border: 1px solid #E5E7EB; margin-bottom: 10px;
    }
    .stat-num { font-size: 22px; font-weight: 700; color: #1F2937; }
    .stat-desc { font-size: 11px; color: #6B7280; text-transform: uppercase; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def render_mobile_card(title, subtitle, metric_label, metric_value):
    st.markdown(f"""
    <div class="mobile-card">
        <div style="font-weight:700; font-size:15px; color:#111827; margin-bottom:4px;">{title}</div>
        <div style="font-size:12px; color:#6B7280;">{subtitle}</div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:10px;">
            <span style="font-size:11px; color:#9CA3AF;">{metric_label}</span>
            <span style="font-size:13px; font-weight:600; color:#4F46E5; background:#EEF2FF; padding:2px 8px; border-radius:12px;">{metric_value}</span>
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

# --- 4. NAVIGATION LOGIC ---
if 'nav' not in st.session_state: st.session_state.nav = "Home"

# Create columns for the icon bar
c1, c2, c3, c4 = st.columns(4)

# Function to create an icon button
def nav_button(col, label, icon, key_val):
    with col:
        # Determine button style based on active state
        btn_type = "primary" if st.session_state.nav == key_val else "secondary"
        # We use standard buttons but they look cleaner due to CSS above
        if st.button(f"{icon}\n{label}", key=f"nav_{key_val}", use_container_width=True):
            st.session_state.nav = key_val
            st.rerun()

# Render the Top Bar
nav_button(c1, "Dash", "🏠", "Home")
nav_button(c2, "Workers", "👷", "Workers")
nav_button(c3, "Masters", "⚙️", "Masters")
nav_button(c4, "Pay", "💰", "Pay")

st.markdown("---")

# =========================================================
# PAGE: DASHBOARD (HOME)
# =========================================================
if st.session_state.nav == "Home":
    st.markdown("### 👋 Dashboard")
    
    pcs, earn, pending, active = db.get_dashboard_stats()
    
    c1, c2 = st.columns(2)
    with c1: render_stat_tile("Pcs Today", f"{pcs:,.0f}", "#10B981")
    with c2: render_stat_tile("Production", f"₹{earn:,.0f}", "#F59E0B")
    
    c3, c4 = st.columns(2)
    with c3: render_stat_tile("Pending", f"₹{pending:,.0f}", "#EF4444")
    with c4: render_stat_tile("Active", str(active), "#6366F1")

    st.markdown("#### ⚡ Quick Entry")
    with st.container(border=True):
        p_date = st.date_input("Date", datetime.date.today())
        
        c_staff, c_item = st.columns(2)
        p_staff = c_staff.selectbox("Staff", [""] + db.get_staff_list())
        p_item = c_item.selectbox("Item", [""] + db.get_items_list())
        
        c_proc, c_qty = st.columns(2)
        p_process = c_proc.selectbox("Process", [""] + db.get_processes_list())
        p_qty = c_qty.number_input("Qty", min_value=1, step=1)
        
        rate_val = db.get_rate(p_item, p_process) if p_item and p_process else 0.0
        p_rate = st.number_input("Rate (₹)", value=rate_val)
        
        if st.button("SAVE PRODUCTION"):
            if p_staff and p_item and p_process:
                db.save_production(str(p_date), p_staff, p_item, p_process, p_qty, p_rate)
                st.success("Saved!")
            else:
                st.error("Missing Info")

# =========================================================
# PAGE: WORKERS
# =========================================================
elif st.session_state.nav == "Workers":
    st.markdown("### 👷 Workers")
    
    search = st.selectbox("Select Worker", [""] + db.get_staff_list())
    
    if search:
        # Mini Info
        details = db.get_staff_details(search)
        role = details.get('role', 'Worker')
        sal_type = details.get('salary_type', 'Piece Rate')
        
        st.caption(f"**{role}** ({sal_type})")

        e, p, bal, hist_df = db.get_worker_history(search)
        
        # Balance Card
        st.markdown(f"""
        <div style="background:#EEF2FF; border:1px solid #C7D2FE; padding:15px; border-radius:12px; margin-bottom:15px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px; font-size:13px; color:#4338CA;">
                <span>Earned: ₹ {e:,.0f}</span>
                <span>Paid: ₹ {p:,.0f}</span>
            </div>
            <div style="font-size:20px; font-weight:800; color:{'#EF4444' if bal > 0 else '#10B981'}; text-align:center; margin-top:5px;">
                ₹ {bal:,.0f} <span style="font-size:12px; color:#6B7280; font-weight:500;">PENDING</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("**History**")
        if not hist_df.empty:
            for _, row in hist_df.head(10).iterrows():
                date_str = pd.to_datetime(row['date']).strftime('%d/%m')
                render_mobile_card(
                    f"{row['item']} ({row['process']})", 
                    f"{date_str} • Rate: ₹{row['rate']}",
                    "Total",
                    f"₹ {row['amount']:,.0f}"
                )
        else: st.info("No work history.")

# =========================================================
# PAGE: MASTERS
# =========================================================
elif st.session_state.nav == "Masters":
    st.markdown("### ⚙️ Masters")
    
    # Use tabs for cleaner mobile nav within section
    t1, t2, t3, t4, t5 = st.tabs(["Staff", "Item", "Proc", "Rate", "Other"])
    
    with t1: # Staff
        with st.form("staff_form"):
            n = st.text_input("Name")
            p = st.text_input("Phone")
            r = st.selectbox("Role", ["Stitching", "Helper", "Cutting", "Ironing"])
            
            st.markdown("---")
            sal_type = st.radio("Type", ["Piece Rate", "Salaried"], horizontal=True)
            m_sal = 0.0
            if sal_type == "Salaried":
                m_sal = st.number_input("Monthly Salary", step=500.0)
            
            if st.form_submit_button("Save Staff"): 
                db.save_staff(n, p, r, sal_type, m_sal)
                st.success("Saved!")
        
        st.markdown("**List**")
        st.dataframe(db.get_df("masters_staff")[['name', 'role']], use_container_width=True, hide_index=True)

    with t2: # Items
        with st.form("item_form"):
            n = st.text_input("Item Name")
            c = st.text_input("Category")
            if st.form_submit_button("Save Item"): 
                db.save_master("masters_items", {"name":n, "category":c})
                st.success("Saved!")
        st.dataframe(db.get_df("masters_items"), use_container_width=True, hide_index=True)

    with t3: # Process
        with st.form("proc_form"):
            n = st.text_input("Process Name")
            if st.form_submit_button("Save"):
                db.save_master("masters_processes", {"name":n})
                st.success("Saved!")
        st.dataframe(db.get_df("masters_processes"), use_container_width=True, hide_index=True)

    with t4: # Rate
        with st.form("rate_form"):
            i = st.selectbox("Item", db.get_items_list())
            p = st.selectbox("Process", db.get_processes_list())
            r = st.number_input("Rate", 0.0)
            if st.form_submit_button("Set Rate"):
                db.save_rate(i, p, r)
                st.success("Saved!")
        st.dataframe(db.get_rates_df(), use_container_width=True, hide_index=True)

    with t5: # Colors/Sizes
        c1, c2 = st.columns(2)
        with c1:
            n = st.text_input("Color")
            if st.button("Add Color"): db.save_master("masters_colors", {"name":n}); st.rerun()
        with c2:
            s = st.text_input("Size")
            if st.button("Add Size"): db.save_master("masters_sizes", {"name":s}); st.rerun()

# =========================================================
# PAGE: PAYMENTS
# =========================================================
elif st.session_state.nav == "Pay":
    st.markdown("### 💸 Payments")
    
    pay_mode = st.radio("Type", ["Salary", "Advance"], horizontal=True)
    
    with st.container(border=True):
        p_date = st.date_input("Date", datetime.date.today())
        p_staff = st.selectbox("Worker", [""] + db.get_staff_list(), key="pay_s")
        
        if p_staff:
            e, p, bal, _ = db.get_worker_history(p_staff)
            st.caption(f"Pending: **₹ {bal:,.0f}**")
        
        amt = st.number_input("Amount (₹)", min_value=1)
        rem = st.text_input("Note", pay_mode)
        
        if st.button(f"CONFIRM {pay_mode.upper()}"):
            if p_staff and amt > 0:
                db.save_payment(str(p_date), p_staff, amt, pay_mode, rem)
                st.success("Recorded!")
            else:
                st.error("Check details")
                
    st.markdown("#### 🕒 History")
    df_pay = db.get_df("payments")
    if not df_pay.empty:
        df_pay = df_pay.sort_values(by="created_at", ascending=False).head(5)
        for _, row in df_pay.iterrows():
            render_mobile_card(
                row['staff_name'], 
                f"{pd.to_datetime(row['date']).strftime('%d %b')} | {row['type']}", 
                "Paid", 
                f"₹ {row['amount']:,.0f}"
            )

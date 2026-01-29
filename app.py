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
    header[data-testid="stHeader"] { visibility: hidden; }
    
    /* NAVIGATION BAR */
    div[role="radiogroup"] {
        display: flex; flex-direction: row; justify-content: space-between;
        width: 100%; background: white; padding: 5px; border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px; overflow-x: auto;
    }
    div[role="radiogroup"] label {
        flex: 1; text-align: center; padding: 10px; border-radius: 8px; 
        border: none !important; margin: 0 2px; transition: all 0.2s;
    }
    div[role="radiogroup"] label[data-checked="true"] {
        background-color: #4F46E5 !important; color: white !important; font-weight: bold;
    }

    /* INPUTS & BUTTONS */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox div[data-baseweb="select"] div {
        min-height: 50px !important; border-radius: 12px !important;
        border: 1px solid #E5E7EB !important; font-size: 16px !important; background-color: white !important;
    }
    .stButton button {
        width: 100%; min-height: 50px; border-radius: 12px; font-weight: 600;
        font-size: 16px; background-color: #4F46E5; color: white; border: none;
    }

    /* CARDS */
    .mobile-card {
        background: white; border-radius: 16px; padding: 16px;
        margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); border: 1px solid #F1F5F9;
    }
    .card-title { font-size: 16px; font-weight: 700; color: #111827; margin-bottom: 4px; }
    .card-subtitle { font-size: 13px; color: #6B7280; font-weight: 500; }
    .card-row { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; }
    .card-metric { font-size: 14px; font-weight: 600; color: #4F46E5; background: #EEF2FF; padding: 4px 10px; border-radius: 20px; }
    
    /* STAT TILES */
    .stat-tile {
        background: white; padding: 15px; border-radius: 12px; text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid #E5E7EB; height: 100%;
    }
    .stat-num { font-size: 24px; font-weight: 800; color: #1F2937; }
    .stat-desc { font-size: 12px; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def render_mobile_card(title, subtitle, metric_label, metric_value):
    st.markdown(f"""
    <div class="mobile-card">
        <div class="card-title">{title}</div>
        <div class="card-subtitle">{subtitle}</div>
        <div class="card-row">
            <span style="color:#9CA3AF; font-size:12px;">{metric_label}</span>
            <span class="card-metric">{metric_value}</span>
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

# --- 4. NAVIGATION ---
nav_options = ["🏠 Home", "👷 Workers", "⚙️ Masters", "💰 Pay"]
selected_nav = st.radio("Navigation", nav_options, horizontal=True, label_visibility="collapsed")

# --- 5. PAGE: DASHBOARD ---
if "Home" in selected_nav:
    st.markdown("### 👋 Hello, Manager")
    
    pcs, earn, pending, active = db.get_dashboard_stats()
    
    c1, c2 = st.columns(2)
    with c1: render_stat_tile("Pcs Today", f"{pcs:,.0f}", "#10B981")
    with c2: render_stat_tile("Production", f"₹{earn:,.0f}", "#F59E0B")
    
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    
    c3, c4 = st.columns(2)
    with c3: render_stat_tile("Pending Pay", f"₹{pending:,.0f}", "#EF4444")
    with c4: render_stat_tile("Active Staff", str(active), "#6366F1")

    st.markdown("---")
    
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
                st.success("Saved Successfully!")
            else:
                st.error("Missing Info")

# --- 6. PAGE: WORKERS ---
elif "Workers" in selected_nav:
    st.markdown("### 👷 Worker List")
    
    staff_list = db.get_staff_list()
    search = st.selectbox("Select Worker", [""] + staff_list)
    
    if search:
        # Get basic details including salary type
        details = db.get_staff_details(search)
        role = details.get('role', 'Worker')
        sal_type = details.get('salary_type', 'Piece Rate')
        
        # Display Basic Info Card
        st.markdown(f"""
        <div style="background:white; padding:15px; border-radius:12px; border:1px solid #E5E7EB; margin-bottom:15px;">
            <div style="font-size:18px; font-weight:700;">{search}</div>
            <div style="color:#6B7280; font-size:13px;">{role} • {sal_type}</div>
        </div>
        """, unsafe_allow_html=True)

        e, p, bal, hist_df = db.get_worker_history(search)
        
        # Financial Card
        st.markdown(f"""
        <div class="mobile-card" style="background:#EEF2FF; border:1px solid #C7D2FE;">
            <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                <span style="color:#4338CA; font-weight:600;">Prod. Value</span>
                <span style="font-weight:700;">₹ {e:,.0f}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                <span style="color:#4338CA; font-weight:600;">Paid</span>
                <span style="font-weight:700;">₹ {p:,.0f}</span>
            </div>
            <hr style="border-color:#C7D2FE;">
            <div style="display:flex; justify-content:space-between; font-size:18px;">
                <span style="color:#4338CA; font-weight:700;">Balance</span>
                <span style="font-weight:800; color:{'#EF4444' if bal > 0 else '#10B981'}">₹ {bal:,.0f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### 📜 Work History")
        if not hist_df.empty:
            for _, row in hist_df.head(10).iterrows():
                date_str = pd.to_datetime(row['date']).strftime('%d %b')
                render_mobile_card(
                    f"{row['item']} - {row['process']}", 
                    f"{date_str} | Rate: ₹{row['rate']}",
                    "Amount",
                    f"₹ {row['amount']:,.0f}"
                )
        else: st.info("No work history found.")

# --- 7. PAGE: MASTERS (UPDATED STAFF FORM) ---
elif "Masters" in selected_nav:
    st.markdown("### ⚙️ Settings")
    type_ = st.selectbox("Manage", ["Staff", "Items", "Processes", "Rates", "Colors", "Sizes"])
    
    with st.form("master_form"):
        st.markdown(f"**Add New {type_}**")
        
        if type_ == "Staff":
            n = st.text_input("Name")
            p = st.text_input("Phone")
            r = st.selectbox("Role", ["Stitching", "Helper", "Cutting", "Ironing"])
            
            st.markdown("---")
            # --- NEW SALARY TYPE LOGIC ---
            sal_type = st.radio("Salary Type", ["Piece Rate", "Salaried"], horizontal=True)
            m_sal = 0.0
            if sal_type == "Salaried":
                m_sal = st.number_input("Monthly Salary (₹)", min_value=0.0, step=500.0)
            else:
                st.caption("ℹ️ Calculation based on daily production entry.")
            # -----------------------------

            if st.form_submit_button("Save Staff"): 
                db.save_staff(n, p, r, sal_type, m_sal)
                st.success("Staff Saved!")
            
        elif type_ == "Items":
            n = st.text_input("Item Name")
            c = st.text_input("Category")
            if st.form_submit_button("Save Item"): db.save_master("masters_items", {"name":n, "category":c}); st.success("Done")
            
        elif type_ == "Rates":
            i = st.selectbox("Item", db.get_items_list())
            p = st.selectbox("Process", db.get_processes_list())
            r = st.number_input("Rate (₹)", 0.0)
            if st.form_submit_button("Set Rate"): db.save_rate(i, p, r); st.success("Done")
            
        else:
            n = st.text_input("Name")
            if st.form_submit_button("Save"): 
                coll = f"masters_{type_.lower()}"
                db.save_master(coll, {"name":n})
                st.success("Done")

    st.markdown("---")
    st.markdown(f"**Existing {type_}**")
    if type_ == "Rates":
        df = db.get_rates_df()
        if not df.empty: st.dataframe(df, use_container_width=True)
    else:
        coll = f"masters_{type_.lower()}"
        df = db.get_df(coll)
        if not df.empty: st.dataframe(df, use_container_width=True)

# --- 8. PAGE: PAYMENTS ---
elif "Pay" in selected_nav:
    st.markdown("### 💸 Payments")
    pay_mode = st.radio("Mode", ["Salary / Payment", "Advance"], horizontal=True)
    
    with st.container(border=True):
        p_date = st.date_input("Date", datetime.date.today())
        p_staff = st.selectbox("Worker", [""] + db.get_staff_list())
        
        if p_staff:
            e, p, bal, _ = db.get_worker_history(p_staff)
            st.caption(f"Current Pending: ₹ {bal:,.0f}")
        
        amount = st.number_input("Amount (₹)", min_value=1)
        note = st.text_input("Note", pay_mode)
        
        if st.button(f"CONFIRM {pay_mode.upper()}"):
            if p_staff and amount > 0:
                p_type = "Salary" if "Salary" in pay_mode else "Advance"
                db.save_payment(str(p_date), p_staff, amount, p_type, note)
                st.success("Recorded Successfully!")
            else:
                st.error("Enter Amount & Staff")
                
    st.markdown("#### 🕒 Recent Transactions")
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

import streamlit as st
import pandas as pd
import db_manager as db
import datetime

# --- 1. CONFIGURATION & CSS ---
st.set_page_config(page_title="Garment ERP", page_icon="🧵", layout="wide")

st.markdown("""
<style>
    /* GLOBAL BACKGROUND */
    .stApp {
        background-color: #F3F4F6; /* Light Grey */
    }
    
    /* REMOVE DEFAULT PADDING */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* --- CARDS DESIGN --- */
    .stat-card {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        text-align: center;
        border-left: 5px solid #4F46E5; /* Indigo Accent */
        margin-bottom: 10px;
    }
    .stat-value {
        font-size: 28px;
        font-weight: 700;
        color: #1F2937;
    }
    .stat-label {
        font-size: 14px;
        color: #6B7280;
        font-weight: 500;
        text-transform: uppercase;
    }

    /* --- TABLES --- */
    .stDataFrame {
        background-color: white;
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    /* --- FORMS & INPUTS --- */
    /* Force inputs to be white with dark text */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox div[data-baseweb="select"] div {
        background-color: #FFFFFF !important;
        color: #111827 !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 8px !important;
    }
    
    /* Input Labels */
    .stMarkdown label {
        color: #374151 !important;
        font-weight: 600 !important;
    }

    /* --- BUTTONS --- */
    .stButton button {
        width: 100%;
        background-color: #4F46E5;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        border: none;
        padding: 10px;
    }
    .stButton button:hover {
        background-color: #4338ca;
    }

    /* --- TABS --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 8px 16px;
        color: #6B7280;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4F46E5 !important;
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("### 🧵 Garment ERP")
    selected_tab = st.radio("Navigate", ["Dashboard", "Workers", "Masters", "Payments"], label_visibility="collapsed")
    st.markdown("---")
    st.caption("v2.0 | Production Manager")

# --- 3. DASHBOARD ---
if selected_tab == "Dashboard":
    st.markdown("## 📊 Factory Dashboard")
    
    # Fetch Data
    pcs_today, earn_today, pending_month, active_staff = db.get_dashboard_stats()
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown(f"""<div class="stat-card">
            <div class="stat-value">{pcs_today:,.0f}</div>
            <div class="stat-label">Pcs Done Today</div>
        </div>""", unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""<div class="stat-card">
            <div class="stat-value">₹ {earn_today:,.0f}</div>
            <div class="stat-label">Staff Earnings (Today)</div>
        </div>""", unsafe_allow_html=True)
        
    with c3:
        st.markdown(f"""<div class="stat-card" style="border-left-color: #EF4444;">
            <div class="stat-value">₹ {pending_month:,.0f}</div>
            <div class="stat-label">Pending Payments (Month)</div>
        </div>""", unsafe_allow_html=True)
        
    with c4:
        st.markdown(f"""<div class="stat-card" style="border-left-color: #10B981;">
            <div class="stat-value">{active_staff}</div>
            <div class="stat-label">Active Staff</div>
        </div>""", unsafe_allow_html=True)

    # Quick Production Entry Form on Dashboard
    st.markdown("### ⚡ Quick Production Entry")
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        p_date = c1.date_input("Date", datetime.date.today())
        p_staff = c2.selectbox("Staff", [""] + db.get_staff_list())
        p_item = c3.selectbox("Item", [""] + db.get_items_list())
        p_process = c4.selectbox("Process", [""] + db.get_processes_list())
        
        c5, c6, c7 = st.columns([1, 1, 2])
        # Auto-fetch rate
        current_rate = db.get_rate(p_item, p_process) if p_item and p_process else 0.0
        p_rate = c5.number_input("Rate", value=current_rate)
        p_qty = c6.number_input("Qty", min_value=1)
        
        if c7.button("✅ Save Production"):
            if p_staff and p_item and p_process and p_qty > 0:
                db.save_production(str(p_date), p_staff, p_item, p_process, p_qty, p_rate)
                st.success("Entry Saved!")
                st.rerun()
            else:
                st.error("Please fill all fields")

# --- 4. WORKERS ---
elif selected_tab == "Workers":
    st.markdown("## 👷 Worker Management")
    
    col_list, col_details = st.columns([1, 3])
    
    with col_list:
        st.markdown("### Select Worker")
        staff_names = db.get_staff_list()
        selected_worker = st.selectbox("Choose a worker to view details", [""] + staff_names)
        
        if selected_worker:
            details = db.get_staff_details(selected_worker)
            with st.container(border=True):
                st.markdown(f"**{details.get('name')}**")
                st.caption(f"Phone: {details.get('phone', '-')}")
                st.caption(f"Role: {details.get('role', '-')}")

    with col_details:
        if selected_worker:
            earned, paid, pending, df_hist = db.get_worker_history(selected_worker)
            
            # Mini Stats for Worker
            s1, s2, s3 = st.columns(3)
            s1.metric("Total Earnings", f"₹ {earned:,.0f}")
            s2.metric("Total Paid", f"₹ {paid:,.0f}")
            s3.metric("Pending Balance", f"₹ {pending:,.0f}", delta_color="inverse")
            
            st.markdown("### 📅 Production History")
            if not df_hist.empty:
                # Clean up dataframe for display
                display_df = df_hist[['date', 'item', 'process', 'qty', 'rate', 'amount']].copy()
                display_df['date'] = pd.to_datetime(display_df['date']).dt.date
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("No production history found.")
        else:
            st.info("👈 Select a worker from the left list to see details.")

# --- 5. MASTERS ---
elif selected_tab == "Masters":
    st.markdown("## ⚙️ Master Configuration")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Items", "Staff", "Colors & Sizes", "Processes", "Rates"])
    
    with tab1: # Product Master
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.container(border=True):
                st.markdown("**Add Item**")
                i_name = st.text_input("Item Name")
                i_cat = st.text_input("Category (e.g. Shirt)")
                if st.button("Save Item"):
                    db.save_master("masters_items", {"name": i_name, "category": i_cat})
                    st.success("Saved")
                    st.rerun()
        with c2:
            st.dataframe(db.get_df("masters_items"), use_container_width=True)

    with tab2: # Staff Master
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.container(border=True):
                st.markdown("**Add Staff**")
                s_name = st.text_input("Staff Name")
                s_phone = st.text_input("Phone")
                s_role = st.selectbox("Role", ["Stitching", "Cutting", "Helper", "Packing"])
                if st.button("Save Staff"):
                    db.save_master("masters_staff", {"name": s_name, "phone": s_phone, "role": s_role})
                    st.success("Saved")
                    st.rerun()
        with c2:
            st.dataframe(db.get_df("masters_staff"), use_container_width=True)

    with tab3: # Color/Size
        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.markdown("**Add Color**")
                col_n = st.text_input("Color Name")
                if st.button("Save Color"):
                    db.save_master("masters_colors", {"name": col_n})
                    st.rerun()
            st.dataframe(db.get_df("masters_colors"), use_container_width=True)
        with c2:
            with st.container(border=True):
                st.markdown("**Add Size**")
                siz_n = st.text_input("Size Name")
                if st.button("Save Size"):
                    db.save_master("masters_sizes", {"name": siz_n})
                    st.rerun()
            st.dataframe(db.get_df("masters_sizes"), use_container_width=True)

    with tab4: # Process Master
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.container(border=True):
                st.markdown("**Add Process**")
                p_name = st.text_input("Process Name (e.g. Buttoning)")
                if st.button("Save Process"):
                    db.save_master("masters_processes", {"name": p_name})
                    st.rerun()
        with c2:
            st.dataframe(db.get_df("masters_processes"), use_container_width=True)

    with tab5: # Rate Master
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.container(border=True):
                st.markdown("**Set Piece Rates**")
                r_item = st.selectbox("Item", db.get_items_list())
                r_proc = st.selectbox("Process", db.get_processes_list())
                r_val = st.number_input("Rate (₹)", min_value=0.0)
                if st.button("Update Rate"):
                    db.save_rate(r_item, r_proc, r_val)
                    st.success("Rate Updated")
                    st.rerun()
        with c2:
            st.dataframe(db.get_rates_df(), use_container_width=True)

# --- 6. PAYMENTS ---
elif selected_tab == "Payments":
    st.markdown("## 💸 Payments & Advances")
    
    tab_pay, tab_adv = st.tabs(["Make Payment", "Record Advance"])
    
    # Helper to calculate pending
    def render_pending_info(staff_name):
        if staff_name:
            e, p, bal, _ = db.get_worker_history(staff_name)
            st.info(f"**Current Balance:** ₹ {bal:,.2f} (Earned: {e} - Paid: {p})")

    with tab_pay:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            pay_date = c1.date_input("Payment Date", datetime.date.today())
            pay_staff = c2.selectbox("Select Staff", [""] + db.get_staff_list(), key="pay_s")
            
            render_pending_info(pay_staff)
            
            c3, c4 = st.columns(2)
            pay_amt = c3.number_input("Amount Paid (₹)", min_value=0.0, key="p_amt")
            pay_rem = c4.text_input("Remarks", "Salary Payment")
            
            if st.button("💾 Record Payment", type="primary"):
                if pay_staff and pay_amt > 0:
                    db.save_payment(str(pay_date), pay_staff, pay_amt, "Salary", pay_rem)
                    st.success("Payment Recorded")
                    st.rerun()
        
        st.markdown("#### Recent Payments")
        df_pay = db.get_df("payments")
        if not df_pay.empty:
            st.dataframe(df_pay[df_pay['type'] == 'Salary'], use_container_width=True)

    with tab_adv:
        with st.container(border=True):
            st.warning("⚠️ Recording Advance Payment")
            c1, c2 = st.columns(2)
            adv_date = c1.date_input("Advance Date", datetime.date.today())
            adv_staff = c2.selectbox("Select Staff", [""] + db.get_staff_list(), key="adv_s")
            
            render_pending_info(adv_staff)
            
            c3, c4 = st.columns(2)
            adv_amt = c3.number_input("Advance Amount (₹)", min_value=0.0, key="a_amt")
            adv_rem = c4.text_input("Remarks", "Advance Given")
            
            if st.button("💾 Record Advance"):
                if adv_staff and adv_amt > 0:
                    db.save_payment(str(adv_date), adv_staff, adv_amt, "Advance", adv_rem)
                    st.success("Advance Recorded")
                    st.rerun()
        
        st.markdown("#### Recent Advances")
        df_pay = db.get_df("payments")
        if not df_pay.empty:
            st.dataframe(df_pay[df_pay['type'] == 'Advance'], use_container_width=True)

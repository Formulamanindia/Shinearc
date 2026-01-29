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
    .block-container { padding-top: 1rem !important; }

    /* --- STICKY NAVIGATION --- */
    div.stSegmentedControl {
        position: sticky; top: 0; z-index: 9999;
        background-color: #F8FAFC; padding: 10px 0; margin-bottom: 10px;
    }

    /* --- DASHBOARD GRID --- */
    .dashboard-grid {
        display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 20px;
    }
    @media (min-width: 768px) {
        .dashboard-grid { grid-template-columns: repeat(4, 1fr); }
    }

    /* --- STAFF GRID --- */
    .staff-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); 
        gap: 12px;
        margin-top: 10px;
    }
    
    .staff-card-html {
        background: white; 
        border-radius: 16px; 
        padding: 15px; 
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03); 
        text-align: center;
        transition: transform 0.1s;
    }
    .staff-card-html:active { transform: scale(0.98); }

    /* --- BEAUTIFUL TABLE CSS --- */
    .styled-table {
        border-collapse: collapse;
        margin: 15px 0;
        font-size: 14px;
        font-family: 'Inter', sans-serif;
        width: 100%;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.05);
        border-radius: 10px;
        overflow: hidden;
        background-color: white;
    }
    .styled-table thead tr {
        background-color: #4F46E5;
        color: #ffffff;
        text-align: left;
        font-weight: 600;
    }
    .styled-table th, .styled-table td {
        padding: 12px 15px;
    }
    .styled-table tbody tr {
        border-bottom: 1px solid #dddddd;
    }
    .styled-table tbody tr:nth-of-type(even) {
        background-color: #F9FAFB;
    }
    .styled-table tbody tr:last-of-type {
        border-bottom: 3px solid #4F46E5;
    }
    /* Status Colors in Table */
    .status-present { color: #10B981; font-weight: 700; }
    .status-absent { color: #EF4444; font-weight: 700; }
    .status-half { color: #F59E0B; font-weight: 700; }

    /* --- INPUTS & BUTTONS --- */
    .stTextInput input, .stNumberInput input, .stDateInput input {
        background-color: white !important; border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important; min-height: 48px !important;
        font-size: 15px !important; color: #1E293B !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }
    
    div[data-baseweb="select"] > div {
        background-color: white !important; border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important; min-height: 48px !important;
        color: #1E293B !important; box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }

    .stButton button {
        width: 100%; min-height: 48px; border-radius: 12px; font-weight: 600;
        background-color: #4F46E5; color: white; border: none;
        box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2);
    }

    /* --- CARDS & TILES --- */
    .mobile-card {
        background: white; border-radius: 12px; padding: 16px;
        margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid #F1F5F9;
    }
    .card-row { display: flex; justify-content: space-between; align-items: center; }
    
    .stat-tile-html {
        background: white; padding: 15px 5px; border-radius: 12px; text-align: center;
        border: 1px solid #E2E8F0; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;
    }
    .stat-num-html { font-size: 18px; font-weight: 800; color: #1E293B; margin-bottom: 4px; }
    .stat-desc-html { font-size: 11px; color: #64748B; font-weight: 600; text-transform: uppercase; }

    div[data-baseweb="segmented-control"] {
        width: 100%; overflow-x: auto; background-color: white;
        border-radius: 12px; padding: 4px; border: 1px solid #E2E8F0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }
</style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def render_mobile_card(title, subtitle, metric_label, metric_value):
    st.markdown(f"""
    <div class="mobile-card">
        <div style="font-weight:700; font-size:15px; color:#111827; margin-bottom:4px;">{title}</div>
        <div style="font-size:12px; color:#6B7280; margin-bottom:8px;">{subtitle}</div>
        <div class="card-row">
            <span style="font-size:11px; color:#9CA3AF; font-weight:500;">{metric_label}</span>
            <span style="font-size:13px; font-weight:700; color:#4F46E5; background:#EEF2FF; padding:4px 10px; border-radius:8px;">{metric_value}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_df(df, file_name="data"):
    if df.empty: st.info("No data."); return
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(f"⬇️ CSV", csv, f"{file_name}.csv", "text/csv", key=f"dl_{file_name}")
    st.dataframe(df, use_container_width=True, hide_index=True)

# --- 4. NAVIGATION ---
nav_options = ["🏠 Home", "🏭 Work", "👥 Staff", "⚙️ Masters"]
selected_nav = st.segmented_control("Main Menu", nav_options, default="🏠 Home", label_visibility="collapsed")
if not selected_nav: selected_nav = "🏠 Home"

# --- 5. PAGE: DASHBOARD ---
if "Home" in selected_nav:
    st.markdown("##### 👋 Dashboard")
    
    pcs, earn, pending, active = db.get_dashboard_stats()
    
    # Dashboard Grid
    dashboard_html = f"""
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
    """
    st.markdown(dashboard_html, unsafe_allow_html=True)

    # --- COLLAPSIBLE QUICK ENTRY ---
    with st.expander("⚡ **Quick Work Entry**", expanded=False):
        with st.container(border=True):
            p_date = st.date_input("Date", datetime.date.today())
            c_lot, c_bun = st.columns(2)
            p_lot = c_lot.text_input("Lot No. *")
            p_bundle = c_bun.text_input("Bundle No. *")
            c_staff, c_item = st.columns(2)
            p_staff = c_staff.selectbox("Worker", [""] + db.get_staff_list())
            p_item = c_item.selectbox("Item", [""] + db.get_items_list())
            c_proc, c_qty = st.columns(2)
            p_process = c_proc.selectbox("Process", [""] + db.get_processes_list())
            p_qty = c_qty.number_input("Qty", min_value=1, step=1)
            
            if st.button("SAVE ENTRY"):
                if not p_lot or not p_bundle: st.error("⚠️ Lot/Bundle Missing!")
                elif not p_staff or not p_item: st.error("⚠️ Staff/Item Missing!")
                else:
                    auto_rate = db.get_rate(p_item, p_process)
                    db.save_production(str(p_date), p_staff, p_item, p_process, p_qty, auto_rate, p_lot, p_bundle)
                    if auto_rate == 0: st.warning("⚠️ Saved with Rate: 0")
                    else: st.success(f"✅ Saved! Rate applied: ₹{auto_rate}")

    # --- STAFF OVERVIEW GRID ---
    st.markdown("##### 👥 Staff Overview")
    staff_list = db.get_staff_list()
    
    if staff_list:
        cards_html = '<div class="staff-grid">'
        for s_name in staff_list:
            e, p, bal, _ = db.get_worker_history(s_name)
            month_paid = db.get_staff_month_paid(s_name)
            bal_col = "#EF4444" if bal < 0 else "#10B981"
            
            card = f"""
<div class="staff-card-html">
<div style="font-weight:700; font-size:15px; color:#1F2937;">{s_name}</div>
<div style="font-size:10px; color:#6B7280; margin-top:6px; text-transform:uppercase; letter-spacing:0.5px;">Paid This Month</div>
<div style="font-weight:700; font-size:16px; color:#4F46E5;">₹ {month_paid:,.0f}</div>
<div style="font-size:10px; color:#6B7280; margin-top:6px; text-transform:uppercase; letter-spacing:0.5px;">Balance</div>
<div style="font-weight:700; font-size:16px; color:{bal_col};">₹ {bal:,.0f}</div>
</div>"""
            cards_html += card
            
        cards_html += '</div>'
        st.markdown(cards_html, unsafe_allow_html=True)
    else:
        st.info("No Staff members found. Go to 'Masters' to add one.")

# --- 6. PAGE: WORK ---
elif "Work" in selected_nav:
    st.markdown("##### 🏭 Work Management")
    
    tab1, tab2, tab3 = st.tabs(["Production", "Attendance", "Log"])
    
    with tab1:
        with st.container(border=True):
            st.markdown("**Production Entry**")
            p_date = st.date_input("Date", datetime.date.today(), key="w_date")
            c_lot, c_bun = st.columns(2)
            p_lot = c_lot.text_input("Lot No. *", key="w_lot")
            p_bundle = c_bun.text_input("Bundle No. *", key="w_bun")
            c_staff, c_item = st.columns(2)
            p_staff = c_staff.selectbox("Worker", [""] + db.get_staff_list(), key="w_staff")
            p_item = c_item.selectbox("Item", [""] + db.get_items_list(), key="w_item")
            c_proc, c_qty = st.columns(2)
            p_process = c_proc.selectbox("Process", [""] + db.get_processes_list(), key="w_proc")
            p_qty = c_qty.number_input("Qty", min_value=1, step=1, key="w_qty")
            
            if st.button("CONFIRM WORK", type="primary"):
                if p_lot and p_bundle and p_staff and p_item:
                    auto_rate = db.get_rate(p_item, p_process)
                    db.save_production(str(p_date), p_staff, p_item, p_process, p_qty, auto_rate, p_lot, p_bundle)
                    if auto_rate == 0: st.warning("⚠️ Saved with Rate: 0")
                    else: st.success(f"✅ Recorded! Rate applied: ₹{auto_rate}")
                else: st.error("Missing Data")
    
    with tab2:
        # MARK ATTENDANCE
        with st.container(border=True):
            st.markdown("**Mark Attendance**")
            a_date = st.date_input("Date", datetime.date.today(), key="a_date")
            a_staff = st.selectbox("Staff", [""] + db.get_staff_list(), key="a_staff")
            a_status = st.radio("Status", ["Present", "Absent", "Half Day"], horizontal=True)
            if st.button("MARK ATTENDANCE"):
                if a_staff:
                    db.save_attendance(str(a_date), a_staff, a_status)
                    st.success("Marked!")
        
        # --- ATTENDANCE LOG VIEWER ---
        st.markdown("---")
        st.subheader("📋 Attendance Logs")
        
        df_att = db.get_df("attendance")
        if not df_att.empty:
            df_att['date'] = pd.to_datetime(df_att['date'])
            
            # FILTERS
            c_date, c_emp = st.columns(2)
            # Date Filter
            use_date = c_date.checkbox("Filter by Date")
            filter_date = c_date.date_input("Select Date", datetime.date.today()) if use_date else None
            # Employee Filter
            filter_emp = c_emp.selectbox("Filter by Staff", ["All"] + db.get_staff_list())
            
            # Apply Filters
            if use_date:
                df_att = df_att[df_att['date'].dt.date == filter_date]
            if filter_emp != "All":
                df_att = df_att[df_att['staff_name'] == filter_emp]
            
            if not df_att.empty:
                # Format for Table
                df_att = df_att.sort_values(by="date", ascending=False)
                df_att['Formatted Date'] = df_att['date'].dt.strftime('%d-%b-%Y')
                
                # Apply Color to Status
                def color_status(val):
                    if val == "Present": return f'<span class="status-present">Present</span>'
                    elif val == "Absent": return f'<span class="status-absent">Absent</span>'
                    return f'<span class="status-half">Half Day</span>'
                
                df_att['Status'] = df_att['status'].apply(color_status)
                
                # Select Columns
                final_df = df_att[['Formatted Date', 'staff_name', 'Status']]
                final_df.columns = ['Date', 'Staff Name', 'Status']
                
                # Convert to HTML Table
                html = final_df.to_html(classes='styled-table', index=False, escape=False)
                st.markdown(html, unsafe_allow_html=True)
            else:
                st.info("No records found for selected filters.")
        else:
            st.info("No attendance data yet.")
    
    with tab3:
        df_prod = db.get_df("production")
        if not df_prod.empty:
            df_prod['date'] = pd.to_datetime(df_prod['date'])
            df_prod = df_prod.sort_values(by="date", ascending=False)
            df_disp = df_prod[['date', 'staff_name', 'qty', 'amount', 'lot_no']].copy()
            df_disp['date'] = df_disp['date'].dt.strftime('%d-%b')
            render_df(df_disp, "work_log")

# --- 7. PAGE: STAFF ---
elif "Staff" in selected_nav:
    st.markdown("##### 👥 Staff Management")
    t_stats, t_pay = st.tabs(["📊 Stats & History", "💸 Payments"])
    
    with t_stats:
        search = st.selectbox("Select Staff Member", [""] + db.get_staff_list(), key="staff_search")
        
        if search:
            details = db.get_staff_details(search)
            role = details.get('role', '-')
            sal_type = details.get('salary_type', 'Piece Rate')
            
            e, p, bal, hist_df = db.get_worker_history(search)
            
            bal_color = "#EF4444" if bal < 0 else "#10B981"
            status_text = "ADVANCE" if bal < 0 else "PAYABLE"
            
            st.markdown(f"""
            <div style="background:white; border:1px solid #E5E7EB; padding:20px; border-radius:16px; margin-bottom:20px; text-align:center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                <div style="font-size:12px; color:#6B7280; font-weight:600; letter-spacing:1px;">{role.upper()} • {sal_type.upper()}</div>
                <div style="font-size:32px; font-weight:800; color:{bal_color}; margin: 5px 0;">₹ {abs(bal):,.0f}</div>
                <div style="font-size:11px; font-weight:700; color:{bal_color}; background-color:#F3F4F6; padding:4px 8px; border-radius:6px; display:inline-block;">{status_text}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("##### 📅 12-Month Trend")
            
            if sal_type == "Salaried":
                df_att = db.get_attendance_history(search)
                if not df_att.empty:
                    df_att['date'] = pd.to_datetime(df_att['date'])
                    df_att['Month'] = df_att['date'].dt.strftime('%Y-%m')
                    monthly_counts = df_att[df_att['status'] == 'Present'].groupby('Month').size()
                    st.bar_chart(monthly_counts)
                    
                    st.markdown("##### 📜 Last 40 Days (Attendance)")
                    last_40 = df_att[df_att['date'] >= (datetime.datetime.now() - datetime.timedelta(days=40))]
                    # Render Table
                    last_40['Status'] = last_40['status'].apply(lambda x: f'<span class="status-present">{x}</span>' if x=='Present' else (f'<span class="status-absent">{x}</span>' if x=='Absent' else f'<span class="status-half">{x}</span>'))
                    last_40['Date'] = last_40['date'].dt.strftime('%d-%b')
                    st.markdown(last_40[['Date', 'Status']].to_html(classes='styled-table', index=False, escape=False), unsafe_allow_html=True)
                else:
                    st.info("No attendance records.")
                    
            else:
                if not hist_df.empty:
                    hist_df['date'] = pd.to_datetime(hist_df['date'])
                    hist_df['Month'] = hist_df['date'].dt.strftime('%Y-%m')
                    monthly_prod = hist_df.groupby('Month')['amount'].sum()
                    st.bar_chart(monthly_prod)
                    
                    st.markdown("##### 📜 Last 40 Days (Work)")
                    last_40 = hist_df[hist_df['date'] >= (datetime.datetime.now() - datetime.timedelta(days=40))]
                    for _, row in last_40.head(10).iterrows():
                        d_str = row['date'].strftime('%d/%m')
                        render_mobile_card(f"{row['item']} ({row['process']})", f"{d_str} • Lot: {row.get('lot_no','-')}", f"Qty: {row['qty']}", f"₹{row['amount']:,.0f}")
                else:
                    st.info("No work history.")

    with t_pay:
        pay_mode = st.radio("Type", ["Salary", "Advance"], horizontal=True)
        with st.container(border=True):
            pd_ = st.date_input("Date", datetime.date.today(), key="pay_date")
            ps = st.selectbox("Select Staff", [""] + db.get_staff_list(), key="pay_staff_sel")
            if ps:
                e, p, bal, _ = db.get_worker_history(ps)
                color = "#EF4444" if bal < 0 else "#10B981"
                lbl = "Advance" if bal < 0 else "Due"
                st.markdown(f"<div style='background:#F8FAFC; padding:8px; border-radius:8px; text-align:center; font-size:12px; border:1px solid #E2E8F0;'>Current: <span style='color:{color}; font-weight:bold;'>₹ {abs(bal):,.0f} ({lbl})</span></div>", unsafe_allow_html=True)
            amt = st.number_input("₹ Amount", min_value=1)
            rem = st.text_input("Note", pay_mode)
            if st.button("CONFIRM PAYMENT"):
                if ps and amt > 0:
                    db.save_payment(str(pd_), ps, amt, pay_mode, rem)
                    st.success("Recorded")
                else: st.error("Invalid")
        
        st.caption("Recent Payments")
        df_pay = db.get_df("payments")
        if not df_pay.empty:
            df_pay = df_pay.sort_values(by="created_at", ascending=False).head(5)
            for _, r in df_pay.iterrows():
                render_mobile_card(r['staff_name'], r['type'], "Paid", f"₹{r['amount']:,.0f}")

# --- 8. PAGE: MASTERS ---
elif "Masters" in selected_nav:
    st.markdown("##### ⚙️ Setup")
    t_list = ["Staff", "Item", "Proc", "Rate", "Clean", "Other"]
    sub_nav = st.segmented_control("Type", t_list, default="Staff") 
    if not sub_nav: sub_nav = "Staff" 

    if sub_nav == "Staff":
        with st.form("f_st"):
            n = st.text_input("Name")
            p = st.text_input("Phone")
            r = st.selectbox("Role", ["Stitching", "Helper", "Cutting"])
            s_type = st.radio("Pay Type", ["Piece Rate", "Salaried"], horizontal=True)
            m_sal = st.number_input("Monthly ₹", step=500.0) if s_type == "Salaried" else 0.0
            if st.form_submit_button("Save Staff"):
                db.save_staff(n, p, r, s_type, m_sal); st.success("Saved!")
        df_staff = db.get_df("masters_staff")
        if not df_staff.empty and 'name' in df_staff.columns:
            cols = [c for c in ['name', 'role', 'salary_type', 'monthly_salary'] if c in df_staff.columns]
            render_df(df_staff[cols])

    elif sub_nav == "Item":
        with st.form("f_it"):
            n = st.text_input("Name")
            if st.form_submit_button("Save"): db.save_master("masters_items", {"name":n}); st.success("Saved")
        render_df(db.get_df("masters_items"))

    elif sub_nav == "Rate":
        with st.form("f_rt"):
            i = st.selectbox("Item", db.get_items_list())
            pr = st.selectbox("Proc", db.get_processes_list())
            rt = st.number_input("Rate", 0.0)
            if st.form_submit_button("Update"): db.save_rate(i, pr, rt); st.success("Updated")
        render_df(db.get_rates_df())
    
    elif sub_nav == "Proc":
        with st.form("f_pr"):
            n = st.text_input("Process")
            if st.form_submit_button("Save"): db.save_master("masters_processes", {"name":n}); st.success("Saved")
        render_df(db.get_df("masters_processes"))
    
    elif sub_nav == "Clean":
        st.warning("⚠️ **DANGER ZONE**")
        options = {"Staff": "masters_staff", "Items": "masters_items", "Rates": "masters_rates", "Process": "masters_processes", "Data": "production"}
        sel = st.multiselect("Select", list(options.keys()))
        if sel and st.button("🗑️ WIPE"):
            db.clean_database([options[x] for x in sel]); st.success("Wiped!"); st.rerun()

    elif sub_nav == "Other":
        c1, c2 = st.columns(2)
        with c1:
            n = st.text_input("Color")
            if st.button("Add Col"): db.save_master("masters_colors", {"name":n}); st.rerun()
        with c2:
            s = st.text_input("Size")
            if st.button("Add Sz"): db.save_master("masters_sizes", {"name":s}); st.rerun()

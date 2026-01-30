import streamlit as st
import pandas as pd
import db_manager as db
import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Sparsh 1.0", 
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
        border-collapse: collapse; margin: 15px 0; font-size: 13px; font-family: 'Inter', sans-serif; width: 100%;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.05); border-radius: 10px; overflow: hidden; background-color: white;
    }
    .styled-table thead tr { background-color: #4F46E5; color: white; text-align: left; }
    .styled-table th, .styled-table td { padding: 10px 15px; }
    .styled-table tbody tr { border-bottom: 1px solid #dddddd; }
    .styled-table tbody tr:nth-of-type(even) { background-color: #F9FAFB; }
    .styled-table tbody tr:last-of-type { border-bottom: 3px solid #4F46E5; }
    
    .status-present { color: #10B981; font-weight: 700; }
    .status-absent { color: #EF4444; font-weight: 700; }
    .money-pos { color: #10B981; font-weight: 600; }
    .money-neg { color: #EF4444; font-weight: 600; }

    /* --- INPUTS & BUTTONS --- */
    .stTextInput input, .stNumberInput input, .stDateInput input {
        background-color: white !important; border: 1px solid #E2E8F0 !important; border-radius: 12px !important;
        min-height: 48px !important; font-size: 15px !important; color: #1E293B !important;
    }
    div[data-baseweb="select"] > div {
        background-color: white !important; border: 1px solid #E2E8F0 !important; border-radius: 12px !important;
        min-height: 48px !important; color: #1E293B !important;
    }
    .stButton button {
        width: 100%; min-height: 48px; border-radius: 12px; font-weight: 600;
        background-color: #4F46E5; color: white; border: none; box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2);
    }
    
    div[data-baseweb="segmented-control"] {
        width: 100%; overflow-x: auto; background-color: white; border-radius: 12px; padding: 4px;
        border: 1px solid #E2E8F0; box-shadow: 0 2px 5px rgba(0,0,0,0.03);
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

def render_html_table(df, cols):
    if df.empty: st.info("No Data"); return
    html = df[cols].to_html(classes='styled-table', index=False, escape=False)
    st.markdown(html, unsafe_allow_html=True)

# --- 4. NAVIGATION ---
nav_options = ["🏠 Home", "🏭 Work", "👥 Staff", "⚙️ Masters"]
selected_nav = st.segmented_control("Main Menu", nav_options, default="🏠 Home", label_visibility="collapsed")
if not selected_nav: selected_nav = "🏠 Home"

# --- 5. PAGE: DASHBOARD ---
if "Home" in selected_nav:
    st.markdown("##### 👋 Dashboard")
    pcs, earn, pending, active = db.get_dashboard_stats()
    
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

    with st.expander("⚡ **Quick Work Entry**", expanded=False):
        with st.container(border=True):
            p_date = st.date_input("Date", datetime.date.today())
            all_lots = db.get_active_lots()
            c_lot, c_bun = st.columns(2)
            p_lot = c_lot.selectbox("Lot No.", [""] + all_lots, key="home_lot")
            avail_bundles = db.get_bundles_for_lot(p_lot) if p_lot else []
            p_bundle = c_bun.selectbox("Bundle No.", [""] + avail_bundles, key="home_bun")
            
            auto_item, auto_qty = "", 0.0
            if p_lot and p_bundle:
                b_det = db.get_bundle_details(p_lot, p_bundle)
                if b_det:
                    auto_item, auto_qty = b_det.get("item_name", ""), float(b_det.get("qty", 0))
                    st.caption(f"Found: **{auto_item}** | Qty: {auto_qty}")
            
            c_staff, c_item = st.columns(2)
            p_staff = c_staff.selectbox("Worker", [""] + db.get_staff_list())
            item_list = db.get_items_list()
            idx_item = item_list.index(auto_item) if auto_item in item_list else 0
            p_item = c_item.selectbox("Item", [""] + item_list, index=idx_item+1 if auto_item else 0)
            
            c_proc, c_qty = st.columns(2)
            p_process = c_proc.selectbox("Process", [""] + db.get_processes_list())
            p_qty = c_qty.number_input("Qty", min_value=0.0, value=auto_qty, step=1.0)
            
            if st.button("SAVE ENTRY"):
                if not p_lot or not p_bundle or not p_staff or not p_item:
                    st.error("⚠️ Missing Fields")
                else:
                    auto_rate = db.get_rate(p_item, p_process)
                    db.save_production(str(p_date), p_staff, p_item, p_process, p_qty, auto_rate, p_lot, p_bundle)
                    st.success(f"✅ Saved! Rate: ₹{auto_rate}")

    st.markdown("##### 👥 Staff Overview")
    staff_list = db.get_staff_list()
    if staff_list:
        cards_html = '<div class="staff-grid">'
        for s_name in staff_list:
            e, p, bal, _ = db.get_worker_history(s_name)
            month_paid = db.get_staff_month_paid(s_name)
            bal_col = "#EF4444" if bal < 0 else "#10B981"
            cards_html += f"""
            <div class="staff-card-html">
                <div style="font-weight:700; font-size:15px; color:#1F2937;">{s_name}</div>
                <div style="font-size:10px; color:#6B7280; margin-top:6px; text-transform:uppercase;">Paid This Month</div>
                <div style="font-weight:700; font-size:15px; color:#4F46E5;">₹ {month_paid:,.0f}</div>
                <div style="font-size:10px; color:#6B7280; margin-top:6px; text-transform:uppercase;">Balance</div>
                <div style="font-weight:700; font-size:15px; color:{bal_col};">₹ {bal:,.0f}</div>
            </div>"""
        cards_html += '</div>'
        st.markdown(cards_html, unsafe_allow_html=True)
    else: st.info("No Staff Found.")

# --- 6. PAGE: WORK ---
elif "Work" in selected_nav:
    st.markdown("##### 🏭 Work Management")
    
    work_opts = ["Production", "Purchase", "Cashbook", "Lots", "Log"]
    work_nav = st.segmented_control("Work Section", work_opts, default="Production")
    
    if work_nav == "Production":
        with st.container(border=True):
            st.markdown("**Production Entry**")
            p_date = st.date_input("Date", datetime.date.today(), key="w_date")
            all_lots = db.get_active_lots()
            c_lot, c_bun = st.columns(2)
            p_lot = c_lot.selectbox("Lot No.", [""] + all_lots, key="w_lot")
            avail_bundles = db.get_bundles_for_lot(p_lot) if p_lot else []
            p_bundle = c_bun.selectbox("Bundle No.", [""] + avail_bundles, key="w_bun")
            
            auto_item, auto_qty = "", 0.0
            if p_lot and p_bundle:
                b_det = db.get_bundle_details(p_lot, p_bundle)
                if b_det:
                    auto_item, auto_qty = b_det.get("item_name", ""), float(b_det.get("qty", 0))
                    st.caption(f"Found: {auto_item} | Qty: {auto_qty}")
            
            c_staff, c_item = st.columns(2)
            p_staff = c_staff.selectbox("Worker", [""] + db.get_staff_list(), key="w_staff")
            item_list = db.get_items_list()
            idx_item = item_list.index(auto_item) if auto_item in item_list else 0
            p_item = c_item.selectbox("Item", [""] + item_list, index=idx_item+1 if auto_item else 0, key="w_item")
            
            c_proc, c_qty = st.columns(2)
            p_process = c_proc.selectbox("Process", [""] + db.get_processes_list(), key="w_proc")
            p_qty = c_qty.number_input("Qty", min_value=0.0, value=auto_qty, step=1.0, key="w_qty")
            
            if st.button("CONFIRM WORK", type="primary"):
                if p_lot and p_bundle and p_staff and p_item:
                    auto_rate = db.get_rate(p_item, p_process)
                    db.save_production(str(p_date), p_staff, p_item, p_process, p_qty, auto_rate, p_lot, p_bundle)
                    st.success(f"✅ Recorded! Rate: ₹{auto_rate}")
                else: st.error("Missing Data")
    
    elif work_nav == "Purchase":
        with st.container(border=True):
            st.markdown("**New Purchase**")
            pd_ = st.date_input("Date", datetime.date.today(), key="pur_date")
            c1, c2 = st.columns(2)
            p_vend = c1.selectbox("Vendor Name", [""] + db.get_vendors_list())
            p_item = c2.text_input("Item Name")
            c3, c4, c5 = st.columns(3)
            p_qty = c3.number_input("Qty", min_value=1.0, step=1.0)
            p_rate = c4.number_input("Rate", min_value=0.0)
            p_bill = c5.text_input("Bill No.")
            if st.button("SAVE PURCHASE"):
                if p_vend and p_item:
                    db.save_purchase(str(pd_), p_vend, p_item, p_qty, p_rate, p_bill)
                    st.success("Purchase Saved!")
                else: st.error("Fill Details")
        st.caption("Recent Purchases")
        df_pur = db.get_df("transactions_purchase")
        if not df_pur.empty:
            df_pur['date'] = pd.to_datetime(df_pur['date']).dt.strftime('%d-%b')
            df_pur['Total'] = df_pur['total_amount'].apply(lambda x: f"₹{x:,.0f}")
            render_html_table(df_pur, ['date', 'vendor', 'item', 'Total'])

    elif work_nav == "Cashbook":
        with st.container(border=True):
            st.markdown("**Cashbook Entry**")
            tx_type = st.radio("Type", ["Money In (Income)", "Money Out (Expense)"], horizontal=True)
            c1, c2 = st.columns(2)
            cb_date = c1.date_input("Date", datetime.date.today(), key="cb_date")
            cb_amt = c2.number_input("Amount (₹)", min_value=1.0)
            c3, c4 = st.columns(2)
            cb_party = c3.selectbox("Source / Party", [""] + db.get_sources_list())
            cb_acc = c4.text_input("Account (Bank/Cash)")
            cb_rem = st.text_input("Remarks")
            if st.button("SAVE TRANSACTION"):
                if cb_amt and cb_party:
                    t_short = "IN" if "In" in tx_type else "OUT"
                    db.save_cash_transaction(str(cb_date), t_short, cb_amt, cb_party, cb_acc, cb_rem)
                    st.success("Saved!")
                else: st.error("Missing Info")
        st.caption("Recent Transactions")
        df_cb = db.get_df("transactions_cashbook")
        if not df_cb.empty:
            df_cb['date'] = pd.to_datetime(df_cb['date']).dt.strftime('%d-%b')
            def fmt_cb(row):
                col = "money-pos" if row['type'] == "IN" else "money-neg"
                return f"<span class='{col}'>₹ {row['amount']:,.0f}</span><br><span style='font-size:10px; color:#666;'>{row['party']}</span>"
            df_cb['Detail'] = df_cb.apply(fmt_cb, axis=1)
            render_html_table(df_cb, ['date', 'type', 'Detail', 'account'])

    elif work_nav == "Lots":
        st.markdown("##### 📦 Lot Management")
        csv_temp = "date,Lot No,Item name,Bundle no.,Color Name,Size,Qty\n2023-10-25,L-101,Shirt,B-01,Blue,M,10"
        st.download_button("📥 Template", csv_temp, "lot_temp.csv", "text/csv")
        up_file = st.file_uploader("Upload CSV", type=["csv"])
        if up_file and st.button("🚀 IMPORT"):
            try:
                if db.save_bulk_lots(pd.read_csv(up_file)): st.success("Imported!")
            except: st.error("Error")
        df_lots = db.get_df("masters_lots")
        if not df_lots.empty: render_df(df_lots, "lots_data")
        
    elif work_nav == "Log":
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
    
    staff_view = st.segmented_control("Staff View", ["📊 Stats", "📅 Attendance", "💸 Payments"], default="📊 Stats")
    
    if staff_view == "📊 Stats":
        search = st.selectbox("Select Staff", [""] + db.get_staff_list(), key="staff_search")
        if search:
            details = db.get_staff_details(search)
            role = details.get('role', '-')
            sal_type = details.get('salary_type', 'Piece Rate')
            m_sal = details.get('monthly_salary', 0)
            e, p, bal, hist_df = db.get_worker_history(search)
            bal_color = "#EF4444" if bal < 0 else "#10B981"
            
            st.markdown(f"""
            <div style="background:white; padding:15px; border-radius:12px; border:1px solid #E5E7EB; text-align:center;">
                <div style="color:#6B7280; font-size:12px; font-weight:600;">{role.upper()} • {sal_type.upper()}</div>
                <div style="font-size:28px; font-weight:800; color:{bal_color};">₹ {abs(bal):,.0f}</div>
                <div style="font-size:11px; font-weight:700; color:{bal_color};">{'ADVANCE' if bal < 0 else 'PAYABLE'}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("##### 📅 12-Month History")
            is_salaried = (sal_type == "Salaried")
            df_sum = db.get_12_month_summary(search, is_salaried, m_sal)
            df_sum['Earned'] = df_sum['Earned'].apply(lambda x: f"₹ {x:,.0f}")
            df_sum['Paid'] = df_sum['Paid'].apply(lambda x: f"₹ {x:,.0f}")
            df_sum['Balance'] = df_sum['Balance'].apply(lambda x: f"<span class='money-neg'>₹ {x:,.0f}</span>" if x < 0 else f"<span class='money-pos'>₹ {x:,.0f}</span>")
            render_html_table(df_sum, ['Month', 'Earned', 'Paid', 'Balance'])
            
            st.markdown("##### 📜 Last 40 Days")
            if is_salaried:
                df_att = db.get_attendance_history(search)
                if not df_att.empty:
                    df_att['date'] = pd.to_datetime(df_att['date'])
                    last_40 = df_att[df_att['date'] >= (datetime.datetime.now() - datetime.timedelta(days=40))]
                    last_40['Date'] = last_40['date'].dt.strftime('%d-%b')
                    def fmt_att_row(row):
                        status_html = f'<span class="status-present">{row["status"]}</span>' if row["status"]=="Present" else f'<span class="status-absent">{row["status"]}</span>'
                        details = f"<br><span style='color:#666; font-size:11px;'>{row['in_time'][:5]}-{row['out_time'][:5]} • <b>₹{row['daily_earnings']}</b></span>"
                        return status_html + (details if row['status']=="Present" else "")
                    last_40['Details'] = last_40.apply(fmt_att_row, axis=1)
                    render_html_table(last_40, ['Date', 'Details', 'note'])
                else: st.info("No records")
            else:
                if not hist_df.empty:
                    hist_df['date'] = pd.to_datetime(hist_df['date'])
                    last_40 = hist_df[hist_df['date'] >= (datetime.datetime.now() - datetime.timedelta(days=40))]
                    last_40['Date'] = last_40['date'].dt.strftime('%d-%b')
                    last_40['Desc'] = last_40['item'] + " (" + last_40['process'] + ")"
                    last_40['Amt'] = last_40['amount'].apply(lambda x: f"₹ {x:,.0f}")
                    render_html_table(last_40, ['Date', 'Desc', 'qty', 'Amt'])
                else: st.info("No records")

    elif staff_view == "📅 Attendance":
        with st.container(border=True):
            st.markdown("**Mark Attendance**")
            a_date = st.date_input("Date", datetime.date.today(), key="a_date")
            a_staff = st.selectbox("Staff", [""] + db.get_staff_list(), key="a_staff")
            a_status = st.radio("Status", ["Present", "Absent", "Half Day"], horizontal=True)
            c_in, c_out = st.columns(2)
            t_in = c_in.time_input("In Time", datetime.time(9, 0))
            t_out = c_out.time_input("Out Time", datetime.time(19, 0))
            if st.button("MARK ATTENDANCE"):
                if a_staff:
                    db.save_attendance(str(a_date), a_staff, a_status, t_in, t_out)
                    st.success("Calculated & Saved!")
        
        st.markdown("---")
        st.subheader("📋 Logs")
        df_att = db.get_df("attendance")
        if not df_att.empty:
            df_att['date'] = pd.to_datetime(df_att['date'])
            df_att = df_att.sort_values(by="date", ascending=False)
            df_att['Date'] = df_att['date'].dt.strftime('%d-%b')
            def fmt_status(row):
                s = row['status']
                col = "status-present" if s=="Present" else "status-absent"
                html = f'<span class="{col}">{s}</span>'
                if s == "Present": html += f"<br><span style='font-size:10px; color:#666;'>{row['worked_hours']} hrs • ₹{row.get('daily_earnings',0)}</span>"
                return html
            df_att['Info'] = df_att.apply(fmt_status, axis=1)
            render_html_table(df_att, ['Date', 'staff_name', 'Info'])

    elif staff_view == "💸 Payments":
        with st.container(border=True):
            pay_mode = st.radio("Type", ["Salary", "Advance"], horizontal=True)
            pd_ = st.date_input("Date", datetime.date.today(), key="pay_date")
            ps = st.selectbox("Staff", [""] + db.get_staff_list(), key="pay_staff")
            if ps:
                _, _, bal, _ = db.get_worker_history(ps)
                st.caption(f"Current Balance: ₹{bal:,.0f}")
            amt = st.number_input("Amount", min_value=1)
            rem = st.text_input("Note", pay_mode)
            if st.button("PAY"):
                if ps and amt: db.save_payment(str(pd_), ps, amt, pay_mode, rem); st.success("Saved!")
        df_pay = db.get_df("payments")
        if not df_pay.empty:
            df_pay = df_pay.sort_values(by="created_at", ascending=False).head(5)
            for _, r in df_pay.iterrows():
                render_mobile_card(r['staff_name'], r['type'], "Paid", f"₹{r['amount']:,.0f}")

# --- 8. MASTERS ---
elif "Masters" in selected_nav:
    st.markdown("##### ⚙️ Setup")
    t_list = ["Staff", "Item", "Proc", "Rate", "Clean", "Other"]
    sub_nav = st.segmented_control("Type", t_list, default="Staff") 
    if not sub_nav: sub_nav = "Staff" 

    if sub_nav == "Staff":
        with st.container(border=True):
            n = st.text_input("Name")
            p = st.text_input("Phone")
            r = st.selectbox("Role", ["Stitching", "Helper", "Cutting"])
            s_type = st.radio("Pay Type", ["Piece Rate", "Salaried"], horizontal=True)
            m_sal = 0.0
            if s_type == "Salaried": m_sal = st.number_input("Monthly Salary", step=500.0)
            if st.button("Save Staff", type="primary"):
                if n: db.save_staff(n, p, r, s_type, m_sal); st.success("Saved!")
                else: st.error("Name Required")
        df_s = db.get_df("masters_staff")
        if not df_s.empty and 'name' in df_s.columns:
            cols = [c for c in ['name', 'role', 'salary_type', 'monthly_salary'] if c in df_s.columns]
            render_df(df_s[cols])

    elif sub_nav == "Item":
        n = st.text_input("Name")
        if st.button("Save"): db.save_master("masters_items", {"name":n}); st.success("Saved")
        render_df(db.get_df("masters_items"))

    elif sub_nav == "Rate":
        c1, c2, c3 = st.columns(3)
        i = c1.selectbox("Item", db.get_items_list())
        p = c2.selectbox("Proc", db.get_processes_list())
        r = c3.number_input("Rate", 0.0)
        if st.button("Update Rate"): db.save_rate(i, p, r); st.success("Updated")
        render_df(db.get_rates_df())
    
    elif sub_nav == "Proc":
        n = st.text_input("Process")
        if st.button("Save"): db.save_master("masters_processes", {"name":n}); st.success("Saved")
        render_df(db.get_df("masters_processes"))
    
    elif sub_nav == "Clean":
        st.warning("⚠️ **DANGER ZONE**")
        opts = {"Staff": "masters_staff", "Items": "masters_items", "Rates": "masters_rates", "Process": "masters_processes", "Colors": "masters_colors", "Sizes": "masters_sizes", "Lots": "masters_lots", "Data": "production", "Pay": "payments", "Att": "attendance", "Pur": "transactions_purchase", "Cash": "transactions_cashbook", "Vendors": "masters_vendors", "Sources": "masters_sources"}
        sel = st.multiselect("Select Tables", list(opts.keys()))
        if sel and st.button("🗑️ WIPE", type="primary"):
            db.clean_database([opts[x] for x in sel]); st.success("Wiped!"); st.rerun()

    elif sub_nav == "Other":
        c1, c2 = st.columns(2)
        with c1:
            n = st.text_input("Color")
            if st.button("Add Col"): db.save_master("masters_colors", {"name":n}); st.rerun()
        with c2:
            s = st.text_input("Size")
            if st.button("Add Sz"): db.save_master("masters_sizes", {"name":s}); st.rerun()
        
        st.markdown("---")
        c3, c4 = st.columns(2)
        with c3:
            v = st.text_input("Vendor / Party")
            if st.button("Add Vendor"): db.save_master("masters_vendors", {"name":v}); st.rerun()
            render_df(db.get_df("masters_vendors"), "vendors")
        with c4:
            src = st.text_input("Source")
            if st.button("Add Source"): db.save_master("masters_sources", {"name":src}); st.rerun()
            render_df(db.get_df("masters_sources"), "sources")

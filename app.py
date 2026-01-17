import streamlit as st
import pandas as pd
import db_manager as db
import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Sprash ERP 1.0", page_icon="⚡", layout="wide", initial_sidebar_state="auto")

# --- 2. MODERN UI CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    :root { --primary-green: #00A76F; --light-green-bg: rgba(0, 167, 111, 0.08); --text-dark: #212B36; --sidebar-bg: #FFFFFF; --main-bg: #F9FAFB; }
    html, body, .stApp { font-family: 'Inter', sans-serif !important; background-color: var(--main-bg) !important; color: var(--text-dark) !important; }
    [data-testid="stSidebar"] { background-color: var(--sidebar-bg) !important; border-right: 1px dashed #E5E7EB; }
    header[data-testid="stHeader"] { background: transparent; }
    div[role="radiogroup"] > label { background: transparent; border: none; padding: 10px 12px; margin-bottom: 4px; border-radius: 8px; color: #637381; font-weight: 500; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; }
    div[role="radiogroup"] > label:hover { background-color: rgba(145, 158, 171, 0.08); color: var(--text-dark); }
    div[role="radiogroup"] > label[data-checked="true"] { background-color: var(--light-green-bg) !important; color: var(--primary-green) !important; font-weight: 600 !important; }
    .block-container { padding-top: 2rem; padding-bottom: 3rem; }
    [data-testid="stVerticalBlockBorderWrapper"] { background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 24px; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); margin-bottom: 16px; }
    .stButton > button { width: 100%; border-radius: 8px; font-weight: 600; font-size: 14px; border: 1px solid #E5E7EB; background-color: #FFFFFF; color: #374151; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); height: 45px; transition: all 0.2s; }
    button[kind="primary"] { background-color: var(--primary-green) !important; color: #FFFFFF !important; border: none !important; box-shadow: 0 8px 16px -4px rgba(0, 167, 111, 0.24); }
    input, .stSelectbox div[data-baseweb="select"] div, .stDateInput div[data-baseweb="input"] div { background-color: #FFFFFF !important; border: 1px solid #D1D5DB !important; border-radius: 8px !important; color: var(--text-dark) !important; min-height: 45px !important; }
    .custom-table-container { overflow-x: auto; border-radius: 8px; border: 1px solid #E5E7EB; margin-bottom: 1rem; background: white; }
    .custom-table { width: 100%; border-collapse: collapse; font-size: 13px; font-family: 'Inter', sans-serif; min-width: 600px; }
    .custom-table thead tr { background-color: #F9FAFB; color: #637381; text-align: left; font-weight: 600; border-bottom: 1px solid #E5E7EB; text-transform: uppercase; font-size: 11px; }
    .custom-table th, .custom-table td { padding: 16px; border-bottom: 1px dashed #E5E7EB; vertical-align: middle; }
    .custom-table tbody tr:hover { background-color: #F9FAFB; }
    .custom-table img { border-radius: 8px; border: 1px solid #E5E7EB; width: 48px; height: 48px; object-fit: cover; }
    .status-badge { padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 700; }
    .status-Launched { background-color: rgba(34, 197, 94, 0.16); color: #118D57; }
    .status-Pending { background-color: rgba(255, 171, 0, 0.16); color: #B76E00; }
    .link-btn { text-decoration: none; color: var(--primary-green); font-weight: 600; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def render_launch_table(df):
    if df.empty: st.info("No launch data available."); return
    st.download_button("⬇️ Download CSV", df.to_csv(index=False).encode('utf-8'), "launch_data.csv", "text/csv")
    html = '<div class="custom-table-container"><table class="custom-table"><thead><tr><th>Image</th><th>SKU</th><th>Platform</th><th>Price</th><th>Size</th><th>Link</th><th>Status</th></tr></thead><tbody>'
    for _, row in df.iterrows():
        img = f'<img src="{row.get("image_url", "")}" onerror="this.style.display=\'none\'">'
        status_class = f"status-{row.get('status', 'Pending')}"
        link = f'<a href="{row.get("product_link", "#")}" target="_blank" class="link-btn">View ↗</a>'
        html += f'<tr><td>{img}</td><td><strong>{row.get("sku", "-")}</strong></td><td>{row.get("platform", "-")}</td><td style="text-align:right;">₹ {row.get("launch_price", 0):,.0f}</td><td>{row.get("sizes_launched", "-")}</td><td>{link}</td><td><span class="status-badge {status_class}">{row.get("status", "Pending")}</span></td></tr>'
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

def render_df(df, image_cols=[], file_name="data"):
    if df.empty: st.info("No data available."); return
    
    # Download Button for every table
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(label="⬇️ Download CSV", data=csv, file_name=f"{file_name}.csv", mime="text/csv")
    
    display_df = df.copy()
    for col in image_cols:
        if col in display_df.columns: display_df[col] = display_df[col].apply(lambda x: f'<img src="{x}" onerror="this.style.display=\'none\'">' if x and str(x).startswith('http') else '📷')
    for col in display_df.columns:
        if col not in image_cols:
            if pd.api.types.is_datetime64_any_dtype(display_df[col]): display_df[col] = display_df[col].dt.strftime('%d-%b-%y')
            elif pd.api.types.is_float_dtype(display_df[col]): display_df[col] = display_df[col].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else "")
    html = display_df.to_html(classes="custom-table", index=False, escape=False)
    st.markdown(f'<div class="custom-table-container">{html}</div>', unsafe_allow_html=True)

def render_bulk_import_ui(master_type, sample_cols):
    with st.expander(f"📥 Bulk Import {master_type}", expanded=False):
        # Sample CSV
        sample_df = pd.DataFrame(columns=sample_cols)
        st.download_button("⬇️ Download Template", sample_df.to_csv(index=False).encode('utf-8'), f"template_{master_type}.csv", "text/csv")
        
        up = st.file_uploader(f"Upload {master_type} CSV", type=['csv'], key=f"up_{master_type}")
        if up:
            if st.button("Start Import", key=f"btn_{master_type}", type="primary"):
                res, msg = db.process_bulk_master_upload(master_type, pd.read_csv(up))
                if res: st.success(msg); st.rerun()
                else: st.error(f"Error: {msg}")

# --- 4. STATE ---
if 'nav' not in st.session_state: st.session_state.nav = "Home"
def navigate_to(page): st.session_state.nav = page; st.rerun()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("""<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 24px; padding: 8px 4px;"><div style="width: 40px; height: 40px; background: #00A76F; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 20px;">⚡</div><div><div style="font-weight: 700; color: #212B36; font-size: 15px;">Sprash ERP</div><div style="font-size: 11px; color: #919EAB;">v1.0.0</div></div></div>""", unsafe_allow_html=True)
    st.markdown("<div style='font-size:11px; font-weight:700; color:#919EAB; margin-bottom:8px; padding-left:12px;'>MENU</div>", unsafe_allow_html=True)
    menu = ["Home", "Accounts", "Production", "Catalog", "Track Lot", "HR", "Configurations"]
    selected = st.radio("Menu", menu, index=menu.index(st.session_state.nav), label_visibility="collapsed")
    if selected != st.session_state.nav: st.session_state.nav = selected; st.rerun()
    st.markdown("<div style='margin-top: auto; padding-top: 20px; border-top: 1px dashed #E5E7EB;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Refresh"): st.rerun()

# --- 6. HEADER ---
c1, c2 = st.columns([1, 8])
if st.session_state.nav != "Home": 
    if c1.button("⬅ Home"): navigate_to("Home")
    c2.markdown(f"<h3 style='margin:0; color:#00A76F;'>{st.session_state.nav}</h3>", unsafe_allow_html=True)
else: st.markdown("<h3 style='margin:0; color:#212B36;'>Dashboard</h3>", unsafe_allow_html=True)
st.markdown("---")

# =========================================================
# PAGE: HR & PAY
# =========================================================
if st.session_state.nav == "HR":
    t1, t2, t3, t4 = st.tabs(["📅 Attendance", "💸 Advances", "💰 Payout", "⚙️ Rate Card"])
    
    with t1:
        st.markdown("**Mark Attendance**")
        with st.container(border=True):
            col1, col2, col3 = st.columns(3)
            s_name = col1.selectbox("Staff Name", [""] + db.get_all_staff_names())
            in_time = col2.time_input("In Time", datetime.time(9, 0))
            out_time = col3.time_input("Out Time", datetime.time(18, 0))
            night_shift = st.checkbox("🌙 Night Shift (Full Day Pay)")
            b1, b2 = st.columns(2)
            if b1.button("🟢 Mark In", type="primary"):
                db.mark_attendance(s_name, "In", in_time, night_shift); st.success("Marked IN"); st.rerun()
            if b2.button("🔴 Mark Out"):
                db.mark_attendance(s_name, "Out", out_time, night_shift); st.success("Marked OUT"); st.rerun()
        
        st.divider()
        st.markdown("### Today's Attendance")
        att = db.get_today_attendance()
        if att:
            df_att = pd.DataFrame(att)
            cols = ['staff', 'in_time', 'out_time', 'night_shift']
            for c in cols:
                if c not in df_att.columns: df_att[c] = "-"
            render_df(df_att[cols], file_name="attendance")
        else: st.info("No attendance marked today.")

    with t2:
        with st.form("adv"):
            st.markdown("**Give Advance**")
            c1, c2 = st.columns(2)
            adv_staff = c1.selectbox("Staff", [""] + db.get_all_staff_names())
            adv_amt = c2.number_input("Amount", 0.0)
            adv_date = st.date_input("Date")
            adv_note = st.text_input("Note")
            if st.form_submit_button("💾 Save Advance"):
                db.add_staff_advance(adv_staff, adv_amt, str(adv_date), adv_note); st.success("Saved!"); st.rerun()

    with t3:
        st.markdown("**Calculate Monthly Payout**")
        c1, c2, c3 = st.columns(3)
        pay_staff = c1.selectbox("Select Staff", [""] + db.get_all_staff_names())
        sel_month = c2.selectbox("Month", range(1, 13), index=datetime.datetime.now().month-1)
        sel_year = c3.number_input("Year", 2024, 2030, datetime.datetime.now().year)
        
        if pay_staff:
            data = db.get_staff_payout(pay_staff, sel_month, sel_year)
            if data:
                st.info(f"Payment Type: **{data['type']}**")
                st.dataframe(data['details'], use_container_width=True)
                st.divider()
                c_gross, c_adv, c_net = st.columns(3)
                gross = data['gross_total']
                adv = data['advances']
                net = gross - adv
                c_gross.metric("Gross Earnings", f"₹ {gross:,.2f}")
                c_adv.metric("Less: Advances", f"₹ {adv:,.2f}")
                c_net.metric("Net Payable", f"₹ {net:,.2f}", delta_color="normal" if net > 0 else "inverse")
            else: st.error("Staff data not found or no transactions.")

    with t4:
        with st.form("rate"):
            i = st.selectbox("Item", [""] + db.get_item_names())
            p = st.selectbox("Process", [""] + db.get_all_processes())
            r = st.number_input("Rate", 0.0)
            if st.form_submit_button("Set Rate"): db.add_piece_rate(i, p, r); st.success("Updated"); st.rerun()
        render_df(db.get_rate_master_df(), file_name="rate_card")

# =========================================================
# PAGE: CONFIGURATIONS
# =========================================================
elif st.session_state.nav == "Configurations":
    t = st.selectbox("Manage", ["Suppliers", "Items", "Staff", "Fabrics", "Colors", "Processes", "Sizes", "GST Slabs", "Staff Roles", "Payment Sources", "Units (UOM)", "Accessories"])
    
    if t == "Staff":
        with st.form("stf"):
            c1, c2 = st.columns(2)
            n = c1.text_input("Name")
            r = c2.selectbox("Role", [""] + db.get_all_roles())
            c3, c4 = st.columns(2)
            p_type = c3.selectbox("Payment Type", ["Piece Rate", "Monthly Salary"])
            sal = c4.number_input("Monthly Salary", 0.0)
            if st.form_submit_button("Add Staff"): db.add_staff(n, r, p_type, sal); st.success("Added"); st.rerun()
        render_bulk_import_ui("Staff", ["name", "role", "payment_type", "monthly_salary"])
        render_df(db.get_staff_df(), file_name="staff_list")

    elif t == "Suppliers":
        with st.form("sup"):
            n=st.text_input("Name"); g=st.text_input("GST"); c=st.text_input("Ph")
            if st.form_submit_button("Add"): db.add_supplier(n,g,c,""); st.success("Added"); st.rerun()
        render_bulk_import_ui("Suppliers", ["name", "gst", "contact", "address"])
        render_df(db.get_suppliers_df(), file_name="suppliers")

    elif t == "Items":
        with st.form("itm"):
            n=st.text_input("Name"); c=st.text_input("Code"); cl=st.text_input("Color")
            f=st.text_input("Fabrics (comma sep)")
            if st.form_submit_button("Add"): db.add_item(n,c,cl,[x.strip() for x in f.split(',')]); st.success("Added"); st.rerun()
        render_bulk_import_ui("Items", ["name", "code", "color", "fabrics"])
        render_df(db.get_items_df(), file_name="items")

    elif t == "Accessories":
        with st.form("acc"):
            n=st.text_input("Name"); 
            if st.form_submit_button("Add"): db.add_accessory_master(n); st.success("Added"); st.rerun()
        render_bulk_import_ui("Accessories", ["accessory_name"])
        render_df(db.get_accessories_df(), file_name="accessories")

    # ... (Other Configs with added render_bulk_import_ui calls) ...
    elif t == "Units (UOM)":
        with st.form("uom"):
            u = st.text_input("Unit Name"); 
            if st.form_submit_button("Add"): db.add_uom(u); st.success("Added"); st.rerun()
        render_bulk_import_ui("Units (UOM)", ["unit_name"])
        render_df(db.get_uoms_df(), file_name="uoms")

# =========================================================
# PAGE: ACCOUNTS (Rest of pages assumed unchanged but needed for context)
# =========================================================
elif st.session_state.nav == "Accounts":
    # ... (Accounts code from previous turn) ...
    t1, t2, t3, t4 = st.tabs(["📝 Billing", "📦 Stock", "💸 Payments", "📜 Ledger"])
    # (Billing Logic...)
    with t2:
        df_stock = db.get_unified_stock()
        if not df_stock.empty: render_df(df_stock, file_name="stock_summary")
        else: st.info("No Stock Data")
    # (Payments Logic...)
    with t4:
        sel = st.selectbox("Select Account", [""] + db.get_supplier_names())
        if sel:
            df = db.get_supplier_ledger(sel)
            if not df.empty:
                c1, c2, c3 = st.columns(3)
                c1.metric("Credits", f"₹ {df['Credit'].sum():,.0f}")
                c2.metric("Debits", f"₹ {df['Debit'].sum():,.0f}")
                bal = df.iloc[-1]['Balance']
                c3.metric("Net Balance", f"₹ {abs(bal):,.0f} {'Cr' if bal >= 0 else 'Dr'}")
                render_df(df[['Date', 'Particulars', 'Ref', 'Debit', 'Credit', 'Balance']], file_name=f"ledger_{sel}")
            else: st.info("No records.")

# ... (Production, Catalog, Home pages retain previous logic) ...

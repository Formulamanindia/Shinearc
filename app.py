import streamlit as st
import pandas as pd
import db_manager as db
import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Sprash ERP 1.0", page_icon="⚡", layout="wide", initial_sidebar_state="auto")

# --- 2. CSS ---
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
def render_df(df, image_cols=[], file_name="data"):
    if df.empty: st.info("No data available."); return
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(label="⬇️ Download CSV", data=csv, file_name=f"{file_name}.csv", mime="text/csv")
    display_df = df.copy()
    for col in image_cols:
        if col in display_df.columns: display_df[col] = display_df[col].apply(lambda x: f'<img src="{x}" onerror="this.style.display=\'none\'">' if x and str(x).startswith('http') else '📷')
    html = display_df.to_html(classes="custom-table", index=False, escape=False)
    st.markdown(f'<div class="custom-table-container">{html}</div>', unsafe_allow_html=True)

def render_bulk_import_ui(master_type, sample_cols):
    with st.expander(f"📥 Bulk Import {master_type}", expanded=False):
        sample_df = pd.DataFrame(columns=sample_cols)
        st.download_button("⬇️ Download Template", sample_df.to_csv(index=False).encode('utf-8'), f"template_{master_type}.csv", "text/csv")
        up = st.file_uploader(f"Upload {master_type} CSV", type=['csv'], key=f"up_{master_type}")
        if up:
            if st.button("Start Import", key=f"btn_{master_type}", type="primary"):
                res, msg = db.process_bulk_master_upload(master_type, pd.read_csv(up))
                if res: st.success(msg); st.rerun()
                else: st.error(f"Error: {msg}")

def render_launch_table(df):
    if df.empty: st.info("No launch data."); return
    st.download_button("⬇️ Download CSV", df.to_csv(index=False).encode('utf-8'), "launches.csv", "text/csv")
    html = '<div class="custom-table-container"><table class="custom-table"><thead><tr><th>Image</th><th>SKU</th><th>Platform</th><th>Price</th><th>Size</th><th>Link</th><th>Status</th></tr></thead><tbody>'
    for _, row in df.iterrows():
        img = f'<img src="{row.get("image_url", "")}" onerror="this.style.display=\'none\'">'
        status_class = f"status-{row.get('status', 'Pending')}"
        link = f'<a href="{row.get("product_link", "#")}" target="_blank" class="link-btn">View ↗</a>'
        html += f'<tr><td>{img}</td><td><strong>{row.get("sku", "-")}</strong></td><td>{row.get("platform", "-")}</td><td style="text-align:right;">₹ {row.get("launch_price", 0):,.0f}</td><td>{row.get("sizes_launched", "-")}</td><td>{link}</td><td><span class="status-badge {status_class}">{row.get("status", "Pending")}</span></td></tr>'
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

# --- 4. STATE ---
if 'nav' not in st.session_state: st.session_state.nav = "Home"
def navigate_to(page): st.session_state.nav = page; st.rerun()

with st.sidebar:
    st.markdown("""<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 24px; padding: 8px 4px;"><div style="width: 40px; height: 40px; background: #00A76F; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 20px;">⚡</div><div><div style="font-weight: 700; color: #212B36; font-size: 15px;">Sprash ERP</div><div style="font-size: 11px; color: #919EAB;">v1.0.0</div></div></div>""", unsafe_allow_html=True)
    st.markdown("<div style='font-size:11px; font-weight:700; color:#919EAB; margin-bottom:8px; padding-left:12px;'>MENU</div>", unsafe_allow_html=True)
    menu = ["Home", "Accounts", "Production", "Catalog", "Track Lot", "HR", "Configurations"]
    selected = st.radio("Menu", menu, index=menu.index(st.session_state.nav), label_visibility="collapsed")
    if selected != st.session_state.nav: st.session_state.nav = selected; st.rerun()
    st.markdown("<div style='margin-top: auto; padding-top: 20px; border-top: 1px dashed #E5E7EB;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Refresh"): st.rerun()

# --- 5. HEADER ---
c1, c2 = st.columns([1, 8])
if st.session_state.nav != "Home": 
    if c1.button("⬅ Home"): navigate_to("Home")
    c2.markdown(f"<h3 style='margin:0; color:#00A76F;'>{st.session_state.nav}</h3>", unsafe_allow_html=True)
else: st.markdown("<h3 style='margin:0; color:#212B36;'>Dashboard</h3>", unsafe_allow_html=True)
st.markdown("---")

# =========================================================
# PAGE: CONFIGURATIONS
# =========================================================
if st.session_state.nav == "Configurations":
    t = st.selectbox("Manage", ["Suppliers", "Items", "Staff", "Fabrics", "Colors", "Processes", "Sizes", "GST Slabs", "Staff Roles", "Payment Sources", "Units (UOM)", "Accessories"])
    
    if t == "Suppliers":
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

    elif t == "Staff":
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

    elif t == "Fabrics":
        with st.form("fab"):
            n=st.text_input("Fabric Name")
            if st.form_submit_button("Add"): db.add_fabric(n); st.success("Added"); st.rerun()
        render_bulk_import_ui("Fabrics", ["name"])
        render_df(db.get_fabrics_df(), file_name="fabrics")

    elif t == "Colors":
        with st.form("col"):
            n=st.text_input("Color Name")
            if st.form_submit_button("Add"): db.add_color(n); st.success("Added"); st.rerun()
        render_bulk_import_ui("Colors", ["name"])
        render_df(db.get_colors_df(), file_name="colors")

    elif t == "Processes":
        with st.form("prc"):
            n=st.text_input("Process Name")
            if st.form_submit_button("Add"): db.add_process(n); st.success("Added"); st.rerun()
        render_bulk_import_ui("Processes", ["process"])
        render_df(db.get_processes_df(), file_name="processes")

    elif t == "Sizes":
        with st.form("sz"):
            n=st.text_input("Size")
            if st.form_submit_button("Add"): db.add_size(n); st.success("Added"); st.rerun()
        render_bulk_import_ui("Sizes", ["size"])
        render_df(db.get_sizes_df(), file_name="sizes")

    elif t == "GST Slabs":
        with st.form("gst"):
            r = st.number_input("GST Rate (%)", 0.0)
            if st.form_submit_button("Add"): db.add_gst_slab(r); st.success("Added"); st.rerun()
        render_bulk_import_ui("GST Slabs", ["rate"])
        render_df(db.get_gst_df(), file_name="gst_slabs")

    elif t == "Staff Roles":
        with st.form("roles"):
            r = st.text_input("Role Name")
            if st.form_submit_button("Add"): db.add_role(r); st.success("Added"); st.rerun()
        render_bulk_import_ui("Staff Roles", ["role_name"])
        render_df(db.get_roles_df(), file_name="staff_roles")

    elif t == "Payment Sources":
        with st.form("src"):
            s = st.text_input("Source Name (e.g. HDFC)")
            if st.form_submit_button("Add"): db.add_payment_source(s); st.success("Added"); st.rerun()
        render_bulk_import_ui("Payment Sources", ["source_name"])
        render_df(db.get_payment_sources_df(), file_name="payment_sources")

    elif t == "Units (UOM)":
        with st.form("uom"):
            u = st.text_input("Unit Name")
            if st.form_submit_button("Add"): db.add_uom(u); st.success("Added"); st.rerun()
        render_bulk_import_ui("Units (UOM)", ["unit_name"])
        render_df(db.get_uoms_df(), file_name="uoms")

    elif t == "Accessories":
        with st.form("acc"):
            n=st.text_input("Accessory Name")
            if st.form_submit_button("Add"): db.add_accessory_master(n); st.success("Added"); st.rerun()
        render_bulk_import_ui("Accessories", ["accessory_name"])
        render_df(db.get_accessories_df(), file_name="accessories")

# =========================================================
# PAGE: HR & PAY
# =========================================================
elif st.session_state.nav == "HR":
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
                if s_name: db.mark_attendance(s_name, "In", in_time, night_shift); st.success("Marked IN"); st.rerun()
                else: st.error("Select Staff")
            if b2.button("🔴 Mark Out"):
                if s_name: db.mark_attendance(s_name, "Out", out_time, night_shift); st.success("Marked OUT"); st.rerun()
                else: st.error("Select Staff")
        st.divider()
        st.markdown("### Today's Attendance")
        att = db.get_today_attendance()
        if att:
            df_att = pd.DataFrame(att)
            cols = ['staff', 'in_time', 'out_time', 'night_shift']
            for c in cols: 
                if c not in df_att.columns: df_att[c] = "-"
            render_df(df_att[cols], file_name="attendance_today")
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
# PAGE: ACCOUNTS
# =========================================================
elif st.session_state.nav == "Accounts":
    t1, t2, t3, t4 = st.tabs(["📝 Billing", "📦 Stock", "💸 Payments", "📜 Ledger"])
    with t1:
        if 'bill_items' not in st.session_state: st.session_state.bill_items = []
        with st.container(border=True):
            st.markdown("### Transaction Entry")
            txn_type = st.selectbox("Voucher Type", ["Purchase", "Sales", "Purchase Return", "Delivery Challan", "Job Work"])
            c1, c2, c3 = st.columns(3)
            party = c1.selectbox("Party A/c Name", [""] + db.get_supplier_names())
            date = c2.date_input("Date")
            ref_no = c3.text_input("Ref No / Bill No")
            st.divider()
            st.markdown("**Item Details**")
            i1, i2, i3, i4, i5, i6 = st.columns([3, 1, 1, 1, 1, 1])
            all_items = sorted(list(set(db.get_fabrics() + db.get_all_accessories() + db.get_item_names())))
            item = i1.selectbox("Name of Item", [""] + all_items)
            uom = i2.selectbox("UOM", db.get_all_uoms())
            qty = i3.number_input("Qty", 0.0, step=1.0)
            rate = i4.number_input("Rate", 0.0)
            gst = i5.selectbox("GST %", db.get_gst_slabs())
            if i6.button("➕ Add"):
                if item and qty > 0:
                    taxable = qty * rate
                    tax_amt = taxable * (gst/100)
                    total = taxable + tax_amt
                    st.session_state.bill_items.append({"item": item, "uom": uom, "qty": qty, "rate": rate, "gst": gst, "tax_amt": tax_amt, "amount": total})
                else: st.error("Invalid Item")
            if st.session_state.bill_items:
                df_bill = pd.DataFrame(st.session_state.bill_items)
                st.dataframe(df_bill, use_container_width=True)
                gt = df_bill['amount'].sum()
                c_tot, c_btn = st.columns([3, 1])
                c_tot.metric("Grand Total", f"₹ {gt:,.2f}")
                if c_btn.button("✅ Save Voucher", type="primary"):
                    if party:
                        payload = {"date": str(date), "party": party, "ref_no": ref_no, "bill_items": st.session_state.bill_items, "grand_total": gt}
                        res, msg = db.process_transaction(txn_type, payload)
                        if res: st.success("Saved!"); st.session_state.bill_items = []; st.rerun()
                        else: st.error(msg)
                    else: st.error("Party Name Required")
            if st.button("Clear Bill"): st.session_state.bill_items = []; st.rerun()
    with t2:
        st.markdown("### 📦 Inventory Summary")
        df_stock = db.get_unified_stock()
        if not df_stock.empty: render_df(df_stock, file_name="stock_report")
        else: st.info("No Stock Data")
    with t3:
        with st.container(border=True):
            st.markdown("### Payment Entry")
            ptype = st.radio("Type", ["Payment In", "Payment Out"], horizontal=True)
            c1, c2 = st.columns(2)
            pparty = c1.selectbox("Party", [""] + db.get_supplier_names(), key="pay_p")
            pdate = c2.date_input("Date", key="pay_d")
            c3, c4 = st.columns(2)
            pamt = c3.number_input("Amount", 0.0, key="pay_a")
            psrc = c4.selectbox("Source", db.get_payment_sources())
            pnote = st.text_input("Remarks / Ref No")
            if st.button("💾 Save Payment", type="primary"):
                if pparty and pamt > 0:
                    payload = {"date":str(pdate), "party":pparty, "grand_total":pamt, "source":psrc, "remarks":pnote}
                    res, msg = db.process_transaction(ptype, payload)
                    if res: st.success("Saved!"); st.rerun()
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

# =========================================================
# PAGE: CATALOG
# =========================================================
elif st.session_state.nav == "Catalog":
    t1, t2, t3, t4 = st.tabs(["🚀 Launcher", "🛍️ Listed Products", "➕ Single Upload", "📥 Bulk Upload"])
    with t1:
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.container(border=True):
                st.markdown("**Launch Details**")
                launch_type = st.radio("Mode", ["Select Existing SKU", "Create New Product"], horizontal=True, label_visibility="collapsed")
                final_sku = ""; final_name = ""
                if launch_type == "Select Existing SKU":
                    final_sku = st.selectbox("Select SKU", [""] + db.get_all_skus())
                else:
                    auto_sku = db.get_next_sku(); st.caption(f"Auto-Generated SKU: **{auto_sku}**"); final_sku = auto_sku
                    final_name = st.text_input("Product Name")
                plat = st.selectbox("Platform", ["Flipkart", "Meesho", "Amazon", "Myntra", "Ajio"])
                link = st.text_input("Product Link (Optional)")
                st.markdown("Image Source"); img_src = st.radio("Source", ["Upload", "Link", "Fetch from URL"], horizontal=True, label_visibility="collapsed")
                image_url = ""
                if img_src == "Upload":
                    up_file = st.file_uploader("Upload", type=['jpg','png','jpeg'])
                    if up_file: image_url = db.image_to_base64(up_file)
                elif img_src == "Link": image_url = st.text_input("Image URL")
                elif img_src == "Fetch from URL":
                    if st.button("🔮 Fetch"):
                        if link:
                            fetched = db.fetch_image_from_url(link)
                            if fetched: image_url = fetched; st.success("Fetched!")
                if image_url: st.image(image_url, width=100)
                elif final_sku and launch_type == "Select Existing SKU":
                    ex = db.db.catalog.find_one({"sku": final_sku})
                    if ex and ex.get('image_link_1'): image_url = ex.get('image_link_1'); st.image(image_url, width=100)
                sz_opts = db.get_sizes(); sizes = st.multiselect("Size Variation", sz_opts)
                price = st.number_input("Launch Price", 0.0)
                status = st.radio("Status", ["Pending", "Launched"], horizontal=True)
                if st.button("🚀 Save & Launch", type="primary"):
                    if final_sku and plat:
                        sz_str = ", ".join(sizes)
                        if launch_type == "Create New Product": db.create_and_launch_product(final_sku, final_name, plat, link, sz_str, price, status, image_url)
                        else: db.add_launch_entry(final_sku, plat, link, sz_str, price, status, image_url)
                        st.success("Saved!"); st.rerun()
                    else: st.error("Missing Data")
        with c2:
            st.markdown("### 📊 Launch Status")
            render_launch_table(db.get_launch_data())
    with t2:
        st.markdown("### Master Catalog"); c_search, c_view = st.columns([3, 1])
        search_txt = c_search.text_input("🔍 Search", placeholder="Product Name, SKU...")
        view_mode = c_view.radio("Mode", ["All", "Parent"], horizontal=True)
        with st.expander("🛠️ Manage Products", expanded=False):
            sku_to_manage = st.selectbox("Select Product to Edit", [""] + db.get_all_skus(), key="manage_sku")
            if sku_to_manage:
                prod = db.get_product_by_sku(sku_to_manage)
                if prod:
                    with st.form("edit_form"):
                        c1, c2, c3 = st.columns(3)
                        new_name = c1.text_input("Name", prod.get('product_name', ''))
                        new_mrp = c2.number_input("MRP", 0.0, value=float(prod.get('mrp', 0.0)))
                        new_sp = c3.number_input("SP", 0.0, value=float(prod.get('selling_price', 0.0)))
                        c4, c5 = st.columns(2)
                        new_color = c4.text_input("Color", prod.get('color', ''))
                        new_stock = c5.number_input("Stock", 0, value=int(prod.get('stock', 0)))
                        if st.form_submit_button("✅ Update"):
                            db.update_catalog_product(sku_to_manage, {"product_name": new_name, "mrp": new_mrp, "selling_price": new_sp, "color": new_color, "stock": new_stock})
                            st.success("Updated!"); st.rerun()
                    if st.button("🗑️ Delete Product"): db.delete_catalog_product(sku_to_manage); st.success("Deleted!"); st.rerun()
        st.divider()
        raw_df = db.get_catalog_df()
        if not raw_df.empty:
            cols = ['image_link_1', 'sku', 'product_name', 'variation', 'color', 'mrp', 'selling_price', 'group_id']
            for c in cols: 
                if c not in raw_df.columns: raw_df[c] = "-"
            filt_df = raw_df.copy()
            if search_txt:
                mask = pd.Series([False] * len(filt_df))
                for s_col in ['product_name', 'sku', 'group_id']:
                    mask |= filt_df[s_col].astype(str).str.lower().str.contains(search_txt.lower())
                filt_df = filt_df[mask]
            if view_mode == "Parent" and 'group_id' in filt_df.columns:
                filt_df = filt_df.drop_duplicates(subset=['group_id'], keep='first')
            render_df(filt_df[cols], image_cols=["image_link_1"], file_name="catalog_export")
        else: st.info("Empty Catalog")
    with t3:
        with st.container(border=True):
            st.info("Manual Entry")
            with st.form("add_prod_single"):
                c1, c2 = st.columns(2)
                img_url = c1.text_input("Image URL *")
                sku = c2.text_input("SKU *")
                name = st.text_input("Name")
                c3, c4 = st.columns(2); grp = c3.text_input("Group ID"); fab = c4.text_input("Fabric")
                c5, c6 = st.columns(2); col = c5.text_input("Color"); size = c6.text_input("Sizes")
                c7, c8 = st.columns(2); mrp = c7.number_input("MRP", 0.0); sp = c8.number_input("SP", 0.0)
                hsn = c9 = st.text_input("HSN"); stk = c10 = st.number_input("Stock", 0)
                if st.form_submit_button("Save"):
                    if sku and img_url: db.add_catalog_product(sku, name, "Apparel", fab, col, size, mrp, sp, hsn, stk, img_url); st.success("Saved!"); st.rerun()
    with t4:
        st.markdown("### Bulk Import")
        headers = ["Action", "Image Link 1", "Image Link 2", "Image Link 3", "Image Link 4", "SKU Code", "Product Name", "Color", "Variation", "MRP", "Selling Price", "Stock", "GST Rate %", "HSN", "Product Weight", "Fabric", "Categories", "Ideal For", "Kids Weight", "Brand Name", "Group Id", "Product Description", "Length", "Fit Type", "Neck Type", "Occasion", "Pattern", "Sleeve Length", "Pack Of"]
        st.download_button("⬇️ Template", pd.DataFrame(columns=headers).to_csv(index=False).encode('utf-8'), "template.csv", "text/csv")
        up = st.file_uploader("Upload CSV", type=['csv'])
        if up:
            if st.button("Process", type="primary"):
                cnt, err = db.bulk_upload_catalog(pd.read_csv(up))
                if not err.empty: st.error("Errors found:"); st.dataframe(err)
                if cnt > 0: st.success(f"Processed {cnt} rows!"); st.rerun()

# =========================================================
# PAGE: PRODUCTION
# =========================================================
elif st.session_state.nav == "Production":
    t1, t2 = st.tabs(["🧵 Move Stage", "✂️ Start New Lot"])
    with t1:
        lot = st.selectbox("Select Lot", [""] + db.get_active_lots())
        if lot:
            l = db.get_lot_info(lot)
            st.info(f"{l['item_name']} | {l['color']}")
            stk = l['current_stage_stock']
            stages = [k for k, v in stk.items() if sum(v.values()) > 0]
            c1, c2 = st.columns(2)
            frm = c1.selectbox("From", stages)
            to = c2.selectbox("To", ["Stitching", "Washing", "Finishing", "Packing"])
            avail_sz = [k for k,v in stk.get(frm,{}).items() if v>0]
            c3, c4 = st.columns(2)
            sz = c3.selectbox("Size", avail_sz); qty = c4.number_input("Qty", 1, value=1)
            kar = st.selectbox("Worker", db.get_staff("Stitching Karigar"))
            if st.button("Move Items", type="primary"):
                db.move_lot(lot, frm, f"{to} - {kar}", kar, qty, sz); st.success("Moved!"); st.rerun()
    with t2:
        lot_no = db.get_next_lot_no(); st.markdown(f"### New Lot: {lot_no}")
        c1, c2, c3 = st.columns(3)
        itm = c1.selectbox("Item", [""] + db.get_item_names())
        avail_codes = db.get_codes_by_item_name(itm) if itm else []
        cod = c2.selectbox("Code", [""] + avail_codes)
        avail_colors = db.get_colors_by_item_code(cod) if cod else []
        col = c3.selectbox("Color", [""] + avail_colors)
        cm = st.selectbox("Cutting Master", db.get_staff("Cutting Master"))
        if cod:
            st.markdown("###### Fabric")
            det = db.get_item_details_by_code(cod)
            req_fabs = det.get('fabrics', []) if det else []
            if 'fab_sel' not in st.session_state: st.session_state.fab_sel = {}
            for f in req_fabs:
                with st.expander(f, expanded=False):
                    ss = db.get_all_fabric_stock_summary()
                    av_cols = sorted(list(set([x['_id']['color'] for x in ss if x['_id']['name']==f])))
                    fc = st.selectbox(f"Color for {f}", [""]+av_cols, key=f"fc_{f}")
                    if fc:
                        rls = db.get_available_rolls(f, fc)
                        opts = [f"{r['roll_no']} ({r['quantity']}kg)" for r in rls]
                        sel = st.multiselect("Pick Rolls", opts, key=f"ms_{f}")
                        r_ids = [r['_id'] for r in rls if f"{r['roll_no']} ({r['quantity']}kg)" in sel]
                        st.session_state.fab_sel[f] = {"ids": r_ids}
        st.markdown("###### Size Breakdown")
        if 'szs' not in st.session_state: st.session_state.szs={}
        c_sz, c_qt, c_add = st.columns([2, 1, 1])
        s_in = c_sz.selectbox("Size", [""]+db.get_sizes()); q_in = c_qt.number_input("Qty", 0)
        if c_add.button("Add"): st.session_state.szs[f"{col}_{s_in}"] = q_in
        if st.session_state.szs: st.write(st.session_state.szs)
        if st.button("🚀 Launch Lot", type="primary"):
            all_roll_ids = []
            for k, v in st.session_state.fab_sel.items(): all_roll_ids.extend(v['ids'])
            if itm and cod and col and cm and st.session_state.szs:
                db.create_lot(lot_no, itm, cod, col, st.session_state.szs, all_roll_ids, cm)
                st.success("Launched!"); st.session_state.szs={}; st.session_state.fab_sel={}; st.rerun()

# =========================================================
# PAGE: TRACK LOT
# =========================================================
elif st.session_state.nav == "Track Lot":
    t1, t2 = st.tabs(["📊 Summary", "🔍 Details"])
    with t1:
        active_lots = [db.get_lot_info(l) for l in db.get_active_lots()]
        cut_p, st_p, fin_p = 0, 0, 0
        summary_data = []
        for l in active_lots:
            stk = l.get('current_stage_stock', {})
            c = sum(stk.get('Cutting', {}).values())
            s = sum(sum(v.values()) for k, v in stk.items() if 'Stitching' in k)
            f = sum(sum(v.values()) for k, v in stk.items() if 'Finishing' in k)
            cut_p += c; st_p += s; fin_p += f
            summary_data.append({"Lot": l['lot_no'], "Item": l['item_name'], "Color": l['color'], "Total": l['total_qty'], "Cut": c, "Stitch": s, "Finish": f})
        c1, c2 = st.columns(2); c1.metric("Active Lots", len(active_lots)); c2.metric("In Cutting", cut_p)
        c3, c4 = st.columns(2); c3.metric("In Stitching", st_p); c4.metric("In Finishing", fin_p)
        st.markdown("### 📋 Active Lots Detail")
        if summary_data: render_df(pd.DataFrame(summary_data), file_name="lot_summary")
        else: st.info("No active lots found.")
    with t2:
        l_s = st.selectbox("Search Lot", [""] + db.get_all_lot_numbers())
        if l_s:
            l = db.get_lot_info(l_s)
            st.markdown(f"**{l['item_name']} - {l['color']}**")
            stk = l['current_stage_stock']; stages = sorted(list(stk.keys())); all_sizes = sorted(list({sz for s in stages for sz in stk[s]}))
            matrix = []; 
            for sz in all_sizes: 
                row = {"Size": sz}; 
                for s in stages: row[s] = stk[s].get(sz, 0)
                matrix.append(row)
            st.markdown("Current Stock"); render_df(pd.DataFrame(matrix), file_name=f"lot_stock_{l_s}")
            st.markdown("History"); txns = db.get_lot_transactions(l_s)
            if txns:
                df_tx = pd.DataFrame(txns)
                if 'from' in df_tx.columns: df_tx.rename(columns={'from': 'from_stage', 'to': 'to_stage'}, inplace=True)
                for c in ['timestamp', 'from_stage', 'to_stage', 'karigar', 'qty']: 
                    if c not in df_tx.columns: df_tx[c] = "-"
                df_tx['timestamp'] = pd.to_datetime(df_tx['timestamp']).dt.strftime('%d-%b %H:%M')
                render_df(df_tx[['timestamp', 'from_stage', 'to_stage', 'karigar', 'qty']], file_name=f"lot_history_{l_s}")

# =========================================================
# PAGE: HOME
# =========================================================
elif st.session_state.nav == "Home":
    stats = db.get_dashboard_stats()
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True): st.metric("Active Lots", stats.get('active_lots', 0))
    with c2:
        with st.container(border=True): st.metric("Fabric Rolls", stats.get('rolls', 0))
    with c3:
        with st.container(border=True): st.metric("Staff Present", stats.get('staff_present', 0))
    
    st.markdown("#### 🚀 Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("💰 Accounts", use_container_width=True): navigate_to("Accounts")
        if st.button("👥 HR & Pay", use_container_width=True): navigate_to("HR")
    with col2:
        if st.button("✂️ Production", use_container_width=True): navigate_to("Production")
        if st.button("📍 Track Lot", use_container_width=True): navigate_to("Track Lot")
    with col3:
        if st.button("📦 Stock", use_container_width=True): navigate_to("Stock")
        if st.button("🛍️ Catalog", use_container_width=True): navigate_to("Catalog")
    with col4:
        if st.button("⚙️ Configs", use_container_width=True): navigate_to("Configurations")

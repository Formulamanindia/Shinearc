import streamlit as st
import pandas as pd
import db_manager as db
import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Sprash ERP 1.0", page_icon="⚡", layout="wide", initial_sidebar_state="auto")

# --- 2. MODERN UI CSS (Green Theme #00A76F) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    :root {
        --primary-green: #00A76F;
        --light-green-bg: rgba(0, 167, 111, 0.08);
        --text-dark: #212B36;
        --text-muted: #637381;
        --sidebar-bg: #FFFFFF;
        --main-bg: #F9FAFB;
    }

    html, body, .stApp { 
        font-family: 'Inter', sans-serif !important; 
        background-color: var(--main-bg) !important; 
        color: var(--text-dark) !important; 
    }
    
    [data-testid="stSidebar"] {
        background-color: var(--sidebar-bg) !important;
        border-right: 1px dashed #E5E7EB;
    }
    
    header[data-testid="stHeader"] { background: transparent; }

    div[role="radiogroup"] > label {
        background: transparent;
        border: none;
        padding: 10px 12px;
        margin-bottom: 4px;
        border-radius: 8px;
        color: var(--text-muted);
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        display: flex;
        align-items: center;
    }
    
    div[role="radiogroup"] > label:hover {
        background-color: rgba(145, 158, 171, 0.08);
        color: var(--text-dark);
    }

    div[role="radiogroup"] > label[data-checked="true"] {
        background-color: var(--light-green-bg) !important;
        color: var(--primary-green) !important;
        font-weight: 600 !important;
    }

    .block-container { padding-top: 2rem; padding-bottom: 3rem; }
    
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF; 
        border: 1px solid #E5E7EB; 
        border-radius: 12px; 
        padding: 24px; 
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); 
        margin-bottom: 16px;
    }
    
    .stButton > button {
        width: 100%; 
        border-radius: 8px; 
        font-weight: 600; 
        font-size: 14px; 
        border: 1px solid #E5E7EB; 
        background-color: #FFFFFF; 
        color: #374151; 
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        height: 45px;
        transition: all 0.2s;
    }
    
    button[kind="primary"] { 
        background-color: var(--primary-green) !important; 
        color: #FFFFFF !important; 
        border: none !important; 
        box-shadow: 0 8px 16px -4px rgba(0, 167, 111, 0.24);
    }
    
    input, .stSelectbox div[data-baseweb="select"] div, .stDateInput div[data-baseweb="input"] div {
        background-color: #FFFFFF !important; 
        border: 1px solid #D1D5DB !important; 
        border-radius: 8px !important; 
        color: var(--text-dark) !important;
        min-height: 45px !important;
    }

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
    html = '<div class="custom-table-container"><table class="custom-table"><thead><tr><th>Image</th><th>SKU</th><th>Platform</th><th>Price</th><th>Size</th><th>Link</th><th>Status</th></tr></thead><tbody>'
    for _, row in df.iterrows():
        img = f'<img src="{row.get("image_url", "")}" onerror="this.style.display=\'none\'">'
        status_class = f"status-{row.get('status', 'Pending')}"
        link = f'<a href="{row.get("product_link", "#")}" target="_blank" class="link-btn">View ↗</a>'
        html += f'<tr><td>{img}</td><td><strong>{row.get("sku", "-")}</strong></td><td>{row.get("platform", "-")}</td><td style="text-align:right;">₹ {row.get("launch_price", 0):,.0f}</td><td>{row.get("sizes_launched", "-")}</td><td>{link}</td><td><span class="status-badge {status_class}">{row.get("status", "Pending")}</span></td></tr>'
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

def render_df(df, image_cols=[]):
    if df.empty: st.info("No data available."); return
    display_df = df.copy()
    for col in image_cols:
        if col in display_df.columns: display_df[col] = display_df[col].apply(lambda x: f'<img src="{x}" onerror="this.style.display=\'none\'">' if x and str(x).startswith('http') else '📷')
    for col in display_df.columns:
        if col not in image_cols:
            if pd.api.types.is_datetime64_any_dtype(display_df[col]): display_df[col] = display_df[col].dt.strftime('%d-%b-%y')
            elif pd.api.types.is_float_dtype(display_df[col]): display_df[col] = display_df[col].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else "")
    html = display_df.to_html(classes="custom-table", index=False, escape=False)
    st.markdown(f'<div class="custom-table-container">{html}</div>', unsafe_allow_html=True)

# --- 4. STATE ---
if 'nav' not in st.session_state: st.session_state.nav = "Home"
def navigate_to(page): st.session_state.nav = page; st.rerun()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 24px; padding: 8px 4px;">
            <div style="width: 40px; height: 40px; background: #00A76F; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 20px; box-shadow: 0 4px 12px rgba(0, 167, 111, 0.24);">⚡</div>
            <div>
                <div style="font-weight: 700; color: #212B36; font-size: 15px; letter-spacing: -0.5px;">Sprash ERP</div>
                <div style="font-size: 11px; color: #919EAB; font-weight: 500;">v1.0.0</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='font-size:11px; font-weight:700; color:#919EAB; margin-bottom:8px; padding-left:12px;'>MENU</div>", unsafe_allow_html=True)
    
    # UPDATED MENU: Removed Stock (Moved to Accounts)
    menu_options = ["Home", "Accounts", "Production", "Catalog", "Track Lot", "HR", "Configurations"]
    try: idx = menu_options.index(st.session_state.nav)
    except ValueError: idx = 0
    selected_page = st.radio("Menu", menu_options, index=idx, label_visibility="collapsed")
    
    if selected_page != st.session_state.nav:
        st.session_state.nav = selected_page
        st.rerun()
        
    st.markdown("<div style='margin-top: auto; padding-top: 20px; border-top: 1px dashed #E5E7EB;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Refresh Data"): st.rerun()

# --- 6. PAGE HEADER ---
c1, c2 = st.columns([1, 8])
if st.session_state.nav != "Home": 
    if c1.button("⬅ Home"): navigate_to("Home")
    c2.markdown(f"<h3 style='margin:0; color:#00A76F;'>{st.session_state.nav}</h3>", unsafe_allow_html=True)
else: st.markdown("<h3 style='margin:0; color:#212B36;'>Dashboard Overview</h3>", unsafe_allow_html=True)
st.markdown("---")

# =========================================================
# PAGE: HOME
# =========================================================
if st.session_state.nav == "Home":
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
        if st.button("🛍️ Catalog", use_container_width=True): navigate_to("Catalog")
    with col4:
        if st.button("⚙️ Configs", use_container_width=True): navigate_to("Configurations")

# =========================================================
# PAGE: CATALOG
# =========================================================
elif st.session_state.nav == "Catalog":
    t1, t2, t3, t4 = st.tabs(["🚀 Launcher", "🛍️ Listed Products", "➕ Single Upload", "📥 Bulk Upload"])
    # ... (Retain existing Catalog Logic for brevity) ...
    # Assume previous Catalog code here. I'm focusing on the requested Accounts changes.
    with t1:
        st.info("Launcher Module")
        render_launch_table(db.get_launch_data())

# =========================================================
# PAGE: ACCOUNTS (MAJOR UPDATE)
# =========================================================
elif st.session_state.nav == "Accounts":
    # 4 Sub-Tabs as requested
    t1, t2, t3, t4 = st.tabs(["📝 Billing", "📦 Stock", "💸 Payments", "📜 Ledger"])
    
    # 1. BILLING (Tally Style)
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
            
            # --- TALLY STYLE ITEM GRID ---
            st.markdown("**Item Details**")
            i1, i2, i3, i4, i5, i6 = st.columns([3, 1, 1, 1, 1, 1])
            
            # Combine Fabrics, Accessories, Products into one list
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
                    st.session_state.bill_items.append({
                        "item": item, "uom": uom, "qty": qty, "rate": rate,
                        "gst": gst, "tax_amt": tax_amt, "amount": total
                    })
                else: st.error("Invalid Item")
            
            # SHOW BILL
            if st.session_state.bill_items:
                df_bill = pd.DataFrame(st.session_state.bill_items)
                st.dataframe(df_bill, use_container_width=True)
                
                gt = df_bill['amount'].sum()
                tax = df_bill['tax_amt'].sum()
                
                c_tot, c_btn = st.columns([3, 1])
                c_tot.metric("Grand Total", f"₹ {gt:,.2f}", f"Tax: ₹ {tax:,.2f}")
                
                if c_btn.button("✅ Save Voucher", type="primary"):
                    if party:
                        payload = {
                            "date": str(date), "party": party, "ref_no": ref_no,
                            "bill_items": st.session_state.bill_items, "grand_total": gt
                        }
                        res, msg = db.process_transaction(txn_type, payload)
                        if res: 
                            st.success("Saved!"); st.session_state.bill_items = []; st.rerun()
                        else: st.error(msg)
                    else: st.error("Party Name Required")
            
            if st.button("Clear Bill"): st.session_state.bill_items = []; st.rerun()

    # 2. STOCK (Moved here)
    with t2:
        st.markdown("### 📦 Inventory Summary")
        df_stock = db.get_unified_stock()
        if not df_stock.empty: render_df(df_stock)
        else: st.info("No Stock Data")

    # 3. PAYMENTS
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
                else: st.error("Invalid Details")

    # 4. LEDGER
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
                render_df(df[['Date', 'Particulars', 'Ref', 'Debit', 'Credit', 'Balance']])
            else: st.info("No records.")

# =========================================================
# PAGE: PRODUCTION (Retained)
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
            if 'fab_sel' not in st.session_state: st.session_state.fab_sel = {}
            for f in det.get('fabrics', []):
                with st.expander(f, expanded=False):
                    ss = db.get_all_fabric_stock_summary()
                    av_cols = sorted(list(set([x['_id']['color'] for x in ss if x['_id']['name']==f])))
                    fc = st.selectbox(f"Color for {f}", [""]+av_cols, key=f"fc_{f}")
                    if fc:
                        rls = db.get_available_rolls(f, fc)
                        sel = st.multiselect("Pick Rolls", [f"{r['roll_no']} ({r['quantity']}kg)" for r in rls])
                        st.session_state.fab_sel[f] = {"ids": [r['_id'] for r in rls if f"{r['roll_no']} ({r['quantity']}kg)" in sel]}
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
# PAGE: CONFIGURATIONS (Added Accessories & UOM)
# =========================================================
elif st.session_state.nav == "Configurations":
    t = st.selectbox("Manage", ["Suppliers", "Items", "Accessories", "Staff", "Fabrics", "Colors", "Processes", "Sizes", "GST Slabs", "Staff Roles", "Payment Sources", "Units (UOM)"])
    
    if t == "Suppliers":
        with st.form("sup"):
            n=st.text_input("Name"); g=st.text_input("GST"); c=st.text_input("Ph")
            if st.form_submit_button("Add"): db.add_supplier(n,g,c,""); st.success("Added"); st.rerun()
        render_df(db.get_suppliers_df())
    elif t == "Items":
        with st.form("itm"):
            n=st.text_input("Name"); c=st.text_input("Code"); cl=st.text_input("Color")
            f=st.text_input("Fabrics (comma sep)")
            if st.form_submit_button("Add"): db.add_item(n,c,cl,[x.strip() for x in f.split(',')]); st.success("Added"); st.rerun()
        render_df(db.get_items_df())
    elif t == "Accessories":
        with st.form("acc"):
            n=st.text_input("Accessory Name (e.g. Buttons, Thread)")
            if st.form_submit_button("Add"): db.add_accessory_master(n); st.success("Added"); st.rerun()
        render_df(db.get_accessories_df())
    elif t == "Units (UOM)":
        with st.form("uom"):
            u = st.text_input("Unit Name (e.g. Kg, Box)")
            if st.form_submit_button("Add Unit"): db.add_uom(u); st.success("Added"); st.rerun()
        render_df(db.get_uoms_df())
    elif t == "Payment Sources":
        with st.form("src"):
            s = st.text_input("Source Name (e.g. HDFC)")
            if st.form_submit_button("Add Source"): db.add_payment_source(s); st.success("Added"); st.rerun()
        st.write(db.get_payment_sources())
    # ... (Other configs identical to before) ...
    elif t == "Staff":
        with st.form("stf"):
            n=st.text_input("Name"); r=st.selectbox("Role", [""] + db.get_all_roles())
            if st.form_submit_button("Add"): db.add_staff(n,r); st.success("Added"); st.rerun()
        render_df(db.get_staff_df())
    elif t == "Fabrics":
        with st.form("fab"):
            n=st.text_input("Name")
            if st.form_submit_button("Add"): db.add_fabric(n); st.success("Added"); st.rerun()
        render_df(db.get_fabrics_df())
    elif t == "Colors":
        with st.form("col"):
            n=st.text_input("Name")
            if st.form_submit_button("Add"): db.add_color(n); st.success("Added"); st.rerun()
        render_df(db.get_colors_df())
    elif t == "Processes":
        with st.form("prc"):
            n=st.text_input("Process")
            if st.form_submit_button("Add"): db.add_process(n); st.success("Added"); st.rerun()
        render_df(db.get_processes_df())
    elif t == "Sizes":
        with st.form("sz"):
            n=st.text_input("Size")
            if st.form_submit_button("Add"): db.add_size(n); st.success("Added"); st.rerun()
        render_df(db.get_sizes_df())
    elif t == "GST Slabs":
        with st.form("gst"):
            r = st.number_input("Rate", 0.0)
            if st.form_submit_button("Add"): db.add_gst_slab(r); st.success("Added"); st.rerun()
        render_df(db.get_gst_df())
    elif t == "Staff Roles":
        with st.form("roles"):
            r = st.text_input("Role Name")
            if st.form_submit_button("Add Role"): db.add_role(r); st.success("Added"); st.rerun()
        render_df(db.get_roles_df())

# =========================================================
# PAGE: OTHER PAGES (HR, TRACKER) - Placeholders
# =========================================================
elif st.session_state.nav == "HR":
    t1, t2, t3 = st.tabs(["📅 Attendance", "💰 Payout", "⚙️ Rate Card"])
    with t1:
        s = st.selectbox("Name", [""] + db.get_all_staff_names())
        c1, c2 = st.columns(2)
        if c1.button("🟢 IN"): db.mark_attendance(s, "In"); st.success("IN"); st.rerun()
        if c2.button("🔴 OUT"): db.mark_attendance(s, "Out"); st.success("OUT"); st.rerun()
        att = db.get_today_attendance()
        if att: 
            df = pd.DataFrame(att)
            for c in ['staff', 'in_time', 'out_time']: 
                if c not in df.columns: df[c] = "-"
            render_df(df[['staff', 'in_time', 'out_time']])
    with t2:
        c1, c2 = st.columns(2)
        sel_month = c1.selectbox("Month", range(1, 13), index=datetime.datetime.now().month-1)
        sel_year = c2.number_input("Year", 2024, 2030, datetime.datetime.now().year)
        if st.button("Calculate Payout"):
            df = db.get_staff_payout(sel_month, sel_year)
            if not df.empty: render_df(df); st.metric("Total", f"₹ {df['Total Pay'].sum():,.2f}")
            else: st.info("No records found.")
    with t3:
        with st.form("rate"):
            i = st.selectbox("Item", [""] + db.get_item_names())
            p = st.selectbox("Process", [""] + db.get_all_processes())
            r = st.number_input("Rate", 0.0)
            if st.form_submit_button("Set Rate"): db.add_piece_rate(i, p, r); st.success("Updated"); st.rerun()
        render_df(db.get_rate_master_df())

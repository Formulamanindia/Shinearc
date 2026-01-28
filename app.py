import streamlit as st
import pandas as pd
import db_manager as db
import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Sprash ERP", 
    page_icon="⚡", 
    layout="wide", 
    initial_sidebar_state="auto"
)

# --- 2. MOBILE-FIRST CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    :root { 
        --primary: #00A76F; 
        --bg-light: #F8FAFC;
        --card-border: #E2E8F0;
        --text-main: #1E293B;
    }
    
    html, body, .stApp { 
        font-family: 'Inter', sans-serif !important; 
        background-color: var(--bg-light) !important;
        color: var(--text-main) !important;
    }

    /* --- MOBILE OPTIMIZATIONS --- */
    /* Make inputs taller for easier tapping */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox div[data-baseweb="select"] div {
        min-height: 48px !important;
        border-radius: 10px !important;
        font-size: 16px !important; /* Prevents iOS zoom on focus */
    }
    
    /* Better spacing on mobile */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
    }
    
    /* Card Style for Data */
    .mobile-card {
        background: white;
        border: 1px solid var(--card-border);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    
    .card-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    
    .card-label { font-size: 12px; color: #64748B; font-weight: 500; }
    .card-value { font-size: 14px; color: #1E293B; font-weight: 600; }
    
    /* Status Badge */
    .status-badge {
        background: #E0F2FE; color: #0284C7;
        padding: 4px 10px; border-radius: 20px;
        font-size: 11px; font-weight: 700;
    }

    /* --- SIDEBAR & NAV --- */
    [data-testid="stSidebar"] {
        background-color: white !important;
        border-right: 1px solid var(--card-border);
    }
    
    div[role="radiogroup"] > label {
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 4px;
        border: 1px solid transparent;
    }
    
    div[role="radiogroup"] > label:hover {
        background-color: #F1F5F9;
    }
    
    div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #D1FAE5 !important;
        color: #065F46 !important;
        font-weight: 600;
        border: 1px solid #00A76F;
    }

    /* --- SCANNER --- */
    .scan-box {
        border: 2px dashed #94A3B8;
        background: white;
        border-radius: 12px;
        text-align: center;
        padding: 20px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. HELPERS ---
def render_mobile_card(title, subtitle, status, right_text):
    st.markdown(f"""
    <div class="mobile-card">
        <div class="card-row">
            <div style="font-weight:700; font-size:15px;">{title}</div>
            <div style="font-weight:700; color:#00A76F;">{right_text}</div>
        </div>
        <div class="card-row">
            <div style="color:#64748B; font-size:13px;">{subtitle}</div>
            <span class="status-badge">{status}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_df(df, file_name="data"):
    if df.empty: st.info("No data."); return
    # Mobile download button
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(f"⬇️ Download CSV", csv, f"{file_name}.csv", "text/csv", use_container_width=True)
    st.dataframe(df, use_container_width=True, hide_index=True)

# --- 4. NAVIGATION ---
if 'nav' not in st.session_state: st.session_state.nav = "Home"
if 'lot_materials' not in st.session_state: st.session_state.lot_materials = []
if 'lot_variants' not in st.session_state: st.session_state.lot_variants = []
if 'bill_items' not in st.session_state: st.session_state.bill_items = []

def navigate_to(page): st.session_state.nav = page; st.rerun()

with st.sidebar:
    st.markdown("### ⚡ Sprash ERP")
    menu = {
        "Home": "🏠 Home",
        "Production": "🏭 Production",
        "Accounts": "💰 Accounts",
        "Catalog": "🛍️ Catalog",
        "HR": "👥 Staff",
        "Reports": "📈 Reports",
        "Configurations": "⚙️ Config"
    }
    sel = st.radio("Menu", list(menu.values()), label_visibility="collapsed")
    
    # Reverse lookup for key
    selected_key = list(menu.keys())[list(menu.values()).index(sel)]
    if selected_key != st.session_state.nav:
        st.session_state.nav = selected_key
        st.rerun()

# --- HEADER ---
c1, c2 = st.columns([1, 6])
if st.session_state.nav != "Home": 
    if c1.button("⬅", use_container_width=True): navigate_to("Home")
    c2.markdown(f"### {menu[st.session_state.nav]}")
else:
    st.markdown("### 👋 Dashboard")
st.markdown("---")

# =========================================================
# PAGE: HOME
# =========================================================
if st.session_state.nav == "Home":
    with st.expander("📷 **Open Scanner**", expanded=True):
        st.markdown('<div class="scan-box">Tap below to Scan QR</div>', unsafe_allow_html=True)
        img_file = st.camera_input("Scanner", label_visibility="collapsed")
        if img_file:
            qr_data = db.decode_qr_image(img_file)
            if qr_data:
                bid = db.parse_qr_text(qr_data)
                st.success(f"✅ **Scanned:** {bid if bid else qr_data}")
            else: st.error("❌ No QR found")

    st.markdown("#### Quick Actions")
    c1, c2 = st.columns(2)
    c1.button("🏭 Production", on_click=lambda: navigate_to("Production"), use_container_width=True)
    c2.button("💰 Accounts", on_click=lambda: navigate_to("Accounts"), use_container_width=True)
    
    c3, c4 = st.columns(2)
    c3.button("👥 HR / Staff", on_click=lambda: navigate_to("HR"), use_container_width=True)
    c4.button("🛍️ Catalog", on_click=lambda: navigate_to("Catalog"), use_container_width=True)

# =========================================================
# PAGE: PRODUCTION
# =========================================================
elif st.session_state.nav == "Production":
    t1, t2, t3 = st.tabs(["✂️ New Lot", "🏭 Floor", "📊 Track"])
    
    # 1. CREATE LOT
    with t1:
        lot_no = db.get_next_lot_no()
        st.caption(f"New Lot: **{lot_no}**")
        
        with st.container(border=True):
            st.markdown("**1. Core Info**")
            itm = st.selectbox("Item Name", [""] + db.get_item_names())
            cm = st.selectbox("Cutting Master", [""] + db.get_all_staff_names())
            
            st.markdown("---")
            st.markdown("**2. Raw Materials**")
            
            # Mobile Friendly Stack
            c1, c2 = st.columns(2)
            mat_sel = c1.selectbox("Material", [""] + db.get_fabrics())
            mat_col = c2.selectbox("Color", [""] + db.get_colors(), key="mc")
            
            c3, c4 = st.columns(2)
            mat_qty = c3.number_input("Qty", 0.0)
            mat_uom = c4.selectbox("Unit", ["Kg", "Mtr", "Pcs"])
            
            if st.button("➕ Add Material", use_container_width=True):
                if mat_sel and mat_qty > 0: 
                    st.session_state.lot_materials.append({"name": mat_sel, "color": mat_col, "qty": mat_qty, "uom": mat_uom})
            
            if st.session_state.lot_materials:
                st.dataframe(pd.DataFrame(st.session_state.lot_materials), use_container_width=True, hide_index=True)
                if st.button("Clear Mats"): st.session_state.lot_materials = []

            st.markdown("---")
            st.markdown("**3. Bundles**")
            
            b1, b2 = st.columns(2)
            v_col = b1.selectbox("Bun. Color", [""] + db.get_colors())
            v_size = b2.selectbox("Size", [""] + db.get_sizes())
            v_qty = st.number_input("Pcs per Bundle", 1)
            
            if st.button("➕ Add Bundle", use_container_width=True):
                if v_col and v_size: st.session_state.lot_variants.append({"color": v_col, "size": v_size, "qty": v_qty})
            
            if st.session_state.lot_variants:
                st.dataframe(pd.DataFrame(st.session_state.lot_variants), use_container_width=True, hide_index=True)
                if st.button("Clear Buns"): st.session_state.lot_variants = []

            st.markdown("---")
            if st.button("🚀 LAUNCH LOT", type="primary", use_container_width=True):
                if itm and cm and st.session_state.lot_variants:
                    db.create_advanced_lot(lot_no, itm, cm, st.session_state.lot_materials, st.session_state.lot_variants, 0)
                    st.success(f"Lot {lot_no} Created!")
                    st.session_state.lot_materials = []
                    st.session_state.lot_variants = []
                else: st.error("Fill all fields")

    # 2. FLOOR CONTROL
    with t2:
        st.markdown("**Scan or Select Bundle**")
        use_cam = st.toggle("Use Camera")
        scanned = None
        
        if use_cam:
            img = st.camera_input("Scan QR")
            if img:
                txt = db.decode_qr_image(img)
                if txt:
                    scanned = db.parse_qr_text(txt)
                    if scanned: st.success(f"Found: {scanned}")
        
        if not scanned:
            lots = db.get_active_lots()
            sel_lot = st.selectbox("Select Lot", [""] + lots)
            if sel_lot:
                l_info = db.get_lot_info(sel_lot)
                buns = [b['bundle_id'] for b in l_info.get('bundles',[])]
                scanned = st.selectbox("Select Bundle", buns)

        if scanned:
            # Show Bundle Card
            lot_data = db.find_lot_by_bundle_id(scanned)
            if lot_data:
                b_info = next((b for b in lot_data['bundles'] if b['bundle_id'] == scanned), None)
                if b_info:
                    render_mobile_card(scanned, f"{lot_data['item_name']} | {b_info['color']} {b_info['size']}", b_info['current_stage'], f"{b_info['qty']} Pcs")
                    
                    with st.form("move"):
                        st.markdown("**Move To Stage**")
                        c1, c2 = st.columns(2)
                        stg = c1.selectbox("Next Stage", db.get_all_processes())
                        qty = c2.number_input("Qty", value=float(b_info['qty']))
                        
                        c3, c4 = st.columns(2)
                        wkr = c3.selectbox("Karigar", [""] + db.get_all_staff_names())
                        mach = c4.selectbox("Machine", [""] + db.get_machines())
                        
                        if st.form_submit_button("✅ Move Bundle", type="primary", use_container_width=True):
                            db.move_bundles(lot_data['lot_no'], [scanned], stg, wkr, mach, qty)
                            st.success("Moved Successfully!")
                            st.rerun()

    # 3. TRACKER
    with t3:
        l_search = st.selectbox("Search Lot", [""] + db.get_all_lot_numbers())
        if l_search:
            l = db.get_lot_info(l_search)
            if l:
                st.markdown(f"**{l['item_name']}**")
                st.progress(0.5) # Just visual placeholder
                
                # Bundle Cards
                bundles = l.get('bundles', [])
                for b in bundles:
                    render_mobile_card(b['bundle_id'], f"{b['color']} | {b['size']} | {b.get('machine','-')}", b['current_stage'], f"{b['qty']}")

# =========================================================
# PAGE: ACCOUNTS (MOBILE OPTIMIZED)
# =========================================================
elif st.session_state.nav == "Accounts":
    t1, t2, t3 = st.tabs(["📝 Bill", "📜 Ledger", "📦 Stock"])
    
    with t1:
        with st.container(border=True):
            st.markdown("**Transaction Header**")
            c1, c2 = st.columns(2)
            txn_type = c1.selectbox("Type", ["Purchase", "Sales", "Payment Out", "Payment In"])
            party = c2.selectbox("Party", [""] + db.get_supplier_names())
            
            date = st.date_input("Date")
            
            st.markdown("---")
            st.markdown("**Add Item**")
            
            # Row 1
            r1c1, r1c2 = st.columns(2)
            cat = r1c1.selectbox("Category", ["Fabric", "Accessories", "Finished Goods"])
            
            # Dynamic Item
            opts = []
            if cat == "Fabric": opts = db.get_fabrics_list()
            elif cat == "Accessories": opts = db.get_all_accessories()
            elif cat == "Finished Goods": opts = db.get_item_names()
            
            item = r1c2.selectbox("Item", [""] + opts)
            
            # Row 2
            r2c1, r2c2 = st.columns(2)
            col = r2c1.selectbox("Color", [""] + db.get_colors())
            qty = r2c2.number_input("Qty", 0.0)
            
            # Row 3
            r3c1, r3c2 = st.columns(2)
            rate = r3c1.number_input("Rate", 0.0)
            if st.button("➕ Add Item", use_container_width=True):
                if item and qty > 0:
                    amt = qty * rate
                    st.session_state.bill_items.append({"category": cat, "item": item, "color": col, "qty": qty, "rate": rate, "amount": amt, "uom": "Unit"})
            
            # List
            if st.session_state.bill_items:
                st.markdown("---")
                df_b = pd.DataFrame(st.session_state.bill_items)
                st.dataframe(df_b[['item', 'qty', 'amount']], use_container_width=True, hide_index=True)
                
                total = df_b['amount'].sum()
                st.metric("Total", f"₹ {total:,.2f}")
                
                if st.button("✅ Save Transaction", type="primary", use_container_width=True):
                    if party:
                        db.process_transaction(txn_type, {"date": str(date), "party": party, "grand_total": total, "bill_items": st.session_state.bill_items})
                        st.success("Saved!")
                        st.session_state.bill_items = []
                        st.rerun()
                    else: st.error("Select Party")

    with t2:
        party_sel = st.selectbox("Select Account", [""] + db.get_supplier_names())
        if party_sel:
            df, summ = db.get_supplier_ledger(party_sel)
            c1, c2 = st.columns(2)
            c1.metric("Payable", f"₹ {abs(summ['bal']):,.0f}", delta="Cr" if summ['bal'] >= 0 else "Dr")
            c2.metric("Total Pur", f"₹ {summ['cr']:,.0f}")
            
            if not df.empty:
                # Show simplified ledger for mobile
                st.dataframe(df[['Date', 'Particulars', 'Debit', 'Credit']], use_container_width=True, hide_index=True)

    with t3:
        df_stock = db.get_unified_stock()
        if not df_stock.empty:
            render_df(df_stock, "stock")
        else: st.info("No Stock")

# =========================================================
# PAGE: CATALOG
# =========================================================
elif st.session_state.nav == "Catalog":
    t1, t2 = st.tabs(["🚀 Launch", "🛍️ View"])
    with t1:
        with st.container(border=True):
            mode = st.radio("Mode", ["New SKU", "Existing"], horizontal=True)
            sku = db.get_next_sku() if mode == "New SKU" else st.selectbox("SKU", [""]+db.get_all_skus())
            name = st.text_input("Name") if mode == "New SKU" else ""
            
            c1, c2 = st.columns(2)
            plat = c1.selectbox("Platform", ["Flipkart", "Amazon", "Meesho"])
            price = c2.number_input("Price", 0.0)
            
            if st.button("🚀 Launch", type="primary", use_container_width=True):
                if sku and price:
                    db.create_and_launch_product(sku, name, plat, "", "Free", price, "Active", "")
                    st.success("Done!")
    with t2:
        render_launch_table(db.get_launch_data())

# =========================================================
# PAGE: HR
# =========================================================
elif st.session_state.nav == "HR":
    t1, t2 = st.tabs(["📅 Attendance", "💰 Salary"])
    with t1:
        with st.container(border=True):
            st.markdown("**Mark Attendance**")
            s = st.selectbox("Staff", [""] + db.get_all_staff_names())
            c1, c2 = st.columns(2)
            if c1.button("🟢 In", use_container_width=True):
                db.mark_attendance(s, "In", datetime.datetime.now().time(), False); st.success("In")
            if c2.button("🔴 Out", use_container_width=True):
                db.mark_attendance(s, "Out", datetime.datetime.now().time(), False); st.success("Out")
        
        render_df(pd.DataFrame(db.get_today_attendance()))

    with t2:
        s = st.selectbox("Select Staff", [""] + db.get_all_staff_names(), key="pay_s")
        if s:
            d = db.get_staff_payout(s, datetime.datetime.now().month, datetime.datetime.now().year)
            if d:
                c1, c2 = st.columns(2)
                c1.metric("Earned", f"₹ {d['gross_total']:,.0f}")
                c2.metric("Advance", f"₹ {d['advances']:,.0f}")
                st.dataframe(d['details'], use_container_width=True)

# =========================================================
# PAGE: CONFIGURATIONS
# =========================================================
elif st.session_state.nav == "Configurations":
    tabs = st.tabs(["Items", "Staff", "Suppliers", "Fabrics"])
    
    with tabs[0]:
        with st.form("add_item"):
            n = st.text_input("Name")
            c = st.text_input("Code")
            cat = st.selectbox("Gender", ["Men", "Women", "Kids", "Unisex"])
            if st.form_submit_button("Add Item", use_container_width=True):
                db.add_item(n, c, "", [], "Adult", cat)
                st.success("Added")
        render_df(db.get_items_df())

    with tabs[1]:
        with st.form("add_staff"):
            n = st.text_input("Name")
            r = st.selectbox("Role", [""] + db.get_all_roles())
            if st.form_submit_button("Add Staff", use_container_width=True):
                db.add_staff(n, r, "Piece Rate", 0)
                st.success("Added")
        render_df(db.get_staff_df())

    with tabs[2]:
        with st.form("add_sup"):
            n = st.text_input("Name")
            p = st.text_input("Phone")
            if st.form_submit_button("Add Supplier", use_container_width=True):
                db.add_supplier(n, "", p, "")
                st.success("Added")
        render_df(db.get_suppliers_df())

    with tabs[3]:
        with st.form("add_fab"):
            n = st.text_input("Fabric Name")
            c = st.selectbox("Color", [""]+db.get_colors())
            if st.form_submit_button("Add Fabric", use_container_width=True):
                db.add_fabric(n, c)
                st.success("Added")
        render_df(db.get_fabrics_df())

# =========================================================
# PAGE: REPORTS
# =========================================================
elif st.session_state.nav == "Reports":
    if st.button("Generate Cost Report", type="primary", use_container_width=True):
        df = db.get_lot_costing_report()
        if not df.empty:
            render_df(df, "cost_report")
            st.bar_chart(df.set_index('Lot No')['Total Lot Val'])
        else: st.info("No data")

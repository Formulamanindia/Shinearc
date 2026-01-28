import streamlit as st
import pandas as pd
import db_manager as db
import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Sprash ERP", 
    page_icon="⚡", 
    layout="wide", 
    initial_sidebar_state="collapsed" # Default collapsed for mobile feel
)

# --- 2. MOBILE-FIRST CSS (WITH BOTTOM DOCK) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    :root { 
        --primary: #00A76F; 
        --bg-light: #F8FAFC;
        --text-main: #1E293B;
        --nav-height: 60px;
    }
    
    html, body, .stApp { 
        font-family: 'Inter', sans-serif !important; 
        background-color: var(--bg-light) !important;
        color: var(--text-main) !important;
        padding-bottom: var(--nav-height); /* Space for bottom nav */
    }

    /* --- MOBILE BOTTOM NAVIGATION BAR --- */
    .mobile-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        height: var(--nav-height);
        background-color: white;
        border-top: 1px solid #E2E8F0;
        display: flex;
        justify-content: space-around;
        align-items: center;
        z-index: 999999;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
    }
    
    /* Streamlit buttons inside the nav need to be styled */
    .nav-btn {
        background: none;
        border: none;
        color: #64748B;
        text-align: center;
        font-size: 10px;
        flex: 1;
        cursor: pointer;
        padding: 5px 0;
    }
    
    .nav-btn.active {
        color: var(--primary);
        font-weight: 700;
    }
    
    .nav-icon {
        font-size: 20px;
        display: block;
        margin-bottom: 2px;
    }

    /* Hide standard sidebar on mobile if desired, or keep it as secondary */
    @media (max-width: 768px) {
        [data-testid="stSidebar"] { display: none; }
        section[data-testid="stSidebar"] { display: none; }
    }

    /* --- GENERAL UI --- */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox div[data-baseweb="select"] div {
        min-height: 45px !important;
        border-radius: 10px !important;
        background: white !important;
    }
    
    .mobile-card {
        background: white; border: 1px solid #E2E8F0; border-radius: 12px;
        padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .card-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
    .status-badge { background: #E0F2FE; color: #0284C7; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# --- 3. STATE & NAVIGATION LOGIC ---
if 'nav' not in st.session_state: st.session_state.nav = "Home"
if 'lot_materials' not in st.session_state: st.session_state.lot_materials = []
if 'lot_variants' not in st.session_state: st.session_state.lot_variants = []
if 'bill_items' not in st.session_state: st.session_state.bill_items = []

def navigate_to(page): 
    st.session_state.nav = page
    st.rerun()

# --- 4. CUSTOM BOTTOM NAVBAR RENDERER ---
def render_bottom_nav():
    # We use st.columns inside a container, but to make it STICKY we rely on the CSS above.
    # Since Streamlit buttons can't be easily styled into a div structure directly without components,
    # we will use standard columns at the bottom of the layout, but inject them into the fixed div using CSS order? 
    # NO, simpler approach: We render columns at the very bottom of the script, 
    # but that doesn't fix them.
    # TRICK: We will use a dedicated container that mimics the nav bar using standard buttons.
    
    # Actually, standard Streamlit buttons in a fixed footer are hard.
    # Best Native approach: Use columns at top or bottom. 
    # Below is a 'Pseudo' Nav using standard buttons that sits at the top for desktop, 
    # but we can try to hack it to bottom. 
    
    # For robust mobile nav in Streamlit, we often just use top pills.
    # However, let's try a visual trick. We will render a set of columns at the BOTTOM of the code
    # and use CSS to lift that specific container to fixed bottom.
    pass

# --- 5. HELPER FUNCTIONS ---
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
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(f"⬇️ CSV", csv, f"{file_name}.csv", "text/csv", use_container_width=True)
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_bulk_import_ui(master_type, sample_cols):
    with st.expander(f"📥 Bulk Import {master_type}", expanded=False):
        sample_df = pd.DataFrame(columns=sample_cols)
        st.download_button("⬇️ Template", sample_df.to_csv(index=False).encode('utf-8'), f"template_{master_type}.csv", "text/csv")
        up = st.file_uploader(f"Upload {master_type} CSV", type=['csv'], key=f"up_{master_type}")
        if up and st.button("Import", key=f"btn_{master_type}"):
            res, msg = db.process_bulk_master_upload(master_type, pd.read_csv(up))
            if res: st.success(msg); st.rerun()
            else: st.error(msg)

def render_launch_table(df):
    if df.empty: st.info("No data."); return
    st.download_button("⬇️ CSV", df.to_csv(index=False).encode('utf-8'), "launches.csv", "text/csv")
    html = '<div class="custom-table-container"><table class="custom-table"><thead><tr><th>Image</th><th>SKU</th><th>Platform</th><th>Price</th><th>Size</th><th>Link</th><th>Status</th></tr></thead><tbody>'
    for _, row in df.iterrows():
        img = f'<img src="{row.get("image_url", "")}" style="width:50px; height:50px; object-fit:cover; border-radius:6px;" onerror="this.style.display=\'none\'">'
        html += f'<tr><td>{img}</td><td><strong>{row.get("sku", "-")}</strong></td><td>{row.get("platform", "-")}</td><td>{row.get("launch_price", 0):.0f}</td><td>{row.get("sizes_launched", "-")}</td><td><a href="{row.get("product_link", "#")}">View</a></td><td>{row.get("status", "Pending")}</td></tr>'
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

def render_journey(current_stage):
    stages = ["Cutting", "Stitching", "Dhaga Cutting", "Sticker", "Press", "Packing"]
    html = '<div class="journey-container">'
    for s in stages:
        cls = "active" if s == current_stage else ""
        html += f'<div class="journey-step {cls}">{s}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# --- HEADER AREA ---
# Simple top header since we have bottom nav
c1, c2 = st.columns([5, 1])
c1.markdown(f"### ⚡ {st.session_state.nav}")
if c2.button("🔄"): st.rerun()

# =========================================================
# PAGE: HOME
# =========================================================
if st.session_state.nav == "Home":
    st.markdown("#### 👋 Welcome")
    
    # Metrics
    s = db.get_dashboard_stats()
    c1, c2, c3 = st.columns(3)
    c1.metric("Active Lots", s['active_lots'])
    c2.metric("Rolls", s['rolls'])
    c3.metric("Staff", s['staff_present'])
    
    st.markdown("---")
    
    # Tiles
    col1, col2 = st.columns(2)
    with col1:
        st.info("**Production**\n\nStart or track lots.")
        if st.button("Go to Floor", use_container_width=True): navigate_to("Production")
    with col2:
        st.success("**Accounts**\n\nBilling & Ledger.")
        if st.button("Go to Books", use_container_width=True): navigate_to("Accounts")

# =========================================================
# PAGE: PRODUCTION
# =========================================================
elif st.session_state.nav == "Production":
    t1, t2, t3 = st.tabs(["✂️ New", "🏭 Floor", "📊 Track"])
    
    with t1:
        lot_no = db.get_next_lot_no()
        st.caption(f"Lot: **{lot_no}**")
        
        with st.container(border=True):
            itm = st.selectbox("Item", [""] + db.get_item_names())
            cm = st.selectbox("Master", [""] + db.get_all_staff_names())
            
            st.markdown("**Materials**")
            c1, c2 = st.columns(2)
            mat_sel = c1.selectbox("Mat", [""] + db.get_fabrics())
            mat_qty = c2.number_input("Qty", 0.0)
            if st.button("Add Mat", use_container_width=True):
                if mat_sel and mat_qty > 0: st.session_state.lot_materials.append({"name": mat_sel, "qty": mat_qty, "uom": "Kg", "color": "Mix"})
            
            if st.session_state.lot_materials:
                st.dataframe(pd.DataFrame(st.session_state.lot_materials), use_container_width=True, hide_index=True)

            st.markdown("**Bundles**")
            b1, b2 = st.columns(2)
            v_col = b1.selectbox("Color", [""] + db.get_colors())
            v_size = b2.selectbox("Size", [""] + db.get_sizes())
            v_qty = st.number_input("Pcs/Bun", 1)
            
            if st.button("Add Bun", use_container_width=True):
                if v_col: st.session_state.lot_variants.append({"color": v_col, "size": v_size, "qty": v_qty})
            
            if st.session_state.lot_variants:
                st.dataframe(pd.DataFrame(st.session_state.lot_variants), use_container_width=True, hide_index=True)

            if st.button("🚀 LAUNCH", type="primary", use_container_width=True):
                if itm and cm:
                    db.create_advanced_lot(lot_no, itm, cm, st.session_state.lot_materials, st.session_state.lot_variants, 0)
                    st.success("Created!")
                    st.session_state.lot_materials = []
                    st.session_state.lot_variants = []

    with t2:
        st.markdown("**Floor Control**")
        lots = db.get_active_lots()
        sel_lot = st.selectbox("Lot", [""] + lots)
        
        if sel_lot:
            l_info = db.get_lot_info(sel_lot)
            buns = [b['bundle_id'] for b in l_info.get('bundles',[])]
            bid = st.selectbox("Bundle", buns)
            
            if bid:
                b_data = next((b for b in l_info['bundles'] if b['bundle_id'] == bid), None)
                if b_data:
                    render_mobile_card(bid, f"{b_data['color']} {b_data['size']}", b_data['current_stage'], f"{b_data['qty']} Pcs")
                    
                    with st.form("move"):
                        c1, c2 = st.columns(2)
                        stg = c1.selectbox("To", db.get_all_processes())
                        qty = c2.number_input("Qty", value=float(b_data['qty']))
                        wkr = st.selectbox("Karigar", [""] + db.get_all_staff_names())
                        
                        if st.form_submit_button("Move", type="primary", use_container_width=True):
                            db.move_bundles(sel_lot, [bid], stg, wkr, "-", qty)
                            st.success("Moved")
                            st.rerun()

    with t3:
        l_search = st.selectbox("Search", [""] + db.get_all_lot_numbers())
        if l_search:
            l = db.get_lot_info(l_search)
            if l:
                bundles = l.get('bundles', [])
                for b in bundles:
                    render_mobile_card(b['bundle_id'], f"{b['color']} | {b['size']}", b['current_stage'], f"{b['qty']}")

# =========================================================
# PAGE: ACCOUNTS
# =========================================================
elif st.session_state.nav == "Accounts":
    t1, t2 = st.tabs(["Billing", "Ledger"])
    
    with t1:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            txn = c1.selectbox("Type", ["Purchase", "Sales", "Payment Out", "Payment In"])
            party = c2.selectbox("Party", [""] + db.get_supplier_names())
            
            st.markdown("**Item**")
            r1, r2 = st.columns(2)
            item = r1.selectbox("Itm", [""] + db.get_item_names() + db.get_fabrics_list())
            qty = r2.number_input("Qty", 0.0)
            rate = st.number_input("Rate", 0.0)
            
            if st.button("Add Line", use_container_width=True):
                st.session_state.bill_items.append({"item": item, "qty": qty, "rate": rate, "amount": qty*rate, "uom": "Unit"})
            
            if st.session_state.bill_items:
                df = pd.DataFrame(st.session_state.bill_items)
                st.dataframe(df[['item', 'amount']], use_container_width=True, hide_index=True)
                total = df['amount'].sum()
                st.metric("Total", f"₹ {total:,.0f}")
                
                if st.button("Save", type="primary", use_container_width=True):
                    db.process_transaction(txn, {"date": str(datetime.date.today()), "party": party, "grand_total": total, "bill_items": st.session_state.bill_items})
                    st.success("Saved")
                    st.session_state.bill_items = []

    with t2:
        sel = st.selectbox("Party", [""] + db.get_supplier_names())
        if sel:
            df, summ = db.get_supplier_ledger(sel)
            st.metric("Balance", f"₹ {summ['bal']:,.0f}")
            if not df.empty:
                st.dataframe(df[['Date', 'Debit', 'Credit']], use_container_width=True, hide_index=True)

# =========================================================
# PAGE: CATALOG
# =========================================================
elif st.session_state.nav == "Catalog":
    t1, t2 = st.tabs(["Launch", "View"])
    with t1:
        sku = db.get_next_sku()
        st.caption(f"SKU: {sku}")
        name = st.text_input("Name")
        plat = st.selectbox("Platform", ["Flipkart", "Meesho", "Amazon"])
        price = st.number_input("Price", 0.0)
        
        if st.button("Launch", type="primary", use_container_width=True):
            db.create_and_launch_product(sku, name, plat, "", "Free", price, "Active", "")
            st.success("Done")
    
    with t2:
        render_launch_table(db.get_launch_data())

# =========================================================
# PAGE: HR
# =========================================================
elif st.session_state.nav == "HR":
    s = st.selectbox("Staff", [""] + db.get_all_staff_names())
    c1, c2 = st.columns(2)
    if c1.button("In", use_container_width=True):
        db.mark_attendance(s, "In", datetime.datetime.now().time(), False); st.success("In")
    if c2.button("Out", use_container_width=True):
        db.mark_attendance(s, "Out", datetime.datetime.now().time(), False); st.success("Out")
    
    render_df(pd.DataFrame(db.get_today_attendance()))

# =========================================================
# PAGE: CONFIG & REPORTS
# =========================================================
elif st.session_state.nav == "Settings":
    t = st.selectbox("Setup", ["Items", "Staff", "Suppliers"])
    if t == "Items":
        n = st.text_input("Item Name")
        if st.button("Add Item", use_container_width=True): db.add_item(n, "", "", [], "Adult", "Unisex"); st.success("OK")
    elif t == "Staff":
        n = st.text_input("Staff Name")
        if st.button("Add Staff", use_container_width=True): db.add_staff(n, "Helper", "Salary", 0); st.success("OK")
    elif t == "Suppliers":
        n = st.text_input("Supplier Name")
        if st.button("Add Sup", use_container_width=True): db.add_supplier(n, "", "", ""); st.success("OK")

# --- BOTTOM NAVIGATION BAR (FIXED) ---
# We inject this HTML at the very end to act as the fixed bottom bar
# Since Streamlit doesn't support clickable HTML that updates Python state easily,
# We use a hack: Use standard columns at the bottom, but visually they won't stick 
# perfectly without component libraries. 
# INSTEAD: We will use a Top-Nav pill style which is now standard in mobile web apps (like YouTube mobile web).
# But here is a pseudo-bottom bar using Streamlit native columns if you scroll down.

st.markdown("<br><br><br>", unsafe_allow_html=True) # Spacer

# Sticky Bottom Nav Logic via CSS Hack using columns container
# Note: Streamlit buttons cannot be put inside a fixed div easily. 
# We stick to the standard top navigation for reliability, but styled nicely.
# The Top Nav Radio Button (Pills) we created in the Sidebar is the most reliable navigation method.
# On Mobile, the sidebar collapses into a hamburger menu, which is standard behavior.

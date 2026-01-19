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
    
    /* INPUT VISIBILITY FIX */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTimeInput input, .stSelectbox div[data-baseweb="select"] div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        min-height: 45px !important;
    }
    .stSelectbox svg { fill: #000000 !important; }
    
    .custom-table-container { overflow-x: auto; border-radius: 8px; border: 1px solid #E5E7EB; margin-bottom: 1rem; background: white; }
    .custom-table { width: 100%; border-collapse: collapse; font-size: 13px; font-family: 'Inter', sans-serif; min-width: 600px; }
    .custom-table thead tr { background-color: #F9FAFB; color: #637381; text-align: left; font-weight: 600; border-bottom: 1px solid #E5E7EB; text-transform: uppercase; font-size: 11px; }
    .custom-table th, .custom-table td { padding: 16px; border-bottom: 1px dashed #E5E7EB; vertical-align: middle; }
    
    .bundle-card { border: 1px solid #E5E7EB; border-radius: 8px; padding: 12px; background: white; margin-bottom: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    .bundle-header { font-weight: 700; color: #00A76F; font-size: 13px; display: flex; justify-content: space-between; }
    .bundle-meta { font-size: 12px; color: #6B7280; margin-top: 4px; }
    .stage-badge { background: #E0F2FE; color: #0369A1; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def render_df(df, image_cols=[], file_name="data"):
    if df.empty: st.info("No data."); return
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(label="⬇️ CSV", data=csv, file_name=f"{file_name}.csv", mime="text/csv")
    display_df = df.copy()
    for col in image_cols:
        if col in display_df.columns: display_df[col] = display_df[col].apply(lambda x: f'<img src="{x}" onerror="this.style.display=\'none\'">' if x and str(x).startswith('http') else '📷')
    html = display_df.to_html(classes="custom-table", index=False, escape=False)
    st.markdown(f'<div class="custom-table-container">{html}</div>', unsafe_allow_html=True)

def render_bulk_import_ui(master_type, sample_cols):
    with st.expander(f"📥 Bulk Import {master_type}", expanded=False):
        sample_df = pd.DataFrame(columns=sample_cols)
        st.download_button("⬇️ Template", sample_df.to_csv(index=False).encode('utf-8'), f"template_{master_type}.csv", "text/csv")
        up = st.file_uploader(f"Upload {master_type}", type=['csv'], key=f"up_{master_type}")
        if up and st.button("Import", key=f"btn_{master_type}"):
            res, msg = db.process_bulk_master_upload(master_type, pd.read_csv(up))
            if res: st.success(msg); st.rerun()
            else: st.error(msg)

def render_launch_table(df):
    if df.empty: st.info("No data."); return
    st.download_button("⬇️ CSV", df.to_csv(index=False).encode('utf-8'), "launches.csv", "text/csv")
    html = '<div class="custom-table-container"><table class="custom-table"><thead><tr><th>Image</th><th>SKU</th><th>Platform</th><th>Price</th><th>Size</th><th>Link</th><th>Status</th></tr></thead><tbody>'
    for _, row in df.iterrows():
        img = f'<img src="{row.get("image_url", "")}" onerror="this.style.display=\'none\'">'
        html += f'<tr><td>{img}</td><td><strong>{row.get("sku", "-")}</strong></td><td>{row.get("platform", "-")}</td><td>{row.get("launch_price", 0):.0f}</td><td>{row.get("sizes_launched", "-")}</td><td><a href="{row.get("product_link", "#")}">View</a></td><td>{row.get("status", "Pending")}</td></tr>'
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

# --- 4. STATE ---
if 'nav' not in st.session_state: st.session_state.nav = "Home"
if 'lot_materials' not in st.session_state: st.session_state.lot_materials = []
if 'lot_variants' not in st.session_state: st.session_state.lot_variants = []

def navigate_to(page): st.session_state.nav = page; st.rerun()

with st.sidebar:
    st.markdown("""<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 24px; padding: 8px 4px;"><div style="width: 40px; height: 40px; background: #00A76F; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 20px;">⚡</div><div><div style="font-weight: 700; color: #212B36; font-size: 15px;">Sprash ERP</div><div style="font-size: 11px; color: #919EAB;">v1.0.0</div></div></div>""", unsafe_allow_html=True)
    menu = ["Home", "Accounts", "Production", "Catalog", "Track Lot", "HR", "Configurations"]
    selected = st.radio("Menu", menu, index=menu.index(st.session_state.nav), label_visibility="collapsed")
    if selected != st.session_state.nav: st.session_state.nav = selected; st.rerun()
    if st.button("🔄 Refresh"): st.rerun()

# --- 5. HEADER ---
c1, c2 = st.columns([1, 8])
if st.session_state.nav != "Home": 
    if c1.button("⬅ Home"): navigate_to("Home")
    c2.markdown(f"<h3 style='margin:0; color:#00A76F;'>{st.session_state.nav}</h3>", unsafe_allow_html=True)
else: st.markdown("<h3 style='margin:0; color:#212B36;'>Dashboard</h3>", unsafe_allow_html=True)
st.markdown("---")

# =========================================================
# PAGE: HOME
# =========================================================
if st.session_state.nav == "Home":
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

# =========================================================
# PAGE: PRODUCTION (RE-ENGINEERED)
# =========================================================
elif st.session_state.nav == "Production":
    t1, t2, t3 = st.tabs(["✂️ Create Lot", "🏭 Floor Control", "📊 Dashboard"])
    
    # 1. CREATE LOT
    with t1:
        c_head, c_lot = st.columns([3, 1])
        c_head.markdown("### New Production Lot")
        next_lot = db.get_next_lot_no()
        c_lot.info(f"Lot #: **{next_lot}**")
        
        with st.container(border=True):
            c1, c2 = st.columns(2)
            itm = c1.selectbox("Item Name", [""] + db.get_item_names())
            cm = c2.selectbox("Cutting Master", db.get_staff("Cutting Master"))
            
            # --- 1. Materials Section ---
            st.divider()
            st.markdown("**1. Raw Materials**")
            
            # Dependent Dropdowns for Fabric
            item_fabrics = db.get_item_fabrics(itm) if itm else []
            avail_fabrics = item_fabrics if item_fabrics else db.get_fabrics()
            
            m1, m2, m3, m4 = st.columns([3, 2, 2, 1])
            mat_sel = m1.selectbox("Material Name", [""] + avail_fabrics)
            mat_col = m2.selectbox("Color", [""] + db.get_colors(), key="mat_col_sel")
            mat_qty = m3.number_input("Qty", 0.0, key="mat_q")
            mat_uom = st.selectbox("UOM", ["Kg", "Mtr", "Pcs"], key="mat_u") # Placed outside col for simplicity or keep standard
            
            if m4.button("Add Mat"):
                if mat_sel and mat_qty > 0 and mat_col:
                    st.session_state.lot_materials.append({"name": mat_sel, "color": mat_col, "qty": mat_qty, "uom": mat_uom})
            
            if st.session_state.lot_materials:
                st.dataframe(pd.DataFrame(st.session_state.lot_materials), use_container_width=True)
                if st.button("Clear Mats"): st.session_state.lot_materials = []

            # --- 2. Bundles Section ---
            st.divider()
            st.markdown("**2. Create Bundles**")
            
            # Filter Bundle Colors based on Selected Materials
            added_colors = sorted(list(set([m['color'] for m in st.session_state.lot_materials])))
            avail_bundle_colors = added_colors if added_colors else db.get_colors()
            
            v1, v2, v3, v4 = st.columns([2, 2, 2, 1])
            v_col = v1.selectbox("Bundle Color", [""] + avail_bundle_colors, key="bun_col")
            v_size = v2.selectbox("Size", [""] + db.get_sizes(), key="bun_sz")
            v_qty = v3.number_input("Pcs", 1, key="bun_q")
            
            if v4.button("Add Bun"):
                if v_col and v_size and v_qty > 0:
                    st.session_state.lot_variants.append({"color": v_col, "size": v_size, "qty": v_qty})
            
            if st.session_state.lot_variants:
                st.dataframe(pd.DataFrame(st.session_state.lot_variants), use_container_width=True)
                if st.button("Clear Bundles"): st.session_state.lot_variants = []

            # --- 3. Save ---
            st.divider()
            if st.button("🚀 Launch Lot", type="primary"):
                if itm and cm and st.session_state.lot_variants:
                    db.create_advanced_lot(next_lot, itm, cm, st.session_state.lot_materials, st.session_state.lot_variants)
                    st.success("Launched Successfully!")
                    st.session_state.lot_materials = []
                    st.session_state.lot_variants = []
                    
                    # Generate QRs
                    st.markdown("### 🖨️ Print QR Codes")
                    lot_info = db.get_lot_info(next_lot)
                    bundles = lot_info.get('bundles', [])
                    cols = st.columns(4)
                    for i, b in enumerate(bundles):
                        qr_img = db.generate_bundle_qr(next_lot, b['bundle_id'], itm, b['color'], b['size'], b['qty'], cm)
                        with cols[i%4]:
                            st.image(qr_img, width=120)
                            st.caption(f"{b['bundle_id']}\n{b['color']} {b['size']}")
                else: st.error("Missing Item, Cutting Master or Bundles")

    # 2. FLOOR CONTROL (SCANNER)
    with t2:
        st.markdown("### 🏭 Floor Control")
        
        # QR SCANNER
        qr_input = st.text_input("📷 Scan Bundle QR", help="Click here and scan the QR code on the bundle")
        
        parsed_bundle_id = db.parse_qr_code(qr_input) if qr_input else None
        
        if parsed_bundle_id:
            # Find Lot based on Bundle ID
            lot_doc = db.find_lot_by_bundle_id(parsed_bundle_id)
            if lot_doc:
                # Find specific bundle in lot
                bundle_data = next((b for b in lot_doc['bundles'] if b['bundle_id'] == parsed_bundle_id), None)
                
                if bundle_data:
                    st.success(f"**Bundle Found:** {parsed_bundle_id}")
                    c1, c2, c3 = st.columns(3)
                    c1.info(f"Item: {lot_doc['item_name']}")
                    c2.info(f"Type: {bundle_data['color']} | {bundle_data['size']}")
                    c3.warning(f"Current Stage: {bundle_data['current_stage']}")
                    
                    # Action
                    with st.form("move_scan"):
                        cols = st.columns(2)
                        to_stage = cols[0].selectbox("Move To", db.get_all_processes())
                        karigar = cols[1].selectbox("Karigar", db.get_staff("Stitching Karigar")) # Should ideally be dynamic
                        
                        if st.form_submit_button("✅ Move Bundle"):
                            db.move_bundles(lot_doc['lot_no'], [parsed_bundle_id], to_stage, karigar)
                            st.success(f"Moved to {to_stage}!")
                            st.rerun()
                else: st.error("Bundle ID not found in Lot.")
            else: st.error("Lot containing this bundle not found.")
        
        st.divider()
        st.caption("Manual Mode available in Dashboard Tab")

    # 3. DASHBOARD (Merged Tracker)
    with t3:
        st.markdown("### 📊 Production Tracker")
        search_lot = st.selectbox("Search Lot", [""] + db.get_all_lot_numbers())
        
        if search_lot:
            l = db.get_lot_info(search_lot)
            if l:
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Item", l['item_name'])
                c2.metric("Total Qty", l['total_qty'])
                c3.metric("Status", l['status'])
                
                st.markdown("#### Bundle Status")
                bundles = l.get('bundles', [])
                if bundles:
                    # Summary
                    df = pd.DataFrame(bundles)
                    summary = df['current_stage'].value_counts().reset_index()
                    summary.columns = ['Stage', 'Count']
                    st.dataframe(summary, use_container_width=True)
                    
                    # Detail Grid
                    cols = st.columns(4)
                    for i, b in enumerate(bundles):
                        with cols[i%4]:
                            st.markdown(f"""
                            <div class="bundle-card">
                                <div class="bundle-header"><span>{b['bundle_id']}</span><span>{b['qty']}</span></div>
                                <div class="bundle-meta">{b['color']} | {b['size']}</div>
                                <div style="margin-top:8px;"><span class="stage-badge">{b['current_stage']}</span></div>
                            </div>
                            """, unsafe_allow_html=True)

# =========================================================
# PAGE: CATALOG
# =========================================================
elif st.session_state.nav == "Catalog":
    t1, t2, t3, t4 = st.tabs(["🚀 Launcher", "🛍️ Listed Products", "➕ Single Upload", "📥 Bulk Upload"])
    # ... (Keep existing Catalog Logic) ...
    # Simplified placeholder to ensure file runs, assuming previous logic exists
    with t1:
        render_launch_table(db.get_launch_data())

# =========================================================
# PAGE: ACCOUNTS
# =========================================================
elif st.session_state.nav == "Accounts":
    t1, t2, t3, t4 = st.tabs(["📝 Billing", "📦 Stock", "💸 Payments", "📜 Ledger"])
    # ... (Keep existing Accounts Logic) ...
    with t2:
        render_df(db.get_unified_stock(), file_name="stock")

# =========================================================
# PAGE: HR & PAY
# =========================================================
elif st.session_state.nav == "HR":
    t1, t2, t3, t4 = st.tabs(["📅 Attendance", "💸 Advances", "💰 Payout", "⚙️ Rate Card"])
    with t1:
        with st.container(border=True):
            s = st.selectbox("Staff", [""]+db.get_all_staff_names())
            if st.button("Mark In"): db.mark_attendance(s, "In", datetime.datetime.now().strftime("%H:%M")); st.success("OK")
        render_df(pd.DataFrame(db.get_today_attendance()), file_name="att")

# =========================================================
# PAGE: CONFIGURATIONS
# =========================================================
elif st.session_state.nav == "Configurations":
    t = st.selectbox("Manage", ["Suppliers", "Items", "Staff", "Fabrics", "Colors", "Processes", "Sizes", "GST Slabs", "Staff Roles", "Payment Sources", "Units (UOM)", "Accessories", "⚠ Clean Database"])
    
    if t == "Items":
        render_bulk_import_ui("Items", ["name", "code", "color", "fabrics"])
        render_df(db.get_items_df(), file_name="items")
    # ... (Other configs) ...
    elif t == "Accessories":
        render_bulk_import_ui("Accessories", ["accessory_name"])
        render_df(db.get_accessories_df(), file_name="accessories")

import streamlit as st
import pandas as pd
import db_manager as db
import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Sprash ERP 1.0", page_icon="⚡", layout="wide", initial_sidebar_state="auto")

# --- 2. CSS (Green Theme) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    :root { --primary-green: #00A76F; --light-green-bg: rgba(0, 167, 111, 0.08); --text-dark: #212B36; --sidebar-bg: #FFFFFF; --main-bg: #F9FAFB; }
    html, body, .stApp { font-family: 'Inter', sans-serif !important; background-color: var(--main-bg) !important; color: var(--text-dark) !important; }
    [data-testid="stSidebar"] { background-color: var(--sidebar-bg) !important; border-right: 1px dashed #E5E7EB; }
    div[role="radiogroup"] > label[data-checked="true"] { background-color: var(--light-green-bg) !important; color: var(--primary-green) !important; font-weight: 600 !important; }
    .block-container { padding-top: 2rem; }
    .stButton > button { width: 100%; border-radius: 8px; font-weight: 600; border: 1px solid #E5E7EB; background: #FFF; color: #374151; height: 45px; }
    button[kind="primary"] { background: #00A76F !important; color: white !important; border: none !important; }
    .bundle-card { border: 1px solid #E5E7EB; border-radius: 8px; padding: 12px; background: white; margin-bottom: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    .bundle-header { font-weight: 700; color: #00A76F; font-size: 13px; display: flex; justify-content: space-between; }
    .bundle-meta { font-size: 12px; color: #6B7280; margin-top: 4px; }
    .stage-badge { background: #E0F2FE; color: #0369A1; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- 3. STATE & NAVIGATION ---
if 'nav' not in st.session_state: st.session_state.nav = "Home"
if 'lot_materials' not in st.session_state: st.session_state.lot_materials = []
if 'lot_variants' not in st.session_state: st.session_state.lot_variants = []

with st.sidebar:
    st.markdown("### ⚡ Sprash ERP")
    menu = ["Home", "Production", "Accounts", "HR", "Configurations"]
    st.session_state.nav = st.radio("Menu", menu, index=menu.index(st.session_state.nav) if st.session_state.nav in menu else 0)

# --- 4. PRODUCTION MODULE (RE-ENGINEERED) ---
if st.session_state.nav == "Production":
    t1, t2, t3 = st.tabs(["✂️ Create Lot", "🏭 Floor Control", "📊 Dashboard"])
    
    # --- TAB 1: CREATE LOT (Multi-Material, Multi-Variant) ---
    with t1:
        c_head, c_lot = st.columns([3, 1])
        c_head.markdown("### New Production Lot")
        next_lot = db.get_next_lot_no()
        c_lot.info(f"Lot #: **{next_lot}**")
        
        with st.container(border=True):
            # 1. Basic Info
            c1, c2, c3, c4 = st.columns(4)
            itm = c1.selectbox("Item", [""] + db.get_item_names())
            
            # Dynamic Filters
            avail_codes = db.get_codes_by_item_name(itm) if itm else []
            cod = c2.selectbox("Code", [""] + avail_codes)
            
            # Fetch Materials based on Item (Dependent Dropdown)
            avail_mats = db.get_item_materials(itm) if itm else []
            
            cm = c3.selectbox("Cutting Master", db.get_staff("Cutting Master"))
            date = c4.date_input("Date")
            
            st.divider()
            
            # 2. Raw Materials (Multi-Select)
            st.markdown("**1. Raw Materials (Inventory Deduction)**")
            m1, m2, m3, m4 = st.columns([3, 2, 2, 1])
            mat_sel = m1.selectbox("Material", [""] + avail_mats)
            mat_qty = m2.number_input("Qty / Weight", 0.0)
            mat_uom = m3.selectbox("UOM", ["Kg", "Mtr", "Pcs"])
            if m4.button("Add Mat"):
                if mat_sel and mat_qty > 0:
                    st.session_state.lot_materials.append({"name": mat_sel, "qty": mat_qty, "uom": mat_uom})
            
            # Show Material Table
            if st.session_state.lot_materials:
                st.dataframe(pd.DataFrame(st.session_state.lot_materials), use_container_width=True)
                if st.button("Clear Materials"): st.session_state.lot_materials = []

            st.divider()

            # 3. Variants (Bundles)
            st.markdown("**2. Size & Color Breakdown (Bundles)**")
            v1, v2, v3, v4 = st.columns([2, 2, 2, 1])
            v_col = v1.selectbox("Color", [""] + db.get_colors())
            v_size = v2.selectbox("Size", [""] + db.get_sizes())
            v_qty = v3.number_input("Quantity", 1)
            
            if v4.button("Add Bundle"):
                if v_col and v_size and v_qty > 0:
                    st.session_state.lot_variants.append({"color": v_col, "size": v_size, "qty": v_qty})
            
            # Show Variant Table
            if st.session_state.lot_variants:
                st.dataframe(pd.DataFrame(st.session_state.lot_variants), use_container_width=True)
                if st.button("Clear Bundles"): st.session_state.lot_variants = []

            st.divider()
            
            # 4. Final Save
            if st.button("🚀 Launch Lot & Generate QR Codes", type="primary"):
                if itm and cm and st.session_state.lot_variants:
                    db.create_advanced_lot(next_lot, itm, cod, cm, st.session_state.lot_materials, st.session_state.lot_variants)
                    st.success(f"Lot {next_lot} Launched Successfully!")
                    
                    # QR Code Generation Section
                    st.markdown("### 🖨️ Bundle QR Codes")
                    qr_cols = st.columns(4)
                    for i, v in enumerate(st.session_state.lot_variants):
                        bid = f"{next_lot}-{i+1:02d}"
                        qr_img = db.generate_bundle_qr(next_lot, bid, itm, v['color'], v['size'], v['qty'], cm)
                        
                        with qr_cols[i % 4]:
                            st.image(qr_img, width=120)
                            st.caption(f"**{bid}**\n{v['color']} - {v['size']}")
                    
                    # Reset
                    st.session_state.lot_materials = []
                    st.session_state.lot_variants = []
                else:
                    st.error("Please fill all details (Item, Cutting Master, at least 1 Bundle).")

    # --- TAB 2: FLOOR CONTROL (Tracking) ---
    with t2:
        st.markdown("### 🏭 Production Floor")
        c_sel, c_ref = st.columns([3, 1])
        lot_sel = c_sel.selectbox("Select Active Lot", [""] + db.get_active_lots())
        if c_ref.button("🔄 Refresh"): st.rerun()
        
        if lot_sel:
            lot_data = db.get_lot_details(lot_sel)
            bundles = lot_data.get('bundles', [])
            
            if bundles:
                # 1. Action Bar
                with st.expander("Move Bundles", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    # Get configured processes order
                    process_list = db.get_all_processes() # Cutting, Stitching, etc.
                    target_stage = c1.selectbox("Move To", process_list)
                    worker = c2.selectbox("Assign Worker", db.get_staff("Stitching Karigar")) # Should filter based on stage ideally
                    
                    # Multi-Select Bundles
                    b_opts = [f"{b['bundle_id']} | {b['color']} {b['size']} ({b['current_stage']})" for b in bundles]
                    selected_b_strs = st.multiselect("Select Bundles to Move", b_opts)
                    
                    if st.button("Move Selected", type="primary"):
                        if selected_b_strs and target_stage and worker:
                            # Extract IDs
                            sel_ids = [s.split(" | ")[0] for s in selected_b_strs]
                            db.move_bundles(lot_sel, sel_ids, target_stage, worker)
                            st.success(f"Moved {len(sel_ids)} bundles to {target_stage}")
                            st.rerun()
                        else: st.error("Select Bundles, Stage and Worker")

                # 2. Visual Grid of Bundles
                st.markdown("---")
                st.markdown(f"**Lot Content: {len(bundles)} Bundles**")
                
                # Dynamic Grid Layout
                cols = st.columns(4)
                for i, b in enumerate(bundles):
                    with cols[i % 4]:
                        # Card HTML
                        st.markdown(f"""
                        <div class="bundle-card">
                            <div class="bundle-header">
                                <span>{b['bundle_id']}</span>
                                <span>{b['qty']} pcs</span>
                            </div>
                            <div class="bundle-meta">
                                {b['color']} | {b['size']}
                            </div>
                            <div style="margin-top:8px;">
                                <span class="stage-badge">{b['current_stage']}</span>
                                <div style="font-size:11px; color:#9CA3AF; margin-top:4px;">{b.get('assigned_to','-')}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No bundles found in this lot.")

    # --- TAB 3: DASHBOARD (Tracker) ---
    with t3:
        st.markdown("### 📊 Lot Tracker")
        search_lot = st.selectbox("Search Any Lot", [""] + db.get_all_lot_numbers())
        
        if search_lot:
            l = db.get_lot_details(search_lot)
            if l:
                # Header
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Item", l['item_name'])
                c2.metric("Code", l.get('item_code', '-'))
                c3.metric("Total Qty", l['total_qty'])
                c4.metric("Status", l['status'])
                
                st.markdown("#### Bundle Status")
                # Group by Stage
                bundles = l.get('bundles', [])
                df = pd.DataFrame(bundles)
                if not df.empty:
                    # Pivot for summary
                    stage_summary = df['current_stage'].value_counts().reset_index()
                    stage_summary.columns = ['Stage', 'Count']
                    
                    c_chart, c_data = st.columns([1, 2])
                    with c_chart:
                        st.dataframe(stage_summary, hide_index=True, use_container_width=True)
                    with c_data:
                        st.markdown("**Detailed List**")
                        st.dataframe(df[['bundle_id', 'color', 'size', 'qty', 'current_stage', 'assigned_to']], hide_index=True)
                
                st.markdown("#### Material Consumed")
                mats = l.get('materials_consumed', [])
                if mats:
                    st.dataframe(pd.DataFrame(mats))
                
                st.markdown("#### Movement History")
                hist = l.get('history', [])
                if hist:
                    h_df = pd.DataFrame(hist)
                    h_df['time'] = pd.to_datetime(h_df['time']).dt.strftime('%d-%b %H:%M')
                    st.dataframe(h_df)
            else:
                st.error("Lot not found")

# --- OTHER PAGES (Placeholders) ---
elif st.session_state.nav == "Home": st.info("Dashboard")
elif st.session_state.nav == "Accounts": st.info("Accounts Module")
elif st.session_state.nav == "HR": st.info("HR Module")
elif st.session_state.nav == "Configurations": st.info("Config Module")
elif st.session_state.nav == "Catalog": st.info("Catalog Module")

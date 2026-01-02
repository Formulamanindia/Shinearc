import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import db_manager as db
import datetime
import base64

# --- 1. CONFIG ---
st.set_page_config(
    page_title="Shine Arc POS", 
    page_icon="🍊", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 2. MOBILE OPTIMIZED CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');
    
    /* GLOBAL MOBILE TWEAKS */
    html, body, .stApp { 
        font-family: 'Nunito', sans-serif !important; 
        background-color: #F8F9FA !important; 
    }

    /* REMOVE STUPID PADDING ON MOBILE */
    .block-container {
        padding-top: 1rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        padding-bottom: 2rem !important;
    }

    /* HIDE SIDEBAR & HAMBURGER */
    [data-testid="stSidebarCollapsedControl"] { display: none; }
    [data-testid="stSidebar"] { display: none; }

    /* CARD STYLING */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 15px;
        border: 1px solid #E9ECEF;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 12px;
    }

    /* BIG FINGER-FRIENDLY BUTTONS */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 50px;
        font-weight: 700;
        font-size: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* PRIMARY BUTTON (Orange) */
    button[kind="primary"] {
        background: linear-gradient(135deg, #FE9F43 0%, #FF8E25 100%) !important;
        color: white !important;
        border: none !important;
    }

    /* INPUTS - LARGER TEXT */
    input, .stSelectbox > div > div, .stDateInput > div > div {
        min-height: 48px !important;
        font-size: 16px !important;
        border-radius: 8px !important;
    }

    /* STICKY HEADER FOR NAVIGATION */
    .sticky-nav {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background: white;
        z-index: 99999;
        padding: 10px;
        border-bottom: 1px solid #eee;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    /* SECTION HEADERS */
    .section-header {
        font-size: 12px;
        font-weight: 800;
        color: #ADB5BD;
        text-transform: uppercase;
        margin: 20px 0 10px 5px;
        letter-spacing: 1px;
    }
    
    /* METRICS FIX */
    [data-testid="stMetricValue"] { font-size: 22px !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. STATE & NAV ---
if 'page' not in st.session_state: st.session_state.page = "Home"

def nav(page_name):
    st.session_state.page = page_name
    st.rerun()

def render_header(title):
    # Sticky header simulation using Columns
    c1, c2 = st.columns([1, 5])
    with c1:
        if st.button("🏠", key=f"home_btn_{title}"): nav("Home")
    with c2:
        st.markdown(f"<h3 style='margin: 10px 0 0 0;'>{title}</h3>", unsafe_allow_html=True)
    st.divider()

# --- 4. APP FLOW ---
page = st.session_state.page

# ==========================================
# HOME SCREEN
# ==========================================
if page == "Home":
    st.markdown("<h2 style='color:#FE9F43; text-align:center;'>⚡ Shine Arc</h2>", unsafe_allow_html=True)
    
    # Quick Stats
    stats = db.get_dashboard_stats()
    c1, c2, c3 = st.columns(3)
    with c1: 
        with st.container(border=True): st.metric("Active", stats.get('active_lots', 0))
    with c2: 
        with st.container(border=True): st.metric("Done", stats.get('completed_lots', 0))
    with c3: 
        with st.container(border=True): st.metric("Rolls", stats.get('fabric_rolls', 0))

    st.markdown('<div class="section-header">💰 ACCOUNTS</div>', unsafe_allow_html=True)
    if st.button("📒 Supplier Ledger", use_container_width=True): nav("Supplier Ledger")

    st.markdown('<div class="section-header">✂️ PRODUCTION</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if c1.button("🧶 Inward", use_container_width=True): nav("Fabric Inward")
    if c2.button("✂️ Cutting", use_container_width=True): nav("Cutting Floor")
    
    c3, c4 = st.columns(2)
    if c3.button("🧵 Stitching", use_container_width=True): nav("Stitching Floor")
    if c4.button("🛠️ BOM Recipe", use_container_width=True): nav("BOM")
    
    if st.button("💰 Productivity & Pay", use_container_width=True): nav("Productivity & Pay")

    st.markdown('<div class="section-header">📦 MANAGEMENT</div>', unsafe_allow_html=True)
    c5, c6 = st.columns(2)
    if c5.button("📦 Stock", use_container_width=True): nav("Inventory")
    if c6.button("👥 Masters", use_container_width=True): nav("Masters")
    
    st.markdown('<div class="section-header">🚀 INTEGRATIONS</div>', unsafe_allow_html=True)
    if st.button("🌐 Vin Lister", use_container_width=True): nav("MCPL")

    st.markdown('<div class="section-header">⚙️ SYSTEM</div>', unsafe_allow_html=True)
    if st.button("📍 Track Lot", use_container_width=True): nav("Track Lot")

# ==========================================
# 1. SUPPLIER LEDGER (MOBILE OPTIMIZED)
# ==========================================
elif page == "Supplier Ledger":
    render_header("Supplier Ledger")
    
    tab = st.radio("Action", ["Add Entry", "View Ledger"], horizontal=True)
    suppliers = [""] + db.get_supplier_names()
    
    if tab == "Add Entry":
        with st.container(border=True):
            sup = st.selectbox("Supplier", suppliers)
            date = st.date_input("Date")
            txn_type = st.selectbox("Type", ["Bill (Purchase)", "Payment (Outgoing)", "Debit Note (Return)"])
            
            st.divider()
            
            if txn_type == "Bill (Purchase)":
                bill_no = st.text_input("Bill No *")
                f = st.file_uploader("Attach", type=['png','jpg','pdf'], label_visibility="collapsed")
                
                st.info("👇 Add Items")
                
                # --- MOBILE FRIENDLY ITEM ENTRY (2 Cols Max) ---
                if 'bill_items' not in st.session_state: st.session_state.bill_items = []
                
                with st.expander("Add New Item", expanded=True):
                    i1, i2 = st.columns(2)
                    it_name = i1.text_input("Item Name")
                    it_qty = i2.number_input("Qty", 1.0)
                    
                    i3, i4 = st.columns(2)
                    it_rate = i3.number_input("Rate", 0.0)
                    it_uom = i4.selectbox("UOM", ["Pcs", "Kg", "Mtr", "Pair"])
                    
                    i5, i6 = st.columns(2)
                    it_tax = i5.selectbox("Tax %", [0, 5, 12, 18])
                    it_hsn = i6.text_input("HSN")
                    
                    it_desc = st.text_input("Desc (Opt)")
                    
                    if st.button("➕ Add", key="add_btn"):
                        if it_name and it_qty > 0:
                            tax_amt = (it_qty * it_rate) * (it_tax/100)
                            total = (it_qty * it_rate) + tax_amt
                            st.session_state.bill_items.append({
                                "Item": it_name, "Qty": it_qty, "Rate": it_rate, 
                                "Tax": it_tax, "Total": total, "TaxAmt": tax_amt
                            })
                        else: st.error("Name & Qty required")

                if st.session_state.bill_items:
                    df = pd.DataFrame(st.session_state.bill_items)
                    st.dataframe(df[["Item", "Qty", "Total"]], use_container_width=True)
                    
                    g_tot = df['Total'].sum()
                    st.success(f"Total: ₹ {g_tot:,.2f}")
                    
                    # Payment Logic
                    is_paid = st.checkbox("Payment Done?")
                    pay_mode = "Cash"
                    if is_paid:
                        pay_mode = st.selectbox("Mode", ["Cash", "UPI", "Bank"])
                    
                    if st.button("💾 Save Bill", type="primary"):
                        if sup and bill_no:
                            rem = f"Items: {len(df)} | Tax: {df['TaxAmt'].sum():.2f}"
                            db.add_supplier_txn(sup, str(date), "Bill", g_tot, bill_no, rem, None, st.session_state.bill_items)
                            
                            if is_paid:
                                db.add_supplier_txn(sup, str(date), "Payment", g_tot, "", f"Ref Bill: {bill_no} ({pay_mode})")
                            
                            st.success("Saved!"); st.session_state.bill_items = []; st.rerun()
                        else: st.error("Supplier & Bill No required")

            elif txn_type == "Payment (Outgoing)":
                amt = st.number_input("Amount (₹)", 0.0)
                mode = st.selectbox("Mode", ["Cash", "UPI", "Bank"])
                rem = st.text_input("Remarks")
                if st.button("Save Payment", type="primary"):
                    if sup and amt > 0:
                        db.add_supplier_txn(sup, str(date), "Payment", amt, "", f"{mode} - {rem}")
                        st.success("Saved!")

            elif txn_type == "Debit Note (Return)":
                amt = st.number_input("Return Amount (₹)", 0.0)
                reason = st.text_input("Reason")
                if st.button("Save Return", type="primary"):
                    if sup and amt > 0:
                        db.add_supplier_txn(sup, str(date), "Debit Note", amt, "", reason)
                        st.success("Saved!")

    elif tab == "View Ledger":
        sel_sup = st.selectbox("Supplier", suppliers)
        if sel_sup:
            df = db.get_supplier_ledger(sel_sup)
            if not df.empty:
                bal = df.iloc[-1]['Balance']
                st.metric("Net Balance", f"₹ {bal:,.2f}", delta="Payable" if bal>0 else "Advance", delta_color="inverse")
                
                st.dataframe(df[["Date", "Type", "Credit (Bill)", "Debit (Paid/Return)", "Balance"]], use_container_width=True)
                
                # Delete Option
                with st.expander("Manage Records"):
                    opts = [f"{r['Date']} | ₹{r['Credit (Bill)'] or r['Debit (Paid/Return)']}" for _, r in df.iterrows()]
                    sel_idx = st.selectbox("Select", range(len(opts)), format_func=lambda x: opts[x])
                    if st.button("Delete Record"):
                        db.delete_supplier_txn(df.iloc[sel_idx]['ID'])
                        st.success("Deleted"); st.rerun()
            else: st.info("No records found.")

# 2. FABRIC INWARD
elif page == "Fabric Inward":
    render_header("Fabric Inward")
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        sup = c1.selectbox("Supplier", [""]+db.get_supplier_names())
        bill = c2.text_input("Bill No")
        
        c3, c4 = st.columns(2)
        fab = c3.selectbox("Fabric", [""]+sorted(db.get_materials()['name'].tolist()))
        col = c4.selectbox("Color", [""]+db.get_colors())
        
        st.markdown("###### Rolls Entry")
        
        if 'r_in' not in st.session_state: st.session_state.r_in = 1
        
        # Dynamic Rows
        r_vals = []
        for i in range(st.session_state.r_in):
            v = st.number_input(f"Roll {i+1} Weight (Kg)", 0.0, key=f"r_{i}")
            if v > 0: r_vals.append(v)
            
        c_add, c_save = st.columns(2)
        if c_add.button("➕ Add Roll"): st.session_state.r_in += 1; st.rerun()
        
        if c_save.button("💾 Save", type="primary"):
            if sup and bill and fab and r_vals:
                db.add_fabric_rolls_batch(fab, col, r_vals, "Kg", sup, bill)
                st.success(f"Saved {len(r_vals)} Rolls!"); st.session_state.r_in=1; st.rerun()
            else: st.error("Missing Data")

    st.markdown("#### Recent Stock")
    s = db.get_all_fabric_stock_summary()
    if s: st.dataframe(pd.DataFrame([{"Fab":x['_id']['name'],"Col":x['_id']['color'],"Qty":x['total_qty']} for x in s]), use_container_width=True)

# 3. CUTTING FLOOR
elif page == "Cutting Floor":
    render_header("Cutting Floor")
    
    lot_no = db.get_next_lot_no()
    st.info(f"Creating Lot: **{lot_no}**")
    
    item = st.selectbox("Item", [""]+db.get_unique_item_names())
    code = st.selectbox("Code", [""]+(db.get_codes_by_item_name(item) if item else []))
    
    if code:
        # Load Fabric
        det = db.get_item_details_by_code(code)
        reqs = det.get('required_fabrics', [])
        
        if 'fab_sel' not in st.session_state: st.session_state.fab_sel = {}
        
        for f in reqs:
            with st.expander(f"Select {f}", expanded=False):
                ss = db.get_all_fabric_stock_summary()
                av_cols = sorted(list(set([x['_id']['color'] for x in ss if x['_id']['name']==f])))
                fc = st.selectbox(f"Color", av_cols, key=f"fc_{f}")
                
                if fc:
                    rls = db.get_available_rolls(f, fc)
                    opts = [f"{r['roll_no']} ({r['quantity']}kg)" for r in rls]
                    sel = st.multiselect("Pick Rolls", opts, key=f"ms_{f}")
                    
                    # Calc weight
                    w = sum([r['quantity'] for r in rls if f"{r['roll_no']} ({r['quantity']}kg)" in sel])
                    r_ids = [r['_id'] for r in rls if f"{r['roll_no']} ({r['quantity']}kg)" in sel]
                    
                    st.session_state.fab_sel[f] = {"ids": r_ids, "w": w}
                    st.caption(f"Total: {w} Kg")

    st.markdown("---")
    l_col = st.text_input("Lot Color")
    
    st.markdown("###### Size Breakdown")
    sizes = db.get_sizes()
    breakdown = {}
    
    # 2 Cols for sizes
    cols = st.columns(2)
    for i, z in enumerate(sizes):
        q = cols[i%2].number_input(z, 0, key=f"z_{z}")
        if q > 0: breakdown[f"{l_col}_{z}"] = q
        
    if st.button("🚀 Create Lot", type="primary"):
        all_r_ids = []
        fab_consum = []
        for f, d in st.session_state.fab_sel.items():
            all_r_ids.extend(d['ids'])
            fab_consum.append({"name": f, "weight": d['w']})
            
        if item and l_col and breakdown:
            db.create_lot({
                "lot_no": lot_no, "item_name": item, "item_code": code, "color": l_col,
                "created_by": "User", "size_breakdown": breakdown,
                "fabrics_consumed": fab_consum, "total_fabric_weight": 0
            }, all_r_ids)
            st.success("Created!"); st.session_state.fab_sel={}; st.rerun()
        else: st.error("Missing Data")

# 4. STITCHING FLOOR
elif page == "Stitching Floor":
    render_header("Stitching Floor")
    
    lots = [l['lot_no'] for l in db.get_active_lots()]
    sel_lot = st.selectbox("Select Lot", [""]+lots)
    
    if sel_lot:
        l = db.get_lot_details(sel_lot)
        st.caption(f"Item: {l['item_name']} | Color: {l['color']}")
        
        with st.form("mov"):
            c1, c2 = st.columns(2)
            # Only show stages with stock
            valid_stages = [k for k,v in l['current_stage_stock'].items() if sum(v.values()) > 0]
            
            frm = c1.selectbox("From", valid_stages)
            to = c2.selectbox("To", db.get_stages_for_item(l['item_name']))
            
            kar = st.selectbox("Worker", db.get_staff_by_role("Stitching Karigar"))
            
            # Show available sizes in 'From' stage
            avail = l['current_stage_stock'].get(frm, {})
            valid_sz = [k for k,v in avail.items() if v>0]
            
            sz_key = st.selectbox("Size", valid_sz)
            qty = st.number_input("Qty", 1, value=1)
            
            if st.form_submit_button("Move"):
                if qty <= avail.get(sz_key, 0):
                    db.move_lot_stage({
                        "lot_no": sel_lot, "from_stage": frm, "to_stage_key": f"{to} - {kar}",
                        "karigar": kar, "size_key": sz_key, "qty": qty
                    })
                    st.success("Moved!"); st.rerun()
                else: st.error("Not enough stock")

# 5. MASTERS
elif page == "Masters":
    render_header("Masters")
    
    t1, t2, t3, t4, t5 = st.tabs(["Supplier", "Item", "Staff", "Fab", "Proc"])
    
    with t1:
        with st.form("sup"):
            n=st.text_input("Name"); g=st.text_input("GST"); c=st.text_input("Ph")
            if st.form_submit_button("Add"): db.add_supplier(n,g,c); st.rerun()
        st.dataframe(db.get_supplier_details_df(), use_container_width=True)
        
    with t2:
        with st.form("itm"):
            n=st.text_input("Name"); c=st.text_input("Code")
            if st.form_submit_button("Add"): db.add_item_master(n,c,"Mix",[]); st.rerun()
        st.dataframe(db.get_all_items(), use_container_width=True)
        
    with t3: # Staff Form
        with st.form("stf"):
            n=st.text_input("Name"); r=st.selectbox("Role", ["Helper", "Stitching Karigar", "Cutting Master"])
            if st.form_submit_button("Add"): db.add_staff(n,r); st.success("Added"); st.rerun()
        st.dataframe(db.get_all_staff(), use_container_width=True)
        
    with t4:
        with st.form("fab"):
            n=st.text_input("Name")
            if st.form_submit_button("Add"): db.add_material(n,""); st.rerun()
            
    with t5:
        with st.form("prc"):
            n=st.text_input("Process")
            if st.form_submit_button("Add"): db.add_process(n); st.rerun()

# 6. BOM
elif page == "BOM":
    render_header("BOM Recipes")
    
    if 'bom_l' not in st.session_state: st.session_state.bom_l=[]
    
    tgt = st.selectbox("Target Item", [""]+db.get_unique_item_names())
    
    c1, c2 = st.columns(2)
    m = c1.selectbox("Mat", [""]+db.get_material_names())
    q = c2.number_input("Qty", 0.0)
    
    if st.button("Add"): st.session_state.bom_l.append({"Mat":m, "Qty":q})
    
    if st.session_state.bom_l:
        st.dataframe(pd.DataFrame(st.session_state.bom_l), use_container_width=True)
        if st.button("Save", type="primary"):
            db.create_bom(tgt, st.session_state.bom_l); st.success("Saved"); st.session_state.bom_l=[]; st.rerun()

# 7. INVENTORY
elif page == "Inventory":
    render_header("Stock")
    
    t1, t2 = st.tabs(["Rolls", "Acc"])
    with t1:
        s = db.get_all_fabric_stock_summary()
        if s: st.dataframe(pd.DataFrame([{"F":x['_id']['name'], "C":x['_id']['color'], "Q":x['total_qty']} for x in s]), use_container_width=True)
    with t2:
        with st.expander("Add"):
            n=st.selectbox("Item", [""]+db.get_accessory_names()); q=st.number_input("Qty")
            if st.button("Add"): db.update_accessory_stock(n, "Inward", q, "Pcs"); st.rerun()
        st.dataframe(pd.DataFrame(db.get_accessory_stock()), use_container_width=True)

# 8. MCPL
elif page == "MCPL":
    render_header("Vin Lister")
    t1, t2 = st.tabs(["Catalog", "Upload"])
    with t1:
        st.dataframe(db.get_mcpl_catalog(), use_container_width=True)
    with t2:
        up = st.file_uploader("CSV", type=['csv'])
        if up and st.button("Run"): db.mcpl_bulk_upload(pd.read_csv(up)); st.success("Done")

# 9. TRACK & CONFIG
elif page == "Track Lot":
    render_header("Track")
    l = st.selectbox("Lot", [""]+db.get_all_lot_numbers())
    if l:
        d = db.get_lot_details(l)['current_stage_stock']
        # Pretty pivot
        data = []
        for stage, sizes in d.items():
            for sz, qty in sizes.items():
                if qty > 0: data.append({"Stage": stage, "Size": sz, "Qty": qty})
        st.dataframe(pd.DataFrame(data), use_container_width=True)

elif page == "Productivity & Pay":
    render_header("Productivity")
    st.dataframe(db.get_staff_productivity(datetime.datetime.now().month, 2025), use_container_width=True)

elif page == "Config":
    render_header("Config")
    with st.form("rate"):
        c1,c2=st.columns(2)
        i=c1.text_input("Item"); r=c2.number_input("Rate")
        m=st.selectbox("Process", db.get_all_processes())
        if st.form_submit_button("Set Rate"): db.add_piece_rate(i,"",m,r,datetime.date.today()); st.success("Saved")

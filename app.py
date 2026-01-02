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

# --- 2. MOBILE CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');
    
    /* RESET & FONT */
    html, body, .stApp { 
        font-family: 'Nunito', sans-serif !important; 
        background-color: #F8F9FA !important; 
        color: #343A40;
    }

    /* HIDE SIDEBAR TOGGLE */
    [data-testid="stSidebarCollapsedControl"] { display: none; }

    /* CARD STYLING */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #E9ECEF;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.04);
        margin-bottom: 16px;
    }

    /* BIG BUTTONS (Mobile Touch Targets) */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 55px;
        font-weight: 700;
        font-size: 16px;
        border: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        transition: transform 0.1s;
    }
    .stButton > button:active { transform: scale(0.98); }

    /* PRIMARY BUTTON (Orange) */
    button[kind="primary"] {
        background: linear-gradient(135deg, #FE9F43 0%, #FF8E25 100%) !important;
        color: white !important;
    }

    /* SECONDARY BUTTON (White/Grey) */
    button[kind="secondary"] {
        background-color: #FFFFFF !important;
        color: #495057 !important;
        border: 1px solid #DEE2E6 !important;
    }

    /* INPUTS */
    input, .stSelectbox > div > div, .stDateInput > div > div {
        background-color: #FFFFFF !important;
        border: 1px solid #CED4DA !important;
        border-radius: 10px !important;
        min-height: 50px !important;
        font-size: 16px !important;
    }

    /* TEXT HEADERS */
    h1, h2, h3 { color: #212529; font-weight: 800 !important; letter-spacing: -0.5px; }
    
    /* METRICS */
    [data-testid="stMetricLabel"] { font-size: 12px; color: #ADB5BD; font-weight: 700; text-transform: uppercase; }
    [data-testid="stMetricValue"] { font-size: 24px; color: #212529; font-weight: 800; }

    /* SECTION HEADERS IN HOME */
    .section-header {
        font-size: 13px;
        font-weight: 800;
        color: #ADB5BD;
        text-transform: uppercase;
        margin-top: 20px;
        margin-bottom: 10px;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. STATE & NAV ---
if 'page' not in st.session_state: st.session_state.page = "Home"

def nav(page_name):
    st.session_state.page = page_name
    st.rerun()

def render_header(title):
    c1, c2 = st.columns([1, 4])
    with c1:
        if st.button("⬅", help="Back to Menu"): nav("Home")
    with c2:
        st.markdown(f"<h2 style='margin:0; padding-top:5px;'>{title}</h2>", unsafe_allow_html=True)
    st.markdown("---")

# --- 4. APP FLOW ---
page = st.session_state.page

# HOME
if page == "Home":
    c_logo, c_yr = st.columns([3, 1])
    with c_logo: st.markdown("<h1 style='color:#FE9F43;'>⚡ Shine Arc</h1>", unsafe_allow_html=True)
    with c_yr: st.selectbox("Year", ["2025", "2024"], label_visibility="collapsed")

    stats = db.get_dashboard_stats()
    s1, s2, s3 = st.columns(3)
    s1.metric("Active", stats.get('active_lots', 0))
    s2.metric("Done", stats.get('completed_lots', 0))
    s3.metric("Stock", stats.get('fabric_rolls', 0))

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
    if c5.button("📦 Inventory", use_container_width=True): nav("Inventory")
    if c6.button("👥 Masters", use_container_width=True): nav("Masters")
    if st.button("📅 Attendance", use_container_width=True): nav("Attendance")

    st.markdown('<div class="section-header">🚀 INTEGRATIONS</div>', unsafe_allow_html=True)
    if st.button("🌐 Vin Lister (MCPL)", use_container_width=True): nav("MCPL")

    st.markdown('<div class="section-header">⚙️ SYSTEM</div>', unsafe_allow_html=True)
    c7, c8 = st.columns(2)
    if c7.button("📍 Track Lot", use_container_width=True): nav("Track Lot")
    if c8.button("⚙️ Config", use_container_width=True): nav("Config")

# 1. SUPPLIER LEDGER
elif page == "Supplier Ledger":
    render_header("Supplier Ledger")
    
    tab_op = st.radio("Mode", ["Add Entry", "View Ledger"], horizontal=True, label_visibility="collapsed")
    suppliers = [""] + db.get_supplier_names()
    
    if tab_op == "Add Entry":
        with st.container(border=True):
            sup = st.selectbox("Supplier", suppliers)
            date = st.date_input("Date")
            
            # Transaction Type Selector
            txn_type = st.selectbox("Transaction Type", ["Bill (Purchase)", "Payment (Outgoing)", "Debit Note (Return)"])
            
            if txn_type == "Bill (Purchase)":
                if 'bill_items' not in st.session_state: st.session_state.bill_items = []
                
                bill_no = st.text_input("Bill No")
                
                # Item Adder
                with st.expander("Add Items", expanded=True):
                    c1, c2 = st.columns(2)
                    nm = c1.text_input("Item Name")
                    qty = c2.number_input("Qty", 1.0)
                    
                    c3, c4 = st.columns(2)
                    rate = c3.number_input("Rate", 0.0)
                    tax = c4.selectbox("Tax %", [0, 5, 12, 18, 28])
                    
                    if st.button("Add Item", key="add_i"):
                        amt = (qty * rate)
                        t_amt = amt * (tax/100)
                        tot = amt + t_amt
                        st.session_state.bill_items.append({
                            "Item": nm, "Qty": qty, "Rate": rate, 
                            "Tax %": tax, "Tax Amt": t_amt, "Total": tot
                        })
                
                if st.session_state.bill_items:
                    df = pd.DataFrame(st.session_state.bill_items)
                    st.dataframe(df, use_container_width=True)
                    g_tot = df['Total'].sum()
                    st.metric("Total Bill Amount", f"₹ {g_tot:,.2f}")
                    
                    if st.button("💾 Save Bill", type="primary", use_container_width=True):
                        if sup and bill_no:
                            rem = f"Items: {len(df)} | Tax: {df['Tax Amt'].sum():.2f}"
                            db.add_supplier_txn(sup, str(date), "Bill", g_tot, bill_no, rem, None, st.session_state.bill_items)
                            st.success("Saved!"); st.session_state.bill_items=[]; st.rerun()
            
            elif txn_type == "Payment (Outgoing)":
                amt = st.number_input("Amount (₹)", 0.0)
                mode = st.selectbox("Mode", ["Cash", "UPI", "Bank"])
                if st.button("Save Payment", type="primary", use_container_width=True):
                    if sup and amt > 0: 
                        db.add_supplier_txn(sup, str(date), "Payment", amt, "", f"Via {mode}")
                        st.success("Saved!")
            
            elif txn_type == "Debit Note (Return)":
                amt = st.number_input("Return Amount (₹)", 0.0)
                reason = st.text_input("Reason")
                if st.button("Save Return", type="primary", use_container_width=True):
                    if sup and amt > 0: 
                        db.add_supplier_txn(sup, str(date), "Debit Note", amt, "", reason)
                        st.success("Saved!")

    elif tab_op == "View Ledger":
        sel_sup = st.selectbox("Supplier", suppliers)
        if sel_sup:
            df = db.get_supplier_ledger(sel_sup)
            if not df.empty:
                bal = df.iloc[-1]['Balance']
                st.metric("Balance", f"₹ {bal:,.2f}", delta="Payable" if bal>0 else "Advance", delta_color="inverse")
                
                # FIXED COLUMN NAMES HERE
                st.dataframe(df[["Date", "Type", "Credit (Bill)", "Debit (Paid/Return)", "Balance"]], use_container_width=True)
                
                # Delete Logic
                txn_opts = [f"{r['Date']} | {r['Type']} | ₹{r['Credit (Bill)'] or r['Debit (Paid/Return)']}" for _, r in df.iterrows()]
                sel_txn_idx = st.selectbox("Manage Transaction", range(len(txn_opts)), format_func=lambda x: txn_opts[x])
                
                if st.button("Delete Selected", type="secondary", use_container_width=True):
                    txn_id = df.iloc[sel_txn_idx]['ID']
                    if db.delete_supplier_txn(txn_id): st.success("Deleted"); st.rerun()
            else: st.info("No Data")

# 2. FABRIC INWARD
elif page == "Fabric Inward":
    render_header("Fabric Inward")
    t1, t2 = st.tabs(["Entry", "Upload"])
    
    with t1:
        sup = st.selectbox("Supplier", [""]+db.get_supplier_names())
        bill = st.text_input("Bill No")
        
        c1, c2 = st.columns(2)
        nm = c1.selectbox("Fabric", [""]+sorted(db.get_materials()['name'].tolist()))
        col = c2.selectbox("Color", [""]+db.get_colors())
        
        st.markdown("###### Rolls")
        if 'r_in' not in st.session_state: st.session_state.r_in = 3
        cols = st.columns(3); r_data=[]
        for i in range(st.session_state.r_in):
            v = cols[i%3].number_input(f"R{i+1}", 0.0, key=f"fr_{i}")
            if v>0: r_data.append(v)
            
        if st.button("Add More Fields", use_container_width=True): st.session_state.r_in += 3; st.rerun()
        
        st.markdown("---")
        if st.button("💾 Save Stock", type="primary", use_container_width=True):
            if sup and nm and r_data:
                db.add_fabric_rolls_batch(nm, col, r_data, "Kg", sup, bill)
                st.success(f"Saved {len(r_data)} Rolls!"); st.rerun()
    
    with t2:
        up = st.file_uploader("CSV", type=['csv'])
        if up and st.button("Upload", use_container_width=True):
            c = db.bulk_add_fabric_rolls(pd.read_csv(up)); st.success(f"Added {c}")

# 3. CUTTING FLOOR
elif page == "Cutting Floor":
    render_header("Cutting Floor")
    next_lot = db.get_next_lot_no()
    st.info(f"New Lot: **{next_lot}**")
    
    if 'lot_breakdown' not in st.session_state: st.session_state.lot_breakdown={}
    if 'fabric_selections' not in st.session_state: st.session_state.fabric_selections={}
    
    item = st.selectbox("Item", [""]+db.get_unique_item_names())
    code = st.selectbox("Code", [""]+(db.get_codes_by_item_name(item) if item else []))
    
    req_fabs = []
    if code:
        det = db.get_item_details_by_code(code)
        if det: req_fabs = det.get('required_fabrics', [])
    
    if req_fabs:
        for f in req_fabs:
            with st.expander(f"Select {f}", expanded=False):
                ss = db.get_all_fabric_stock_summary()
                avail_c = sorted(list(set([s['_id']['color'] for s in ss if s['_id']['name']==f])))
                fc = st.selectbox(f"Color", avail_c, key=f"c_{f}")
                if fc:
                    rls = db.get_available_rolls(f, fc)
                    if rls:
                        sel = []; w = 0.0
                        sel_indices = st.multiselect(f"Rolls ({rls[0]['uom']})", [f"{r['roll_no']} ({r['quantity']})" for r in rls], key=f"ms_{f}")
                        for si in sel_indices:
                            r_no = si.split(' ')[0]
                            for r in rls:
                                if r['roll_no'] == r_no: sel.append(r['_id']); w += r['quantity']
                        st.session_state.fabric_selections[f] = {"roll_ids": sel, "total_weight": w}
    
    st.markdown("---")
    l_col = st.text_input("Lot Color")
    sizes = db.get_sizes()
    if sizes:
        c1, c2, c3 = st.columns(3)
        cols_ref = [c1, c2, c3]
        for i, z in enumerate(sizes):
            q = cols_ref[i%3].number_input(z, 0, key=f"sz_{z}")
            if q > 0 and l_col: st.session_state.lot_breakdown[f"{l_col}_{z}"] = q
            
    if st.button("🚀 Create Lot", type="primary", use_container_width=True):
        flat_ids=[]; fs=[]
        for f,d in st.session_state.fabric_selections.items(): flat_ids.extend(d['roll_ids']); fs.append({"name":f,"weight":d['total_weight']})
        if item and code and st.session_state.lot_breakdown:
            db.create_lot({
                "lot_no": next_lot, "item_name": item, "item_code": code, "color": l_col,
                "created_by": "MobileUser", "size_breakdown": st.session_state.lot_breakdown,
                "fabrics_consumed": fs, "total_fabric_weight": 0
            }, flat_ids)
            st.success("Created!"); st.session_state.lot_breakdown={}; st.session_state.fabric_selections={}; st.rerun()

# 4. STITCHING FLOOR
elif page == "Stitching Floor":
    render_header("Stitching Floor")
    active = db.get_active_lots()
    lot = st.selectbox("Select Lot", [""]+[x['lot_no'] for x in active])
    
    if lot:
        l = db.get_lot_details(lot)
        st.markdown(f"**Item:** {l['item_name']}")
        with st.form("move_form"):
            c1, c2 = st.columns(2)
            stages = [k for k,v in l['current_stage_stock'].items() if sum(v.values()) > 0]
            frm = c1.selectbox("From", stages)
            to = c2.selectbox("To", db.get_stages_for_item(l['item_name']))
            staff = st.selectbox("Karigar", db.get_staff_by_role("Stitching Karigar"))
            
            avail_stock = l['current_stage_stock'].get(frm, {})
            valid_keys = [k for k,v in avail_stock.items() if v > 0]
            key = st.selectbox("Size/Color", valid_keys)
            qty = st.number_input("Qty", 1, value=1)
            
            if st.form_submit_button("Move Items", use_container_width=True):
                if key and qty <= avail_stock[key]:
                    db.move_lot_stage({"lot_no": lot, "from_stage": frm, "to_stage_key": f"{to} - {staff}", "karigar": staff, "size_key": key, "qty": qty})
                    st.success("Moved!"); st.rerun()

# 5. MCPL
elif page == "MCPL":
    render_header("Vin Lister (MCPL)")
    m = st.radio("Action", ["Catalog", "Upload", "Price"], horizontal=True, label_visibility="collapsed")
    
    if m == "Catalog":
        df = db.get_mcpl_catalog()
        if not df.empty: st.dataframe(df[["sku", "name", "base_price"]], use_container_width=True)
        else: st.info("Empty")
        with st.expander("Add Product"):
            sku = st.text_input("SKU"); nm = st.text_input("Name"); bp = st.number_input("Price")
            if st.button("Add"): db.mcpl_add_product(sku, nm, "Gen", bp); st.rerun()
            
    elif m == "Upload":
        up = st.file_uploader("CSV", type=['csv'])
        if up and st.button("Upload", use_container_width=True):
            c, e = db.mcpl_bulk_upload(pd.read_csv(up)); st.success(f"Done: {c}")

# 6. INVENTORY
elif page == "Inventory":
    render_header("Inventory")
    t1, t2 = st.tabs(["Fabrics", "Accessories"])
    with t1:
        s = db.get_all_fabric_stock_summary()
        if s: st.dataframe(pd.DataFrame([{"Name":x['_id']['name'], "Color":x['_id']['color'], "Qty":x['total_qty']} for x in s]), use_container_width=True)
    with t2:
        df = pd.DataFrame(db.get_accessory_stock())
        if not df.empty: st.dataframe(df[['name', 'quantity']], use_container_width=True)
        with st.expander("Add Stock"):
            n = st.selectbox("Item", [""]+db.get_accessory_names()); q = st.number_input("Qty", 0.0)
            if st.button("Add", use_container_width=True): 
                db.update_accessory_stock(n, "Inward", q, "Pcs"); st.rerun()

# 7. MASTERS
elif page == "Masters":
    render_header("Masters")
    opt = st.selectbox("Manage", ["Suppliers", "Items", "Staff", "Fabric", "Process"])
    
    if opt == "Suppliers":
        with st.form("sup"):
            n = st.text_input("Name"); g = st.text_input("GST")
            if st.form_submit_button("Add Supplier", use_container_width=True):
                db.add_supplier(n, g); st.success("Added"); st.rerun()
        st.dataframe(db.get_supplier_details_df(), use_container_width=True)
        
    elif opt == "Items":
        with st.form("it"):
            n = st.text_input("Name"); c = st.text_input("Code")
            if st.form_submit_button("Add Item", use_container_width=True):
                db.add_item_master(n, c, "Mix", []); st.success("Added"); st.rerun()
        st.dataframe(db.get_all_items(), use_container_width=True)

# 8. BOM
elif page == "BOM":
    render_header("BOM Recipes")
    if 'bom_list' not in st.session_state: st.session_state.bom_list=[]
    tgt = st.selectbox("Target Item", [""]+db.get_unique_item_names())
    c1, c2 = st.columns(2)
    mat = c1.selectbox("Material", [""]+db.get_material_names())
    qty = c2.number_input("Qty", 0.0)
    if st.button("Add to List", use_container_width=True): st.session_state.bom_list.append({"Mat":mat, "Qty":qty})
    if st.session_state.bom_list:
        st.dataframe(pd.DataFrame(st.session_state.bom_list), use_container_width=True)
        if st.button("Save Recipe", type="primary", use_container_width=True):
            db.create_bom(tgt, st.session_state.bom_list); st.success("Saved!"); st.session_state.bom_list=[]; st.rerun()

# 9. OTHER
elif page == "Attendance":
    render_header("Attendance")
    st.info("Mark Attendance logic here...")

elif page == "Productivity & Pay":
    render_header("Productivity")
    st.dataframe(db.get_staff_productivity(datetime.datetime.now().month, 2025), use_container_width=True)

elif page == "Track Lot":
    render_header("Track Lot")
    l = st.selectbox("Lot", [""]+db.get_all_lot_numbers())
    if l: st.json(db.get_lot_details(l)['current_stage_stock'])

elif page == "Config":
    render_header("Configuration")
    st.write("Settings")

import streamlit as st
import pandas as pd
import db_manager as db
import datetime

# --- 1. MOBILE CONFIG ---
st.set_page_config(page_title="Shine Arc Lite", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

# --- 2. CLEAN MOBILE CSS ---
st.markdown("""
<style>
    /* Remove padding/margins for full screen feel */
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    
    /* Hide default elements */
    header, footer, [data-testid="stSidebar"] { display: none !important; }
    
    /* CARD STYLE */
    .card {
        background: white; border-radius: 12px; padding: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #eee; margin-bottom: 15px;
    }
    
    /* BIG BUTTONS */
    .stButton>button {
        width: 100%; height: 55px; border-radius: 12px; font-weight: bold; font-size: 16px;
        border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* PRIMARY BUTTON COLOR */
    button[kind="primary"] { background: #FE9F43 !important; color: white !important; }
    
    /* NAVIGATION BAR */
    .nav-bar {
        display: flex; justify-content: space-around; background: white; padding: 10px;
        position: fixed; bottom: 0; left: 0; width: 100%; border-top: 1px solid #eee; z-index: 1000;
    }
    .nav-item { text-align: center; font-size: 10px; color: #888; cursor: pointer; }
    
    /* METRICS */
    [data-testid="stMetricValue"] { font-size: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 3. NAVIGATION STATE ---
if 'nav' not in st.session_state: st.session_state.nav = "Home"

def go_home(): st.session_state.nav = "Home"; st.rerun()

# --- 4. HEADER ---
c1, c2 = st.columns([1, 4])
if st.session_state.nav != "Home":
    if c1.button("⬅"): go_home()
    c2.markdown(f"### {st.session_state.nav}")
else:
    st.markdown("### ⚡ Shine Arc App")

# =========================================================
# PAGE: HOME (DASHBOARD)
# =========================================================
if st.session_state.nav == "Home":
    # 1. Quick Stats
    stats = db.get_dashboard_stats()
    c1, c2, c3 = st.columns(3)
    c1.metric("Active Lots", stats['active_lots'])
    c2.metric("Fab Rolls", stats['rolls'])
    c3.metric("Pending", "₹ 0") # Placeholder

    st.divider()

    # 2. MAIN ACTIONS (BIG BUTTONS)
    st.markdown("##### 🚀 Quick Actions")
    
    if st.button("🛒 New Purchase (Bill + Stock)", type="primary"): 
        st.session_state.nav = "Purchase"
        st.rerun()
        
    c1, c2 = st.columns(2)
    if c1.button("✂️ Start Lot"): 
        st.session_state.nav = "Create Lot"
        st.rerun()
    if c2.button("🧵 Move Stage"): 
        st.session_state.nav = "Production"
        st.rerun()
        
    st.divider()
    
    st.markdown("##### 📂 Management")
    m1, m2 = st.columns(2)
    if m1.button("📒 Ledger"): 
        st.session_state.nav = "Ledger"
        st.rerun()
    if m2.button("📦 Stock"): 
        st.session_state.nav = "Inventory"
        st.rerun()
        
    if st.button("⚙️ Settings & Masters"): 
        st.session_state.nav = "Settings"
        st.rerun()

# =========================================================
# PAGE: SMART PURCHASE (BILL + STOCK)
# =========================================================
elif st.session_state.nav == "Purchase":
    with st.container():
        # A. BASIC BILL INFO
        c1, c2 = st.columns(2)
        sup = c1.selectbox("Supplier", [""] + db.get_supplier_names())
        date = c2.date_input("Date")
        bill_no = st.text_input("Bill Number")
        
        # B. STOCK TOGGLE
        st.markdown("---")
        stock_type = st.radio("Contains Stock?", ["No Stock (Expense)", "Fabric Rolls", "Accessories"], horizontal=True)
        
        stock_data = {}
        
        if stock_type == "Fabric Rolls":
            f_name = st.selectbox("Fabric", [""]+db.get_materials())
            f_col = st.selectbox("Color", [""]+db.get_colors())
            n_rolls = st.number_input("Number of Rolls", 1, 50, 1)
            
            rolls_wt = []
            cols = st.columns(3)
            for i in range(int(n_rolls)):
                w = cols[i%3].number_input(f"R{i+1}", 0.0, key=f"r{i}")
                if w > 0: rolls_wt.append(w)
            
            stock_data = {"name": f_name, "color": f_col, "rolls": rolls_wt}
            
        elif stock_type == "Accessories":
            a_name = st.selectbox("Item", [""]+db.get_acc_names())
            a_qty = st.number_input("Quantity", 0.0)
            a_uom = st.selectbox("UOM", ["Pcs", "Box", "Kg"])
            stock_data = {"name": a_name, "qty": a_qty, "uom": a_uom}

        # C. BILL DETAILS (ITEM WISE)
        st.markdown("---")
        st.markdown("###### Bill Items")
        if 'p_items' not in st.session_state: st.session_state.p_items = []
        
        i1, i2, i3 = st.columns([2, 1, 1])
        it_nm = i1.text_input("Item")
        it_qty = i2.number_input("Qty", 1.0)
        it_rate = i3.number_input("Rate", 0.0)
        
        if st.button("Add Line Item"):
            st.session_state.p_items.append({"Item": it_nm, "Qty": it_qty, "Rate": it_rate, "Amt": it_qty*it_rate})
            
        if st.session_state.p_items:
            df_i = pd.DataFrame(st.session_state.p_items)
            st.dataframe(df_i, use_container_width=True)
            base_tot = df_i['Amt'].sum()
            
            # D. TAX & TOTAL
            c_tax, c_tot = st.columns(2)
            tax_slab = c_tax.selectbox("Tax %", [0, 5, 12, 18])
            tax_amt = base_tot * (tax_slab/100)
            grand_tot = base_tot + tax_amt
            c_tot.metric("Payable", f"₹ {grand_tot:,.0f}")
            
            # E. PAYMENT
            pay_now = st.checkbox("Pay Now?")
            pay_data = None
            if pay_now:
                pm = st.selectbox("Mode", ["Cash", "UPI", "Bank"])
                pay_data = {"amount": grand_tot, "mode": pm}
            
            # F. SAVE BUTTON
            if st.button("✅ SAVE TRANSACTION", type="primary"):
                if sup and bill_no:
                    payload = {
                        "supplier": sup, "date": str(date), "bill_no": bill_no,
                        "amount": base_tot, "tax_slab": tax_slab, "tax_amt": tax_amt, "grand_total": grand_tot,
                        "items": st.session_state.p_items,
                        "stock_type": "None" if stock_type=="No Stock (Expense)" else "Fabric" if stock_type=="Fabric Rolls" else "Accessory",
                        "stock_data": stock_data,
                        "payment": pay_data
                    }
                    res, msg = db.process_smart_purchase(payload)
                    if res: 
                        st.success("Saved Successfully!"); st.session_state.p_items=[]; st.rerun()
                    else: st.error(msg)
                else: st.error("Supplier and Bill No Required")

# =========================================================
# PAGE: PRODUCTION (MOVE)
# =========================================================
elif st.session_state.nav == "Production":
    active_lots = db.get_active_lots()
    sel_lot = st.selectbox("Select Lot to Move", [""] + active_lots)
    
    if sel_lot:
        l = db.get_lot_info(sel_lot)
        st.info(f"Item: {l['item_name']} | Color: {l['color']}")
        
        # Show Current Status (Simple Table)
        stock = l['current_stage_stock']
        stages = [k for k, v in stock.items() if sum(v.values()) > 0]
        
        from_st = st.selectbox("Move From", stages)
        avail_stock = stock.get(from_st, {})
        
        # Select what to move
        c1, c2 = st.columns(2)
        sz = c1.selectbox("Size", [k for k, v in avail_stock.items() if v>0])
        max_q = avail_stock.get(sz, 0)
        qty = c2.number_input(f"Qty (Max {max_q})", 1, max_q, max_q)
        
        # Select Destination
        to_st = st.selectbox("Move To", ["Stitching", "Washing", "Finishing", "Packing"])
        karigar = st.selectbox("Worker", db.get_staff("Stitching Karigar"))
        
        if st.button("Move Items", type="primary"):
            db.move_lot(sel_lot, from_st, f"{to_st} - {karigar}", karigar, qty, sz)
            st.success("Moved!"); st.rerun()

# =========================================================
# PAGE: LEDGER
# =========================================================
elif st.session_state.nav == "Ledger":
    sup = st.selectbox("Select Supplier", [""] + db.get_supplier_names())
    
    if sup:
        # Quick Payment Button
        with st.expander("➕ Add Payment"):
            c1, c2 = st.columns(2)
            amt = c1.number_input("Amount", 0.0)
            mode = c2.selectbox("Mode", ["Cash", "UPI"])
            if st.button("Save Payment"):
                if amt > 0: 
                    db.add_simple_payment(sup, datetime.date.today(), amt, mode, "Manual Pay")
                    st.success("Saved"); st.rerun()
        
        # View Ledger
        df = db.get_supplier_ledger(sup)
        if not df.empty:
            bal = df.iloc[-1]['Balance']
            st.metric("Balance", f"₹ {bal:,.2f}", delta="Payable" if bal>0 else "Advance", delta_color="inverse")
            st.dataframe(df[["Date", "Type", "Credit", "Debit", "Balance"]], use_container_width=True)
        else: st.warning("No History")

# =========================================================
# PAGE: SETTINGS (MASTERS)
# =========================================================
elif st.session_state.nav == "Settings":
    t = st.selectbox("Manage", ["Suppliers", "Items", "Staff", "Fabrics"])
    
    with st.form("add_m"):
        if t == "Suppliers":
            n=st.text_input("Name"); g=st.text_input("GST"); c=st.text_input("Phone"); a=st.text_input("Address")
            if st.form_submit_button("Add Supplier"): db.add_supplier(n,g,c,a); st.success("Done")
            
        elif t == "Items":
            n=st.text_input("Item Name"); c=st.text_input("Item Code")
            if st.form_submit_button("Add Item"): db.add_item(n,c); st.success("Done")
            
        elif t == "Staff":
            n=st.text_input("Name"); r=st.selectbox("Role", ["Helper", "Stitching Karigar"])
            if st.form_submit_button("Add Staff"): db.add_staff(n,r); st.success("Done")
            
        elif t == "Fabrics":
            n=st.text_input("Fabric Name")
            if st.form_submit_button("Add Fabric"): db.add_fabric(n); st.success("Done")

# =========================================================
# PAGE: INVENTORY VIEW
# =========================================================
elif st.session_state.nav == "Inventory":
    st.markdown("#### 🧶 Fabric Stock")
    s = db.get_all_fabric_stock_summary()
    st.dataframe(pd.DataFrame([{"Fab":x['_id']['name'], "Col":x['_id']['color'], "Kg":x['total_qty']} for x in s]), use_container_width=True)

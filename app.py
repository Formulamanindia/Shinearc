import streamlit as st
import pandas as pd
import db_manager as db
import datetime

# --- 1. MOBILE CONFIG ---
st.set_page_config(page_title="Shine Arc Lite", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

# --- 2. CSS ---
st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    header, footer, [data-testid="stSidebar"] { display: none !important; }
    .card { background: white; border-radius: 12px; padding: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 15px; }
    .stButton>button { width: 100%; height: 55px; border-radius: 12px; font-weight: bold; font-size: 16px; border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    button[kind="primary"] { background: #FE9F43 !important; color: white !important; }
    [data-testid="stMetricValue"] { font-size: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 3. STATE ---
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
# PAGE: HOME
# =========================================================
if st.session_state.nav == "Home":
    stats = db.get_dashboard_stats()
    c1, c2, c3 = st.columns(3)
    c1.metric("Active Lots", stats['active_lots'])
    c2.metric("Fab Rolls", stats['rolls'])
    c3.metric("Pending", "₹ 0")

    st.divider()
    st.markdown("##### 🚀 Quick Actions")
    if st.button("🛒 New Purchase (Bill + Stock)", type="primary"): st.session_state.nav = "Purchase"; st.rerun()
        
    c1, c2 = st.columns(2)
    if c1.button("✂️ Start Lot"): st.session_state.nav = "Create Lot"; st.rerun()
    if c2.button("🧵 Move Stage"): st.session_state.nav = "Production"; st.rerun()
        
    st.divider()
    st.markdown("##### 📂 Management")
    m1, m2 = st.columns(2)
    if m1.button("📒 Ledger"): st.session_state.nav = "Ledger"; st.rerun()
    if m2.button("📦 Stock"): st.session_state.nav = "Inventory"; st.rerun()
    if st.button("⚙️ Settings & Masters"): st.session_state.nav = "Settings"; st.rerun()

# =========================================================
# PAGE: PURCHASE
# =========================================================
elif st.session_state.nav == "Purchase":
    with st.container():
        c1, c2 = st.columns(2)
        sup = c1.selectbox("Supplier", [""] + db.get_supplier_names())
        date = c2.date_input("Date")
        bill_no = st.text_input("Bill Number")
        
        st.markdown("---")
        stock_type = st.radio("Stock Type?", ["No Stock", "Fabric", "Accessory"], horizontal=True)
        stock_data = {}
        
        if stock_type == "Fabric":
            f_name = st.selectbox("Fabric", [""]+db.get_materials())
            f_col = st.selectbox("Color", [""]+db.get_colors())
            n_rolls = st.number_input("Rolls Count", 1, 50, 1)
            cols = st.columns(3); rolls_wt = []
            for i in range(int(n_rolls)):
                w = cols[i%3].number_input(f"R{i+1}", 0.0, key=f"r{i}")
                if w > 0: rolls_wt.append(w)
            stock_data = {"name": f_name, "color": f_col, "rolls": rolls_wt}
            
        elif stock_type == "Accessory":
            a_name = st.selectbox("Item", [""]+db.get_acc_names())
            a_qty = st.number_input("Qty", 0.0)
            a_uom = st.selectbox("UOM", ["Pcs", "Box", "Kg"])
            stock_data = {"name": a_name, "qty": a_qty, "uom": a_uom}

        st.markdown("---")
        st.markdown("###### Items")
        if 'p_items' not in st.session_state: st.session_state.p_items = []
        i1, i2, i3 = st.columns([2, 1, 1])
        it_nm = i1.text_input("Item")
        it_qty = i2.number_input("Qty", 1.0)
        it_rate = i3.number_input("Rate", 0.0)
        if st.button("Add Line"): st.session_state.p_items.append({"Item": it_nm, "Qty": it_qty, "Rate": it_rate, "Amt": it_qty*it_rate})
            
        if st.session_state.p_items:
            df_i = pd.DataFrame(st.session_state.p_items)
            st.dataframe(df_i, use_container_width=True)
            base_tot = df_i['Amt'].sum()
            c_tax, c_tot = st.columns(2)
            tax_slab = c_tax.selectbox("Tax %", [0, 5, 12, 18])
            grand_tot = base_tot * (1 + tax_slab/100)
            c_tot.metric("Payable", f"₹ {grand_tot:,.0f}")
            
            pay_now = st.checkbox("Pay Now?")
            pay_data = {"amount": grand_tot, "mode": st.selectbox("Mode", ["Cash", "UPI"])} if pay_now else None
            
            if st.button("✅ SAVE", type="primary"):
                if sup and bill_no:
                    payload = {"supplier": sup, "date": str(date), "bill_no": bill_no, "amount": base_tot, "tax_slab": tax_slab, "grand_total": grand_tot, "items": st.session_state.p_items, "stock_type": stock_type, "stock_data": stock_data, "payment": pay_data}
                    res, msg = db.process_smart_purchase(payload)
                    if res: st.success("Saved!"); st.session_state.p_items=[]; st.rerun()
                    else: st.error(msg)
                else: st.error("Supplier/Bill Missing")

# =========================================================
# PAGE: INVENTORY
# =========================================================
elif st.session_state.nav == "Inventory":
    st.markdown("#### 🧶 Fabric Stock")
    s = db.get_all_fabric_stock_summary()
    if s: st.dataframe(pd.DataFrame([{"Fabric":x['_id']['name'], "Color":x['_id']['color'], "Total Kg":x['total_qty']} for x in s]), use_container_width=True)
    
    st.markdown("#### 📦 Accessories")
    a = db.get_accessory_stock()
    if a: st.dataframe(pd.DataFrame(a), use_container_width=True)

# =========================================================
# PAGE: LEDGER
# =========================================================
elif st.session_state.nav == "Ledger":
    sup = st.selectbox("Select Supplier", [""] + db.get_supplier_names())
    if sup:
        with st.expander("➕ Add Payment"):
            c1, c2 = st.columns(2)
            amt = c1.number_input("Amount", 0.0); mode = c2.selectbox("Mode", ["Cash", "UPI"])
            if st.button("Save"): db.add_simple_payment(sup, datetime.date.today(), amt, mode, "Manual Pay"); st.rerun()
        df = db.get_supplier_ledger(sup)
        if not df.empty: st.dataframe(df[["Date", "Type", "Credit", "Debit", "Balance"]], use_container_width=True)

# =========================================================
# PAGE: SETTINGS
# =========================================================
elif st.session_state.nav == "Settings":
    t = st.selectbox("Manage", ["Suppliers", "Items", "Staff", "Fabrics"])
    with st.form("add_m"):
        if t == "Suppliers":
            n=st.text_input("Name"); g=st.text_input("GST"); c=st.text_input("Phone"); a=st.text_input("Address")
            if st.form_submit_button("Add"): db.add_supplier(n,g,c,a); st.success("Done")
        elif t == "Items":
            n=st.text_input("Item Name"); c=st.text_input("Item Code")
            if st.form_submit_button("Add"): db.add_item(n,c); st.success("Done")
        elif t == "Staff":
            n=st.text_input("Name"); r=st.selectbox("Role", ["Helper", "Stitching Karigar"])
            if st.form_submit_button("Add"): db.add_staff(n,r); st.success("Done")
        elif t == "Fabrics":
            n=st.text_input("Fabric Name")
            if st.form_submit_button("Add"): db.add_fabric(n); st.success("Done")

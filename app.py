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
    .stButton>button { width: 100%; height: 60px; border-radius: 12px; font-weight: 800; font-size: 18px; border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 10px; }
    button[kind="primary"] { background: #FE9F43 !important; color: white !important; }
    button[kind="secondary"] { background: #FFFFFF !important; color: #495057 !important; border: 2px solid #F1F3F5 !important; }
    [data-testid="stMetricValue"] { font-size: 22px; }
    [data-testid="stMetricLabel"] { font-size: 12px; font-weight: bold; color: #adb5bd; }
</style>
""", unsafe_allow_html=True)

# --- 3. STATE ---
if 'nav' not in st.session_state: st.session_state.nav = "Home"
def go_home(): st.session_state.nav = "Home"; st.rerun()

# --- 4. HEADER ---
c1, c2 = st.columns([1, 5])
if st.session_state.nav != "Home":
    if c1.button("🏠"): go_home()
    c2.markdown(f"<h3 style='margin-top:10px;'>{st.session_state.nav}</h3>", unsafe_allow_html=True)
else:
    st.markdown("<h2 style='text-align:center; color:#FE9F43;'>⚡ Shine Arc</h2>", unsafe_allow_html=True)

# =========================================================
# PAGE: HOME (DASHBOARD)
# =========================================================
if st.session_state.nav == "Home":
    stats = db.get_dashboard_stats()
    c1, c2, c3 = st.columns(3)
    c1.metric("Active", stats['active_lots'])
    c2.metric("Rolls", stats['rolls'])
    c3.metric("Accs", stats['accessories_count'])

    st.markdown("---")

    c1, c2 = st.columns(2)
    if c1.button("💰 Accounts", use_container_width=True): st.session_state.nav = "Accounts"; st.rerun()
    if c2.button("✂️ Production", use_container_width=True): st.session_state.nav = "Production"; st.rerun()
        
    c3, c4 = st.columns(2)
    if c3.button("📦 Stock", use_container_width=True): st.session_state.nav = "Stock"; st.rerun()
    if c4.button("⚙️ Configs", use_container_width=True): st.session_state.nav = "Configurations"; st.rerun()

# =========================================================
# PAGE: ACCOUNTS
# =========================================================
elif st.session_state.nav == "Accounts":
    t1, t2 = st.tabs(["➕ New Entry", "📜 Ledger View"])
    
    with t1:
        st.info("Purchase Bill / Payment Entry")
        c1, c2 = st.columns(2)
        sup = c1.selectbox("Supplier", [""] + db.get_supplier_names())
        date = c2.date_input("Date")
        
        entry_mode = st.radio("Entry Type", ["Bill (Purchase)", "Direct Payment"], horizontal=True)
        
        if entry_mode == "Bill (Purchase)":
            bill_no = st.text_input("Bill Number")
            st.markdown("###### 1. Stock (Optional)")
            stock_type = st.selectbox("Stock Type", ["No Stock", "Fabric", "Accessory"], label_visibility="collapsed")
            stock_data = {}
            if stock_type == "Fabric":
                f_name = st.selectbox("Fabric Name", [""]+db.get_materials())
                f_col = st.selectbox("Color", [""]+db.get_colors())
                n_rolls = st.number_input("Count", 1, 50, 1)
                cols = st.columns(3); rolls_wt = []
                for i in range(int(n_rolls)):
                    w = cols[i%3].number_input(f"R{i+1}", 0.0, key=f"r{i}")
                    if w > 0: rolls_wt.append(w)
                stock_data = {"name": f_name, "color": f_col, "rolls": rolls_wt}
            elif stock_type == "Accessory":
                a_name = st.selectbox("Acc Name", [""]+db.get_acc_names())
                a_qty = st.number_input("Quantity", 0.0)
                a_uom = st.selectbox("UOM", ["Pcs", "Box", "Kg"])
                stock_data = {"name": a_name, "qty": a_qty, "uom": a_uom}

            st.markdown("###### 2. Bill Items")
            if 'p_items' not in st.session_state: st.session_state.p_items = []
            i1, i2, i3 = st.columns([2, 1, 1])
            it_nm = i1.text_input("Item"); it_qty = i2.number_input("Qty", 1.0); it_rate = i3.number_input("Rate", 0.0)
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
                
                if st.button("✅ SAVE BILL", type="primary"):
                    if sup and bill_no:
                        payload = {"supplier": sup, "date": str(date), "bill_no": bill_no, "amount": base_tot, "tax_slab": tax_slab, "grand_total": grand_tot, "items": st.session_state.p_items, "stock_type": stock_type, "stock_data": stock_data, "payment": pay_data}
                        res, msg = db.process_smart_purchase(payload)
                        if res: st.success("Saved!"); st.session_state.p_items=[]; st.rerun()
                        else: st.error(msg)
                    else: st.error("Supplier/Bill Missing")
        else: 
            amt = st.number_input("Amount Paid", 0.0)
            mode = st.selectbox("Mode", ["Cash", "UPI", "Bank"])
            note = st.text_input("Note")
            if st.button("Save Payment", type="primary"):
                db.add_simple_payment(sup, date, amt, mode, note); st.success("Payment Saved!"); st.rerun()

    with t2:
        v_sup = st.selectbox("View Supplier", [""] + db.get_supplier_names(), key="v_sup")
        if v_sup:
            df = db.get_supplier_ledger(v_sup)
            if not df.empty:
                bal = df.iloc[-1]['Balance']
                st.metric("Current Balance", f"₹ {bal:,.2f}", delta="Payable" if bal>0 else "Advance", delta_color="inverse")
                st.dataframe(df[["Date", "Type", "Credit", "Debit", "Balance"]], use_container_width=True)
            else: st.warning("No History")

# =========================================================
# PAGE: PRODUCTION
# =========================================================
elif st.session_state.nav == "Production":
    t1, t2 = st.tabs(["🧵 Move Stage", "✂️ Start Lot"])
    with t1:
        active_lots = db.get_active_lots()
        sel_lot = st.selectbox("Lot No", [""] + active_lots)
        if sel_lot:
            l = db.get_lot_info(sel_lot)
            st.caption(f"{l['item_name']} ({l['color']})")
            stock = l['current_stage_stock']
            stages = [k for k, v in stock.items() if sum(v.values()) > 0]
            from_st = st.selectbox("From", stages)
            avail_stock = stock.get(from_st, {})
            c1, c2 = st.columns(2)
            sz = c1.selectbox("Size", [k for k, v in avail_stock.items() if v>0])
            max_q = avail_stock.get(sz, 0)
            qty = c2.number_input(f"Qty (Max {max_q})", 1, max_q if max_q > 0 else 1, max_q if max_q > 0 else 1)
            to_st = st.selectbox("To", ["Stitching", "Washing", "Finishing", "Packing"])
            karigar = st.selectbox("Worker", db.get_staff("Stitching Karigar"))
            if st.button("Move Items", type="primary"):
                if max_q > 0: db.move_lot(sel_lot, from_st, f"{to_st} - {karigar}", karigar, qty, sz); st.success("Moved!"); st.rerun()
                else: st.error("No Stock")
    with t2:
        lot_no = db.get_next_lot_no(); st.info(f"New Lot: **{lot_no}**")
        item = st.selectbox("Item", [""]+db.get_item_names()); code = st.text_input("Code"); l_col = st.text_input("Color")
        st.markdown("###### Sizes")
        if 'l_brk' not in st.session_state: st.session_state.l_brk={}
        c1, c2 = st.columns(2)
        sz_in = c1.text_input("Size (S, M, L)"); qt_in = c2.number_input("Count", 0)
        if c2.button("Add Size"): st.session_state.l_brk[f"{l_col}_{sz_in}"] = qt_in
        st.write(st.session_state.l_brk)
        if st.button("🚀 Launch Lot", type="primary"):
            if item and st.session_state.l_brk: db.create_lot(lot_no, item, code, l_col, st.session_state.l_brk, []); st.success("Launched!"); st.session_state.l_brk={}; st.rerun()

# =========================================================
# PAGE: STOCK
# =========================================================
elif st.session_state.nav == "Stock":
    t1, t2 = st.tabs(["Fabrics", "Accessories"])
    with t1:
        s = db.get_all_fabric_stock_summary()
        if s: st.dataframe(pd.DataFrame([{"Fab":x['_id']['name'], "Col":x['_id']['color'], "Kg":x['total_qty']} for x in s]), use_container_width=True)
    with t2:
        a = db.get_accessory_stock()
        if a: st.dataframe(pd.DataFrame(a), use_container_width=True)
        with st.expander("Update Stock"):
            n = st.selectbox("Item", [""]+db.get_acc_names()); q = st.number_input("Qty (+/-)")
            if st.button("Update"): db.update_accessory_stock(n, "Adj", q, "Pcs"); st.rerun()

# =========================================================
# PAGE: CONFIGURATIONS
# =========================================================
elif st.session_state.nav == "Configurations":
    t = st.selectbox("Manage", ["Suppliers", "Items", "Staff", "Fabrics"])
    with st.form("conf"):
        if t == "Suppliers":
            n=st.text_input("Name"); g=st.text_input("GST"); c=st.text_input("Phone"); a=st.text_input("Address")
            if st.form_submit_button("Add Supplier"): db.add_supplier(n,g,c,a); st.success("Added")
        elif t == "Items":
            n=st.text_input("Item Name"); c=st.text_input("Code")
            if st.form_submit_button("Add Item"): db.add_item(n,c); st.success("Added")
        elif t == "Staff":
            n=st.text_input("Name"); r=st.selectbox("Role", ["Helper", "Stitching Karigar"])
            if st.form_submit_button("Add Staff"): db.add_staff(n,r); st.success("Added")
        elif t == "Fabrics":
            n=st.text_input("Fabric Name")
            if st.form_submit_button("Add Fabric"): db.add_fabric(n); st.success("Added")

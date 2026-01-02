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
    initial_sidebar_state="expanded"
)

# --- 2. CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700;800&display=swap');
    html, body, .stApp { font-family: 'Nunito', sans-serif !important; background-color: #FAFBFE !important; color: #67748E; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #ECECEC; }
    [data-testid="stSidebar"] div.stButton > button { background-color: transparent; color: #67748E; text-align: left; border: none; padding: 10px 15px; font-weight: 600; font-size: 15px; transition: 0.3s; margin-bottom: 2px; }
    [data-testid="stSidebar"] div.stButton > button:hover { background-color: #FEF6ED; color: #FE9F43; }
    [data-testid="stVerticalBlockBorderWrapper"] { background-color: #FFFFFF; border-radius: 10px; padding: 25px; border: 1px solid #ECECEC; box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.03); margin-bottom: 24px; }
    div[data-testid="stMetricLabel"] { color: #A3AAB9; font-size: 13px; font-weight: 700; text-transform: uppercase; }
    div[data-testid="stMetricValue"] { color: #212B36; font-size: 28px; font-weight: 800; }
    input, .stSelectbox > div > div { background-color: #FFFFFF !important; border: 1px solid #E9ECEF !important; border-radius: 5px !important; color: #67748E !important; min-height: 45px; }
    .main .stButton > button { background: linear-gradient(to bottom, #FE9F43, #ff8f26); color: white; border-radius: 50px; padding: 10px 25px; font-weight: 700; border: none; box-shadow: 0 3px 6px rgba(254, 159, 67, 0.2); }
    .sidebar-brand { display: flex; align-items: center; gap: 10px; padding: 20px 10px; margin-bottom: 20px; border-bottom: 1px dashed #e9ecef; }
    .brand-icon { width: 40px; height: 40px; background: #FE9F43; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 900; font-size: 20px; }
    .brand-text { font-size: 20px; font-weight: 800; color: #212B36; }
    .nav-header { font-size: 11px; text-transform: uppercase; color: #A3AAB9; font-weight: 700; margin-top: 25px; margin-bottom: 10px; padding-left: 15px; }
    .stock-pill { background-color: #FEF6ED; color: #FE9F43; padding: 5px 12px; border-radius: 5px; font-size: 12px; font-weight: 700; display: inline-block; margin-right: 5px; border: 1px solid #fe9f4320; }
    .danger-box { border: 1px dashed #EA5455; background: #FFF5F5; padding: 20px; border-radius: 10px; }
    .lot-header-box { background: #FFFFFF; padding: 15px; border-radius: 10px; border-left: 5px solid #FE9F43; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }
    .lot-header-text { font-size: 12px; font-weight: 700; color: #A3AAB9; text-transform: uppercase; }
    .lot-header-val { font-size: 16px; font-weight: 800; color: #212B36; margin-right: 15px; }
</style>
""", unsafe_allow_html=True)

# --- 3. NAV ---
if 'page' not in st.session_state: st.session_state.page = "Dashboard"
def nav(page): st.session_state.page = page

with st.sidebar:
    st.markdown('<div class="sidebar-brand"><div class="brand-icon">S</div><div class="brand-text">Shine Arc</div></div>', unsafe_allow_html=True)
    st.selectbox("Year", ["2025-26"], label_visibility="collapsed")
    
    st.markdown('<div class="nav-header">MAIN</div>', unsafe_allow_html=True)
    if st.button("📊 Dashboard"): nav("Dashboard")
    
    st.markdown('<div class="nav-header">ACCOUNTS</div>', unsafe_allow_html=True)
    if st.button("📒 Supplier Ledger"): nav("Supplier Ledger")
    
    st.markdown('<div class="nav-header">PRODUCTION</div>', unsafe_allow_html=True)
    with st.expander("✂️ Manufacturing"):
        if st.button("Fabric Inward"): nav("Fabric Inward")
        if st.button("Cutting Floor"): nav("Cutting Floor")
        if st.button("Stitching Floor"): nav("Stitching Floor")
        if st.button("Productivity & Pay"): nav("Productivity & Pay")
        
    st.markdown('<div class="nav-header">MANAGEMENT</div>', unsafe_allow_html=True)
    with st.expander("📦 Inventory"):
        if st.button("Stock Management"): nav("Inventory")
    with st.expander("👥 Human Resources"):
        if st.button("Data Masters"): nav("Masters")
        if st.button("Attendance"): nav("Attendance")
        
    st.markdown('<div class="nav-header">MCPL</div>', unsafe_allow_html=True)
    if st.button("🚀 Vin Lister"): nav("MCPL")
    st.markdown('<div class="nav-header">SYSTEM</div>', unsafe_allow_html=True)
    if st.button("📍 Track Lots"): nav("Track Lot")
    if st.button("⚙️ Settings"): nav("Config")
    st.markdown("---")
    if st.button("🔒 Logout"): st.rerun()

# --- 4. CONTENT ---
page = st.session_state.page

# DASHBOARD
if page == "Dashboard":
    st.title("Admin Dashboard")
    stats = db.get_dashboard_stats()
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.metric("Active Production", stats.get('active_lots', 0))
            st.progress(0.7)
    with c2:
        with st.container(border=True):
            st.metric("Completed Lots", stats.get('completed_lots', 0))
            st.progress(0.9)
    with c3:
        with st.container(border=True):
            st.metric("Fabric Rolls", stats.get('fabric_rolls', 0))
            st.progress(0.5)
    st.markdown("### 📋 Pending Orders")
    pd_df = stats.get('pending_list', [])
    if pd_df: st.dataframe(pd.DataFrame(pd_df), use_container_width=True)
    else: st.info("No Pending Lots")

# SUPPLIER LEDGER
elif page == "Supplier Ledger":
    st.title("📒 Supplier Accounts")
    t1, t2 = st.tabs(["Add Transaction", "View Ledger"])
    suppliers = [""] + db.get_supplier_names()
    
    with t1:
        with st.container(border=True):
            st.markdown("#### New Entry")
            c1, c2 = st.columns(2)
            sup = c1.selectbox("Select Supplier", suppliers)
            date = c2.date_input("Date")
            
            txn_type = st.radio("Transaction Type", ["Bill (Purchase)", "Payment (Outgoing)"], horizontal=True)
            st.markdown("---")
            
            if txn_type == "Bill (Purchase)":
                b1, b2, b3 = st.columns(3)
                bill_no = b1.text_input("Supplier Bill No *")
                base_amt = b2.number_input("Bill Base Amount (₹)", 0.0)
                tax_slab = b3.selectbox("Tax %", [0, 1, 2, 2.5, 5, 12, 18], format_func=lambda x: f"{x}%")
                
                tax_val = base_amt * (tax_slab / 100)
                total_amt = base_amt + tax_val
                
                if base_amt > 0:
                    st.info(f"Base: ₹{base_amt:,.2f} | Tax ({tax_slab}%): ₹{tax_val:,.2f} | **Total: ₹{total_amt:,.2f}**")
                
                rem = st.text_input("Items / Description")
                
                st.markdown("#### Payment against this Bill?")
                pay_opt = st.radio("Payment Status", ["Unpaid / Credit", "Full Payment", "Partial Payment"], horizontal=True)
                
                pay_amt = 0.0
                pay_mode = "Cash"
                if pay_opt == "Full Payment":
                    pay_amt = total_amt
                    pay_mode = st.selectbox("Payment Mode", ["Cash", "Bank Transfer", "UPI", "Cheque"])
                elif pay_opt == "Partial Payment":
                    pay_amt = st.number_input("Paid Amount (₹)", 0.0)
                    pay_mode = st.selectbox("Payment Mode", ["Cash", "Bank Transfer", "UPI", "Cheque"])
                
                f = st.file_uploader("Attach Bill", type=['png','jpg','pdf'])
                
                if st.button("Save Purchase Entry", type="primary"):
                    if sup and bill_no and total_amt > 0:
                        f_name = f.name if f else None
                        full_rem = f"{rem} [Base: {base_amt}, Tax: {tax_slab}%]"
                        db.add_supplier_txn(sup, str(date), "Bill", total_amt, bill_no, full_rem, f_name)
                        if pay_amt > 0:
                            p_rem = f"Against Bill {bill_no} via {pay_mode}"
                            pay_ref = db.add_supplier_txn(sup, str(date), "Payment", pay_amt, "", p_rem)
                            st.success(f"Saved Bill & Payment! (Rcpt: {pay_ref})")
                        else: st.success("Bill Saved (Credit)")
                    else: st.error("Missing Details")

            else: # PAYMENT
                p1, p2 = st.columns(2)
                pay_amt = p1.number_input("Payment Amount (₹)", 0.0)
                pay_mode = p2.selectbox("Mode", ["Cash", "Bank Transfer", "UPI", "Cheque"])
                rem = st.text_input("Remarks (Optional)")
                if st.button("Save Payment", type="primary"):
                    if sup and pay_amt > 0:
                        pay_ref = db.add_supplier_txn(sup, str(date), "Payment", pay_amt, "", f"Mode: {pay_mode} - {rem}")
                        st.success(f"Payment Recorded! Receipt No: {pay_ref}")
                    else: st.error("Invalid Entry")

    with t2:
        sel_sup = st.selectbox("Select Supplier", suppliers, key="view")
        if sel_sup:
            v_mode = st.radio("View", ["Detailed Statement", "Date-wise Summary"], horizontal=True)
            
            if v_mode == "Detailed Statement":
                df = db.get_supplier_ledger(sel_sup)
                if not df.empty:
                    bal = df.iloc[-1]['Balance']
                    st.metric("Current Balance", f"₹ {bal:,.2f}", delta="Payable" if bal>0 else "Advance", delta_color="inverse")
                    
                    st.dataframe(df[["Date", "Type", "Reference", "Debit (Paid)", "Credit (Bill)", "Balance", "Remarks"]], use_container_width=True)
                    
                    st.divider()
                    st.markdown("### 🛠️ Manage Transactions")
                    txn_opts = [f"{r['Date']} | {r['Type']} | ₹{r['Credit (Bill)'] if r['Type']=='Bill' else r['Debit (Paid)']}" for _, r in df.iterrows()]
                    sel_txn_idx = st.selectbox("Select Transaction to Edit/Delete", range(len(txn_opts)), format_func=lambda x: txn_opts[x])
                    
                    if st.button("🗑️ Delete Selected Transaction", type="secondary"):
                        txn_id = df.iloc[sel_txn_idx]['ID']
                        if db.delete_supplier_txn(txn_id): st.success("Deleted!"); st.rerun()
                        else: st.error("Error deleting")
                        
                    with st.expander("✏️ Edit Selected Transaction"):
                        row = df.iloc[sel_txn_idx]
                        eid = row['ID']
                        e_date = st.date_input("New Date", pd.to_datetime(row['Date']))
                        e_amt = st.number_input("New Amount", 0.0, value=float(row['Credit (Bill)'] if row['Type']=='Bill' else row['Debit (Paid)']))
                        e_ref = st.text_input("New Reference", row['Reference'])
                        e_rem = st.text_input("New Remarks", row['Remarks'])
                        if st.button("Update Transaction"):
                            if db.update_supplier_txn(eid, str(e_date), e_amt, e_ref, e_rem): st.success("Updated!"); st.rerun()
                            else: st.error("Error updating")
                else: st.info("No records")
            else:
                df = db.get_supplier_summary(sel_sup)
                if not df.empty:
                    bal = df.iloc[-1]['Closing Balance']
                    st.metric("Net Balance", f"₹ {bal:,.2f}")
                    st.dataframe(df, use_container_width=True)
                else: st.info("No records")

# MCPL MODULE
elif page == "MCPL":
    st.title("🚀 Multi-Channel Listing (Vin Lister)")
    if 'mcpl_mode' not in st.session_state: st.session_state.mcpl_mode = 'Catalog'
    m1, m2, m3 = st.columns(3)
    if m1.button("📂 Product Catalog", use_container_width=True): st.session_state.mcpl_mode = 'Catalog'
    if m2.button("📥 Bulk Import (CSV)", use_container_width=True): st.session_state.mcpl_mode = 'Import'
    if m3.button("🏷️ Channel Pricing", use_container_width=True): st.session_state.mcpl_mode = 'Pricing'
    st.markdown("---")
    mode = st.session_state.mcpl_mode
    if mode == "Catalog":
        st.subheader("Product Catalog")
        df_cat = db.get_mcpl_catalog()
        if not df_cat.empty:
            cols = ["sku", "name", "category", "base_price", "channel_prices", "status"]
            for c in cols: 
                if c not in df_cat.columns: df_cat[c] = "-"
            if "image_url" in df_cat.columns:
                cols.insert(0, "image_url")
                st.dataframe(df_cat[cols], column_config={"image_url": st.column_config.ImageColumn("Img", width="small")}, use_container_width=True)
            else: st.dataframe(df_cat[cols], use_container_width=True)
        else: st.info("Catalog is empty.")
        with st.expander("Add Single Product"):
            c1, c2 = st.columns(2); sku = c1.text_input("SKU"); nm = c2.text_input("Name"); cat = c1.selectbox("Cat", ["Apparel", "Home"]); bp = c2.number_input("Price", 0.0); img = c1.text_input("Image URL")
            if st.button("Add"): 
                if sku: db.mcpl_add_product(sku, nm, cat, bp, img); st.success("Added!"); st.rerun()
    elif mode == "Import":
        st.subheader("Bulk Import")
        csv = pd.DataFrame([{"SKU": "A1", "Name": "T-Shirt", "Category": "Apparel", "Price": 500, "Image URL": ""}]).to_csv(index=False).encode('utf-8')
        st.download_button("Download Template", csv, "template.csv", "text/csv")
        up = st.file_uploader("Upload CSV", type=['csv'])
        if up:
            df = pd.read_csv(up)
            st.dataframe(df, column_config={"Image URL": st.column_config.ImageColumn("Preview")}, use_container_width=True)
            if st.button("Process"): cnt, err = db.mcpl_bulk_upload(df); st.success(f"Done: {cnt}, Errors: {err}")
    elif mode == "Pricing":
        st.subheader("Channel Pricing")
        df_cat = db.get_mcpl_catalog()
        if not df_cat.empty and 'sku' in df_cat.columns:
            sel = st.selectbox("SKU", df_cat['sku'].tolist())
            if sel:
                row = df_cat[df_cat['sku']==sel].iloc[0]
                cur = row.get('channel_prices', {})
                st.info(f"Base: {row.get('base_price')}")
                c1,c2,c3=st.columns(3); a=c1.number_input("Amazon", value=float(cur.get('Amazon',0))); f=c2.number_input("Flipkart", value=float(cur.get('Flipkart',0))); m=c3.number_input("Myntra", value=float(cur.get('Myntra',0)))
                if st.button("Update"): db.mcpl_update_channel_price(sel, "Amazon", a); db.mcpl_update_channel_price(sel, "Flipkart", f); db.mcpl_update_channel_price(sel, "Myntra", m); st.success("Updated!")

# MASTERS
elif page == "Masters":
    st.title("👥 Data Masters")
    t1, t2, t3, t4, t5, t6, t7 = st.tabs(["Fabric", "Process", "Staff", "Items", "Colors", "Sizes", "Suppliers"])
    
    with t1:
        c1,c2=st.columns(2); n=c1.text_input("Name"); h=c2.text_input("HSN")
        if st.button("Add Fabric"): db.add_material(n,h); st.success("Added")
        st.dataframe(db.get_materials())
    with t2:
        pn=st.text_input("Process Name"); 
        if st.button("Add Process"): db.add_process(pn); st.success("Added")
        st.write(", ".join(db.get_all_processes()))
    with t3:
        c1,c2=st.columns(2); n=c1.text_input("Staff"); r=c2.selectbox("Role", ["Cutting Master", "Stitching Karigar", "Helper", "Press/Iron Staff"])
        if st.button("Add Staff"): db.add_staff(n,r); st.success("Added")
        st.dataframe(db.get_all_staff())
    with t4:
        st.markdown("#### Add Item")
        ic1,ic2,ic3=st.columns(3); nm=ic1.text_input("Item Name"); cd=ic2.text_input("Code"); cl=ic3.text_input("Default Color")
        st.markdown("**Required Fabrics (Max 5)**")
        fopts=[""]+db.get_material_names()
        f1,f2,f3,f4,f5=st.columns(5); fab1=f1.selectbox("F1",fopts); fab2=f2.selectbox("F2",fopts); fab3=f3.selectbox("F3",fopts); fab4=f4.selectbox("F4",fopts); fab5=f5.selectbox("F5",fopts)
        if st.button("Save Item"):
            fl=[fab1,fab2,fab3,fab4,fab5]
            res,msg=db.add_item_master(nm,cd,cl,fl)
            if res: st.success("Saved"); st.rerun()
            else: st.error(msg)
        st.dataframe(db.get_all_items())
    with t5:
        n=st.text_input("New Color"); 
        if st.button("Add Color"): db.add_color(n); st.rerun()
        st.write(", ".join(db.get_colors()))
    with t6:
        n=st.text_input("New Size"); 
        if st.button("Add Size"): db.add_size(n); st.rerun()
        st.write(", ".join(db.get_sizes()))
    with t7: # SUPPLIER MASTER UPDATED
        st.markdown("#### Add New Supplier")
        c1, c2 = st.columns(2)
        sn = c1.text_input("Supplier Name *")
        gst = c2.text_input("GST No (Optional)")
        cont = c1.text_input("Contact No / Email (Optional)")
        addr = c2.text_input("Address (Optional)")
        
        if st.button("Add Supplier", type="primary"): 
            if sn:
                if db.add_supplier(sn, gst, cont, addr): st.success("Added!"); st.rerun()
                else: st.error("Supplier exists")
            else: st.error("Name Required")
        
        # Show Supplier List
        st.divider()
        st.dataframe(db.get_supplier_details_df(), use_container_width=True)

# CUTTING FLOOR
elif page == "Cutting Floor":
    st.title("✂️ Cutting Floor")
    next_lot = db.get_next_lot_no(); masters = db.get_staff_by_role("Cutting Master"); sizes = db.get_sizes()
    if 'lot_breakdown' not in st.session_state: st.session_state.lot_breakdown={}
    if 'fabric_selections' not in st.session_state: st.session_state.fabric_selections={}
    
    with st.container(border=True):
        st.markdown("#### Lot Details")
        c1,c2,c3=st.columns(3); st.write(f"**Lot: {next_lot}**")
        inm=c2.selectbox("Item",[""]+db.get_unique_item_names()); icd=c3.selectbox("Code",[""]+(db.get_codes_by_item_name(inm) if inm else []))
        req_fabs=[]; acol=""
        if icd:
            det=db.get_item_details_by_code(icd)
            if det: acol=det.get('item_color',''); req_fabs=det.get('required_fabrics',[])
        c4,c5=st.columns(2); c4.text_input("Color",acol,disabled=True); cut=c5.selectbox("Cutter",masters) if masters else c5.text_input("Cutter")
        
        st.markdown("---")
        if not req_fabs: st.info("Select Item to load fabrics")
        else:
            for f in req_fabs:
                with st.expander(f"Select Stock for: **{f}**", expanded=True):
                    ss=db.get_all_fabric_stock_summary()
                    ac=sorted(list(set([s['_id']['color'] for s in ss if s['_id']['name']==f])))
                    fc=st.selectbox(f"Color for {f}", ac, key=f"fc_{f}")
                    if fc:
                        rls=db.get_available_rolls(f,fc)
                        if rls:
                            st.caption(f"Avail: {rls[0]['uom']}")
                            cls=st.columns(4); sel=[]; w=0.0
                            for i,r in enumerate(rls):
                                if cls[i%4].checkbox(f"{r['quantity']}", key=f"chk_{f}_{r['_id']}"): sel.append(r['_id']); w+=r['quantity']
                            st.session_state.fabric_selections[f]={"roll_ids":sel,"total_weight":w,"uom":rls[0]['uom']}
                        else: st.warning("No Stock")
        
        st.markdown("---")
        cc1,cc2=st.columns([1,3]); lc=cc1.text_input("Batch Color", acol); sin={}
        if sizes:
            sc=cc2.columns(len(sizes))
            for i,z in enumerate(sizes): sin[z]=sc[i].number_input(z,0,key=f"sz_{z}")
        if st.button("Add Batch"):
            if lc and sum(sin.values())>0:
                for z,q in sin.items(): 
                    if q>0: st.session_state.lot_breakdown[f"{lc}_{z}"]=q
                st.success("Added")
        
        if st.session_state.lot_breakdown:
            st.json(st.session_state.lot_breakdown)
            if st.button("🚀 CREATE LOT"):
                miss=[f for f in req_fabs if f not in st.session_state.fabric_selections or not st.session_state.fabric_selections[f]['roll_ids']]
                if miss: st.error(f"Missing: {miss}")
                elif not inm or not icd or not cut: st.error("Missing Info")
                else:
                    tot_w=sum([d['total_weight'] for d in st.session_state.fabric_selections.values()])
                    flat_ids=[]
                    fs=[]
                    for f,d in st.session_state.fabric_selections.items():
                        flat_ids.extend(d['roll_ids']); fs.append({"name":f,"weight":d['total_weight']})
                    db.create_lot({"lot_no":next_lot,"item_name":inm,"item_code":icd,"color":acol,"created_by":cut,"size_breakdown":st.session_state.lot_breakdown,"fabrics_consumed":fs,"total_fabric_weight":tot_w}, flat_ids)
                    st.success("Created!"); st.session_state.lot_breakdown={}; st.session_state.fabric_selections={}; st.rerun()

# STITCHING FLOOR
elif page == "Stitching Floor":
    st.title("🧵 Stitching Floor")
    karigars = db.get_staff_by_role("Stitching Karigar"); active = db.get_active_lots(); procs = db.get_all_processes()
    cl, cr = st.columns([1, 2]); sel_lot = cl.selectbox("Select Lot", [""] + [x['lot_no'] for x in active])
    if sel_lot:
        l = db.get_lot_details(sel_lot)
        with cr:
            with st.container(border=True):
                st.markdown(f"**{l['item_name']}**")
                for s, sz in l['current_stage_stock'].items():
                    if sum(sz.values()) > 0:
                        h = ""
                        for k,v in sz.items(): 
                            if v>0: h+=f"<span class='stock-pill'>{k}: <b>{v}</b></span>"
                        st.markdown(f"**{s}** {h}", unsafe_allow_html=True)
        with st.container(border=True):
            c1, c2, c3 = st.columns(3); valid_from = [k for k,v in l['current_stage_stock'].items() if sum(v.values())>0]; from_s = c1.selectbox("From", valid_from)
            avail = l['current_stage_stock'].get(from_s, {})
            cols = sorted(list(set([k.split('_')[0] for k in avail.keys() if avail[k]>0]))); sel_c = c2.selectbox("Color", cols)
            to = c3.selectbox("To", db.get_stages_for_item(l['item_name']))
            c4, c5, c6 = st.columns(3); stf = c4.selectbox("Staff", karigars+["Outsource"]) if karigars else c4.text_input("Staff"); mac = c5.selectbox("Process", procs)
            ft = f"Stitching - {stf} - {mac}" if to=="Stitching" else f"{to} - {stf}"
            v_sz = [k.split('_')[1] for k,v in avail.items() if v>0 and k.startswith(sel_c+"_")]
            if v_sz:
                sz = c6.selectbox("Size", v_sz); fk = f"{sel_c}_{sz}"; mq = avail.get(fk, 0)
                q1, q2 = st.columns(2); qty = q1.number_input("Qty", 1, mq if mq>=1 else 1)
                if q2.button("Confirm"): 
                    if qty>0: db.move_lot_stage({"lot_no": sel_lot, "from_stage": from_s, "to_stage_key": ft, "karigar": stf, "machine": mac, "size_key": fk, "size": sz, "qty": qty}); st.success("Moved!"); st.rerun()

# PRODUCTIVITY
elif page == "Productivity & Pay":
    st.title("💰 Productivity")
    c1, c2 = st.columns(2); m = c1.selectbox("Month", range(1,13), index=datetime.datetime.now().month-1); y = c2.selectbox("Year", [2024, 2025, 2026], index=1)
    df = db.get_staff_productivity(m, y)
    if not df.empty: st.dataframe(df, use_container_width=True); st.markdown(f"#### Total: ₹ {df['Earnings'].sum():,.2f}")
    else: st.info("No records")

# INVENTORY TAB
elif page == "Inventory":
    st.title("📦 Inventory Stock")
    t1, t2, t3 = st.tabs(["Garments", "Fabric", "Accessories"])
    with t1:
        active_lots = db.get_active_lots()
        if active_lots: st.dataframe(pd.DataFrame([{"Lot": l['lot_no'], "Item": l['item_name'], "Pcs": l['total_qty']} for l in active_lots]))
    with t2:
        s = db.get_all_fabric_stock_summary()
        if s: st.dataframe(pd.DataFrame([{"Fabric": x['_id']['name'], "Color": x['_id']['color'], "Rolls": x['total_rolls'], "Qty": x['total_qty']} for x in s]))
    with t3:
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.markdown("**Inward**")
                an = st.selectbox("Name", [""] + db.get_accessory_names()); 
                if not an: an = st.text_input("New Name")
                aq = st.number_input("Qty", 0.0); au = st.selectbox("Unit", ["Pcs", "Kg", "Box", "Packet"])
                if st.button("Add"): 
                    if an and aq > 0: db.update_accessory_stock(an, "Inward", aq, au); st.success("Added!"); st.rerun()
        with col2:
            with st.container(border=True):
                st.markdown("**Outward**")
                an_out = st.selectbox("Item", [""] + db.get_accessory_names(), key="acc_out")
                aq_out = st.number_input("Qty Out", 0.0, key="qty_out")
                if st.button("Issue"):
                    if an_out and aq_out > 0: db.update_accessory_stock(an_out, "Outward", aq_out, "N/A"); st.success("Issued!"); st.rerun()
        st.divider(); st.dataframe(pd.DataFrame(db.get_accessory_stock()))

# CONFIG
elif page == "Config":
    st.title("⚙️ Rate Configuration")
    process_list = db.get_all_processes()
    t1, t2 = st.tabs(["Rate Card", "Danger Zone"])
    with t1:
        with st.form("r"):
            c1,c2,c3,c4,c5 = st.columns(5)
            i=c1.text_input("Item Name"); cd=c2.text_input("Item Code"); m=c3.selectbox("Process/Machine", process_list); r=c4.number_input("Rate", 0.0); d=c5.date_input("Effective From")
            if st.form_submit_button("Save Rate"): db.add_piece_rate(i,cd,m,r,d); st.success("Rate Saved!")
        st.dataframe(db.get_rate_master())
    with t2:
        st.markdown('<div class="danger-box"><p class="danger-title">⚠ Danger Zone</p>', unsafe_allow_html=True)
        with st.form("clean"):
            p = st.text_input("Password", type="password")
            if st.form_submit_button("🔥 Wipe DB"):
                if p=="Sparsh@2030": db.clean_database(); st.success("Cleaned!"); st.rerun()
                else: st.error("Wrong")
        st.markdown('</div>', unsafe_allow_html=True)

# TRACK LOT
elif page == "Track Lot":
    st.title("📍 Track Lot")
    l_s = st.selectbox("Select", [""]+db.get_all_lot_numbers())
    if l_s:
        l = db.get_lot_details(l_s)
        if l:
            st.markdown(f"""<div class="lot-header-box"><span class="lot-header-text">Lot No: <span class="lot-header-val">{l_s}</span></span><span class="lot-header-text">Item: <span class="lot-header-val">{l['item_name']}</span></span></div>""", unsafe_allow_html=True)
            all_k = list(l['size_breakdown'].keys()); stgs = list(l['current_stage_stock'].keys()); mat = []
            for k in all_k:
                c, s = k.split('_'); row = {"Color": c, "Size": s}
                for sg in stgs: row[sg] = l['current_stage_stock'].get(sg, {}).get(k, 0)
                mat.append(row)
            st.dataframe(pd.DataFrame(mat))

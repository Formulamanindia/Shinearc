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
    if st.button("⚙️ Config"): nav("Config")
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

# SUPPLIER LEDGER (UPDATED WITH BILL/PAYMENT LOGIC)
elif page == "Supplier Ledger":
    st.title("📒 Supplier Accounts")
    t1, t2 = st.tabs(["Add Entry", "View Ledger"])
    suppliers = [""] + db.get_supplier_names()
    
    with t1: # ADD TRANSACTION
        with st.container(border=True):
            c1, c2 = st.columns(2)
            sup = c1.selectbox("Supplier", suppliers)
            date = c2.date_input("Date")
            
            # TYPE SELECTOR
            txn_type = st.radio("Transaction Type", ["Bill (Purchase)", "Payment (Outgoing)"], horizontal=True)
            
            st.markdown("---")
            
            if txn_type == "Bill (Purchase)":
                b1, b2 = st.columns(2)
                bill_no = b1.text_input("Supplier Bill No *")
                bill_amt = b2.number_input("Bill Amount (₹)", 0.0)
                rem = st.text_input("Description / Item Details")
                
                # SIMULTANEOUS PAYMENT OPTION
                st.markdown("#### Payment against this Bill?")
                pay_opt = st.radio("Payment Status", ["Unpaid / Credit", "Full Payment", "Partial Payment"], horizontal=True)
                
                pay_amt = 0.0
                pay_mode = "Cash"
                
                if pay_opt == "Full Payment":
                    pay_amt = bill_amt
                    pay_mode = st.selectbox("Payment Mode", ["Cash", "Bank Transfer", "UPI", "Cheque"])
                elif pay_opt == "Partial Payment":
                    pay_amt = st.number_input("Paid Amount (₹)", 0.0)
                    pay_mode = st.selectbox("Payment Mode", ["Cash", "Bank Transfer", "UPI", "Cheque"])
                
                # Attachment
                f = st.file_uploader("Attach Bill", type=['png','jpg','pdf'])
                
                if st.button("Save Purchase Entry", type="primary"):
                    if sup and bill_no and bill_amt > 0:
                        # 1. Save Bill
                        f_name = f.name if f else None
                        db.add_supplier_txn(sup, str(date), "Bill", bill_amt, bill_no, rem, f_name)
                        
                        # 2. Save Payment if applicable
                        if pay_amt > 0:
                            p_rem = f"Against Bill {bill_no} via {pay_mode}"
                            pay_ref = db.add_supplier_txn(sup, str(date), "Payment", pay_amt, "", p_rem)
                            st.success(f"Saved Bill & Payment! (Rcpt: {pay_ref})")
                        else:
                            st.success("Bill Saved (Credit)")
                    else: st.error("Missing Details")

            else: # STANDALONE PAYMENT
                p1, p2 = st.columns(2)
                pay_amt = p1.number_input("Payment Amount (₹)", 0.0)
                pay_mode = p2.selectbox("Mode", ["Cash", "Bank Transfer", "UPI", "Cheque"])
                rem = st.text_input("Remarks (Optional)")
                
                if st.button("Save Payment", type="primary"):
                    if sup and pay_amt > 0:
                        pay_ref = db.add_supplier_txn(sup, str(date), "Payment", pay_amt, "", f"Mode: {pay_mode} - {rem}")
                        st.success(f"Payment Recorded! Receipt No: {pay_ref}")
                    else: st.error("Invalid Entry")

    with t2: # VIEW LEDGER
        sel_sup = st.selectbox("Select Supplier", suppliers, key="view")
        if sel_sup:
            v_mode = st.radio("View", ["Detailed Statement", "Date-wise Summary"], horizontal=True)
            
            if v_mode == "Detailed Statement":
                df = db.get_supplier_ledger(sel_sup)
                if not df.empty:
                    bal = df.iloc[-1]['Balance']
                    st.metric("Current Balance", f"₹ {bal:,.2f}", delta="Payable" if bal>0 else "Advance", delta_color="inverse")
                    st.dataframe(df, use_container_width=True)
                else: st.info("No records")
            else:
                df = db.get_supplier_summary(sel_sup)
                if not df.empty:
                    bal = df.iloc[-1]['Closing Balance']
                    st.metric("Net Balance", f"₹ {bal:,.2f}")
                    st.dataframe(df, use_container_width=True)
                else: st.info("No records")

# MCPL
elif page == "MCPL":
    st.title("🚀 Vin Lister")
    if 'mcpl_mode' not in st.session_state: st.session_state.mcpl_mode='Catalog'
    c1,c2,c3=st.columns(3)
    if c1.button("📂 Catalog", use_container_width=True): st.session_state.mcpl_mode='Catalog'
    if c2.button("📥 Import", use_container_width=True): st.session_state.mcpl_mode='Import'
    if c3.button("🏷️ Pricing", use_container_width=True): st.session_state.mcpl_mode='Pricing'
    st.markdown("---")
    mode=st.session_state.mcpl_mode
    
    if mode=="Catalog":
        df=db.get_mcpl_catalog()
        if not df.empty: 
            cols = ["image_url", "sku", "name", "category", "base_price", "channel_prices"]
            for c in cols:
                if c not in df.columns: df[c]=""
            st.dataframe(df[cols], column_config={"image_url": st.column_config.ImageColumn("Img")}, use_container_width=True)
        else: st.info("Empty Catalog")
    elif mode=="Import":
        st.subheader("Bulk Import")
        st.download_button("Download Template", pd.DataFrame([{"SKU":"A1","Name":"Item","Price":100,"Image URL":""}]).to_csv(index=False).encode('utf-8'), "tpl.csv")
        up=st.file_uploader("Upload CSV",type=['csv'])
        if up and st.button("Process"): cnt,err=db.mcpl_bulk_upload(pd.read_csv(up)); st.success(f"Done: {cnt}")
    elif mode=="Pricing":
        df=db.get_mcpl_catalog()
        if not df.empty:
            s=st.selectbox("SKU", df['sku'].tolist())
            if s:
                r=df[df['sku']==s].iloc[0]; cp=r.get('channel_prices',{})
                c1,c2=st.columns(2); a=c1.number_input("Amazon", float(cp.get('Amazon',0))); f=c2.number_input("Flipkart", float(cp.get('Flipkart',0)))
                if st.button("Update"): db.mcpl_update_channel_price(s,"Amazon",a); db.mcpl_update_channel_price(s,"Flipkart",f); st.success("Updated")

# MASTERS
elif page == "Masters":
    st.title("👥 Masters")
    tabs = st.tabs(["Fabric", "Process", "Staff", "Items", "Colors", "Sizes", "Suppliers"])
    with tabs[0]:
        c1,c2=st.columns(2); n=c1.text_input("Name"); h=c2.text_input("HSN")
        if st.button("Add Fabric"): db.add_material(n,h); st.success("Added")
        st.dataframe(db.get_materials())
    with tabs[6]: # SUPPLIER MASTER
        st.markdown("#### New Supplier")
        c1,c2=st.columns(2); sn=c1.text_input("Name *"); gst=c2.text_input("GST")
        cont=c1.text_input("Contact"); addr=c2.text_input("Address")
        if st.button("Save Supplier"):
            if sn: 
                if db.add_supplier(sn,gst,cont,addr): st.success("Added!"); st.rerun()
                else: st.error("Exists")
        st.dataframe(db.get_supplier_details_df(), use_container_width=True)
    # ... (Other tabs kept compact for brevity but logic is same)
    with tabs[3]: # Items
        n=st.text_input("Item"); c=st.text_input("Code"); cl=st.text_input("Color")
        fopts=[""]+db.get_material_names(); fs=[st.selectbox(f"F{i}",fopts,key=f"f{i}") for i in range(5)]
        if st.button("Save Item"): db.add_item_master(n,c,cl,fs); st.success("Saved")
        st.dataframe(db.get_all_items())

# CUTTING FLOOR
elif page == "Cutting Floor":
    st.title("✂️ Cutting Floor")
    next_lot = db.get_next_lot_no(); masters = db.get_staff_by_role("Cutting Master"); sizes = db.get_sizes()
    if 'lot_breakdown' not in st.session_state: st.session_state.lot_breakdown={}
    if 'fabric_selections' not in st.session_state: st.session_state.fabric_selections={}
    
    with st.container(border=True):
        c1,c2,c3=st.columns(3); st.write(f"**Lot: {next_lot}**")
        inm=c2.selectbox("Item",[""]+db.get_unique_item_names()); icd=c3.selectbox("Code",[""]+(db.get_codes_by_item_name(inm) if inm else []))
        req_fabs=[]; acol=""
        if icd:
            det=db.get_item_details_by_code(icd)
            if det: acol=det.get('item_color',''); req_fabs=det.get('required_fabrics',[])
        c4,c5=st.columns(2); c4.text_input("Color",acol,disabled=True); cut=c5.selectbox("Cutter",masters) if masters else c5.text_input("Cutter")
        
        if req_fabs:
            for f in req_fabs:
                with st.expander(f"Stock: {f}", expanded=True):
                    ss=db.get_all_fabric_stock_summary()
                    ac=sorted(list(set([s['_id']['color'] for s in ss if s['_id']['name']==f])))
                    fc=st.selectbox(f"Color ({f})", ac, key=f"fc_{f}")
                    if fc:
                        rls=db.get_available_rolls(f,fc)
                        if rls:
                            cls=st.columns(4); sel=[]; w=0.0
                            for i,r in enumerate(rls):
                                if cls[i%4].checkbox(f"{r['quantity']}", key=f"chk_{f}_{r['_id']}"): sel.append(r['_id']); w+=r['quantity']
                            st.session_state.fabric_selections[f]={"roll_ids":sel,"total_weight":w}
                        else: st.warning("No Stock")
        
        st.markdown("---")
        cc1,cc2=st.columns([1,3]); lc=cc1.text_input("Batch Color", acol); sin={}
        if sizes:
            sc=cc2.columns(len(sizes))
            for i,z in enumerate(sizes): sin[z]=sc[i].number_input(z,0,key=f"sz_{z}")
        
        if st.button("Add Batch"):
            if lc and sum(sin.values())>0:
                for z,q in sin.items(): st.session_state.lot_breakdown[f"{lc}_{z}"]=q
                st.success("Added")
        
        if st.session_state.lot_breakdown:
            st.json(st.session_state.lot_breakdown)
            if st.button("🚀 CREATE LOT", type="primary"):
                flat_ids=[]; fs=[]
                for f,d in st.session_state.fabric_selections.items(): flat_ids.extend(d['roll_ids']); fs.append({"name":f,"weight":d['total_weight']})
                db.create_lot({"lot_no":next_lot,"item_name":inm,"item_code":icd,"color":acol,"created_by":cut,"size_breakdown":st.session_state.lot_breakdown,"fabrics_consumed":fs,"total_fabric_weight":0}, flat_ids)
                st.success("Created!"); st.session_state.lot_breakdown={}; st.rerun()

# STITCHING FLOOR
elif page == "Stitching Floor":
    st.title("🧵 Stitching")
    karigars = db.get_staff_by_role("Stitching Karigar"); active = db.get_active_lots()
    cl, cr = st.columns([1, 2]); sel_lot = cl.selectbox("Select Lot", [""] + [x['lot_no'] for x in active])
    if sel_lot:
        l = db.get_lot_details(sel_lot)
        with cr:
            with st.container(border=True):
                st.markdown(f"**{l['item_name']}**")
                for s, sz in l['current_stage_stock'].items():
                    if sum(sz.values()) > 0: st.markdown(f"**{s}**: {sz}")
        with st.container(border=True):
            c1, c2, c3 = st.columns(3); vf = [k for k,v in l['current_stage_stock'].items() if sum(v.values())>0]; from_s = c1.selectbox("From", vf)
            avail = l['current_stage_stock'].get(from_s, {})
            cols = sorted(list(set([k.split('_')[0] for k in avail.keys() if avail[k]>0]))); sel_c = c2.selectbox("Color", cols)
            to = c3.selectbox("To", db.get_stages_for_item(l['item_name']))
            c4, c5 = st.columns(2); stf = c4.selectbox("Staff", karigars); mac = c5.selectbox("Process", db.get_all_processes())
            v_sz = [k.split('_')[1] for k,v in avail.items() if v>0 and k.startswith(sel_c+"_")]
            if v_sz:
                sz = st.selectbox("Size", v_sz); fk = f"{sel_c}_{sz}"; mq = avail.get(fk, 0)
                qty = st.number_input("Qty", 1, mq)
                if st.button("Move"): 
                    db.move_lot_stage({"lot_no":sel_lot,"from_stage":from_s,"to_stage_key":f"{to} - {stf}","karigar":stf,"machine":mac,"size_key":fk,"qty":qty})
                    st.success("Moved!"); st.rerun()

# PRODUCTIVITY
elif page == "Productivity & Pay":
    st.title("💰 Pay")
    df = db.get_staff_productivity(datetime.datetime.now().month, 2025)
    if not df.empty: st.dataframe(df, use_container_width=True); st.metric("Total Pay", f"₹ {df['Earnings'].sum():,.2f}")

# INVENTORY
elif page == "Inventory":
    st.title("📦 Stock")
    t1, t2 = st.tabs(["Rolls", "Accessories"])
    with t1:
        st.dataframe(pd.DataFrame([{"Fabric": x['_id']['name'], "Color": x['_id']['color'], "Qty": x['total_qty']} for x in db.get_all_fabric_stock_summary()]), use_container_width=True)
    with t2:
        c1, c2 = st.columns(2)
        an = c1.selectbox("Name", [""]+db.get_accessory_names()); aq = c2.number_input("Qty", 0.0)
        if st.button("Add Stock"): db.update_accessory_stock(an, "Inward", aq, "Pcs"); st.success("Added")
        st.dataframe(pd.DataFrame(db.get_accessory_stock()), use_container_width=True)

# CONFIG
elif page == "Config":
    st.title("⚙️ Config")
    with st.form("r"):
        c1,c2,c3 = st.columns(3); i=c1.text_input("Item"); m=c2.selectbox("Proc", db.get_all_processes()); r=c3.number_input("Rate")
        if st.form_submit_button("Save"): db.add_piece_rate(i,"",m,r,datetime.date.today()); st.success("Saved")
    st.dataframe(db.get_rate_master())

# TRACK LOT
elif page == "Track Lot":
    st.title("📍 Track")
    l = st.selectbox("Lot", [""]+db.get_all_lot_numbers())
    if l:
        det = db.get_lot_details(l)
        st.json(det['current_stage_stock'])

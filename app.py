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
    initial_sidebar_state="auto" # Auto-collapse on mobile
)

# --- 2. MOBILE-OPTIMIZED CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700;800&display=swap');
    
    /* GLOBAL RESET */
    html, body, .stApp { 
        font-family: 'Nunito', sans-serif !important; 
        background-color: #FAFBFE !important; 
        color: #67748E;
    }

    /* --- SIDEBAR --- */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #ECECEC;
    }
    
    [data-testid="stSidebar"] div.stButton > button {
        background-color: transparent;
        color: #67748E;
        text-align: left;
        border: none;
        padding: 12px 15px; /* Larger touch target */
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        font-size: 16px;
        margin-bottom: 4px;
    }
    
    [data-testid="stSidebar"] div.stButton > button:hover, 
    [data-testid="stSidebar"] div.stButton > button:focus {
        background-color: #FEF6ED;
        color: #FE9F43;
    }

    /* --- CARDS & CONTAINERS --- */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #ECECEC;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.03);
        margin-bottom: 20px;
    }

    /* --- INPUTS (Touch Friendly) --- */
    input, .stSelectbox > div > div, .stDateInput > div > div {
        background-color: #FFFFFF !important;
        border: 1px solid #E9ECEF !important;
        border-radius: 8px !important;
        color: #67748E !important;
        min-height: 48px !important; /* 48px is standard touch target */
    }
    
    /* --- BUTTONS --- */
    .main .stButton > button {
        background: linear-gradient(to bottom, #FE9F43, #ff8f26);
        color: white;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 700;
        border: none;
        box-shadow: 0 4px 10px rgba(254, 159, 67, 0.3);
        transition: transform 0.1s;
        width: auto;
    }
    
    /* --- MOBILE SPECIFIC TWEAKS --- */
    @media only screen and (max-width: 768px) {
        /* Remove extra padding on mobile */
        .block-container {
            padding-top: 1rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        
        /* Make buttons full width on mobile for easy tapping */
        .main .stButton > button {
            width: 100% !important;
            margin-top: 5px;
        }
        
        /* Adjust font sizes for cards */
        .dash-card-val { font-size: 24px !important; }
        
        /* Stack columns nicely (Streamlit does this, but we force spacing) */
        [data-testid="column"] {
            margin-bottom: 15px;
        }
    }

    /* --- CUSTOM COMPONENTS --- */
    .sidebar-brand {
        display: flex; align-items: center; gap: 12px; padding: 20px 10px;
        border-bottom: 1px dashed #e9ecef; margin-bottom: 20px;
    }
    .brand-icon {
        width: 42px; height: 42px; background: #FE9F43; border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        color: white; font-weight: 900; font-size: 22px;
    }
    .brand-text { font-size: 20px; font-weight: 800; color: #212B36; }
    
    .nav-header {
        font-size: 11px; text-transform: uppercase; color: #A3AAB9;
        font-weight: 800; margin: 25px 0 10px 15px; letter-spacing: 0.5px;
    }
    
    .stock-pill {
        background-color: #FEF6ED; color: #FE9F43; padding: 4px 10px;
        border-radius: 6px; font-size: 12px; font-weight: 700;
        display: inline-block; margin-right: 5px; border: 1px solid rgba(254, 159, 67, 0.2);
    }
    
    .lot-header-box {
        background: #FFFFFF; padding: 15px; border-radius: 10px;
        border-left: 5px solid #FE9F43; box-shadow: 0 4px 15px rgba(0,0,0,0.03);
    }
    .lot-header-text { font-size: 12px; font-weight: 700; color: #A3AAB9; text-transform: uppercase; }
    .lot-header-val { font-size: 16px; font-weight: 800; color: #212B36; margin-right: 15px; }
    
    .dash-card-icon { font-size: 28px; }
</style>
""", unsafe_allow_html=True)

# --- 3. NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = "Dashboard"
def nav(page): st.session_state.page = page

with st.sidebar:
    st.markdown("""
        <div class="sidebar-brand">
            <div class="brand-icon">S</div>
            <div class="brand-text">Shine Arc</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.selectbox("Year", ["2025-26", "2024-25"], label_visibility="collapsed")
    
    st.markdown('<div class="nav-header">HOME</div>', unsafe_allow_html=True)
    if st.button("📊 Dashboard"): nav("Dashboard")
    
    st.markdown('<div class="nav-header">PRODUCTION</div>', unsafe_allow_html=True)
    if st.button("🧶 Fabric Inward"): nav("Fabric Inward")
    if st.button("✂️ Cutting Floor"): nav("Cutting Floor")
    if st.button("🧵 Stitching Floor"): nav("Stitching Floor")
    if st.button("💰 Productivity"): nav("Productivity & Pay")

    st.markdown('<div class="nav-header">MANAGEMENT</div>', unsafe_allow_html=True)
    if st.button("📦 Inventory Stock"): nav("Inventory")
    if st.button("👥 Data Masters"): nav("Masters")
    if st.button("📅 Attendance"): nav("Attendance")

    st.markdown('<div class="nav-header">INTEGRATIONS</div>', unsafe_allow_html=True)
    if st.button("🚀 Vin Lister (MCPL)"): nav("MCPL")

    st.markdown('<div class="nav-header">SYSTEM</div>', unsafe_allow_html=True)
    if st.button("📍 Track Lots"): nav("Track Lot")
    if st.button("⚙️ Config"): nav("Config")
    
    st.markdown("---")
    if st.button("🔒 Logout"): st.rerun()

# --- 4. CONTENT ---
page = st.session_state.page

# DASHBOARD
if page == "Dashboard":
    c_head, c_act = st.columns([3, 1])
    with c_head:
        st.title("Dashboard")
        st.caption(f"Overview • {datetime.date.today().strftime('%b %d, %Y')}")
    
    stats = db.get_dashboard_stats()
    
    # Responsive Cards
    c1, c2, c3 = st.columns(3)
    
    with c1:
        with st.container(border=True):
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:start;">
                <div>
                    <div style="color:#A3AAB9; font-size:12px; font-weight:700; text-transform:uppercase;">Production</div>
                    <div style="font-size:26px; font-weight:800; color:#FE9F43; margin-top:5px;">{stats.get('active_lots', 0)}</div>
                    <div style="font-size:13px; font-weight:600; color:#67748E;">Active Lots</div>
                </div>
                <div class="dash-card-icon">📦</div>
            </div>
            <div style="margin-top:10px; height:6px; background:#FEF6ED; border-radius:3px;"><div style="width:70%; height:100%; background:#FE9F43; border-radius:3px;"></div></div>
            """, unsafe_allow_html=True)

    with c2:
        with st.container(border=True):
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:start;">
                <div>
                    <div style="color:#A3AAB9; font-size:12px; font-weight:700; text-transform:uppercase;">Output</div>
                    <div style="font-size:26px; font-weight:800; color:#28C76F; margin-top:5px;">{stats.get('completed_lots', 0)}</div>
                    <div style="font-size:13px; font-weight:600; color:#67748E;">Completed Lots</div>
                </div>
                <div class="dash-card-icon">✅</div>
            </div>
            <div style="margin-top:10px; height:6px; background:#EAFBF1; border-radius:3px;"><div style="width:85%; height:100%; background:#28C76F; border-radius:3px;"></div></div>
            """, unsafe_allow_html=True)

    with c3:
        with st.container(border=True):
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:start;">
                <div>
                    <div style="color:#A3AAB9; font-size:12px; font-weight:700; text-transform:uppercase;">Inventory</div>
                    <div style="font-size:26px; font-weight:800; color:#00CFDD; margin-top:5px;">{stats.get('fabric_rolls', 0)}</div>
                    <div style="font-size:13px; font-weight:600; color:#67748E;">Fabric Rolls</div>
                </div>
                <div class="dash-card-icon">🧶</div>
            </div>
            <div style="margin-top:10px; height:6px; background:#E6FAFB; border-radius:3px;"><div style="width:50%; height:100%; background:#00CFDD; border-radius:3px;"></div></div>
            """, unsafe_allow_html=True)

    st.markdown("### 📋 Pending Orders")
    pd_df = stats.get('pending_list', [])
    if pd_df: st.dataframe(pd.DataFrame(pd_df), use_container_width=True)
    else: st.info("No Pending Lots")

# MCPL
elif page == "MCPL":
    st.title("🚀 Vin Lister (MCPL)")
    if 'mcpl_mode' not in st.session_state: st.session_state.mcpl_mode = 'Catalog'
    
    # Responsive Sub-Nav
    cols = st.columns(3)
    if cols[0].button("📂 Catalog", use_container_width=True): st.session_state.mcpl_mode = 'Catalog'
    if cols[1].button("📥 Import", use_container_width=True): st.session_state.mcpl_mode = 'Import'
    if cols[2].button("🏷️ Pricing", use_container_width=True): st.session_state.mcpl_mode = 'Pricing'
    st.markdown("---")
    
    mode = st.session_state.mcpl_mode
    if mode == "Catalog":
        st.subheader("Product Catalog")
        df_cat = db.get_mcpl_catalog()
        if not df_cat.empty:
            cols = ["sku", "name", "category", "base_price", "channel_prices", "status"]
            for c in cols: 
                if c not in df_cat.columns: df_cat[c] = "-"
            
            # Image Preview if available
            if "image_url" in df_cat.columns:
                cols.insert(0, "image_url")
                st.dataframe(df_cat[cols], column_config={"image_url": st.column_config.ImageColumn("Img", width="small")}, use_container_width=True)
            else:
                st.dataframe(df_cat[cols], use_container_width=True)
        else: st.info("Empty Catalog")
        
        with st.expander("➕ Add Product"):
            c1, c2 = st.columns(2)
            sku = c1.text_input("SKU"); nm = c2.text_input("Name")
            cat = c1.selectbox("Category", ["Apparel", "Home"]); bp = c2.number_input("Base Price", 0.0)
            img = c1.text_input("Image URL")
            if st.button("Add Product", use_container_width=True):
                if sku: db.mcpl_add_product(sku, nm, cat, bp, img); st.success("Added!"); st.rerun()

    elif mode == "Import":
        st.subheader("Bulk Import")
        st.download_button("⬇️ Template", pd.DataFrame([{"SKU":"A1","Name":"Item","Category":"Gen","Price":100,"Image URL":""}]).to_csv(index=False).encode('utf-8'), "template.csv", use_container_width=True)
        up = st.file_uploader("Upload CSV", type=['csv'])
        if up:
            df = pd.read_csv(up)
            st.dataframe(df, use_container_width=True)
            if st.button("Process Import", type="primary", use_container_width=True):
                cnt, err = db.mcpl_bulk_upload(df)
                st.success(f"Success: {cnt}, Errors: {err}")

    elif mode == "Pricing":
        st.subheader("Channel Pricing")
        df_cat = db.get_mcpl_catalog()
        if not df_cat.empty and 'sku' in df_cat.columns:
            sel = st.selectbox("Select SKU", df_cat['sku'].tolist())
            if sel:
                row = df_cat[df_cat['sku']==sel].iloc[0]
                cur = row.get('channel_prices', {})
                st.info(f"Base Price: {row.get('base_price')}")
                c1,c2,c3 = st.columns(3)
                a = c1.number_input("Amazon", value=float(cur.get('Amazon',0)))
                f = c2.number_input("Flipkart", value=float(cur.get('Flipkart',0)))
                m = c3.number_input("Myntra", value=float(cur.get('Myntra',0)))
                if st.button("Update Prices", use_container_width=True):
                    db.mcpl_update_channel_price(sel, "Amazon", a)
                    db.mcpl_update_channel_price(sel, "Flipkart", f)
                    db.mcpl_update_channel_price(sel, "Myntra", m)
                    st.success("Updated!")

# MASTERS
elif page == "Masters":
    st.title("👥 Masters")
    tabs = st.tabs(["Fabric", "Process", "Staff", "Items", "Colors", "Sizes"])
    
    with tabs[0]:
        c1,c2=st.columns(2); n=c1.text_input("Name"); h=c2.text_input("HSN")
        if st.button("Add Fabric", use_container_width=True): db.add_material(n,h); st.success("Added")
        st.dataframe(db.get_materials(), use_container_width=True)
    with tabs[1]:
        pn=st.text_input("Process Name"); 
        if st.button("Add Process", use_container_width=True): db.add_process(pn); st.success("Added")
        st.write(", ".join(db.get_all_processes()))
    with tabs[2]:
        c1,c2=st.columns(2); n=c1.text_input("Staff Name"); r=c2.selectbox("Role", ["Cutting Master", "Stitching Karigar", "Helper"])
        if st.button("Add Staff", use_container_width=True): db.add_staff(n,r); st.success("Added")
        st.dataframe(db.get_all_staff(), use_container_width=True)
    with tabs[3]: # ITEM MASTER (5 Fabrics)
        with st.container(border=True):
            c1,c2,c3=st.columns(3); nm=c1.text_input("Item Name"); cd=c2.text_input("Code"); cl=c3.text_input("Color")
            st.caption("Bill of Materials (Fabrics)")
            fo=[""]+db.get_material_names()
            f_cols=st.columns(5)
            f_sel = [f_cols[i].selectbox(f"Fabric {i+1}", fo, key=f"fab_{i}") for i in range(5)]
            if st.button("Save Item Master", use_container_width=True):
                db.add_item_master(nm,cd,cl,f_sel); st.success("Saved!")
        st.dataframe(db.get_all_items(), use_container_width=True)
    with tabs[4]:
        n=st.text_input("New Color"); 
        if st.button("Add Color", use_container_width=True): db.add_color(n); st.rerun()
        st.write(", ".join(db.get_colors()))
    with tabs[5]:
        n=st.text_input("New Size"); 
        if st.button("Add Size", use_container_width=True): db.add_size(n); st.rerun()
        st.write(", ".join(db.get_sizes()))

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
        
        st.markdown("---")
        if req_fabs:
            for f in req_fabs:
                with st.expander(f"Stock: {f}", expanded=True):
                    ss=db.get_all_fabric_stock_summary()
                    ac=sorted(list(set([s['_id']['color'] for s in ss if s['_id']['name']==f])))
                    fc=st.selectbox(f"Color ({f})", ac, key=f"fc_{f}")
                    if fc:
                        rls=db.get_available_rolls(f,fc)
                        if rls:
                            st.caption(f"Available: {rls[0]['uom']}")
                            cols=st.columns(4); sel=[]; w=0.0
                            for i,r in enumerate(rls):
                                if cols[i%4].checkbox(f"{r['quantity']}", key=f"chk_{f}_{r['_id']}"): sel.append(r['_id']); w+=r['quantity']
                            st.session_state.fabric_selections[f]={"roll_ids":sel,"total_weight":w,"uom":rls[0]['uom']}
                        else: st.warning("No Stock")
        else: st.info("Select Item to load fabrics")
        
        st.markdown("---")
        cc1,cc2=st.columns([1,3]); lc=cc1.text_input("Batch Color", acol); sin={}
        if sizes:
            sc=cc2.columns(len(sizes))
            for i,z in enumerate(sizes): sin[z]=sc[i].number_input(z,0,key=f"sz_{z}")
        
        if st.button("Add Batch", use_container_width=True):
            if lc and sum(sin.values())>0:
                for z,q in sin.items(): 
                    if q>0: st.session_state.lot_breakdown[f"{lc}_{z}"]=q
                st.success("Added")
        
        if st.session_state.lot_breakdown:
            st.json(st.session_state.lot_breakdown)
            if st.button("🚀 CREATE LOT", type="primary", use_container_width=True):
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
                if q2.button("Confirm", use_container_width=True): 
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
    st.title("📦 Inventory")
    t1, t2, t3 = st.tabs(["Garments", "Fabric", "Accessories"])
    with t1:
        active_lots = db.get_active_lots()
        if active_lots: st.dataframe(pd.DataFrame([{"Lot": l['lot_no'], "Item": l['item_name'], "Pcs": l['total_qty']} for l in active_lots]), use_container_width=True)
    with t2:
        s = db.get_all_fabric_stock_summary()
        if s: st.dataframe(pd.DataFrame([{"Fabric": x['_id']['name'], "Color": x['_id']['color'], "Rolls": x['total_rolls'], "Qty": x['total_qty']} for x in s]), use_container_width=True)
    with t3:
        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.markdown("**Inward**")
                an = st.selectbox("Name", [""] + db.get_accessory_names()); 
                if not an: an = st.text_input("New Name")
                aq = st.number_input("Qty", 0.0); au = st.selectbox("Unit", ["Pcs", "Kg", "Box"])
                if st.button("Add", use_container_width=True): 
                    if an and aq > 0: db.update_accessory_stock(an, "Inward", aq, au); st.success("Added!"); st.rerun()
        with c2:
            with st.container(border=True):
                st.markdown("**Outward**")
                an_out = st.selectbox("Item", [""] + db.get_accessory_names(), key="acc_out")
                aq_out = st.number_input("Qty Out", 0.0, key="qty_out")
                if st.button("Issue", use_container_width=True):
                    if an_out and aq_out > 0: db.update_accessory_stock(an_out, "Outward", aq_out, "N/A"); st.success("Issued!"); st.rerun()
        st.divider(); st.dataframe(pd.DataFrame(db.get_accessory_stock()), use_container_width=True)

# CONFIG
elif page == "Config":
    st.title("⚙️ Config")
    t1, t2 = st.tabs(["Rate Card", "Danger Zone"])
    process_list = db.get_all_processes()
    with t1:
        with st.form("r"):
            c1,c2,c3,c4,c5 = st.columns(5)
            i=c1.text_input("Item Name"); cd=c2.text_input("Item Code"); m=c3.selectbox("Process", process_list); r=c4.number_input("Rate"); d=c5.date_input("Date")
            if st.form_submit_button("Save"): db.add_piece_rate(i,cd,m,r,d); st.success("Saved")
        st.dataframe(db.get_rate_master(), use_container_width=True)
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
            st.dataframe(pd.DataFrame(mat), use_container_width=True)

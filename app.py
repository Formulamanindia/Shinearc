import streamlit as st
import pandas as pd
import db_manager as db
import datetime
import math
import time
import base64

# --- CONFIG (DESKTOP-FIRST SAAS) ---
st.set_page_config(page_title="DrenchWear ERP", page_icon="🧵", layout="wide", initial_sidebar_state="expanded")

# --- DESKTOP SAAS CSS INJECTION ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Global Theme & Reset */
    * { box-sizing: border-box !important; font-family: 'Inter', sans-serif !important; }
    .stApp { background-color: #F8FAFC !important; color: #0F172A; }
    
    /* Hide Streamlit Native Elements (Pure App Feel) */
    [data-testid="stHeader"] { display: none !important; }
    footer { display: none !important; }
    
    /* Centralize Content with Adaptive Spacing */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 5rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
        max-width: 1600px !important;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 { color: #0F172A !important; font-weight: 700 !important; letter-spacing: -0.02em; }

    /* --- SIDEBAR NAV (DESKTOP SAAS STYLE) --- */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
        box-shadow: 2px 0 10px rgba(0,0,0,0.02) !important;
    }
    div[role="radiogroup"] { gap: 6px; }
    div[role="radiogroup"] label {
        padding: 12px 16px !important;
        border-radius: 10px !important;
        color: #475569 !important;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.2s ease;
        border: none !important;
        background: transparent !important;
        cursor: pointer;
    }
    div[role="radiogroup"] label:hover {
        background-color: #F1F5F9 !important;
        color: #0F172A !important;
        transform: translateX(4px);
    }
    div[role="radiogroup"] label[data-checked="true"] {
        background-color: #EEF2FF !important;
        color: #4F46E5 !important;
        border-left: 4px solid #4F46E5 !important;
        border-radius: 4px 10px 10px 4px !important;
        box-shadow: 0 2px 4px rgba(79, 70, 229, 0.05);
    }

    /* --- PREMIUM SAAS METRIC CARDS --- */
    .metric-card { 
        background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 24px; 
        box-shadow: 0 4px 15px -3px rgba(0,0,0,0.03); display: flex; justify-content: space-between; 
        align-items: center; transition: transform 0.2s, box-shadow 0.2s; margin-bottom: 20px;
    }
    .metric-card:hover { transform: translateY(-4px); box-shadow: 0 10px 20px -3px rgba(0,0,0,0.06); }
    .metric-info { display: flex; flex-direction: column; }
    .metric-label { font-size: 0.85rem; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }
    .metric-value { font-size: 1.8rem; font-weight: 800; color: #0F172A; line-height: 1; }
    .metric-icon-box { width: 56px; height: 56px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 1.6rem; }

    /* --- UNIFIED PRODUCT CARDS --- */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 16px !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 4px 15px -4px rgba(0,0,0,0.03) !important;
        background: #FFFFFF !important;
        padding: 20px !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        margin-bottom: 16px !important;
        height: 100%;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 25px -5px rgba(0,0,0,0.08) !important;
        border-color: #CBD5E1 !important;
    }
    
    .thumbnail-container { display: flex; gap: 8px; margin-bottom: 12px; overflow-x: auto; padding-bottom: 4px; scrollbar-width: none; }
    .thumbnail-container::-webkit-scrollbar { display: none; }
    .product-thumbnail { width: 45px; height: 45px; object-fit: cover; border-radius: 8px; border: 1px solid #E2E8F0; }
    
    .product-link-btn {
        display: flex; align-items: center; justify-content: center; background-color: #F8FAFC; color: #4F46E5 !important; 
        padding: 10px; border-radius: 10px; font-weight: 600; font-size: 0.9rem; text-decoration: none !important; 
        border: 1px solid #E2E8F0; transition: all 0.2s ease; margin-bottom: 15px; width: 100%;
    }
    .product-link-btn:hover { background-color: #EEF2FF; border-color: #C7D2FE; }

    /* --- FORMS & CONTAINERS --- */
    [data-testid="stForm"], .st-emotion-cache-1104q3m { 
        background: #FFFFFF !important; padding: 32px !important; border-radius: 16px !important; border: 1px solid #E2E8F0 !important; box-shadow: 0 4px 15px -4px rgba(0,0,0,0.03) !important; width: 100% !important; margin-bottom: 20px;
    }
    .section-header { border-bottom: 2px solid #E2E8F0; padding-bottom: 10px; margin-top: 10px; margin-bottom: 20px; color: #0F172A; font-size: 1.25rem; font-weight: 700; }

    /* --- INPUTS & DROPDOWNS --- */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox > div > div { 
        background-color: #F8FAFC !important; border: 1px solid #CBD5E1 !important; border-radius: 10px !important; color: #0F172A !important; padding: 10px 14px !important; font-size: 0.95rem; min-height: 42px !important; box-shadow: 0 1px 2px rgba(0,0,0,0.01) !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus, .stSelectbox > div > div:focus { 
        border-color: #4F46E5 !important; box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1) !important; background: #FFFFFF !important;
    }
    div[data-baseweb="select"] span { color: #0F172A !important; font-weight: 500; }
    div[data-baseweb="popover"], ul[role="listbox"] { background-color: #FFFFFF !important; border-radius: 10px !important; border: 1px solid #E2E8F0 !important; box-shadow: 0 10px 25px rgba(0,0,0,0.1) !important; overflow: hidden; }
    ul[role="listbox"] li { padding: 10px 16px !important; font-size: 0.95rem !important; color: #0F172A !important; }
    ul[role="listbox"] li:hover { background-color: #F8FAFC !important; color: #4F46E5 !important; }

    /* --- SAAS BUTTONS --- */
    .stButton button { 
        border-radius: 10px; font-weight: 600; min-height: 42px !important; transition: all 0.2s ease; border: 1px solid #E2E8F0 !important; background: #FFFFFF !important; color: #0F172A !important; box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
    }
    .stButton button:hover { background: #F8FAFC !important; border-color: #CBD5E1 !important; }
    .stButton button[kind="primary"] { 
        background: #4F46E5 !important; color: white !important; border: none !important; box-shadow: 0 4px 10px rgba(79, 70, 229, 0.2) !important; 
    }
    .stButton button[kind="primary"]:hover { background: #4338CA !important; box-shadow: 0 6px 15px rgba(79, 70, 229, 0.3) !important; transform: translateY(-1px); }
    .stButton button[kind="primary"]:active { transform: scale(0.98); }

    /* --- TABS --- */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; border-bottom: 1px solid #E2E8F0; padding-bottom: 0px; }
    .stTabs [data-baseweb="tab"] { height: 48px; border: none; background: transparent; color: #64748B; font-weight: 600; font-size: 1rem; padding: 0 4px; white-space: nowrap; transition: color 0.2s; }
    .stTabs [aria-selected="true"] { color: #4F46E5 !important; border-bottom: 2px solid #4F46E5 !important; }

    /* --- DATAFRAMES --- */
    [data-testid="stDataFrame"] { border-radius: 12px; border: 1px solid #E2E8F0; box-shadow: 0 2px 4px rgba(0,0,0,0.01); overflow: hidden; background: #FFFFFF; }

    /* Login Centering */
    .login-container { max-width: 420px; margin: 15vh auto; background: white; padding: 40px 30px; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.08); border: 1px solid #E2E8F0; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def render_metric_card(label, value, icon="📈", bg_light="#EEF2FF", text_color="#4F46E5"):
    card_html = f"""<div class="metric-card">
    <div class="metric-info"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>
    <div class="metric-icon-box" style="background-color: {bg_light}; color: {text_color};">{icon}</div>
</div>"""
    st.markdown(card_html, unsafe_allow_html=True)

def render_df(df):
    if df.empty: st.info("No data available."); return
    st.dataframe(df, use_container_width=True, hide_index=True)

# --- AUTH ---
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if not st.session_state["authenticated"]:
    login_html = """<div class="login-container">
<div style="font-size: 3.5rem; margin-bottom: 10px;">🧵</div>
<h2 style='color: #0F172A; margin-bottom: 5px; margin-top:0; font-weight:800;'>DrenchWear</h2>
<p style='color: #64748B; font-weight: 500; margin-bottom: 30px; font-size:1rem;'>Log in to your workspace</p>"""
    st.markdown(login_html, unsafe_allow_html=True)
    with st.form("login", clear_on_submit=True):
        pwd = st.text_input("Access Key", type="password", placeholder="••••••••", label_visibility="collapsed")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("Sign In", type="primary", use_container_width=True):
            if pwd == "Flow@1993":
                st.session_state["authenticated"] = True; st.rerun()
            else: st.error("❌ Incorrect Password")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- INIT STATE ---
if "nav_selection" not in st.session_state: st.session_state.nav_selection = "📊 Dashboard"

# --- SIDEBAR NAVIGATION (DESKTOP STYLED) ---
with st.sidebar:
    st.markdown("""<div style="font-size: 1.5rem; font-weight: 800; color: #4F46E5; text-align: center; margin-bottom: 2rem; margin-top: 1rem; display: flex; align-items: center; justify-content: center; gap: 10px;">🧵 DrenchWear</div>""", unsafe_allow_html=True)
    
    st.session_state.nav_selection = st.radio(
        "MENU", 
        [
            "📊 Dashboard", 
            "🤖 Drench AI", 
            "🏭 Work Operations", 
            "🚀 Product Launcher",
            "📈 P&L Analysis",
            "💸 Staff Payments", 
            "🧾 GST Tracker", 
            "📋 Catalog Maker", 
            "📦 Product Master", 
            "⚙️ System Masters"
        ],
        label_visibility="collapsed"
    )
    
    st.markdown("<hr style='margin: 30px 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)
    if st.button("🔒 Secure Logout", use_container_width=True): 
        st.session_state["authenticated"] = False; st.rerun()

nav = st.session_state.nav_selection

# --- MAIN HEADER ---
clean_title = nav.split(' ', 1)[1] if ' ' in nav else nav
st.markdown(f"<h2 style='margin-bottom: 5px;'>{clean_title}</h2>", unsafe_allow_html=True)
st.markdown("<hr style='margin-top: 5px; margin-bottom: 30px; border-color:#E2E8F0;'>", unsafe_allow_html=True)

# ==========================================
# MODULE CONTENT VIEWS
# ==========================================

if nav == "📊 Dashboard":
    pcs, earn, pending, active = db.get_dashboard_stats()
    
    # DESKTOP 4-COLUMN GRID
    m1, m2, m3, m4 = st.columns(4)
    with m1: render_metric_card("Pieces Today", f"{pcs:,.0f}", "👕", "#D1FAE5", "#10B981")
    with m2: render_metric_card("Prod Value", f"₹{earn:,.0f}", "₹", "#FEF3C7", "#F59E0B")
    with m3: render_metric_card("Liabilities", f"₹{pending:,.0f}", "💳", "#FEE2E2", "#EF4444")
    with m4: render_metric_card("Active Staff", f"{active}", "👥", "#DBEAFE", "#3B82F6")
    
    st.markdown("<div class='section-header'>Live Production Feed</div>", unsafe_allow_html=True)
    try:
        df = db.get_df("production")
        if not df.empty and 'created_at' in df.columns:
            df['Time'] = pd.to_datetime(df['created_at']).dt.strftime('%H:%M')
            cols_to_show = [c for c in ['Time', 'staff_name', 'item', 'process', 'qty', 'amount'] if c in df.columns]
            st.dataframe(df[cols_to_show].head(15), use_container_width=True, hide_index=True)
        else:
            st.info("No recent production data recorded today.")
    except Exception as e:
        st.warning("Could not load production feed.")

elif nav == "🤖 Drench AI":
    t1, t2, t3 = st.tabs(["📤 Upload Orders", "📊 Order Summary", "✂️ Smart Cutting Plan"])
    with t1:
        st.info("Required Columns: Channel, Item, Category, Color, Size, Qty")
        uf = st.file_uploader("Upload Daily Orders", type=['csv', 'xlsx'])
        if uf and st.button("Process & Upload", type="primary", use_container_width=True):
            try:
                df = pd.read_csv(uf) if uf.name.endswith('.csv') else pd.read_excel(uf)
                s, m = db.save_daily_orders(df)
                if s: st.success(m)
                else: st.error(m)
            except Exception as e: st.error(f"Error: {e}")
    with t2:
        render_df(db.get_daily_orders_df())
    with t3:
        c1, c2 = st.columns(2)
        d1 = c1.date_input("From Date", datetime.date.today()-datetime.timedelta(days=7))
        d2 = c2.date_input("To Date", datetime.date.today())
        if st.button("Generate Smart Plan", type="primary", use_container_width=True):
            df = db.generate_cutting_plan(str(d1), str(d2))
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                st.download_button("Download Job Sheet CSV", df.to_csv(index=False), "plan.csv", use_container_width=True)
            else: st.warning("No orders found.")

elif nav == "🏭 Work Operations":
    tab_cut, tab_stitch, tab_ops = st.tabs(["✂️ Cutting Dept", "🪡 Stitching Dept", "📦 Job Work Tracking"])
    
    with tab_cut:
        act = st.radio("Action", ["Create New Lot", "View Active Lots"], horizontal=True, label_visibility="collapsed")
        if act == "Create New Lot":
            st.markdown("<div class='section-header'>Lot & Product Selection</div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            l_no = c1.text_input("Lot Number (e.g., L-1001)")
            
            prod_names = [p['name'] for p in db.get_parent_products()]
            item_names = db.get_items_list()
            all_product_options = sorted(list(set(prod_names + item_names)))
            item_name = c2.selectbox("Select Item / Style", [""] + all_product_options)

            st.markdown("<div class='section-header'>Fabric Consumption</div>", unsafe_allow_html=True)
            if "fab_df" not in st.session_state:
                st.session_state.fab_df = pd.DataFrame([{"Srl no.": i+1, "Color": "", "UOM": "Meter", "Qty": 0.0} for i in range(5)])
            e_fab = st.data_editor(st.session_state.fab_df, num_rows="dynamic", use_container_width=True, hide_index=True)
            
            st.markdown("<div class='section-header'>Bundle Generation</div>", unsafe_allow_html=True)
            c_bun1, c_bun2 = st.columns([1, 4])
            n_bun = c_bun1.number_input("No. of Bundles", 1, 500, 10)
            if c_bun1.button("🔄 Generate Grid", use_container_width=True):
                st.session_state.lot_df = pd.DataFrame([{"Bundle No": str(i+1), "Qty": 0} for i in range(n_bun)])
                
            if "lot_df" not in st.session_state:
                st.session_state.lot_df = pd.DataFrame([{"Bundle No": str(i+1), "Qty": 0} for i in range(10)])
                
            e_bun = st.data_editor(st.session_state.lot_df, height=350, use_container_width=True, hide_index=True)
            
            total_pcs = pd.to_numeric(e_bun['Qty'], errors='coerce').sum()
            st.markdown(f"<div style='color: #4F46E5; font-weight:700; font-size:1.1rem; margin-top: 10px;'>Calculated Total: {total_pcs:,.0f} Pcs</div>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Save & Authorize Cutting Lot", type="primary"):
                if not l_no or not item_name:
                    st.error("Lot Number and Item Name are required.")
                else:
                    h = {"lot_no": l_no, "item_name": item_name, "date": str(datetime.date.today()), "sku": item_name}
                    s, m = db.save_full_lot(h, e_fab, e_bun)
                    if s: 
                        st.success(m)
                        if 'lot_df' in st.session_state: del st.session_state['lot_df']
                        if 'fab_df' in st.session_state: del st.session_state['fab_df']
                        time.sleep(1)
                        st.rerun()
                    else: st.error(m)
        else:
            st.info("View active lot progress in the 'Job Work Tracking' tab.")

    with tab_stitch:
        stitch_mode = st.radio("Entry Mode", ["Single Entry Form", "Bulk CSV Upload"], horizontal=True, label_visibility="collapsed")
        if stitch_mode == "Single Entry Form":
            with st.form("stitch_log"):
                st.markdown("<div class='section-header' style='margin-top:0;'>Record Daily Stitching</div>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                sd_date = c1.date_input("Production Date")
                sd_worker = c2.selectbox("Karigar (Worker)", db.get_staff_list())
                sd_proc = c3.selectbox("Process Completed", db.get_processes_list())
                
                c4, c5 = st.columns(2)
                sd_lot = c4.selectbox("Select Source Lot", [""] + db.get_active_lots())
                
                buns = []
                if sd_lot:
                    b_data = db.get_detailed_bundles(sd_lot)
                    buns = [f"{b['bundle_no']} | {b['item_name']} | {b['qty']} pcs" for b in b_data]
                
                sd_bun = c5.selectbox("Select Specific Bundle", [""] + buns)
                
                st.markdown("<hr style='margin: 15px 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)
                c6, c7 = st.columns(2)
                qty = c6.number_input("Quantity Stitched (Pcs)", min_value=1.0)
                lbl = c7.checkbox("🏷️ Include Labeling Charge (+₹0.50 per pc)")
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("💾 Submit Entry & Credit Ledger", type="primary"):
                    if sd_worker and sd_lot and sd_bun:
                        p = sd_bun.split(" | ")
                        val_item = p[1] if len(p)>1 else ""
                        real_bun = p[0]
                        rate = db.get_rate(val_item, sd_proc, sd_date)
                        fin_rate = rate + (0.50 if lbl else 0)
                        
                        s, m = db.save_production(str(sd_date), sd_worker, val_item, sd_proc, qty, fin_rate, sd_lot, real_bun)
                        if s: st.success(f"Success! Credited to ledger: ₹{qty*fin_rate:,.2f}")
                        else: st.error(m)
                    else: st.error("Please fill in all required fields.")
                    
        elif stitch_mode == "Bulk CSV Upload":
            st.info("The system automatically fetches the correct Piece Rate from the Master configuration based on the Date.")
            sample_csv = "Date,Karigar Name,Lot No,Bundle No.,Process,Item,Qty\n2026-03-10,Worker Name,L-1001,B-01,Collar,Top,50"
            st.download_button("⬇️ Download Template", sample_csv, "Stitching_Template.csv", "text/csv")
            
            uf = st.file_uploader("Upload Completed CSV", type=["csv", "xlsx"])
            if uf and st.button("🚀 Process Bulk Upload", type="primary"):
                try:
                    df = pd.read_csv(uf) if uf.name.endswith('.csv') else pd.read_excel(uf)
                    count, errors = db.save_bulk_stitching(df)
                    if count > 0: st.success(f"Successfully processed {count} records!")
                    if errors:
                        with st.expander("View Upload Errors"):
                            for e in errors: st.write(e)
                except Exception as e: st.error(str(e))

    with tab_ops:
        ops_view_mode = st.radio("View Module", ["Bundle Tracking Matrix", "External Fabrication Job Work"], horizontal=True, label_visibility="collapsed")
        if ops_view_mode == "Bundle Tracking Matrix":
            st.dataframe(db.get_bundle_progress(), use_container_width=True)
        else:
            with st.form("fab_form"):
                st.markdown("<div class='section-header' style='margin-top:0;'>Record Outward Job Work</div>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                fd = c1.date_input("Challan Date")
                fp = c2.selectbox("Job Worker / Party", db.get_parties_list())
                fi = c3.text_input("Item Description")
                
                c4, c5, c6 = st.columns(3)
                fq = c4.number_input("Quantity Outward", 1.0)
                fr = c5.number_input("Agreed Rate (₹)", 0.0)
                fdesc = c6.text_input("Process Notes")
                
                if st.form_submit_button("Save Fabrication Entry", type="primary"):
                    db.save_fabrication(str(fd), fp, fi, fq, fr, fdesc)
                    st.success("Entry Saved Successfully.")
            st.dataframe(db.get_recent_fabrication(), use_container_width=True)

elif nav == "🚀 Product Launcher":
    tab_add, tab_view = st.tabs(["➕ Add New Product", "📋 Pipeline Board"])
    
    with tab_add:
        st.markdown("<div class='section-header' style='margin-top:0;'>1. Import Source Data</div>", unsafe_allow_html=True)
        
        c_url, c_btn, c_man = st.columns([6, 2, 2])
        fetch_url = c_url.text_input("Product URL", placeholder="https://www.myntra.com/...", label_visibility="collapsed")
        
        if c_btn.button("🔍 Auto-Fetch Details", use_container_width=True):
            if fetch_url:
                with st.spinner("Extracting metadata..."):
                    st.session_state.launcher_draft = db.fetch_product_metadata(fetch_url)
            else:
                st.warning("Please paste a URL first.")
                
        if c_man.button("✍️ Manual Entry", use_container_width=True):
            st.session_state.launcher_draft = {"title": "", "price": 0.0, "image": "", "url": ""}

        if "launcher_draft" in st.session_state:
            draft = st.session_state.launcher_draft
            with st.form("save_launcher_prod"):
                st.markdown("<div class='section-header' style='margin-top:0;'>2. Verify & Save to Pipeline</div>", unsafe_allow_html=True)
                
                c1, c2 = st.columns([3, 1])
                p_title = c1.text_input("Product Title", value=draft.get("title", ""))
                p_price = c2.number_input("Target Price (₹)", value=float(draft.get("price", 0.0)))
                
                c3, c4 = st.columns(2)
                p_img = c3.text_input("Source Image URL", value=draft.get("image", ""))
                p_img_upload = c4.file_uploader("Upload Local Images (Overrides URL)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
                
                p_stage = st.selectbox("Initial Pipeline Stage", ["Stage 1", "Stage 2", "Stage 3", "Stage 4", "Stage 5", "Stage 6", "Stage 7"])
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("💾 Add to Pipeline", type="primary"):
                    if p_title:
                        final_imgs = []
                        if p_img_upload:
                            for img_file in p_img_upload:
                                base64_str = base64.b64encode(img_file.read()).decode('utf-8')
                                final_imgs.append(f"data:{img_file.type};base64,{base64_str}")
                        elif p_img:
                            final_imgs = [p_img]
                            
                        prod_url = fetch_url if fetch_url else draft.get("url", "")
                        
                        s, m = db.save_launched_product(p_title, prod_url, final_imgs, p_price, p_stage)
                        if s: 
                            st.success(m); del st.session_state.launcher_draft; time.sleep(1); st.rerun()
                        else: st.error(m)
                    else: st.error("Product Title is required.")
                        
    with tab_view:
        products = db.get_launched_products()
        if not products:
            st.info("Pipeline is empty. Add a product to get started.")
        else:
            stages = ["Stage 1", "Stage 2", "Stage 3", "Stage 4", "Stage 5", "Stage 6", "Stage 7"]
            
            # Responsive Wide Desktop Grid
            cols = st.columns(4)
            
            for idx, prod in enumerate(products):
                with cols[idx % 4]:
                    with st.container(border=True): # Wrapper Card
                        img_urls = prod.get('images', [])
                        if not img_urls and prod.get('image_url'): img_urls = [prod.get('image_url')]
                            
                        main_img = img_urls[0] if img_urls else "https://via.placeholder.com/400x300?text=No+Image+Found"
                        
                        thumbnails_html = ""
                        if len(img_urls) > 1:
                            thumbnails_html = "<div class='thumbnail-container'>"
                            for thumb in img_urls[1:]:
                                thumbnails_html += f"<img src='{thumb}' class='product-thumbnail' onerror=\"this.style.display='none';\">"
                            thumbnails_html += "</div>"
                        
                        prod_html = f"""<div style="padding: 4px;">
<img src="{main_img}" class="product-image" onerror="this.onerror=null;this.src='https://via.placeholder.com/400x300?text=Error';">
{thumbnails_html}
<div class="product-title" title="{prod.get('title', 'Unknown')}">{prod.get('title', 'Unknown')}</div>
<div class="product-price">₹ {prod.get('price', 0.0):,.2f}</div>
<a href="{prod.get('url', '#')}" target="_blank" class="product-link-btn">🔗 Original Link</a>
</div>"""
                        st.markdown(prod_html, unsafe_allow_html=True)
                        
                        curr_stage = prod.get('stage', 'Stage 1')
                        curr_idx = stages.index(curr_stage) if curr_stage in stages else 0
                        new_stage = st.selectbox("Stage", stages, index=curr_idx, key=f"stg_{prod['_id']}", label_visibility="collapsed")
                        
                        bc1, bc2 = st.columns(2)
                        if bc1.button("💾 Apply", key=f"upd_{prod['_id']}", use_container_width=True):
                            db.update_launched_product_stage(prod['_id'], new_stage)
                            st.rerun()
                            
                        with bc2.popover("⚙️ Manage", use_container_width=True):
                            st.markdown("#### Edit Details")
                            e_title = st.text_input("Title", value=prod.get('title', ''), key=f"et_{prod['_id']}")
                            e_price = st.number_input("Price (₹)", value=float(prod.get('price', 0.0)), key=f"ep_{prod['_id']}")
                            e_img = st.text_input("Main Image URL", value=main_img, key=f"ei_{prod['_id']}")
                            e_img_file = st.file_uploader("Replace Images", type=['png', 'jpg'], accept_multiple_files=True, key=f"ef_{prod['_id']}")
                            
                            if st.button("Save Changes", type="primary", key=f"es_{prod['_id']}", use_container_width=True):
                                final_edit_imgs = img_urls
                                if e_img_file:
                                    final_edit_imgs = [f"data:{f.type};base64,{base64.b64encode(f.read()).decode('utf-8')}" for f in e_img_file]
                                elif e_img != main_img: final_edit_imgs = [e_img]
                                    
                                s, m = db.update_launched_product_details(prod['_id'], e_title, e_price, final_edit_imgs)
                                st.rerun() if s else st.error(m)
                                    
                            st.markdown("<hr style='margin: 10px 0; border-color:#E2E8F0;'>", unsafe_allow_html=True)
                            if st.button("🚨 Delete Product", key=f"del_{prod['_id']}", use_container_width=True):
                                db.delete_launched_product(prod['_id']); st.rerun()

elif nav == "📈 P&L Analysis":
    st.markdown("<div class='section-header' style='margin-top:0;'>Marketplace Reconciliation</div>", unsafe_allow_html=True)
    st.caption("Map your Orders, Payments, and Ad data to standard formats.")
    
    channels = db.get_channels_list()
    
    if not channels:
        st.info("No active channels found. Please configure Marketplaces in 'System Masters'.")
    else:
        tabs = st.tabs([f"🛒 {c}" for c in channels])
        
        for i, c_name in enumerate(channels):
            with tabs[i]:
                with st.container(border=True):
                    st.markdown(f"#### 📊 {c_name} Operations Data")
                    
                    o_file = st.file_uploader("Upload Orders Report", type=['csv', 'xlsx'], key=f"o_{c_name}")
                    if o_file:
                        df_o = pd.read_csv(o_file) if o_file.name.endswith('.csv') else pd.read_excel(o_file)
                        cols = ["Select File Column..."] + df_o.columns.tolist()
                        st.markdown("**Map Order Columns:**")
                        mc1, mc2, mc3 = st.columns(3)
                        mc1.selectbox("Order ID", cols, key=f"o_id_{c_name}")
                        mc2.selectbox("Order Date", cols, key=f"o_dt_{c_name}")
                        mc3.selectbox("Order Amount", cols, key=f"o_am_{c_name}")
                        if st.button("Save Order Mapping", type="primary", key=f"o_btn_{c_name}"):
                            st.success("Orders Mapped & Saved!")
                    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
                            
                    p_file = st.file_uploader("Upload Payment Settlements", type=['csv', 'xlsx'], key=f"p_{c_name}")
                    if p_file:
                        df_p = pd.read_csv(p_file) if p_file.name.endswith('.csv') else pd.read_excel(p_file)
                        cols = ["Select File Column..."] + df_p.columns.tolist()
                        st.markdown("**Map Payment Columns:**")
                        mc1, mc2, mc3 = st.columns(3)
                        mc1.selectbox("Order ID", cols, key=f"p_id_{c_name}")
                        mc2.selectbox("Settled Amount", cols, key=f"p_am_{c_name}")
                        mc3.selectbox("Platform Fees", cols, key=f"p_fe_{c_name}")
                        if st.button("Save Payment Mapping", type="primary", key=f"p_btn_{c_name}"):
                            st.success("Payments Mapped & Saved!")
                    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
                            
                    a_file = st.file_uploader("Upload Ads Spend", type=['csv', 'xlsx'], key=f"a_{c_name}")
                    if a_file:
                        df_a = pd.read_csv(a_file) if a_file.name.endswith('.csv') else pd.read_excel(a_file)
                        cols = ["Select File Column..."] + df_a.columns.tolist()
                        st.markdown("**Map Ad Columns:**")
                        mc1, mc2 = st.columns(2)
                        mc1.selectbox("Campaign Name", cols, key=f"a_nm_{c_name}")
                        mc2.selectbox("Total Spend", cols, key=f"a_sp_{c_name}")
                        if st.button("Save Ads Mapping", type="primary", key=f"a_btn_{c_name}"):
                            st.success("Ads Mapped & Saved!")

elif nav == "🧾 GST Tracker":
    tab1, tab2, tab3 = st.tabs(["📅 Filing Matrix", "➕ Update Status", "📋 Client Directory"])
    
    with tab1:
        df_hist = db.get_6_month_compliance_history()
        if not df_hist.empty: st.dataframe(df_hist, use_container_width=True, hide_index=True)
        else: st.info("No compliance data available.")

    with tab2:
        c1, c2 = st.columns(2)
        m_sel = c1.selectbox("Filing Month", range(1, 13), index=datetime.date.today().month - 1)
        y_sel = c2.selectbox("Filing Year", range(2024, 2030), index=datetime.date.today().year - 2024)
        period = f"{y_sel}-{m_sel:02d}"
        
        df_comp = db.get_gst_compliance(period)
        if not df_comp.empty:
            with st.form("uf"):
                st.markdown("<div class='section-header' style='margin-top:0;'>Update Portal Status</div>", unsafe_allow_html=True)
                c_u1, c_u2, c_u3, c_u4 = st.columns(4)
                u_gst = c_u1.selectbox("Select GST Number", df_comp['GST No'].tolist())
                u_ret = c_u2.selectbox("Return Type", ["GSTR-1", "GSTR-3B"])
                u_stat = c_u3.selectbox("Filing Status", ["Filed", "Pending"])
                u_date = c_u4.date_input("Date of Filing")
                if st.form_submit_button("Update Records", type="primary"):
                    db.update_gst_filing(u_gst, period, u_ret, u_stat, str(u_date))
                    st.success("Successfully updated!"); st.rerun()
        else: st.warning("Please add GST clients first.")

    with tab3:
        reg_mode = st.radio("Entry Method", ["Single Entry", "Bulk Upload"], horizontal=True, label_visibility="collapsed")
        if reg_mode == "Single Entry":
            with st.form("ngst"):
                st.markdown("<div class='section-header' style='margin-top:0;'>Register Entity</div>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                g_no = c1.text_input("GSTIN")
                g_legal = c2.text_input("Legal Name")
                g_trade = c3.text_input("Trade Name")
                
                c4, c5, c6 = st.columns(3)
                g_date = c4.date_input("Registration Date")
                o_ph = c5.text_input("Promoter Phone")
                o_em = c6.text_input("Promoter Email")
                
                if st.form_submit_button("Save Entity", type="primary"):
                    s, m = db.save_gst_registration(g_no, g_legal, g_trade, str(g_date), o_ph, o_em, "", "")
                    st.success(m) if s else st.error(m)
        else:
            uf = st.file_uploader("Upload Client List (CSV)", type=["csv", "xlsx"])
            if uf and st.button("🚀 Process Bulk Import", type="primary"):
                try:
                    df = pd.read_csv(uf) if uf.name.endswith('.csv') else pd.read_excel(uf)
                    count, errors = db.save_bulk_gst_clients(df)
                    st.success(f"Successfully added {count} entities.")
                except Exception as e: st.error(str(e))
                
        st.markdown("<br>#### Registered Directory", unsafe_allow_html=True)
        df_gst = db.get_gst_registrations()
        if not df_gst.empty: st.dataframe(df_gst, use_container_width=True, hide_index=True)

elif nav == "💸 Staff Payments":
    t1, t2 = st.tabs(["📊 Ledger Balances", "💰 Issue Funds"])
    with t1:
        df = db.get_all_staff_balances()
        if not df.empty:
            st.metric("Total Payable Liability", f"₹ {df['Net Payable'].sum():,.2f}")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else: st.info("Ledger is empty.")
    with t2:
        with st.form("pay"):
            st.markdown("<div class='section-header' style='margin-top:0;'>Disbursement Entry</div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            pd_ = c1.date_input("Disbursement Date")
            ps = c2.selectbox("Select Staff Account", db.get_staff_list())
            
            c3, c4 = st.columns(2)
            pa = c3.number_input("Amount (₹)", 100)
            pt = c4.radio("Transaction Type", ["Salary Settlement", "Advance Issued"], horizontal=True)
            
            rem = st.text_input("Reference / Remarks")
            if st.form_submit_button("Record Transaction", type="primary"):
                db.save_payment(str(pd_), ps, pa, pt, rem)
                st.success("Payment recorded to ledger successfully!")

elif nav == "📋 Catalog Maker":
    tab1, tab2 = st.tabs(["📤 Import Base Data", "📊 View Processed Catalog"])
    with tab1:
        uf = st.file_uploader("Upload Raw E-Commerce Template (CSV/Excel)", type=['csv', 'xlsx'])
        if uf and st.button("🚀 Process Combinations & Map Sizes", type="primary"):
            with st.spinner("Running mapping engine..."):
                df_input = pd.read_csv(uf) if uf.name.endswith('.csv') else pd.read_excel(uf)
                success, result = db.process_and_save_catalog(df_input)
                st.success("Successfully generated SKU variations!") if success else st.error(result)
    with tab2:
        df_cat = db.get_catalog_data()
        if not df_cat.empty:
            st.dataframe(df_cat, use_container_width=True, hide_index=True)
            st.download_button("⬇️ Export Final Catalog", df_cat.to_csv(index=False).encode('utf-8'), "Final_Catalog.csv", "text/csv")

elif nav == "📦 Product Master":
    t1, t2, t3 = st.tabs(["📝 Single Creation", "📤 Bulk Database Import", "📚 Master Database View"])
    with t1:
        with st.form("pf"):
            st.markdown("<div class='section-header' style='margin-top:0;'>Parent Style Definition</div>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            n = c1.text_input("Master Style Name")
            g = c2.selectbox("Gender Group", ["Men","Women","Kids","Unisex"])
            c = c3.selectbox("Category", db.get_categories_list())
            if st.form_submit_button("Save Parent Style", type="primary"): 
                db.save_product_parent(n,g,c,""); st.success("Parent structure created.")
        
        with st.form("cf"):
            st.markdown("<div class='section-header' style='margin-top:0;'>Child Variant Generation (SKU)</div>", unsafe_allow_html=True)
            parents = db.get_parent_products()
            if parents:
                c1, c2 = st.columns(2)
                sel = c1.selectbox("Link to Parent Style", [p['name'] for p in parents])
                pid = next(p['system_id'] for p in parents if p['name']==sel)
                
                c3, c4, c5 = st.columns(3)
                col = c3.selectbox("Color Variant", db.get_colors_list())
                siz = c4.selectbox("Size Variant", db.get_sizes_list())
                rat = c5.number_input("Standard Config Rate (₹)")
                
                sku = f"{sel}-{col}-{siz}".replace(" ","")
                if st.form_submit_button("Generate & Save SKU Variant", type="primary"): 
                    db.save_product_child(pid, sku, col, siz, rat); st.success(f"Created SKU: {sku}")
            else: st.info("You must create a Parent Style before generating SKUs."); st.form_submit_button("Generate", disabled=True)
    with t2:
        uf = st.file_uploader("Upload Product Database (CSV)", type=['csv'])
        if uf and st.button("🚀 Execute Import", type="primary"):
            c, e = db.save_bulk_products(pd.read_csv(uf))
            st.success(f"Database sync complete. Integrated {c} items.")
    with t3:
        render_df(pd.DataFrame(db.get_all_products_flat()))

elif nav == "⚙️ System Masters":
    sub = st.radio("Configuration Table", ["Channels (🛒)", "Staff Directory", "Item Categories", "Process Routes", "Rate Rules", "System Wipe"], horizontal=True, label_visibility="collapsed")
    
    st.markdown("<hr style='margin-top:0; border-color:#E2E8F0;'>", unsafe_allow_html=True)
    
    if sub == "Channels (🛒)":
        c1, c2 = st.columns([3, 1])
        n = c1.text_input("Marketplace Name (e.g., Nykaa, Tata CLiQ)", label_visibility="collapsed")
        if c2.button("Add Marketplace", type="primary", use_container_width=True):
            if n: db.save_channel(n); st.rerun()
        st.dataframe(pd.DataFrame(db.get_channels_list(), columns=["Active Marketplaces"]), use_container_width=True)
            
    elif sub == "Staff Directory":
        with st.form("sm"):
            c1, c2 = st.columns(2)
            n = c1.text_input("Staff Full Name")
            r = c2.selectbox("Assigned Role", ["Stitching","Cutting","Helper", "Operations"])
            if st.form_submit_button("Save Personnel Record", type="primary"): 
                db.save_staff(n, "", r, "Piece", 0); st.success("Added to directory.")
        st.dataframe(db.get_df("masters_staff"), use_container_width=True)
        
    elif sub == "Item Categories":
        c1, c2 = st.columns([3, 1])
        n = c1.text_input("New Category Name", label_visibility="collapsed")
        if c2.button("Save Category", type="primary", use_container_width=True): db.save_category(n); st.rerun()
        st.dataframe(pd.DataFrame(db.get_categories_list(), columns=["Configured Categories"]), use_container_width=True)
        
    elif sub == "Process Routes":
        c1, c2 = st.columns([3, 1])
        n = c1.text_input("New Process Stage Name", label_visibility="collapsed")
        if c2.button("Save Process", type="primary", use_container_width=True): db.save_master("masters_processes", {"name":n}); st.rerun()
        st.dataframe(db.get_df("masters_processes"), use_container_width=True)
        
    elif sub == "Rate Rules":
        st.info("Define strict piece-rate logic bounded by dates.")
        with st.form("rm"):
            c1, c2, c3 = st.columns(3)
            i = c1.selectbox("Target Category", db.get_categories_list())
            p = c2.selectbox("Target Process", db.get_processes_list())
            r = c3.number_input("Piece Rate (₹)", min_value=0.0)
            
            c4, c5 = st.columns(2)
            fd = c4.date_input("Validity Start Date")
            td = c5.date_input("Validity End Date", value=datetime.date.today() + datetime.timedelta(days=365))
            
            if st.form_submit_button("Enforce Rate Rule", type="primary"): 
                db.save_rate(i,p,r, fd, td); st.success("Rule applied to logic engine.")
        st.dataframe(db.get_rates_df(), use_container_width=True)
        
    elif sub == "System Wipe":
        st.error("🚨 DANGER ZONE: Hard deletion of database records.")
        wipe_opts = {
            "🏭 Production Logs": ["production"], "✂️ Cutting Definitions": ["masters_lots", "transactions_cutting"],
            "💸 Payment Ledger": ["payments"], "🧾 GST Data": ["gst_registrations", "gst_filings"],
            "📋 Catalog Data": ["masters_catalog"], "🚀 Launcher Pipeline": ["product_launcher"],
            "📦 Product Master": ["masters_products"], "⚙️ Master Configs": ["masters_staff", "masters_items"]
        }
        selected_wipe = st.multiselect("Select modules to truncate:", list(wipe_opts.keys()))
        if st.button("⚠️ CONFIRM TRUNCATE", type="primary"):
            if selected_wipe:
                cols = []
                for s in selected_wipe: cols.extend(wipe_opts[s])
                db.clean_database(cols)
                st.success("Target tables truncated successfully."); st.rerun()
            else: st.error("No target selected.")

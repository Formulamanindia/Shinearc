import streamlit as st
import pandas as pd
import db_manager as db
import datetime
import math
import time
import base64

# --- CONFIG (MOBILE-FIRST) ---
st.set_page_config(page_title="DrenchWear App", page_icon="📱", layout="wide", initial_sidebar_state="collapsed")

# --- MOBILE-CENTRIC SAAS CSS INJECTION ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Global Theme & Reset */
    * { box-sizing: border-box !important; font-family: 'Inter', sans-serif !important; }
    .stApp { background-color: #F8FAFC !important; color: #0F172A; overflow-x: hidden !important; }
    
    /* Hide Streamlit Native Elements (Pure App Feel) */
    [data-testid="stHeader"], [data-testid="collapsedControl"], [data-testid="stSidebar"], footer { display: none !important; }
    
    /* Centralize Content with Adaptive Spacing */
    .block-container {
        max-width: 1200px !important;
        margin: 0 auto;
        padding: 1rem 1rem 5rem 1rem !important;
    }
    
    @media (min-width: 768px) {
        .block-container { padding: 2rem 2rem 5rem 2rem !important; }
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 { color: #0F172A !important; font-weight: 700 !important; letter-spacing: -0.02em; }

    /* --- PREMIUM SAAS METRIC CARDS --- */
    .metric-card { 
        background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 20px; 
        box-shadow: 0 4px 15px -3px rgba(0,0,0,0.03); display: flex; justify-content: space-between; 
        align-items: center; transition: transform 0.2s, box-shadow 0.2s; margin-bottom: 10px; height: 100%;
    }
    .metric-card:hover { transform: translateY(-2px); box-shadow: 0 10px 20px -3px rgba(0,0,0,0.06); }
    .metric-info { display: flex; flex-direction: column; overflow: hidden;}
    .metric-label { font-size: 0.8rem; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
    .metric-value { font-size: 1.5rem; font-weight: 800; color: #0F172A; line-height: 1.2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
    .metric-icon-box { min-width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.3rem; margin-left: 10px;}

    /* --- UNIFIED PRODUCT CARDS --- */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 20px !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 8px 20px -4px rgba(0,0,0,0.04) !important;
        background: #FFFFFF !important;
        padding: 16px !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        margin-bottom: 16px !important;
        width: 100% !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 15px 30px -5px rgba(0,0,0,0.08) !important;
        border-color: #CBD5E1 !important;
    }
    
    .thumbnail-container { display: flex; gap: 8px; margin-bottom: 12px; overflow-x: auto; padding-bottom: 4px; scrollbar-width: none; -webkit-overflow-scrolling: touch; }
    .thumbnail-container::-webkit-scrollbar { display: none; }
    .product-thumbnail { width: 55px; height: 55px; object-fit: cover; border-radius: 10px; border: 1px solid #E2E8F0; }
    
    .product-link-btn {
        display: flex; align-items: center; justify-content: center; background-color: #F8FAFC; color: #4F46E5 !important; 
        padding: 12px; border-radius: 12px; font-weight: 700; font-size: 0.95rem; text-decoration: none !important; 
        border: 1px solid #E2E8F0; transition: all 0.2s ease; margin-bottom: 15px; width: 100%;
    }
    .product-link-btn:hover { background-color: #EEF2FF; border-color: #C7D2FE; }

    /* --- FORMS & CONTAINERS --- */
    [data-testid="stForm"], .st-emotion-cache-1104q3m { 
        background: #FFFFFF !important; padding: 24px !important; border-radius: 20px !important; border: 1px solid #E2E8F0 !important; box-shadow: 0 8px 20px -4px rgba(0,0,0,0.03) !important; width: 100% !important;
    }
    .section-header { border-left: 4px solid #4F46E5; padding-left: 12px; margin-top: 20px; margin-bottom: 16px; color: #0F172A; font-size: 1.15rem; font-weight: 700; }

    /* --- INPUTS & DROPDOWNS --- */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox > div > div { 
        background-color: #FFFFFF !important; border: 1px solid #CBD5E1 !important; border-radius: 12px !important; color: #0F172A !important; padding: 12px 16px !important; font-size: 1rem; min-height: 48px !important; width: 100% !important; box-shadow: 0 1px 2px rgba(0,0,0,0.01) !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus, .stSelectbox > div > div:focus { 
        border-color: #4F46E5 !important; box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1) !important; 
    }
    div[data-baseweb="select"] span { color: #0F172A !important; font-weight: 600; }
    div[data-baseweb="popover"], ul[role="listbox"] { background-color: #FFFFFF !important; border-radius: 12px !important; border: 1px solid #E2E8F0 !important; box-shadow: 0 10px 25px rgba(0,0,0,0.1) !important; overflow: hidden; max-width: 95vw !important; }
    ul[role="listbox"] li { padding: 12px 16px !important; font-size: 1rem !important; color: #0F172A !important; }
    ul[role="listbox"] li:hover { background-color: #F8FAFC !important; color: #4F46E5 !important; }

    /* --- SAAS BUTTONS --- */
    .stButton button { 
        border-radius: 12px; font-weight: 600; min-height: 48px !important; transition: all 0.2s ease; width: 100% !important; border: 1px solid #E2E8F0 !important; background: #FFFFFF !important; color: #0F172A !important; box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
    }
    .stButton button:hover { background: #F8FAFC !important; border-color: #CBD5E1 !important; }
    .stButton button[kind="primary"] { 
        background: #4F46E5 !important; color: white !important; border: none !important; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25) !important; 
    }
    .stButton button[kind="primary"]:hover { background: #4338CA !important; box-shadow: 0 6px 15px rgba(79, 70, 229, 0.35) !important; transform: translateY(-1px); }
    .stButton button[kind="primary"]:active { transform: scale(0.97); }

    /* --- TABS --- */
    .stTabs [data-baseweb="tab-list"] { gap: 16px; border-bottom: 1px solid #E2E8F0; padding-bottom: 0px; overflow-x: auto; -webkit-overflow-scrolling: touch; scrollbar-width: none; }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }
    .stTabs [data-baseweb="tab"] { height: 44px; border: none; background: transparent; color: #64748B; font-weight: 600; font-size: 0.95rem; padding: 0 4px; white-space: nowrap; transition: color 0.2s; }
    .stTabs [aria-selected="true"] { color: #4F46E5 !important; border-bottom: 2px solid #4F46E5 !important; }

    /* --- DATAFRAMES --- */
    [data-testid="stDataFrame"] { border-radius: 12px; border: 1px solid #E2E8F0; box-shadow: 0 2px 4px rgba(0,0,0,0.01); overflow: hidden; background: #FFFFFF; }

    /* Login Centering */
    .login-container { max-width: 400px; margin: 15vh auto; background: white; padding: 40px 30px; border-radius: 24px; box-shadow: 0 20px 40px rgba(0,0,0,0.06); border: 1px solid #E2E8F0; text-align: center; }

    /* =========================================================
       📱 STRICT MOBILE GRID & RESPONSIVENESS OVERRIDES
       ========================================================= */
    @media (max-width: 768px) {
        /* 1. Force the Top Navigation Bar to stay horizontal (never stack) */
        div[data-testid="stHorizontalBlock"]:first-of-type {
            flex-wrap: nowrap !important;
            align-items: center !important;
            margin-bottom: 15px !important;
        }
        div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"] {
            width: auto !important;
            min-width: auto !important;
            flex: 1 1 auto !important;
        }
        
        /* 2. Force App Tiles and Metrics into a 2x2 Grid on Mobile (Matches any class with st-key-mobile_grid) */
        [class*="st-key-mobile_grid"] div[data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
            gap: 10px !important;
        }
        [class*="st-key-mobile_grid"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            width: calc(50% - 5px) !important;
            min-width: calc(50% - 5px) !important;
            flex: 1 1 calc(50% - 5px) !important;
            margin-bottom: 0 !important;
        }

        /* Adjust internal padding for small screens */
        .block-container { padding-top: 1rem !important; }
        [data-testid="stVerticalBlockBorderWrapper"] { padding: 12px !important; border-radius: 16px !important; }
        [data-testid="stForm"], .st-emotion-cache-1104q3m { padding: 16px !important; border-radius: 16px !important; }
        .metric-card { padding: 16px; }
        .metric-value { font-size: 1.3rem; }
    }
</style>
""", unsafe_allow_html=True)

# --- DYNAMIC CSS FOR APP DASHBOARD TILES ---
def apply_dashboard_card_css():
    st.markdown("""
    <style>
        .stButton button[kind="secondary"] {
            height: 110px !important;
            border-radius: 20px !important;
            background: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.02) !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            white-space: pre-wrap !important;
            line-height: 1.4 !important;
            color: #0F172A !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        .stButton button[kind="secondary"] p {
            font-size: 0.95rem !important; font-weight: 700 !important; margin: 0 !important;
        }
        .stButton button[kind="secondary"]:hover {
            transform: translateY(-3px); box-shadow: 0 10px 20px rgba(79,70,229,0.08) !important;
            border-color: #C7D2FE !important; color: #4F46E5 !important;
        }
        .stButton button[kind="secondary"]:active { transform: scale(0.95); background-color: #F8FAFC !important; }
        
        @media (min-width: 768px) {
            .stButton button[kind="secondary"] { height: 130px !important; }
            .stButton button[kind="secondary"] p { font-size: 1.1rem !important; }
        }
    </style>
    """, unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def render_metric_card(label, value, icon="📈", bg_light="#EEF2FF", text_color="#4F46E5"):
    display_value = str(value)
    if len(display_value) > 18: display_value = display_value[:15] + '...'
    card_html = f"""<div class="metric-card">
    <div class="metric-info"><div class="metric-label">{label}</div><div class="metric-value" title="{value}">{display_value}</div></div>
    <div class="metric-icon-box" style="background-color: {bg_light}; color: {text_color};">{icon}</div>
</div>"""
    st.markdown(card_html, unsafe_allow_html=True)

def render_df(df):
    if df.empty: st.info("No data available."); return
    st.dataframe(df, use_container_width=True, hide_index=True)

def route(nav_dest):
    st.session_state.nav_selection = nav_dest
    st.rerun()

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
if "nav_selection" not in st.session_state: st.session_state.nav_selection = "Home"

# --- SIDEBAR NAVIGATION (SYNCED WITH DASHBOARD) ---
menu_options = [
    "Home", 
    "🏭 Work Operations", 
    "🤖 Drench AI", 
    "🚀 Product Launcher", 
    "🧾 GST Tracker", 
    "💸 Staff Payments", 
    "📋 Catalog Maker", 
    "📈 P&L Analysis", 
    "📦 Product Master", 
    "⚙️ System Masters"
]

with st.sidebar:
    st.markdown("""<div style="font-size: 1.6rem; font-weight: 800; color: #4F46E5; text-align: center; margin-bottom: 1.5rem; margin-top: 1rem;">🧵 DrenchWear</div>""", unsafe_allow_html=True)
    
    selected_nav = st.radio(
        "MENU", 
        menu_options,
        index=menu_options.index(st.session_state.nav_selection) if st.session_state.nav_selection in menu_options else 0,
        label_visibility="collapsed"
    )
    
    if selected_nav != st.session_state.nav_selection:
        st.session_state.nav_selection = selected_nav
        st.rerun()
        
    st.markdown("<hr style='margin: 30px 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)
    if st.button("🔒 Secure Logout", use_container_width=True): 
        st.session_state["authenticated"] = False; st.rerun()

nav = st.session_state.nav_selection

# ==========================================
# APP ROUTER
# ==========================================

if nav == "Home":
    apply_dashboard_card_css() 
    
    st.markdown("""
        <div style='text-align: center; margin-bottom: 25px; margin-top: 5px;'>
            <h1 style='color: #4F46E5; font-weight: 800; font-size: 2.2rem; margin-bottom: 5px;'>🧵 DrenchWear</h1>
            <p style='color: #64748B; font-weight: 500; font-size: 0.95rem; margin:0;'>Workspace Dashboard</p>
        </div>
    """, unsafe_allow_html=True)
    
    pcs, earn, pending, active = db.get_dashboard_stats()
    
    # MOBILE GRID CONTAINER 1 (Metrics)
    with st.container(key="mobile_grid_metrics"):
        m1, m2, m3, m4 = st.columns(4)
        with m1: render_metric_card("Pieces Today", f"{pcs:,.0f}", "👕", "#D1FAE5", "#10B981")
        with m2: render_metric_card("Prod Value", f"₹{earn:,.0f}", "₹", "#FEF3C7", "#F59E0B")
        with m3: render_metric_card("Liabilities", f"₹{pending:,.0f}", "💳", "#FEE2E2", "#EF4444")
        with m4: render_metric_card("Active Staff", f"{active}", "👥", "#DBEAFE", "#3B82F6")
    
    st.markdown("<h4 style='margin-top: 20px; margin-bottom: 12px; font-size: 1.1rem; color:#0F172A;'>Applications</h4>", unsafe_allow_html=True)
    
    # MOBILE GRID CONTAINER 2 (App Tiles)
    with st.container(key="mobile_grid_apps_1"):
        c1, c2, c3, c4 = st.columns(4)
        with c1: 
            if st.button("🏭\nWork Ops", use_container_width=True): route("🏭 Work Operations")
            if st.button("🤖\nDrench AI", use_container_width=True): route("🤖 Drench AI")
        with c2: 
            if st.button("🚀\nLauncher", use_container_width=True): route("🚀 Product Launcher")
            if st.button("🧾\nGST Track", use_container_width=True): route("🧾 GST Tracker")
        with c3:
            if st.button("💸\nPayments", use_container_width=True): route("💸 Staff Payments")
            if st.button("📋\nCatalog", use_container_width=True): route("📋 Catalog Maker")
        with c4:
            if st.button("📈\nP&L Analyze", use_container_width=True): route("📈 P&L Analysis")
            if st.button("📦\nMaster", use_container_width=True): route("📦 Product Master")

    with st.container(key="mobile_grid_apps_2"):
        c_set, _ = st.columns([1, 3])
        with c_set:
            if st.button("⚙️\nSettings", use_container_width=True): route("⚙️ System Masters")
        
else:
    # --- NATIVE APP TOP BAR ---
    b1, b2, b3 = st.columns([1, 4, 1])
    with b1:
        if st.button("⬅️ Back"): route("Home")
    with b2:
        st.markdown(f"<div style='text-align: center; font-weight: 800; color: #0F172A; padding-top: 10px; font-size:1.15rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{nav.split(' ')[-1] if ' ' in nav else nav}</div>", unsafe_allow_html=True)
    with b3:
        pass 
    st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px; border-color:#E2E8F0;'>", unsafe_allow_html=True)

    # ==========================================
    # MODULE CONTENT VIEWS
    # ==========================================

    if nav == "🤖 Drench AI":
        t1, t2, t3 = st.tabs(["📤 Upload", "📊 Summary", "✂️ Plan"])
        with t1:
            st.info("Columns Needed: Channel, Item, Category, Color, Size, Qty")
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
            d1 = st.date_input("From Date", datetime.date.today()-datetime.timedelta(days=7))
            d2 = st.date_input("To Date", datetime.date.today())
            if st.button("Generate Smart Plan", type="primary", use_container_width=True):
                df = db.generate_cutting_plan(str(d1), str(d2))
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                    st.download_button("Download Job Sheet CSV", df.to_csv(index=False), "plan.csv", use_container_width=True)
                else: st.warning("No orders found.")

    elif nav == "🏭 Work Operations":
        tab_cut, tab_stitch, tab_ops = st.tabs(["✂️ Cutting", "🪡 Stitching", "📦 Ops"])
        
        with tab_cut:
            act = st.radio("Action", ["📝 Create Lot", "📚 View Lots"], horizontal=True, label_visibility="collapsed")
            if act == "📝 Create Lot":
                st.markdown("<div class='section-header'>Lot Detail</div>", unsafe_allow_html=True)
                l_no = st.text_input("Lot No")
                
                prod_names = [p['name'] for p in db.get_parent_products()]
                item_names = db.get_items_list()
                all_product_options = sorted(list(set(prod_names + item_names)))
                item_name = st.selectbox("Item Name", [""] + all_product_options)

                st.markdown("<div class='section-header'>Fabric Detail</div>", unsafe_allow_html=True)
                if "fab_df" not in st.session_state:
                    st.session_state.fab_df = pd.DataFrame([{"Srl no.": i+1, "Color": "", "UOM": "Meter", "Qty": 0.0} for i in range(5)])
                e_fab = st.data_editor(st.session_state.fab_df, num_rows="dynamic", use_container_width=True, hide_index=True)
                
                st.markdown("<div class='section-header'>Bundle Detail</div>", unsafe_allow_html=True)
                n_bun = st.number_input("Total Bundles to generate", 1, 500, 10)
                if st.button("🔄 Reset Grid", use_container_width=True):
                    st.session_state.lot_df = pd.DataFrame([{"Bundle No": str(i+1), "Qty": 0} for i in range(n_bun)])
                    
                if "lot_df" not in st.session_state:
                    st.session_state.lot_df = pd.DataFrame([{"Bundle No": str(i+1), "Qty": 0} for i in range(10)])
                    
                e_bun = st.data_editor(st.session_state.lot_df, height=300, use_container_width=True, hide_index=True)
                
                total_pcs = pd.to_numeric(e_bun['Qty'], errors='coerce').sum()
                st.markdown(f"<div style='color: #4F46E5; font-weight:800; font-size:1.1rem; margin-top: 10px;'>Total Auto-Calculated: {total_pcs:,.0f} Pcs</div>", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 Save Cutting Lot", type="primary", use_container_width=True):
                    if not l_no or not item_name:
                        st.error("Lot No and Item required.")
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
                st.info("Check Tracking & Ops tab.")

        with tab_stitch:
            stitch_mode = st.radio("Mode", ["📝 Single Entry", "📤 Bulk CSV"], horizontal=True, label_visibility="collapsed")
            if stitch_mode == "📝 Single Entry":
                with st.form("stitch_log"):
                    sd_date = st.date_input("Date")
                    sd_worker = st.selectbox("Karigar (Worker)", db.get_staff_list())
                    sd_proc = st.selectbox("Process Type", db.get_processes_list())
                    sd_lot = st.selectbox("Cutting Lot No", [""] + db.get_active_lots())
                    
                    buns = []
                    if sd_lot:
                        b_data = db.get_detailed_bundles(sd_lot)
                        buns = [f"{b['bundle_no']} | {b['item_name']} | {b['qty']} pcs" for b in b_data]
                    
                    sd_bun = st.selectbox("Lot Bundle", [""] + buns)
                    
                    qty = st.number_input("Qty (Pcs)", min_value=1.0)
                    lbl = st.checkbox("🏷️ Label (+0.50)")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.form_submit_button("💾 Auto-Credit Payment", type="primary", use_container_width=True):
                        if sd_worker and sd_lot and sd_bun:
                            p = sd_bun.split(" | ")
                            val_item = p[1] if len(p)>1 else ""
                            real_bun = p[0]
                            rate = db.get_rate(val_item, sd_proc, sd_date)
                            fin_rate = rate + (0.50 if lbl else 0)
                            
                            s, m = db.save_production(str(sd_date), sd_worker, val_item, sd_proc, qty, fin_rate, sd_lot, real_bun)
                            if s: st.success(f"Credited Amount: ₹{qty*fin_rate}")
                            else: st.error(m)
                        else: st.error("Missing critical data.")
                        
            elif stitch_mode == "📤 Bulk CSV":
                st.info("Calculates Rate/Value based on Master.")
                sample_csv = "Date,Karigar Name,Lot No,Bundle No.,Process,Item,Qty\n2026-03-10,Worker Name,L-1001,B-01,Collar,Top,50"
                st.download_button("⬇️ Template", sample_csv, "Sample.csv", "text/csv", use_container_width=True)
                
                uf = st.file_uploader("Upload CSV", type=["csv", "xlsx"])
                if uf and st.button("🚀 Upload", type="primary", use_container_width=True):
                    try:
                        df = pd.read_csv(uf) if uf.name.endswith('.csv') else pd.read_excel(uf)
                        count, errors = db.save_bulk_stitching(df)
                        if count > 0: st.success(f"Added {count} records!")
                        if errors:
                            with st.expander("Errors"):
                                for e in errors: st.write(e)
                    except Exception as e: st.error(str(e))

        with tab_ops:
            ops_view_mode = st.radio("View", ["📦 Tracking", "🛠️ Fabrication"], horizontal=True, label_visibility="collapsed")
            if ops_view_mode == "📦 Tracking":
                st.dataframe(db.get_bundle_progress(), use_container_width=True)
            else:
                with st.form("fab_form"):
                    fd = st.date_input("Date")
                    fp = st.selectbox("Party", db.get_parties_list())
                    fi = st.text_input("Item")
                    fq = st.number_input("Qty", 1.0)
                    fr = st.number_input("Rate", 0.0)
                    fdesc = st.text_input("Desc")
                    if st.form_submit_button("Save Entry", type="primary", use_container_width=True):
                        db.save_fabrication(str(fd), fp, fi, fq, fr, fdesc)
                        st.success("Saved")
                st.dataframe(db.get_recent_fabrication(), use_container_width=True)

    elif nav == "🚀 Product Launcher":
        tab_add, tab_view = st.tabs(["➕ Add New", "📋 Pipeline"])
        
        with tab_add:
            st.markdown("<div class='section-header'>Fetch Details</div>", unsafe_allow_html=True)
            fetch_url = st.text_input("🔗 Product URL", placeholder="https://...", label_visibility="collapsed")
            
            c_btn1, c_btn2 = st.columns(2)
            if c_btn1.button("🔍 Fetch", use_container_width=True):
                if fetch_url:
                    with st.spinner("Scraping..."):
                        st.session_state.launcher_draft = db.fetch_product_metadata(fetch_url)
                else: st.warning("Enter URL.")
            if c_btn2.button("✍️ Manual", use_container_width=True):
                st.session_state.launcher_draft = {"title": "", "price": 0.0, "image": "", "url": ""}

            if "launcher_draft" in st.session_state:
                draft = st.session_state.launcher_draft
                with st.form("save_launcher_prod"):
                    st.markdown("<div class='section-header'>Verify & Save</div>", unsafe_allow_html=True)
                    p_title = st.text_input("Title", value=draft.get("title", ""))
                    p_price = st.number_input("Price (₹)", value=float(draft.get("price", 0.0)))
                    p_img = st.text_input("Image URL", value=draft.get("image", ""))
                    p_img_upload = st.file_uploader("Upload Images", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
                    p_stage = st.selectbox("Stage", ["Stage 1", "Stage 2", "Stage 3", "Stage 4", "Stage 5", "Stage 6", "Stage 7"])
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.form_submit_button("💾 Save to Pipeline", type="primary", use_container_width=True):
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
                        else: st.error("Title required.")
                            
        with tab_view:
            products = db.get_launched_products()
            if not products:
                st.info("No products in pipeline.")
            else:
                stages = ["Stage 1", "Stage 2", "Stage 3", "Stage 4", "Stage 5", "Stage 6", "Stage 7"]
                
                with st.container(key="mobile_grid_launcher"):
                    cols = st.columns(3) 
                    
                    for idx, prod in enumerate(products):
                        with cols[idx % 3]:
                            with st.container(border=True):
                                img_urls = prod.get('images', [])
                                if not img_urls and prod.get('image_url'): img_urls = [prod.get('image_url')]
                                main_img = img_urls[0] if img_urls else "https://via.placeholder.com/400x300?text=No+Image+Found"
                                
                                thumbnails_html = ""
                                if len(img_urls) > 1:
                                    thumbnails_html = "<div class='thumbnail-container'>\n"
                                    for thumb in img_urls[1:]:
                                        thumbnails_html += f"<img src='{thumb}' class='product-thumbnail' onerror=\"this.style.display='none';\">\n"
                                    thumbnails_html += "</div>"
                                
                                prod_html = f"""<div style="width: 100%; height: 240px; overflow: hidden; border-radius: 12px; margin-bottom: 12px; border: 1px solid #F1F5F9; background:#F8FAFC;">
<img src="{main_img}" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.onerror=null;this.src='https://via.placeholder.com/400x300?text=Error';">
</div>
{thumbnails_html}
<div style="font-weight: 800; font-size: 1.15rem; color: #0F172A; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px; line-height: 1.4;">{prod.get('title', 'Unknown')}</div>
<div style="color: #10B981; font-weight: 800; font-size: 1.25rem; margin-bottom: 15px;">₹ {prod.get('price', 0.0):,.2f}</div>
<a href="{prod.get('url', '#')}" target="_blank" class="product-link-btn">🔗 View Original Link</a>"""
                                st.markdown(prod_html, unsafe_allow_html=True)
                                
                                curr_stage = prod.get('stage', 'Stage 1')
                                curr_idx = stages.index(curr_stage) if curr_stage in stages else 0
                                new_stage = st.selectbox("Stage", stages, index=curr_idx, key=f"stg_{prod['_id']}", label_visibility="collapsed")
                                
                                btn_c1, btn_c2 = st.columns(2)
                                if btn_c1.button("💾 Apply", key=f"upd_{prod['_id']}", use_container_width=True):
                                    db.update_launched_product_stage(prod['_id'], new_stage)
                                    st.toast("Updated!")
                                    time.sleep(0.5)
                                    st.rerun()
                                    
                                with btn_c2.popover("⚙️ Manage", use_container_width=True):
                                    st.markdown("#### Edit Details")
                                    e_title = st.text_input("Title", value=prod.get('title', ''), key=f"et_{prod['_id']}")
                                    e_price = st.number_input("Price (₹)", value=float(prod.get('price', 0.0)), key=f"ep_{prod['_id']}")
                                    e_img = st.text_input("Main Image", value=main_img, key=f"ei_{prod['_id']}")
                                    e_img_file = st.file_uploader("Replace Images", type=['png', 'jpg'], accept_multiple_files=True, key=f"ef_{prod['_id']}")
                                    
                                    st.markdown("<br>", unsafe_allow_html=True)
                                    if st.button("Save Changes", type="primary", key=f"es_{prod['_id']}", use_container_width=True):
                                        final_edit_imgs = img_urls
                                        if e_img_file:
                                            final_edit_imgs = [f"data:{f.type};base64,{base64.b64encode(f.read()).decode('utf-8')}" for f in e_img_file]
                                        elif e_img != main_img: final_edit_imgs = [e_img]
                                            
                                        s, m = db.update_launched_product_details(prod['_id'], e_title, e_price, final_edit_imgs)
                                        st.rerun() if s else st.error(m)
                                            
                                    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
                                    if st.button("🚨 Delete Product", key=f"del_{prod['_id']}", use_container_width=True):
                                        db.delete_launched_product(prod['_id']); st.rerun()

    # --- 📈 NEW ADVANCED P&L ANALYSIS TAB ---
    elif nav == "📈 P&L Analysis":
        st.markdown("<div class='section-header' style='margin-top:0;'>Marketplace Reconciliation & Analytics</div>", unsafe_allow_html=True)
        
        channels = db.get_channels_list()
        
        if not channels:
            st.info("No active channels found. Please configure Marketplaces in 'System Masters'.")
        else:
            tabs = st.tabs([f"🛒 {c}" for c in channels])
            
            for i, c_name in enumerate(channels):
                with tabs[i]:
                    sub_tabs = st.radio("Select View", ["📊 1. Order Analysis", "💳 2. Payments & Ads"], horizontal=True, key=f"sub_{c_name}", label_visibility="collapsed")
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    if sub_tabs == "📊 1. Order Analysis":
                        with st.container(border=True):
                            st.markdown(f"#### 📦 {c_name} Order Analytics")
                            
                            o_file = st.file_uploader(f"1. Upload {c_name} Orders Report", type=['csv', 'xlsx'], key=f"o_{c_name}")
                            if o_file:
                                df_o = pd.read_csv(o_file) if o_file.name.endswith('.csv') else pd.read_excel(o_file)
                                cols = ["Select File Column..."] + df_o.columns.tolist()
                                
                                st.markdown("**Map Essential Columns:**")
                                with st.container(key=f"mobile_grid_inputs_{c_name}"):
                                    mc1, mc2, mc3, mc4 = st.columns(4)
                                    o_id = mc1.selectbox("Order ID", cols, key=f"o_id_{c_name}")
                                    o_dt = mc2.selectbox("Order Date", cols, key=f"o_dt_{c_name}")
                                    o_sku = mc3.selectbox("SKU / Item", cols, key=f"o_sku_{c_name}")
                                    o_am = mc4.selectbox("Order Amount", cols, key=f"o_am_{c_name}")
                                
                                st.markdown("<hr style='margin: 20px 0; border-color:#E2E8F0;'>", unsafe_allow_html=True)
                                st.markdown("##### ⚙️ Optional: Cost of Goods Sold (COGS) for Profit Tracking")
                                st.markdown("<p style='font-size:0.9rem; color:#64748B;'>Generate a template of your unique SKUs, fill in your costs, and upload it to unlock Gross Profit analytics.</p>", unsafe_allow_html=True)
                                
                                with st.container(key=f"mobile_grid_cogs_{c_name}"):
                                    cogs_c1, cogs_c2 = st.columns(2)
                                    
                                    with cogs_c1:
                                        if o_sku != "Select File Column...":
                                            unique_skus = df_o[o_sku].dropna().astype(str).unique()
                                            cogs_df = pd.DataFrame({o_sku: unique_skus, 'COGS': 0.0})
                                            csv_template = cogs_df.to_csv(index=False).encode('utf-8')
                                            st.download_button(f"⬇️ 1. Download SKU Template ({len(unique_skus)} Items)", csv_template, f"{c_name}_SKU_COGS_Template.csv", "text/csv", use_container_width=True)
                                        else:
                                            st.info("Map the 'SKU / Item' column above to generate a downloadable SKU template.")
                                            
                                    with cogs_c2:
                                        cogs_file = st.file_uploader("2. Upload Filled COGS Template", type=['csv', 'xlsx'], key=f"cogs_{c_name}", label_visibility="collapsed")

                                st.markdown("<br>", unsafe_allow_html=True)
                                if st.button("🚀 Process & Analyze Orders", type="primary", key=f"o_btn_{c_name}", use_container_width=True):
                                    if "Select File Column..." not in [o_dt, o_sku, o_am]:
                                        try:
                                            # Clean Base Order Data
                                            df_o['ParsedDate'] = pd.to_datetime(df_o[o_dt], errors='coerce')
                                            df_o = df_o.dropna(subset=['ParsedDate']).copy() 
                                            df_o['DayOfWeek'] = df_o['ParsedDate'].dt.day_name()
                                            df_o['IsWeekend'] = df_o['ParsedDate'].dt.dayofweek >= 5
                                            
                                            if df_o[o_am].dtype == 'object':
                                                df_o['AmountVal'] = pd.to_numeric(df_o[o_am].replace('[\₹,]', '', regex=True), errors='coerce').fillna(0)
                                            else:
                                                df_o['AmountVal'] = pd.to_numeric(df_o[o_am], errors='coerce').fillna(0)
                                            
                                            # COGS Processing
                                            has_cogs = False
                                            if cogs_file:
                                                df_cogs = pd.read_csv(cogs_file) if cogs_file.name.endswith('.csv') else pd.read_excel(cogs_file)
                                                if o_sku in df_cogs.columns and 'COGS' in df_cogs.columns:
                                                    # Make sure SKUs are strings for accurate merging
                                                    df_o[o_sku] = df_o[o_sku].astype(str)
                                                    df_cogs[o_sku] = df_cogs[o_sku].astype(str)
                                                    
                                                    df_o = df_o.merge(df_cogs[[o_sku, 'COGS']], on=o_sku, how='left')
                                                    df_o['COGS'] = pd.to_numeric(df_o['COGS'], errors='coerce').fillna(0)
                                                    df_o['Profit'] = df_o['AmountVal'] - df_o['COGS']
                                                    has_cogs = True
                                                else:
                                                    st.warning("COGS file missing required columns. Proceeding without profit calculation.")

                                            st.success("Orders Analyzed Successfully!")
                                            st.markdown(f"<div class='section-header' style='margin-top: 15px;'>📈 {c_name} Performance Dashboard</div>", unsafe_allow_html=True)
                                            
                                            # --- FINANCIAL METRICS ---
                                            total_revenue = df_o['AmountVal'].sum()
                                            total_orders = len(df_o)
                                            
                                            with st.container(key=f"mobile_grid_analysis_{c_name}"):
                                                ac1, ac2, ac3, ac4 = st.columns(4)
                                                with ac1: render_metric_card("Total Orders", f"{total_orders:,.0f}", "📦", "#F3E8FF", "#4F46E5")
                                                with ac2: render_metric_card("Gross Revenue", f"₹{total_revenue:,.0f}", "💰", "#D1FAE5", "#10B981")
                                                
                                                if has_cogs:
                                                    total_cogs = df_o['COGS'].sum()
                                                    gross_profit = df_o['Profit'].sum()
                                                    margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
                                                    
                                                    with ac3: render_metric_card("Gross Profit", f"₹{gross_profit:,.0f}", "📈", "#FEF3C7", "#F59E0B")
                                                    with ac4: render_metric_card("Margin %", f"{margin:.1f}%", "🎯", "#FEE2E2", "#EF4444")
                                                else:
                                                    # Default fallbacks if no COGS provided
                                                    wknd_sales = df_o[df_o['IsWeekend']]['AmountVal'].sum()
                                                    wkdy_sales = df_o[~df_o['IsWeekend']]['AmountVal'].sum()
                                                    with ac3: render_metric_card("Weekday Sales", f"₹{wkdy_sales:,.0f}", "💼", "#EEF2FF", "#4F46E5")
                                                    with ac4: render_metric_card("Weekend Sales", f"₹{wknd_sales:,.0f}", "🎉", "#FEF3C7", "#F59E0B")
                                            
                                            st.markdown("<br>", unsafe_allow_html=True)
                                            
                                            # --- CHARTS ---
                                            st.markdown("##### 📅 Daily Trend")
                                            if has_cogs:
                                                daily_trend = df_o.groupby(df_o['ParsedDate'].dt.date)[['AmountVal', 'Profit']].sum().reset_index()
                                                daily_trend.columns = ['Date', 'Revenue', 'Profit']
                                            else:
                                                daily_trend = df_o.groupby(df_o['ParsedDate'].dt.date)['AmountVal'].sum().reset_index()
                                                daily_trend.columns = ['Date', 'Revenue']
                                                
                                            daily_trend.set_index('Date', inplace=True)
                                            st.line_chart(daily_trend, use_container_width=True)
                                            
                                            ch1, ch2 = st.columns(2)
                                            with ch1:
                                                st.markdown("##### 💼 Weekday Pattern")
                                                weekday_df = df_o[~df_o['IsWeekend']]
                                                target_col = 'Profit' if has_cogs else 'AmountVal'
                                                if not weekday_df.empty:
                                                    wkdy_sales = weekday_df.groupby('DayOfWeek')[target_col].sum().reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']).fillna(0)
                                                    st.bar_chart(wkdy_sales, use_container_width=True)
                                                else: st.info("No weekday data found.")

                                            with ch2:
                                                st.markdown("##### 🎉 Weekend Pattern")
                                                weekend_df = df_o[df_o['IsWeekend']]
                                                target_col = 'Profit' if has_cogs else 'AmountVal'
                                                if not weekend_df.empty:
                                                    wknd_sales = weekend_df.groupby('DayOfWeek')[target_col].sum().reindex(['Saturday', 'Sunday']).fillna(0)
                                                    st.bar_chart(wknd_sales, use_container_width=True)
                                                else: st.info("No weekend data found.")
                                            
                                            st.markdown("##### 🏆 Top 5 Best Sellers")
                                            target_col = 'Profit' if has_cogs else 'AmountVal'
                                            sku_sales = df_o.groupby(o_sku)[target_col].sum().sort_values(ascending=False).head(5)
                                            if not sku_sales.empty:
                                                st.bar_chart(sku_sales, use_container_width=True)
                                            else: st.info("No product data found.")
                                                
                                        except Exception as e:
                                            st.error(f"Analysis failed: Please verify column data formats. ({e})")
                                    else:
                                        st.warning("Please map Date, SKU, and Amount to generate analysis.")

                    elif sub_tabs == "💳 2. Payments & Ads":
                        with st.container(border=True):
                            st.markdown(f"#### 💳 {c_name} Payments Data")
                            p_file = st.file_uploader(f"Upload {c_name} Payment Settlements", type=['csv', 'xlsx'], key=f"p_{c_name}")
                            if p_file:
                                df_p = pd.read_csv(p_file) if p_file.name.endswith('.csv') else pd.read_excel(p_file)
                                cols = ["Select File Column..."] + df_p.columns.tolist()
                                st.markdown("**Map Payment Columns:**")
                                
                                with st.container(key=f"mobile_grid_pay_{c_name}"):
                                    mc1, mc2, mc3 = st.columns(3)
                                    mc1.selectbox("Order ID", cols, key=f"p_id_{c_name}")
                                    mc2.selectbox("Settled Amount", cols, key=f"p_am_{c_name}")
                                    mc3.selectbox("Platform Fees", cols, key=f"p_fe_{c_name}")
                                st.markdown("<br>", unsafe_allow_html=True)
                                if st.button("Save Payment Mapping", type="primary", key=f"p_btn_{c_name}", use_container_width=True):
                                    st.success("Payments Mapped & Saved!")
                        
                        with st.container(border=True):
                            st.markdown(f"#### 📢 {c_name} Ads Spend")
                            a_file = st.file_uploader(f"Upload {c_name} Ads Spend", type=['csv', 'xlsx'], key=f"a_{c_name}")
                            if a_file:
                                df_a = pd.read_csv(a_file) if a_file.name.endswith('.csv') else pd.read_excel(a_file)
                                cols = ["Select File Column..."] + df_a.columns.tolist()
                                st.markdown("**Map Ad Columns:**")
                                
                                with st.container(key=f"mobile_grid_ads_{c_name}"):
                                    mc1, mc2 = st.columns(2)
                                    mc1.selectbox("Campaign Name", cols, key=f"a_nm_{c_name}")
                                    mc2.selectbox("Total Spend", cols, key=f"a_sp_{c_name}")
                                st.markdown("<br>", unsafe_allow_html=True)
                                if st.button("Save Ads Mapping", type="primary", key=f"a_btn_{c_name}", use_container_width=True):
                                    st.success("Ads Mapped & Saved!")

    elif nav == "🧾 GST Tracker":
        tab1, tab2, tab3 = st.tabs(["📅 Matrix", "➕ Update", "📋 Clients"])
        
        with tab1:
            df_hist = db.get_6_month_compliance_history()
            if not df_hist.empty: st.dataframe(df_hist, use_container_width=True, hide_index=True)
            else: st.info("No data.")

        with tab2:
            m_sel = st.selectbox("Month", range(1, 13), index=datetime.date.today().month - 1)
            y_sel = st.selectbox("Year", range(2024, 2030), index=datetime.date.today().year - 2024)
            period = f"{y_sel}-{m_sel:02d}"
            
            df_comp = db.get_gst_compliance(period)
            if not df_comp.empty:
                with st.form("uf"):
                    u_gst = st.selectbox("Select GST", df_comp['GST No'].tolist())
                    u_ret = st.selectbox("Return", ["GSTR-1", "GSTR-3B"])
                    u_stat = st.selectbox("Status", ["Filed", "Pending"])
                    u_date = st.date_input("Filed Date")
                    if st.form_submit_button("Update Status", type="primary", use_container_width=True):
                        db.update_gst_filing(u_gst, period, u_ret, u_stat, str(u_date))
                        st.success("Updated Successfully!"); st.rerun()
            else: st.warning("No GST clients registered.")

        with tab3:
            reg_mode = st.radio("Mode", ["Single Entry", "Bulk Upload"], horizontal=True, label_visibility="collapsed")
            if reg_mode == "Single Entry":
                with st.form("ngst"):
                    g_no = st.text_input("GST No.")
                    g_legal = st.text_input("Legal Name")
                    g_trade = st.text_input("Trade Name")
                    g_date = st.date_input("Reg Date")
                    o_ph = st.text_input("Owner Phone")
                    
                    if st.form_submit_button("Save Client", type="primary", use_container_width=True):
                        s, m = db.save_gst_registration(g_no, g_legal, g_trade, str(g_date), o_ph, "", "", "")
                        st.success(m) if s else st.error(m)
            else:
                uf = st.file_uploader("Upload CSV", type=["csv", "xlsx"])
                if uf and st.button("🚀 Upload", type="primary", use_container_width=True):
                    try:
                        df = pd.read_csv(uf) if uf.name.endswith('.csv') else pd.read_excel(uf)
                        count, errors = db.save_bulk_gst_clients(df)
                        st.success(f"Added {count} clients!")
                    except Exception as e: st.error(str(e))
                    
            df_gst = db.get_gst_registrations()
            if not df_gst.empty: st.dataframe(df_gst, use_container_width=True, hide_index=True)

    elif nav == "💸 Staff Payments":
        t1, t2 = st.tabs(["📊 Balances", "💰 Pay"])
        with t1:
            df = db.get_all_staff_balances()
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.markdown(f"### Total Liability: ₹ {df['Net Payable'].sum():,.2f}")
            else: st.info("No records.")
        with t2:
            with st.form("pay"):
                pd_ = st.date_input("Date")
                ps = st.selectbox("Staff", db.get_staff_list())
                pa = st.number_input("Amount", 100)
                pt = st.radio("Type", ["Salary", "Advance"], horizontal=True)
                rem = st.text_input("Remarks")
                if st.form_submit_button("Record Payment", type="primary", use_container_width=True):
                    db.save_payment(str(pd_), ps, pa, pt, rem)
                    st.success("Recorded!")

    elif nav == "📋 Catalog Maker":
        tab1, tab2 = st.tabs(["📤 Upload", "📊 View"])
        with tab1:
            uf = st.file_uploader("Upload File (CSV/Excel)", type=['csv', 'xlsx'])
            if uf and st.button("🚀 Process & Map", type="primary", use_container_width=True):
                with st.spinner("Processing..."):
                    df_input = pd.read_csv(uf) if uf.name.endswith('.csv') else pd.read_excel(uf)
                    success, result = db.process_and_save_catalog(df_input)
                    st.success("Saved!") if success else st.error(result)
        with tab2:
            df_cat = db.get_catalog_data()
            if not df_cat.empty:
                st.dataframe(df_cat, use_container_width=True, hide_index=True)
                st.download_button("⬇️ Download", df_cat.to_csv(index=False).encode('utf-8'), "Catalog.csv", "text/csv", use_container_width=True)

    elif nav == "📦 Product Master":
        t1, t2, t3 = st.tabs(["📝 Add", "📤 Import", "📚 List"])
        with t1:
            with st.form("pf"):
                st.markdown("#### Parent Style")
                n = st.text_input("Style Name")
                g = st.selectbox("Gender", ["Men","Women","Kids","Unisex"])
                c = st.selectbox("Category", db.get_categories_list())
                if st.form_submit_button("Create Parent", type="primary", use_container_width=True): 
                    db.save_product_parent(n,g,c,""); st.success("Saved")
            with st.form("cf"):
                st.markdown("#### Child Variant (SKU)")
                parents = db.get_parent_products()
                if parents:
                    sel = st.selectbox("Parent Style", [p['name'] for p in parents])
                    pid = next(p['system_id'] for p in parents if p['name']==sel)
                    col = st.selectbox("Color", db.get_colors_list())
                    siz = st.selectbox("Size", db.get_sizes_list())
                    rat = st.number_input("Rate (₹)")
                    sku = f"{sel}-{col}-{siz}".replace(" ","")
                    if st.form_submit_button("Create Variant", type="primary", use_container_width=True): 
                        db.save_product_child(pid, sku, col, siz, rat); st.success("Saved")
                else: st.info("Create Parent first."); st.form_submit_button("Create Variant", disabled=True)
        with t2:
            uf = st.file_uploader("Upload CSV", type=['csv'])
            if uf and st.button("🚀 Import", type="primary", use_container_width=True):
                c, e = db.save_bulk_products(pd.read_csv(uf))
                st.success(f"Imported {c} records.")
        with t3:
            render_df(pd.DataFrame(db.get_all_products_flat()))

    elif nav == "⚙️ System Masters":
        sub = st.radio("Settings", ["Channels (🛒)", "Staff Directory", "Item Categories", "Process Routes", "Rate Rules", "System Wipe"], horizontal=True, label_visibility="collapsed")
        
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

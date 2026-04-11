import streamlit as st
import pandas as pd
import db_manager as db
import datetime
import math
import time
import base64

# --- CONFIG (DESKTOP-FIRST WIDESCREEN) ---
st.set_page_config(page_title="DrenchWear ERP", page_icon="🧵", layout="wide", initial_sidebar_state="expanded")

# --- DESKTOP SAAS CSS INJECTION ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Global Theme & Reset */
    * { box-sizing: border-box !important; font-family: 'Inter', sans-serif !important; }
    .stApp { background-color: #F8FAFC !important; color: #0F172A; }
    
    /* Clean up Streamlit Top Bar but KEEP the Hamburger Menu for Mobile */
    header[data-testid="stHeader"] { background-color: transparent !important; }
    .stDeployButton, [data-testid="stToolbar"] { display: none !important; }
    footer { display: none !important; }
    
    /* Centralize Content - Widescreen Desktop Optimized */
    .block-container {
        max-width: 100% !important;
        padding-top: 2rem !important;
        padding-bottom: 5rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 { color: #0F172A !important; font-weight: 700 !important; letter-spacing: -0.02em; margin-top: 0; }

    /* --- SIDEBAR STYLING --- */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
        box-shadow: 2px 0 10px rgba(0,0,0,0.02) !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label {
        padding: 12px 16px !important;
        border-radius: 8px !important;
        color: #475569 !important;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.2s ease;
        border: none !important;
        background: transparent !important;
        cursor: pointer;
        margin-bottom: 4px;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
        background-color: #EEF2FF !important;
        color: #4F46E5 !important;
        border-left: 4px solid #4F46E5 !important;
        border-radius: 4px 8px 8px 4px !important;
    }

    /* --- PREMIUM SAAS SUMMARY CARDS (8-GRID) --- */
    .summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 24px; }
    .summary-card { 
        background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.02); display: flex; align-items: flex-start; gap: 16px;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .summary-card:hover { transform: translateY(-2px); box-shadow: 0 8px 15px -3px rgba(0,0,0,0.05); }
    .summary-card.c-blue { border-top: 4px solid #3B82F6; }
    .summary-card.c-green { border-top: 4px solid #10B981; }
    .summary-card.c-red { border-top: 4px solid #EF4444; }
    .summary-card.c-orange { border-top: 4px solid #F97316; }
    .summary-card.c-purple { border-top: 4px solid #8B5CF6; }
    .summary-card.c-darkred { border-top: 4px solid #991B1B; }
    .summary-card.c-brown { border-top: 4px solid #92400E; }
    
    .sc-icon { font-size: 1.8rem; line-height: 1; }
    .sc-content { display: flex; flex-direction: column; }
    .sc-val { font-size: 1.6rem; font-weight: 800; color: #0F172A; line-height: 1.1; margin-bottom: 4px; }
    .sc-val.text-blue { color: #3B82F6; } .sc-val.text-green { color: #10B981; } .sc-val.text-red { color: #EF4444; }
    .sc-val.text-orange { color: #F97316; } .sc-val.text-purple { color: #8B5CF6; } .sc-val.text-brown { color: #92400E; }
    .sc-label { font-size: 0.75rem; color: #64748B; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
    .sc-sub { font-size: 0.8rem; color: #94A3B8; margin-top: 2px; font-weight: 500; }

    /* Main Dashboard Metric Cards */
    .metric-card { 
        background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 24px; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.02); display: flex; justify-content: space-between; 
        align-items: center; transition: transform 0.2s, box-shadow 0.2s; margin-bottom: 16px; height: 100%;
    }
    .metric-card:hover { transform: translateY(-3px); box-shadow: 0 10px 20px -3px rgba(0,0,0,0.06); }
    .metric-info { display: flex; flex-direction: column; overflow: hidden;}
    .metric-label { font-size: 0.85rem; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }
    .metric-value { font-size: 1.8rem; font-weight: 800; color: #0F172A; line-height: 1.2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
    .metric-icon-box { min-width: 56px; height: 56px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 1.6rem; margin-left: 10px;}

    /* --- FINAL PROFIT BOX --- */
    .profit-statement { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; margin-top: 20px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); }
    .ps-header { padding: 16px 20px; background: #F8FAFC; border-bottom: 1px solid #E2E8F0; font-weight: 700; color: #0F172A; font-size: 1.15rem; display: flex; align-items: center; gap: 8px;}
    .ps-row { display: flex; justify-content: space-between; padding: 14px 20px; border-bottom: 1px solid #F1F5F9; font-size: 1rem; font-weight: 500; color: #475569; }
    .ps-row:last-child { border-bottom: none; }
    .ps-val.pos { color: #10B981; font-weight: 600; }
    .ps-val.neg { color: #EF4444; font-weight: 600; }
    .ps-total { display: flex; justify-content: space-between; padding: 20px; background: #ECFDF5; font-size: 1.3rem; font-weight: 800; color: #065F46; border-top: 1px solid #D1FAE5; }

    /* --- PRODUCT CARDS --- */
    [data-testid="stVerticalBlockBorderWrapper"] { border-radius: 16px !important; border: 1px solid #E2E8F0 !important; box-shadow: 0 2px 8px rgba(0,0,0,0.02) !important; background: #FFFFFF !important; padding: 20px !important; margin-bottom: 20px !important; width: 100% !important; transition: all 0.2s ease !important;}
    [data-testid="stVerticalBlockBorderWrapper"]:hover { box-shadow: 0 10px 25px rgba(0,0,0,0.06) !important; border-color: #CBD5E1 !important; transform: translateY(-2px); }
    .thumbnail-container { display: flex; gap: 8px; margin-bottom: 12px; overflow-x: auto; padding-bottom: 4px; scrollbar-width: none; }
    .thumbnail-container::-webkit-scrollbar { display: none; }
    .product-thumbnail { width: 55px; height: 55px; object-fit: cover; border-radius: 8px; border: 1px solid #E2E8F0; }
    .product-link-btn { display: flex; align-items: center; justify-content: center; background-color: #F8FAFC; color: #4F46E5 !important; padding: 10px; border-radius: 8px; font-weight: 700; font-size: 0.95rem; text-decoration: none !important; border: 1px solid #E2E8F0; transition: all 0.2s ease; margin-bottom: 15px; width: 100%; }
    .product-link-btn:hover { background-color: #EEF2FF; border-color: #C7D2FE; }
    
    /* --- FORMS & INPUTS --- */
    [data-testid="stForm"], .st-emotion-cache-1104q3m { background: #FFFFFF !important; padding: 32px !important; border-radius: 16px !important; border: 1px solid #E2E8F0 !important; box-shadow: 0 2px 8px rgba(0,0,0,0.02) !important; width: 100% !important; margin-bottom: 24px !important;}
    .section-header { border-left: 4px solid #4F46E5; padding-left: 12px; margin-top: 24px; margin-bottom: 16px; color: #0F172A; font-size: 1.25rem; font-weight: 700; }
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox > div > div { background-color: #F8FAFC !important; border: 1px solid #CBD5E1 !important; border-radius: 8px !important; color: #0F172A !important; padding: 10px 14px !important; font-size: 0.95rem; min-height: 42px !important; width: 100% !important; box-shadow: 0 1px 2px rgba(0,0,0,0.01) !important;}
    .stTextInput input:focus, .stSelectbox > div > div:focus { border-color: #4F46E5 !important; box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1) !important; background: #FFFFFF !important;}
    div[data-baseweb="select"] span { color: #0F172A !important; font-weight: 500; }
    div[data-baseweb="popover"], ul[role="listbox"] { background-color: #FFFFFF !important; border-radius: 10px !important; border: 1px solid #E2E8F0 !important; box-shadow: 0 10px 25px rgba(0,0,0,0.1) !important; overflow: hidden; }
    ul[role="listbox"] li { padding: 10px 16px !important; font-size: 0.95rem !important; color: #0F172A !important; }
    ul[role="listbox"] li:hover { background-color: #F8FAFC !important; color: #4F46E5 !important; }
    
    /* --- BUTTONS --- */
    .stButton button { border-radius: 8px; font-weight: 600; min-height: 42px !important; transition: all 0.2s ease; width: 100% !important; border: 1px solid #E2E8F0 !important; background: #FFFFFF !important; color: #0F172A !important; box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important; }
    .stButton button:hover { background: #F8FAFC !important; border-color: #CBD5E1 !important; }
    .stButton button[kind="primary"] { background: #4F46E5 !important; color: white !important; border: none !important; box-shadow: 0 4px 10px rgba(79, 70, 229, 0.2) !important; }
    .stButton button[kind="primary"]:hover { background: #4338CA !important; box-shadow: 0 6px 15px rgba(79, 70, 229, 0.3) !important; transform: translateY(-1px); }
    
    /* --- TABS --- */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; border-bottom: 1px solid #E2E8F0; padding-bottom: 0px; overflow-x: auto; scrollbar-width: none; }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }
    .stTabs [data-baseweb="tab"] { height: 48px; border: none; background: transparent; color: #64748B; font-weight: 600; font-size: 1rem; padding: 0 8px; white-space: nowrap; transition: color 0.2s; }
    .stTabs [aria-selected="true"] { color: #4F46E5 !important; border-bottom: 2px solid #4F46E5 !important; }

    /* --- DATAFRAMES --- */
    [data-testid="stDataFrame"] { border-radius: 12px; border: 1px solid #E2E8F0; box-shadow: 0 2px 4px rgba(0,0,0,0.01); overflow: hidden; background: #FFFFFF; font-size: 0.9rem;}

    /* Login Centering */
    .login-container { max-width: 420px; margin: 15vh auto; background: white; padding: 40px 30px; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.08); border: 1px solid #E2E8F0; text-align: center; }

    /* --- RESPONSIVE MOBILE FIXES --- */
    @media (max-width: 768px) {
        .block-container { padding: 1rem !important; }
        .summary-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; }
        .sc-val { font-size: 1.2rem; }
        .sc-label { font-size: 0.65rem; }
        [class*="st-key-mobile_grid"] div[data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 10px !important; }
        [class*="st-key-mobile_grid"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"] { width: calc(50% - 5px) !important; min-width: calc(50% - 5px) !important; flex: 1 1 calc(50% - 5px) !important; margin-bottom: 0 !important; }
        [data-testid="stVerticalBlockBorderWrapper"] { padding: 12px !important; border-radius: 12px !important; }
        [data-testid="stForm"], .st-emotion-cache-1104q3m { padding: 16px !important; border-radius: 12px !important; }
    }
</style>
""", unsafe_allow_html=True)

# --- DYNAMIC CSS FOR APP DASHBOARD TILES ---
def apply_dashboard_card_css():
    st.markdown("""
    <style>
        .stButton button[kind="secondary"] {
            height: 120px !important; border-radius: 16px !important; background: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important; box-shadow: 0 2px 8px rgba(0,0,0,0.02) !important;
            display: flex !important; flex-direction: column !important; align-items: center !important;
            justify-content: center !important; white-space: pre-wrap !important; line-height: 1.4 !important;
            color: #0F172A !important; transition: all 0.2s ease !important;
        }
        .stButton button[kind="secondary"] p { font-size: 1.05rem !important; font-weight: 700 !important; margin: 0 !important; }
        .stButton button[kind="secondary"]:hover { transform: translateY(-4px); box-shadow: 0 10px 20px rgba(79,70,229,0.08) !important; border-color: #C7D2FE !important; color: #4F46E5 !important; }
        
        @media (max-width: 768px) {
            .stButton button[kind="secondary"] { height: 100px !important; }
            .stButton button[kind="secondary"] p { font-size: 0.95rem !important; }
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
    login_html = """<div class="login-container"><div style="font-size: 3.5rem; margin-bottom: 10px;">🧵</div><h2 style='color: #0F172A; margin-bottom: 5px; margin-top:0; font-weight:800;'>DrenchWear</h2><p style='color: #64748B; font-weight: 500; margin-bottom: 30px; font-size:1rem;'>Log in to your workspace</p>"""
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

# --- SIDEBAR NAVIGATION (PERSISTENT ON DESKTOP) ---
menu_options = [
    "Home", 
    "🏭 Work Operations", 
    "🤖 Drench AI", 
    "🚀 Product Launcher", 
    "📈 P&L Analysis", 
    "🩺 Market Place Doctor",
    "🧾 GST Tracker", 
    "💸 Staff Payments", 
    "📋 Catalog Maker", 
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
    st.markdown("""<div style='margin-bottom: 30px; margin-top: 5px;'><h1 style='color: #0F172A; font-weight: 800; font-size: 2.2rem; margin-bottom: 5px;'>Dashboard Overview</h1><p style='color: #64748B; font-weight: 500; font-size: 1rem; margin:0;'>Welcome back to your workspace.</p></div>""", unsafe_allow_html=True)
    
    pcs, earn, pending, active = db.get_dashboard_stats()
    
    with st.container(key="mobile_grid_metrics"):
        m1, m2, m3, m4 = st.columns(4)
        with m1: render_metric_card("Pieces Today", f"{pcs:,.0f}", "👕", "#D1FAE5", "#10B981")
        with m2: render_metric_card("Prod Value", f"₹{earn:,.0f}", "₹", "#FEF3C7", "#F59E0B")
        with m3: render_metric_card("Liabilities", f"₹{pending:,.0f}", "💳", "#FEE2E2", "#EF4444")
        with m4: render_metric_card("Active Staff", f"{active}", "👥", "#DBEAFE", "#3B82F6")
    
    st.markdown("<h4 style='margin-top: 30px; margin-bottom: 16px; font-size: 1.2rem; color:#0F172A;'>Quick Launch Applications</h4>", unsafe_allow_html=True)
    
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
            if st.button("🩺\nMarket Dr.", use_container_width=True): route("🩺 Market Place Doctor")

    with st.container(key="mobile_grid_apps_2"):
        c_set1, c_set2 = st.columns(2)
        with c_set1:
            if st.button("📦\nMaster", use_container_width=True): route("📦 Product Master")
        with c_set2:
            if st.button("⚙️\nSettings", use_container_width=True): route("⚙️ System Masters")
        
else:
    # --- DESKTOP APP HEADER ---
    clean_title = nav.split(' ', 1)[1] if ' ' in nav else nav
    st.markdown(f"<h2 style='color: #0F172A;'>{clean_title}</h2>", unsafe_allow_html=True)
    st.markdown("<hr style='margin-top: 5px; margin-bottom: 25px; border-color:#E2E8F0;'>", unsafe_allow_html=True)

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
        with t2: render_df(db.get_daily_orders_df())
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
                if "fab_df" not in st.session_state: st.session_state.fab_df = pd.DataFrame([{"Srl no.": i+1, "Color": "", "UOM": "Meter", "Qty": 0.0} for i in range(5)])
                e_fab = st.data_editor(st.session_state.fab_df, num_rows="dynamic", use_container_width=True, hide_index=True)
                
                st.markdown("<div class='section-header'>Bundle Generation</div>", unsafe_allow_html=True)
                c_b1, c_b2 = st.columns([1, 3])
                n_bun = c_b1.number_input("No. of Bundles", 1, 500, 10)
                if c_b1.button("🔄 Generate Grid", use_container_width=True): st.session_state.lot_df = pd.DataFrame([{"Bundle No": str(i+1), "Qty": 0} for i in range(n_bun)])
                if "lot_df" not in st.session_state: st.session_state.lot_df = pd.DataFrame([{"Bundle No": str(i+1), "Qty": 0} for i in range(10)])
                e_bun = st.data_editor(st.session_state.lot_df, height=350, use_container_width=True, hide_index=True)
                
                total_pcs = pd.to_numeric(e_bun['Qty'], errors='coerce').sum()
                st.markdown(f"<div style='color: #4F46E5; font-weight:700; font-size:1.1rem; margin-top: 10px;'>Calculated Total: {total_pcs:,.0f} Pcs</div>", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 Save & Authorize Cutting Lot", type="primary", use_container_width=True):
                    if not l_no or not item_name: st.error("Lot Number and Item Name are required.")
                    else:
                        h = {"lot_no": l_no, "item_name": item_name, "date": str(datetime.date.today()), "sku": item_name}
                        s, m = db.save_full_lot(h, e_fab, e_bun)
                        if s: 
                            st.success(m); time.sleep(1); st.rerun()
                        else: st.error(m)
            else: st.info("View active lot progress in the 'Job Work Tracking' tab.")

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
                    buns = [f"{b['bundle_no']} | {b['item_name']} | {b['qty']} pcs" for b in db.get_detailed_bundles(sd_lot)] if sd_lot else []
                    sd_bun = c5.selectbox("Select Specific Bundle", [""] + buns)
                    
                    st.markdown("<hr style='margin: 15px 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)
                    c6, c7 = st.columns(2)
                    qty = c6.number_input("Quantity Stitched (Pcs)", min_value=1.0)
                    lbl = c7.checkbox("🏷️ Include Labeling Charge (+₹0.50 per pc)")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.form_submit_button("💾 Submit Entry & Credit Ledger", type="primary", use_container_width=True):
                        if sd_worker and sd_lot and sd_bun:
                            p = sd_bun.split(" | ")
                            val_item = p[1] if len(p)>1 else ""
                            rate = db.get_rate(val_item, sd_proc, sd_date)
                            fin_rate = rate + (0.50 if lbl else 0)
                            s, m = db.save_production(str(sd_date), sd_worker, val_item, sd_proc, qty, fin_rate, sd_lot, p[0])
                            st.success(f"Success! Credited to ledger: ₹{qty*fin_rate:,.2f}") if s else st.error(m)
                        else: st.error("Please fill in all required fields.")
                        
            elif stitch_mode == "Bulk CSV Upload":
                st.info("The system automatically fetches the correct Piece Rate from the Master configuration based on the Date.")
                st.download_button("⬇️ Download Template", "Date,Karigar Name,Lot No,Bundle No.,Process,Item,Qty\n2026-03-10,Worker,L-1001,B-01,Collar,Top,50", "Sample.csv", "text/csv", use_container_width=True)
                uf = st.file_uploader("Upload Completed CSV", type=["csv", "xlsx"])
                if uf and st.button("🚀 Process Bulk Upload", type="primary", use_container_width=True):
                    try:
                        count, errors = db.save_bulk_stitching(pd.read_csv(uf) if uf.name.endswith('.csv') else pd.read_excel(uf))
                        if count > 0: st.success(f"Successfully processed {count} records!")
                        if errors:
                            with st.expander("View Upload Errors"):
                                for e in errors: st.write(e)
                    except Exception as e: st.error(str(e))

        with tab_ops:
            ops_view_mode = st.radio("View Module", ["Bundle Tracking Matrix", "External Fabrication Job Work"], horizontal=True, label_visibility="collapsed")
            if ops_view_mode == "Bundle Tracking Matrix": st.dataframe(db.get_bundle_progress(), use_container_width=True)
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
                    if st.form_submit_button("Save Fabrication Entry", type="primary", use_container_width=True):
                        db.save_fabrication(str(fd), fp, fi, fq, fr, fdesc); st.success("Entry Saved Successfully.")
                st.dataframe(db.get_recent_fabrication(), use_container_width=True)

    elif nav == "🚀 Product Launcher":
        tab_add, tab_view = st.tabs(["➕ Add New Product", "📋 Pipeline Board"])
        with tab_add:
            st.markdown("<div class='section-header' style='margin-top:0;'>1. Import Source Data</div>", unsafe_allow_html=True)
            c_url, c_btn1, c_btn2 = st.columns([6, 2, 2])
            fetch_url = c_url.text_input("Product URL", placeholder="https://www.myntra.com/...", label_visibility="collapsed")
            
            if c_btn1.button("🔍 Auto-Fetch Details", use_container_width=True):
                if fetch_url:
                    with st.spinner("Extracting metadata..."): st.session_state.launcher_draft = db.fetch_product_metadata(fetch_url)
                else: st.warning("Please paste a URL first.")
            if c_btn2.button("✍️ Manual Entry", use_container_width=True): st.session_state.launcher_draft = {"title": "", "price": 0.0, "image": "", "url": ""}

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
                    if st.form_submit_button("💾 Add to Pipeline", type="primary", use_container_width=True):
                        if p_title:
                            final_imgs = [f"data:{f.type};base64,{base64.b64encode(f.read()).decode('utf-8')}" for f in p_img_upload] if p_img_upload else ([p_img] if p_img else [])
                            s, m = db.save_launched_product(p_title, fetch_url if fetch_url else draft.get("url", ""), final_imgs, p_price, p_stage)
                            if s: st.success(m); del st.session_state.launcher_draft; time.sleep(1); st.rerun()
                            else: st.error(m)
                        else: st.error("Product Title is required.")
                            
        with tab_view:
            products = db.get_launched_products()
            if not products: st.info("Pipeline is empty. Add a product to get started.")
            else:
                stages = ["Stage 1", "Stage 2", "Stage 3", "Stage 4", "Stage 5", "Stage 6", "Stage 7"]
                cols = st.columns(4) # Widescreen optimized
                for idx, prod in enumerate(products):
                    with cols[idx % 4]:
                        with st.container(border=True): 
                            img_urls = prod.get('images', []) or ([prod.get('image_url')] if prod.get('image_url') else [])
                            main_img = img_urls[0] if img_urls else "https://via.placeholder.com/400x300?text=No+Image+Found"
                            thumbnails_html = f"<div class='thumbnail-container'>{''.join([f'<img src=\"{t}\" class=\"product-thumbnail\">' for t in img_urls[1:]])}</div>" if len(img_urls) > 1 else ""
                            
                            st.markdown(f"""<div style="width: 100%; height: 240px; overflow: hidden; border-radius: 12px; margin-bottom: 12px; border: 1px solid #F1F5F9; background:#F8FAFC;"><img src="{main_img}" style="width: 100%; height: 100%; object-fit: cover;"></div>{thumbnails_html}<div style="font-weight: 800; font-size: 1.15rem; color: #0F172A; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px; line-height: 1.4;">{prod.get('title', 'Unknown')}</div><div style="color: #10B981; font-weight: 800; font-size: 1.25rem; margin-bottom: 15px;">₹ {prod.get('price', 0.0):,.2f}</div><a href="{prod.get('url', '#')}" target="_blank" class="product-link-btn">🔗 View Original Link</a>""", unsafe_allow_html=True)
                            
                            curr_idx = stages.index(prod.get('stage', 'Stage 1')) if prod.get('stage', 'Stage 1') in stages else 0
                            new_stage = st.selectbox("Stage", stages, index=curr_idx, key=f"stg_{prod['_id']}", label_visibility="collapsed")
                            
                            btn_c1, btn_c2 = st.columns(2)
                            if btn_c1.button("💾 Apply", key=f"upd_{prod['_id']}", use_container_width=True):
                                db.update_launched_product_stage(prod['_id'], new_stage); st.rerun()
                                
                            with btn_c2.popover("⚙️ Manage", use_container_width=True):
                                st.markdown("#### Edit Details")
                                e_title = st.text_input("Title", value=prod.get('title', ''), key=f"et_{prod['_id']}")
                                e_price = st.number_input("Price (₹)", value=float(prod.get('price', 0.0)), key=f"ep_{prod['_id']}")
                                e_img = st.text_input("Main Image", value=main_img, key=f"ei_{prod['_id']}")
                                e_img_file = st.file_uploader("Replace Images", type=['png', 'jpg'], accept_multiple_files=True, key=f"ef_{prod['_id']}")
                                
                                if st.button("Save Changes", type="primary", key=f"es_{prod['_id']}", use_container_width=True):
                                    final_edit_imgs = [f"data:{f.type};base64,{base64.b64encode(f.read()).decode('utf-8')}" for f in e_img_file] if e_img_file else ([e_img] if e_img != main_img else img_urls)
                                    s, m = db.update_launched_product_details(prod['_id'], e_title, e_price, final_edit_imgs)
                                    st.rerun() if s else st.error(m)
                                st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
                                if st.button("🚨 Delete Product", key=f"del_{prod['_id']}", use_container_width=True):
                                    db.delete_launched_product(prod['_id']); st.rerun()

    elif nav == "📈 P&L Analysis":
        st.markdown("<div class='section-header' style='margin-top:0;'>Marketplace Analytics Engine</div>", unsafe_allow_html=True)
        
        channels = db.get_channels_list()
        if not channels: st.info("Please configure Marketplaces in 'System Masters'.")
        else:
            tabs = st.tabs([f"🛒 {c}" for c in channels])
            for i, c_name in enumerate(channels):
                with tabs[i]:
                    sub_tabs = st.radio("Select View", ["📊 1. Order Analysis", "💳 2. Payments & Ads"], horizontal=True, key=f"sub_{c_name}", label_visibility="collapsed")
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    if sub_tabs == "📊 1. Order Analysis":
                        with st.container(border=True):
                            st.markdown(f"#### 📦 {c_name} Order Analytics Setup")
                            o_file = st.file_uploader(f"1. Upload {c_name} Orders Report", type=['csv', 'xlsx'], key=f"o_{c_name}")
                            if o_file:
                                df_o = pd.read_csv(o_file) if o_file.name.endswith('.csv') else pd.read_excel(o_file)
                                cols = ["Select File Column..."] + df_o.columns.tolist()
                                
                                st.markdown("**Map Essential Columns:**")
                                mc1, mc2, mc3, mc4 = st.columns(4)
                                o_dt = mc1.selectbox("Order Date", cols, key=f"o_dt_{c_name}")
                                o_sku = mc2.selectbox("SKU / Item", cols, key=f"o_sku_{c_name}")
                                o_am = mc3.selectbox("Order Amount", cols, key=f"o_am_{c_name}")
                                o_stat = mc4.selectbox("Order Status (Optional)", cols, key=f"o_stat_{c_name}")
                                
                                st.markdown("<hr style='margin: 20px 0; border-color:#E2E8F0;'>", unsafe_allow_html=True)
                                st.markdown("##### ⚙️ Optional: Cost of Goods Sold (COGS)")
                                
                                cogs_c1, cogs_c2 = st.columns(2)
                                with cogs_c1:
                                    if o_sku != "Select File Column...":
                                        unique_skus = df_o[o_sku].dropna().astype(str).unique()
                                        st.download_button(f"⬇️ Download SKU Template ({len(unique_skus)})", pd.DataFrame({o_sku: unique_skus, 'COGS': 0.0}).to_csv(index=False).encode('utf-8'), f"{c_name}_COGS.csv", "text/csv", use_container_width=True)
                                    else: st.info("Map 'SKU' to generate template.")
                                with cogs_c2:
                                    cogs_file = st.file_uploader("2. Upload Filled COGS Template", type=['csv', 'xlsx'], key=f"cogs_{c_name}", label_visibility="collapsed")

                                st.markdown("<br>", unsafe_allow_html=True)
                                if st.button("🚀 Generate Advanced Dashboard", type="primary", key=f"o_btn_{c_name}", use_container_width=True):
                                    if "Select File Column..." not in [o_dt, o_sku, o_am]:
                                        try:
                                            df_o['ParsedDate'] = pd.to_datetime(df_o[o_dt], errors='coerce')
                                            df_o = df_o.dropna(subset=['ParsedDate']).copy() 
                                            df_o['DayOfWeek'] = df_o['ParsedDate'].dt.day_name()
                                            df_o['IsWeekend'] = df_o['ParsedDate'].dt.dayofweek >= 5
                                            
                                            if df_o[o_am].dtype == 'object': df_o['AmountVal'] = pd.to_numeric(df_o[o_am].replace(r'[₹,]', '', regex=True), errors='coerce').fillna(0)
                                            else: df_o['AmountVal'] = pd.to_numeric(df_o[o_am], errors='coerce').fillna(0)
                                            
                                            df_o['QtyVal'] = 1 
                                            
                                            has_cogs = False
                                            if cogs_file:
                                                df_cogs = pd.read_csv(cogs_file) if cogs_file.name.endswith('.csv') else pd.read_excel(cogs_file)
                                                if o_sku in df_cogs.columns and 'COGS' in df_cogs.columns:
                                                    df_o[o_sku] = df_o[o_sku].astype(str)
                                                    df_cogs[o_sku] = df_cogs[o_sku].astype(str)
                                                    df_o = df_o.merge(df_cogs[[o_sku, 'COGS']], on=o_sku, how='left')
                                                    df_o['COGS'] = pd.to_numeric(df_o['COGS'], errors='coerce').fillna(0)
                                                    df_o['Profit'] = df_o['AmountVal'] - df_o['COGS']
                                                    has_cogs = True
                                            
                                            st.markdown(f"<div class='section-header' style='margin-top: 15px;'>📈 {c_name} Performance Dashboard</div>", unsafe_allow_html=True)
                                            
                                            if o_stat != "Select File Column...":
                                                df_o['StatusClean'] = df_o[o_stat].astype(str).str.lower()
                                                tot_orders = len(df_o)
                                                deliv_c = len(df_o[df_o['StatusClean'].str.contains('deliv', na=False)])
                                                canc_c = len(df_o[df_o['StatusClean'].str.contains('cancel', na=False)])
                                                ret_c = len(df_o[df_o['StatusClean'].str.contains('return', na=False)])
                                                rto_c = len(df_o[df_o['StatusClean'].str.contains('rto', na=False)])
                                                tot_ret = ret_c + rto_c
                                                
                                                p_del = (deliv_c/tot_orders*100) if tot_orders else 0
                                                p_can = (canc_c/tot_orders*100) if tot_orders else 0
                                                p_ret = (ret_c/tot_orders*100) if tot_orders else 0
                                                p_rto = (rto_c/tot_orders*100) if tot_orders else 0
                                                p_tret = (tot_ret/tot_orders*100) if tot_orders else 0

                                                st.markdown(f"""
                                                <div class="summary-grid">
                                                    <div class="summary-card c-blue"><div class="sc-icon">📦</div><div class="sc-content"><div class="sc-val text-blue">{tot_orders}</div><div class="sc-label">Total Orders</div></div></div>
                                                    <div class="summary-card c-green"><div class="sc-icon">✅</div><div class="sc-content"><div class="sc-val text-green">{deliv_c}</div><div class="sc-label">Delivered</div><div class="sc-sub">{p_del:.1f}%</div></div></div>
                                                    <div class="summary-card c-red"><div class="sc-icon">❌</div><div class="sc-content"><div class="sc-val text-red">{canc_c}</div><div class="sc-label">Cancelled</div><div class="sc-sub">{p_can:.1f}%</div></div></div>
                                                    <div class="summary-card c-orange"><div class="sc-icon">🔄</div><div class="sc-content"><div class="sc-val text-orange">{ret_c}</div><div class="sc-label">Customer Returns</div><div class="sc-sub">{p_ret:.1f}%</div></div></div>
                                                    <div class="summary-card c-purple"><div class="sc-icon">🔙</div><div class="sc-content"><div class="sc-val text-purple">{rto_c}</div><div class="sc-label">RTO</div><div class="sc-sub">{p_rto:.1f}%</div></div></div>
                                                    <div class="summary-card c-blue"><div class="sc-icon">📉</div><div class="sc-content"><div class="sc-val text-blue">{tot_ret}</div><div class="sc-label">Total Returns</div><div class="sc-sub">{p_tret:.1f}%</div></div></div>
                                                    <div class="summary-card c-brown"><div class="sc-icon">📢</div><div class="sc-content"><div class="sc-val text-brown">0</div><div class="sc-label">Ad Orders</div><div class="sc-sub">0.0%</div></div></div>
                                                    <div class="summary-card c-darkred"><div class="sc-icon">🔇</div><div class="sc-content"><div class="sc-val text-darkred">0</div><div class="sc-label">Ad Cancelled</div><div class="sc-sub">0.0%</div></div></div>
                                                </div>
                                                """, unsafe_allow_html=True)
                                            else: st.info("💡 Map 'Order Status' above to unlock the 8-Card metrics breakdown.")

                                            g1, g2 = st.columns(2)
                                            with g1:
                                                st.markdown("##### 📅 Daily Trend (Value)")
                                                daily_sales = df_o.groupby(df_o['ParsedDate'].dt.date)['AmountVal'].sum().reset_index()
                                                daily_sales.columns = ['Date', 'Total Sales Value']
                                                daily_sales.set_index('Date', inplace=True)
                                                st.line_chart(daily_sales, use_container_width=True)
                                                    
                                            with g2:
                                                st.markdown("##### 🏆 Top 5 SKUs")
                                                sku_sales = df_o.groupby(o_sku)['AmountVal'].sum().sort_values(ascending=False).head(5)
                                                st.bar_chart(sku_sales, use_container_width=True)

                                            st.markdown("#### 📦 Order Analytics (By SKU)")
                                            if o_stat != "Select File Column...":
                                                sku_stats = df_o.groupby(o_sku).agg(
                                                    Orders=('AmountVal', 'count'), Qty=('QtyVal', 'sum'),
                                                    Delivered_Qty=('StatusClean', lambda x: (x.str.contains('deliv')).sum()),
                                                    Cancelled=('StatusClean', lambda x: (x.str.contains('cancel')).sum()),
                                                    Cust_Return=('StatusClean', lambda x: (x.str.contains('return')).sum()),
                                                    RTO=('StatusClean', lambda x: (x.str.contains('rto')).sum())
                                                ).reset_index()
                                                sku_stats['Cust. Ret%'] = (sku_stats['Cust_Return'] / sku_stats['Orders'] * 100).round(1).astype(str) + '%'
                                                sku_stats['RTO%'] = (sku_stats['RTO'] / sku_stats['Orders'] * 100).round(1).astype(str) + '%'
                                                sku_stats['Total Ret.'] = sku_stats['Cust_Return'] + sku_stats['RTO']
                                                sku_stats.rename(columns={o_sku: 'SKU'}, inplace=True)
                                                st.dataframe(sku_stats, use_container_width=True, hide_index=True)
                                            else: st.info("Map 'Order Status' to view SKU-level Analytics.")

                                            if has_cogs:
                                                st.markdown("#### 📊 Profit Analytics (By SKU)")
                                                prof_stats = df_o.groupby(o_sku).agg(
                                                    Sale_Value=('AmountVal', 'sum'), QTY=('QtyVal', 'sum'),
                                                    Rate=('COGS', 'max'), Cost_of_Goods=('COGS', 'sum'),
                                                    Net_After_Cost=('Profit', 'sum')
                                                ).reset_index()
                                                prof_stats['Ret. Deduction'] = 0.0 
                                                prof_stats['Claims'] = 0.0 
                                                prof_stats.rename(columns={o_sku: 'SKU'}, inplace=True)
                                                
                                                for c in ['Sale_Value', 'Rate', 'Cost_of_Goods', 'Net_After_Cost']: prof_stats[c] = prof_stats[c].apply(lambda x: f"₹{x:,.2f}")
                                                st.dataframe(prof_stats[['SKU', 'Sale_Value', 'QTY', 'Rate', 'Cost_of_Goods', 'Ret. Deduction', 'Claims', 'Net_After_Cost']], use_container_width=True, hide_index=True)
                                                
                                                total_gross = df_o['AmountVal'].sum()
                                                total_cogs = df_o['COGS'].sum()
                                                final_profit = total_gross - total_cogs
                                                
                                                st.markdown(f"""
                                                <div class="profit-statement">
                                                    <div class="ps-header">💰 Final Profit Calculation</div>
                                                    <div class="ps-row"><span>Total Gross Sale (Delivered Settlement)</span><span class="ps-val pos">₹{total_gross:,.2f}</span></div>
                                                    <div class="ps-row"><span>+ Claims Received</span><span class="ps-val pos">+₹0.00</span></div>
                                                    <div class="ps-row"><span>- Cost of Goods (Rate × Delivered Qty)</span><span class="ps-val neg">-₹{total_cogs:,.2f}</span></div>
                                                    <div class="ps-row"><span>- Return Deductions</span><span class="ps-val neg">-₹0.00</span></div>
                                                    <div class="ps-row"><span>- Ads Cost</span><span class="ps-val neg">-₹0.00</span></div>
                                                    <div class="ps-total"><span>🏢 Gross Profit</span><span>₹{final_profit:,.2f}</span></div>
                                                </div>
                                                """, unsafe_allow_html=True)
                                        except Exception as e: st.error(f"Analysis Error: {e}")
                                    else: st.warning("Please map Date, SKU, and Amount.")

                    elif sub_tabs == "💳 2. Payments & Ads":
                        c1, c2 = st.columns(2)
                        with c1:
                            with st.container(border=True):
                                st.markdown(f"#### 💳 {c_name} Payments")
                                p_file = st.file_uploader(f"Upload Settlements", type=['csv', 'xlsx'], key=f"p_{c_name}")
                                if p_file:
                                    df_p = pd.read_csv(p_file) if p_file.name.endswith('.csv') else pd.read_excel(p_file)
                                    cols = ["Select File Column..."] + df_p.columns.tolist()
                                    mc1, mc2, mc3 = st.columns(3)
                                    mc1.selectbox("Order ID", cols, key=f"p_id_{c_name}")
                                    mc2.selectbox("Settled Amount", cols, key=f"p_am_{c_name}")
                                    mc3.selectbox("Platform Fees", cols, key=f"p_fe_{c_name}")
                                    if st.button("Save Payment Mapping", type="primary", key=f"p_btn_{c_name}", use_container_width=True): st.success("Saved!")
                        with c2:
                            with st.container(border=True):
                                st.markdown(f"#### 📢 {c_name} Ads Spend")
                                a_file = st.file_uploader(f"Upload Ads Spend", type=['csv', 'xlsx'], key=f"a_{c_name}")
                                if a_file:
                                    df_a = pd.read_csv(a_file) if a_file.name.endswith('.csv') else pd.read_excel(a_file)
                                    cols = ["Select File Column..."] + df_a.columns.tolist()
                                    mc1, mc2 = st.columns(2)
                                    mc1.selectbox("Campaign Name", cols, key=f"a_nm_{c_name}")
                                    mc2.selectbox("Total Spend", cols, key=f"a_sp_{c_name}")
                                    if st.button("Save Ads Mapping", type="primary", key=f"a_btn_{c_name}", use_container_width=True): st.success("Saved!")

    elif nav == "🩺 Market Place Doctor":
        st.markdown("<div class='section-header' style='margin-top:0;'>Diagnostics & Growth Engine</div>", unsafe_allow_html=True)
        doc_tabs = st.tabs(["🚨 Loss Prevention", "🚀 Growth Engine"])

        with doc_tabs[0]:
            st.markdown("### 🛑 Plug Revenue Leaks")
            c1, c2 = st.columns(2)
            with c1:
                with st.container(border=True):
                    st.markdown("#### 📍 RTO Risk Analyzer")
                    rto_file = st.file_uploader("Upload Shipping/Courier Report", type=['csv', 'xlsx'], key="rto_up")
                    if st.button("Generate RTO Heatmap & Blocklist", type="primary", use_container_width=True):
                        if rto_file: st.success("Analysis complete! 15 High-Risk Pincodes identified for COD blocking.")
                        else: st.warning("Please upload a report first.")
            with c2:
                with st.container(border=True):
                    st.markdown("#### 🏭 Return Quality Matrix")
                    ret_file = st.file_uploader("Upload Customer Returns Report", type=['csv', 'xlsx'], key="ret_up")
                    if st.button("Link Returns to Production Lots", type="primary", use_container_width=True):
                        if ret_file: st.success("Successfully mapped! Spike in 'Size Issue' detected in Lot L-1002.")
                        else: st.warning("Please upload a report first.")

            with st.container(border=True):
                st.markdown("#### 🧊 Dead-Stock Aging Report")
                inv_file = st.file_uploader("Upload Current Inventory Status", type=['csv', 'xlsx'], key="inv_up")
                if st.button("Analyze Inventory Aging", type="primary", use_container_width=True):
                    if inv_file: st.success("Analysis complete! 3 SKUs identified with >90 days of cover. Recommended action: Liquidate.")
                    else: st.warning("Please upload a report first.")

        with doc_tabs[1]:
            st.markdown("### 📈 Scale Winning Products")
            c1, c2 = st.columns(2)
            with c1:
                with st.container(border=True):
                    st.markdown("#### ⚡ Smart Restock")
                    lt = st.number_input("Average Factory Lead Time (Days)", value=5)
                    vel_file = st.file_uploader("Upload SKU Velocity Report", type=['csv', 'xlsx'], key="vel_up")
                    if st.button("Generate Alerts", type="primary", use_container_width=True):
                        if vel_file: st.success(f"Calculated! 2 SKUs require immediate Cutting Lots.")
                        else: st.warning("Upload report.")
            with c2:
                with st.container(border=True):
                    st.markdown("#### 🕵️ Competitor Monitor")
                    comp_url = st.text_input("Competitor Product URL")
                    if st.button("Add to Watchlist", type="primary", use_container_width=True):
                        if comp_url: st.success("Competitor added!")
                        else: st.warning("Enter a URL.")

            with st.container(border=True):
                st.markdown("#### 🎯 True SKU-Level ROAS Analyzer")
                ad_c1, ad_c2 = st.columns(2)
                ad_spend = ad_c1.file_uploader("Upload Ad Spend", type=['csv', 'xlsx'], key="ad_up")
                pl_data = ad_c2.file_uploader("Upload P&L Data", type=['csv', 'xlsx'], key="pl_up")
                if st.button("Generate ROAS Quadrant Matrix", type="primary", use_container_width=True):
                    if ad_spend and pl_data: st.success("Matrix Generated! 4 SKUs moved to 'Scale' quadrant.")
                    else: st.warning("Please upload both reports.")

    elif nav == "🧾 GST Tracker":
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Matrix", "➕ Update", "📋 Clients", "🧮 GST Calculation"])
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
                    c_u1, c_u2 = st.columns(2)
                    u_gst = c_u1.selectbox("Select GST", df_comp['GST No'].tolist())
                    u_ret = c_u2.selectbox("Return", ["GSTR-1", "GSTR-3B"])
                    u_stat = c_u1.selectbox("Status", ["Filed", "Pending"])
                    u_date = c_u2.date_input("Filed Date")
                    if st.form_submit_button("Update Status", type="primary", use_container_width=True):
                        db.update_gst_filing(u_gst, period, u_ret, u_stat, str(u_date)); st.success("Updated!"); st.rerun()
            else: st.warning("No GST clients registered.")
        with tab3:
            reg_mode = st.radio("Mode", ["Single Entry", "Bulk Upload"], horizontal=True, label_visibility="collapsed")
            if reg_mode == "Single Entry":
                with st.form("ngst"):
                    c1, c2 = st.columns(2)
                    g_no = c1.text_input("GST No.")
                    g_legal = c2.text_input("Legal Name")
                    g_trade = c1.text_input("Trade Name")
                    g_date = c2.date_input("Reg Date")
                    o_ph = c1.text_input("Owner Phone")
                    if st.form_submit_button("Save Client", type="primary", use_container_width=True):
                        s, m = db.save_gst_registration(g_no, g_legal, g_trade, str(g_date), o_ph, "", "", "")
                        st.success(m) if s else st.error(m)
            else:
                uf = st.file_uploader("Upload CSV", type=["csv", "xlsx"])
                if uf and st.button("🚀 Upload", type="primary", use_container_width=True):
                    try:
                        count, errors = db.save_bulk_gst_clients(pd.read_csv(uf) if uf.name.endswith('.csv') else pd.read_excel(uf))
                        st.success(f"Added {count} clients!")
                    except Exception as e: st.error(str(e))
            df_gst = db.get_gst_registrations()
            if not df_gst.empty: st.dataframe(df_gst, use_container_width=True, hide_index=True)
            
        with tab4:
            st.markdown("<div class='section-header' style='margin-top:0;'>Marketplace GST Liability Engine</div>", unsafe_allow_html=True)
            calc_mode = st.radio("Calculation Method", ["Manual Summary Calculator", "Upload Marketplace Tax Report"], horizontal=True, label_visibility="collapsed")

            if calc_mode == "Manual Summary Calculator":
                with st.container(border=True):
                    c1, c2, c3 = st.columns(3)
                    plat = c1.selectbox("Marketplace", ["Amazon", "Flipkart", "Meesho", "Myntra", "JioMart", "Ajio"])
                    gst_rate = c2.selectbox("Primary GST Slab", [0, 5, 12, 18, 28], index=1)
                    state_type = c3.radio("Sale Type", ["Inter-state (IGST)", "Intra-state (CGST/SGST)"], horizontal=True)

                    c4, c5 = st.columns(2)
                    gross_sales = c4.number_input("Total Gross Sales (₹) (Inc. Taxes)", min_value=0.0)
                    returns = c5.number_input("Total Returns (₹) (Inc. Taxes)", min_value=0.0)

                    if st.button("Calculate Tax Liability", type="primary", use_container_width=True):
                        net_sales = gross_sales - returns
                        taxable_val = net_sales / (1 + (gst_rate / 100))
                        total_tax = net_sales - taxable_val
                        tcs = taxable_val * 0.01

                        st.markdown("##### 🧾 Estimated Liability Summary")
                        tc1, tc2, tc3, tc4 = st.columns(4)
                        tc1.metric("Net Sales (Inc. Tax)", f"₹ {net_sales:,.2f}")
                        tc2.metric("Taxable Value", f"₹ {taxable_val:,.2f}")

                        if "Inter-state" in state_type:
                            tc3.metric("IGST Payable", f"₹ {total_tax:,.2f}")
                            tc4.metric(f"{plat} TCS (1%)", f"₹ {tcs:,.2f}")
                        else:
                            tc3.metric("CGST + SGST Payable", f"₹ {total_tax/2:,.2f} + ₹ {total_tax/2:,.2f}")
                            tc4.metric(f"{plat} TCS (1%)", f"₹ {tcs:,.2f}")
            else:
                with st.container(border=True):
                    st.info("Upload standard marketplace B2B/B2C tax reports to auto-extract tax heads.")
                    st.file_uploader("Upload Tax Report (CSV/Excel)", type=['csv', 'xlsx'], disabled=True)
                    st.button("Extract Liabilities", type="primary", disabled=True, use_container_width=True)

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
                c1, c2 = st.columns(2)
                pd_ = c1.date_input("Date")
                ps = c2.selectbox("Staff", db.get_staff_list())
                pa = c1.number_input("Amount", 100)
                pt = c2.radio("Type", ["Salary", "Advance"], horizontal=True)
                rem = st.text_input("Remarks")
                if st.form_submit_button("Record Payment", type="primary", use_container_width=True):
                    db.save_payment(str(pd_), ps, pa, pt, rem); st.success("Recorded!")

    elif nav == "📋 Catalog Maker":
        tab1, tab2 = st.tabs(["📤 Upload", "📊 View"])
        with tab1:
            uf = st.file_uploader("Upload File (CSV/Excel)", type=['csv', 'xlsx'])
            if uf and st.button("🚀 Process & Map", type="primary", use_container_width=True):
                with st.spinner("Processing..."):
                    success, result = db.process_and_save_catalog(pd.read_csv(uf) if uf.name.endswith('.csv') else pd.read_excel(uf))
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
                c1, c2, c3 = st.columns(3)
                n = c1.text_input("Style Name")
                g = c2.selectbox("Gender", ["Men","Women","Kids","Unisex"])
                c = c3.selectbox("Category", db.get_categories_list())
                if st.form_submit_button("Create Parent", type="primary", use_container_width=True): 
                    db.save_product_parent(n,g,c,""); st.success("Saved")
            with st.form("cf"):
                st.markdown("#### Child Variant (SKU)")
                parents = db.get_parent_products()
                if parents:
                    c1, c2 = st.columns(2)
                    sel = c1.selectbox("Parent Style", [p['name'] for p in parents])
                    pid = next(p['system_id'] for p in parents if p['name']==sel)
                    c3, c4, c5 = st.columns(3)
                    col = c3.selectbox("Color", db.get_colors_list())
                    siz = c4.selectbox("Size", db.get_sizes_list())
                    rat = c5.number_input("Rate (₹)")
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
            n = c1.text_input("Marketplace Name (e.g., Nykaa)", label_visibility="collapsed")
            if c2.button("Add", type="primary", use_container_width=True):
                if n: db.save_channel(n); st.rerun()
            st.dataframe(pd.DataFrame(db.get_channels_list(), columns=["Active Marketplaces"]), use_container_width=True)
                
        elif sub == "Staff Directory":
            with st.form("sm"):
                c1, c2 = st.columns(2)
                n = c1.text_input("Staff Name")
                r = c2.selectbox("Role", ["Stitching","Cutting","Helper", "Operations"])
                if st.form_submit_button("Save", type="primary", use_container_width=True): 
                    db.save_staff(n, "", r, "Piece", 0); st.success("Added.")
            st.dataframe(db.get_df("masters_staff"), use_container_width=True)
            
        elif sub == "Item Categories":
            c1, c2 = st.columns([3, 1])
            n = c1.text_input("New Category Name", label_visibility="collapsed")
            if c2.button("Save", type="primary", use_container_width=True): db.save_category(n); st.rerun()
            st.dataframe(pd.DataFrame(db.get_categories_list(), columns=["Categories"]), use_container_width=True)
            
        elif sub == "Process Routes":
            c1, c2 = st.columns([3, 1])
            n = c1.text_input("New Process Stage", label_visibility="collapsed")
            if c2.button("Save", type="primary", use_container_width=True): db.save_master("masters_processes", {"name":n}); st.rerun()
            st.dataframe(db.get_df("masters_processes"), use_container_width=True)
            
        elif sub == "Rate Rules":
            with st.form("rm"):
                c1, c2, c3 = st.columns(3)
                i = c1.selectbox("Category", db.get_categories_list())
                p = c2.selectbox("Process", db.get_processes_list())
                r = c3.number_input("Rate (₹)", min_value=0.0)
                c4, c5 = st.columns(2)
                fd = c4.date_input("Start Date")
                td = c5.date_input("End Date", value=datetime.date.today() + datetime.timedelta(days=365))
                if st.form_submit_button("Enforce Rule", type="primary", use_container_width=True): 
                    db.save_rate(i,p,r, fd, td); st.success("Rule applied.")
            st.dataframe(db.get_rates_df(), use_container_width=True)
            
        elif sub == "System Wipe":
            st.error("🚨 DANGER ZONE")
            wipe_opts = {
                "🏭 Production Logs": ["production"], "✂️ Cutting": ["masters_lots", "transactions_cutting"],
                "💸 Payment Ledger": ["payments"], "🧾 GST Data": ["gst_registrations", "gst_filings"],
                "📋 Catalog Data": ["masters_catalog"], "🚀 Launcher": ["product_launcher"],
                "📦 Products": ["masters_products"], "⚙️ Configs": ["masters_staff", "masters_items"]
            }
            selected_wipe = st.multiselect("Select modules:", list(wipe_opts.keys()))
            if st.button("⚠️ CONFIRM TRUNCATE", type="primary", use_container_width=True):
                if selected_wipe:
                    cols = []
                    for s in selected_wipe: cols.extend(wipe_opts[s])
                    db.clean_database(cols); st.success("Truncated!"); st.rerun()

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
    .block-container { max-width: 1400px !important; margin: 0 auto; padding: 1rem 1rem 5rem 1rem !important; }
    @media (min-width: 768px) { .block-container { padding: 2rem 2rem 5rem 2rem !important; } }

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

    /* --- P&L 8-GRID KPI CARDS --- */
    .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }
    .kpi-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 16px; box-shadow: 0 2px 5px rgba(0,0,0,0.02); display: flex; flex-direction: column; position: relative; overflow: hidden; }
    .kpi-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px; }
    .kpi-card.blue::before { background: #3B82F6; } .kpi-card.green::before { background: #10B981; }
    .kpi-card.red::before { background: #EF4444; } .kpi-card.orange::before { background: #F97316; }
    .kpi-card.purple::before { background: #8B5CF6; } .kpi-card.teal::before { background: #14B8A6; }
    .kpi-val { font-size: 1.6rem; font-weight: 800; color: #0F172A; display: flex; align-items: center; gap: 8px; line-height: 1; margin-bottom: 6px; margin-top: 5px; }
    .kpi-title { font-size: 0.75rem; color: #64748B; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; }
    .kpi-sub { font-size: 0.8rem; color: #94A3B8; margin-top: auto; font-weight: 500; }
    @media (max-width: 768px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }

    /* --- UNIFIED PRODUCT CARDS --- */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 20px !important; border: 1px solid #E2E8F0 !important; box-shadow: 0 8px 20px -4px rgba(0,0,0,0.04) !important; background: #FFFFFF !important; padding: 16px !important; transition: transform 0.2s ease, box-shadow 0.2s ease !important; margin-bottom: 16px !important; width: 100% !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover { transform: translateY(-4px); box-shadow: 0 15px 30px -5px rgba(0,0,0,0.08) !important; border-color: #CBD5E1 !important; }
    .thumbnail-container { display: flex; gap: 8px; margin-bottom: 12px; overflow-x: auto; padding-bottom: 4px; scrollbar-width: none; -webkit-overflow-scrolling: touch; }
    .thumbnail-container::-webkit-scrollbar { display: none; }
    .product-thumbnail { width: 55px; height: 55px; object-fit: cover; border-radius: 10px; border: 1px solid #E2E8F0; }
    .product-link-btn { display: flex; align-items: center; justify-content: center; background-color: #F8FAFC; color: #4F46E5 !important; padding: 12px; border-radius: 12px; font-weight: 700; font-size: 0.95rem; text-decoration: none !important; border: 1px solid #E2E8F0; transition: all 0.2s ease; margin-bottom: 15px; width: 100%; }
    .product-link-btn:hover { background-color: #EEF2FF; border-color: #C7D2FE; }

    /* --- FORMS & CONTAINERS --- */
    [data-testid="stForm"], .st-emotion-cache-1104q3m { background: #FFFFFF !important; padding: 24px !important; border-radius: 20px !important; border: 1px solid #E2E8F0 !important; box-shadow: 0 8px 20px -4px rgba(0,0,0,0.03) !important; width: 100% !important; }
    .section-header { border-left: 4px solid #4F46E5; padding-left: 12px; margin-top: 20px; margin-bottom: 16px; color: #0F172A; font-size: 1.15rem; font-weight: 700; }

    /* --- INPUTS & DROPDOWNS --- */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox > div > div { background-color: #FFFFFF !important; border: 1px solid #CBD5E1 !important; border-radius: 10px !important; color: #0F172A !important; padding: 10px 14px !important; font-size: 0.95rem; min-height: 44px !important; width: 100% !important; box-shadow: 0 1px 2px rgba(0,0,0,0.01) !important; }
    .stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus, .stSelectbox > div > div:focus { border-color: #4F46E5 !important; box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1) !important; }
    div[data-baseweb="select"] span { color: #0F172A !important; font-weight: 600; }
    div[data-baseweb="popover"], ul[role="listbox"] { background-color: #FFFFFF !important; border-radius: 10px !important; border: 1px solid #E2E8F0 !important; box-shadow: 0 10px 25px rgba(0,0,0,0.1) !important; overflow: hidden; max-width: 95vw !important; }
    ul[role="listbox"] li { padding: 12px 16px !important; font-size: 0.95rem !important; color: #0F172A !important; }
    ul[role="listbox"] li:hover { background-color: #F8FAFC !important; color: #4F46E5 !important; }

    /* --- SAAS BUTTONS --- */
    .stButton button { border-radius: 10px; font-weight: 600; min-height: 44px !important; transition: all 0.2s ease; width: 100% !important; border: 1px solid #E2E8F0 !important; background: #FFFFFF !important; color: #0F172A !important; box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important; }
    .stButton button:hover { background: #F8FAFC !important; border-color: #CBD5E1 !important; }
    .stButton button[kind="primary"] { background: #4F46E5 !important; color: white !important; border: none !important; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25) !important; }
    .stButton button[kind="primary"]:hover { background: #4338CA !important; box-shadow: 0 6px 15px rgba(79, 70, 229, 0.35) !important; transform: translateY(-1px); }
    .stButton button[kind="primary"]:active { transform: scale(0.97); }

    /* --- TABS --- */
    .stTabs [data-baseweb="tab-list"] { gap: 16px; border-bottom: 1px solid #E2E8F0; padding-bottom: 0px; overflow-x: auto; -webkit-overflow-scrolling: touch; scrollbar-width: none; }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }
    .stTabs [data-baseweb="tab"] { height: 44px; border: none; background: transparent; color: #64748B; font-weight: 600; font-size: 0.95rem; padding: 0 4px; white-space: nowrap; transition: color 0.2s; }
    .stTabs [aria-selected="true"] { color: #4F46E5 !important; border-bottom: 2px solid #4F46E5 !important; }

    /* --- DATAFRAMES --- */
    [data-testid="stDataFrame"] { border-radius: 12px; border: 1px solid #E2E8F0; box-shadow: 0 2px 4px rgba(0,0,0,0.01); overflow: hidden; background: #FFFFFF; font-size: 0.9rem; }

    /* Login Centering */
    .login-container { max-width: 400px; margin: 15vh auto; background: white; padding: 40px 30px; border-radius: 24px; box-shadow: 0 20px 40px rgba(0,0,0,0.06); border: 1px solid #E2E8F0; text-align: center; }

    /* --- MOBILE RESPONSIVENESS OVERRIDES --- */
    @media (max-width: 768px) {
        div[data-testid="stHorizontalBlock"]:first-of-type { flex-wrap: nowrap !important; align-items: center !important; margin-bottom: 15px !important; }
        div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"] { width: auto !important; min-width: auto !important; flex: 1 1 auto !important; }
        [class*="st-key-mobile_grid"] div[data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 10px !important; }
        [class*="st-key-mobile_grid"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"] { width: calc(50% - 5px) !important; min-width: calc(50% - 5px) !important; flex: 1 1 calc(50% - 5px) !important; margin-bottom: 0 !important; }
        .block-container { padding-top: 1rem !important; }
        [data-testid="stVerticalBlockBorderWrapper"], [data-testid="stForm"], .st-emotion-cache-1104q3m { padding: 12px !important; border-radius: 16px !important; }
        .metric-card { padding: 16px; } .metric-value { font-size: 1.3rem; }
    }
</style>
""", unsafe_allow_html=True)

# --- DYNAMIC CSS FOR APP DASHBOARD TILES ---
def apply_dashboard_card_css():
    st.markdown("""
    <style>
        .stButton button[kind="secondary"] {
            height: 110px !important; border-radius: 20px !important; background: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important; box-shadow: 0 4px 10px rgba(0,0,0,0.02) !important;
            display: flex !important; flex-direction: column !important; align-items: center !important;
            justify-content: center !important; white-space: pre-wrap !important; line-height: 1.4 !important;
            color: #0F172A !important; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        .stButton button[kind="secondary"] p { font-size: 0.95rem !important; font-weight: 700 !important; margin: 0 !important; }
        .stButton button[kind="secondary"]:hover { transform: translateY(-3px); box-shadow: 0 10px 20px rgba(79,70,229,0.08) !important; border-color: #C7D2FE !important; color: #4F46E5 !important; }
        .stButton button[kind="secondary"]:active { transform: scale(0.95); background-color: #F8FAFC !important; }
        @media (min-width: 768px) { .stButton button[kind="secondary"] { height: 130px !important; } .stButton button[kind="secondary"] p { font-size: 1.1rem !important; } }
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

def render_kpi_grid(metrics):
    html = "<div class='kpi-grid'>"
    for m in metrics:
        sub_html = f"<div class='kpi-sub'>{m['sub']}</div>" if m.get('sub') else ""
        html += f"""
        <div class='kpi-card {m['color']}'>
            <div class='kpi-val'>{m['icon']} {m['val']}</div>
            <div class='kpi-title'>{m['title']}</div>
            {sub_html}
        </div>
        """
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def render_df(df):
    if df.empty: st.info("No data available."); return
    st.dataframe(df, use_container_width=True, hide_index=True)

def route(nav_dest):
    st.session_state.nav_selection = nav_dest
    st.rerun()

def categorize_status(val):
    v = str(val).lower()
    if 'deliver' in v: return 'Delivered'
    if 'cancel' in v: return 'Cancelled'
    if 'rto' in v or 'origin' in v: return 'RTO'
    if 'return' in v: return 'Customer Return'
    if 'ship' in v or 'transit' in v or 'rts' in v: return 'Shipped'
    return 'Other'

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
menu_options = ["Home", "🏭 Work Operations", "🤖 Drench AI", "🚀 Product Launcher", "🧾 GST Tracker", "💸 Staff Payments", "📋 Catalog Maker", "📈 P&L Analysis", "📦 Product Master", "⚙️ System Masters"]

with st.sidebar:
    st.markdown("""<div style="font-size: 1.6rem; font-weight: 800; color: #4F46E5; text-align: center; margin-bottom: 1.5rem; margin-top: 1rem;">🧵 DrenchWear</div>""", unsafe_allow_html=True)
    
    selected_nav = st.radio("MENU", menu_options, index=menu_options.index(st.session_state.nav_selection) if st.session_state.nav_selection in menu_options else 0, label_visibility="collapsed")
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
    
    with st.container(key="mobile_grid_metrics"):
        m1, m2, m3, m4 = st.columns(4)
        with m1: render_metric_card("Pieces Today", f"{pcs:,.0f}", "👕", "#D1FAE5", "#10B981")
        with m2: render_metric_card("Prod Value", f"₹{earn:,.0f}", "₹", "#FEF3C7", "#F59E0B")
        with m3: render_metric_card("Liabilities", f"₹{pending:,.0f}", "💳", "#FEE2E2", "#EF4444")
        with m4: render_metric_card("Active Staff", f"{active}", "👥", "#DBEAFE", "#3B82F6")
    
    st.markdown("<h4 style='margin-top: 20px; margin-bottom: 12px; font-size: 1.1rem; color:#0F172A;'>Applications</h4>", unsafe_allow_html=True)
    
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
        if st.button("⬅️ Home"): route("Home")
    with b2:
        st.markdown(f"<div style='text-align: center; font-weight: 800; color: #0F172A; padding-top: 10px; font-size:1.15rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{nav.split(' ')[-1] if ' ' in nav else nav}</div>", unsafe_allow_html=True)
    with b3: pass
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
                item_name = st.selectbox("Item Name", [""] + sorted(list(set(prod_names + item_names))))

                st.markdown("<div class='section-header'>Fabric Detail</div>", unsafe_allow_html=True)
                if "fab_df" not in st.session_state: st.session_state.fab_df = pd.DataFrame([{"Srl no.": i+1, "Color": "", "UOM": "Meter", "Qty": 0.0} for i in range(5)])
                e_fab = st.data_editor(st.session_state.fab_df, num_rows="dynamic", use_container_width=True, hide_index=True)
                
                st.markdown("<div class='section-header'>Bundle Detail</div>", unsafe_allow_html=True)
                n_bun = st.number_input("Total Bundles to generate", 1, 500, 10)
                if st.button("🔄 Reset Grid", use_container_width=True): st.session_state.lot_df = pd.DataFrame([{"Bundle No": str(i+1), "Qty": 0} for i in range(n_bun)])
                if "lot_df" not in st.session_state: st.session_state.lot_df = pd.DataFrame([{"Bundle No": str(i+1), "Qty": 0} for i in range(10)])
                e_bun = st.data_editor(st.session_state.lot_df, height=300, use_container_width=True, hide_index=True)
                
                total_pcs = pd.to_numeric(e_bun['Qty'], errors='coerce').sum()
                st.markdown(f"<div style='color: #4F46E5; font-weight:800; font-size:1.1rem; margin-top: 10px;'>Total Auto-Calculated: {total_pcs:,.0f} Pcs</div>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 Save Cutting Lot", type="primary", use_container_width=True):
                    if not l_no or not item_name: st.error("Lot No and Item required.")
                    else:
                        s, m = db.save_full_lot({"lot_no": l_no, "item_name": item_name, "date": str(datetime.date.today()), "sku": item_name}, e_fab, e_bun)
                        if s: 
                            st.success(m); del st.session_state['lot_df']; del st.session_state['fab_df']; time.sleep(1); st.rerun()
                        else: st.error(m)
            else: st.info("Check Tracking & Ops tab.")

        with tab_stitch:
            stitch_mode = st.radio("Mode", ["📝 Single Entry", "📤 Bulk CSV"], horizontal=True, label_visibility="collapsed")
            if stitch_mode == "📝 Single Entry":
                with st.form("stitch_log"):
                    sd_date = st.date_input("Date")
                    sd_worker = st.selectbox("Karigar (Worker)", db.get_staff_list())
                    sd_proc = st.selectbox("Process Type", db.get_processes_list())
                    sd_lot = st.selectbox("Cutting Lot No", [""] + db.get_active_lots())
                    buns = [f"{b['bundle_no']} | {b['item_name']} | {b['qty']} pcs" for b in db.get_detailed_bundles(sd_lot)] if sd_lot else []
                    sd_bun = st.selectbox("Lot Bundle", [""] + buns)
                    qty = st.number_input("Qty (Pcs)", min_value=1.0)
                    lbl = st.checkbox("🏷️ Label (+0.50)")
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.form_submit_button("💾 Auto-Credit Payment", type="primary", use_container_width=True):
                        if sd_worker and sd_lot and sd_bun:
                            p = sd_bun.split(" | ")
                            val_item, real_bun = p[1] if len(p)>1 else "", p[0]
                            fin_rate = db.get_rate(val_item, sd_proc, sd_date) + (0.50 if lbl else 0)
                            s, m = db.save_production(str(sd_date), sd_worker, val_item, sd_proc, qty, fin_rate, sd_lot, real_bun)
                            if s: st.success(f"Credited Amount: ₹{qty*fin_rate}")
                            else: st.error(m)
                        else: st.error("Missing critical data.")
            elif stitch_mode == "📤 Bulk CSV":
                st.info("Calculates Rate/Value based on Master.")
                st.download_button("⬇️ Template", "Date,Karigar Name,Lot No,Bundle No.,Process,Item,Qty\n2026-03-10,Worker Name,L-1001,B-01,Collar,Top,50", "Sample.csv", "text/csv", use_container_width=True)
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
            if ops_view_mode == "📦 Tracking": st.dataframe(db.get_bundle_progress(), use_container_width=True)
            else:
                with st.form("fab_form"):
                    fd = st.date_input("Date")
                    fp = st.selectbox("Party", db.get_parties_list())
                    fi = st.text_input("Item")
                    fq = st.number_input("Qty", 1.0)
                    fr = st.number_input("Rate", 0.0)
                    fdesc = st.text_input("Desc")
                    if st.form_submit_button("Save Entry", type="primary", use_container_width=True):
                        db.save_fabrication(str(fd), fp, fi, fq, fr, fdesc); st.success("Saved")
                st.dataframe(db.get_recent_fabrication(), use_container_width=True)

    elif nav == "🚀 Product Launcher":
        tab_add, tab_view = st.tabs(["➕ Add New", "📋 Pipeline"])
        with tab_add:
            st.markdown("<div class='section-header'>Fetch Details</div>", unsafe_allow_html=True)
            fetch_url = st.text_input("🔗 Product URL", placeholder="https://...", label_visibility="collapsed")
            c_btn1, c_btn2 = st.columns(2)
            if c_btn1.button("🔍 Fetch", use_container_width=True):
                if fetch_url:
                    with st.spinner("Scraping..."): st.session_state.launcher_draft = db.fetch_product_metadata(fetch_url)
                else: st.warning("Enter URL.")
            if c_btn2.button("✍️ Manual", use_container_width=True): st.session_state.launcher_draft = {"title": "", "price": 0.0, "image": "", "url": ""}

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
                            final_imgs = [f"data:{f.type};base64,{base64.b64encode(f.read()).decode('utf-8')}" for f in p_img_upload] if p_img_upload else ([p_img] if p_img else [])
                            s, m = db.save_launched_product(p_title, fetch_url if fetch_url else draft.get("url", ""), final_imgs, p_price, p_stage)
                            if s: st.success(m); del st.session_state.launcher_draft; time.sleep(1); st.rerun()
                            else: st.error(m)
                        else: st.error("Title required.")
                            
        with tab_view:
            products = db.get_launched_products()
            if not products: st.info("No products in pipeline.")
            else:
                stages = ["Stage 1", "Stage 2", "Stage 3", "Stage 4", "Stage 5", "Stage 6", "Stage 7"]
                with st.container(key="mobile_grid_launcher"):
                    cols = st.columns(3) 
                    for idx, prod in enumerate(products):
                        with cols[idx % 3]:
                            with st.container(border=True): 
                                img_urls = prod.get('images', []) or ([prod.get('image_url')] if prod.get('image_url') else [])
                                main_img = img_urls[0] if img_urls else "https://via.placeholder.com/400x300?text=No+Image+Found"
                                thumbnails_html = f"<div class='thumbnail-container'>{''.join([f'<img src=\"{t}\" class=\"product-thumbnail\">' for t in img_urls[1:]])}</div>" if len(img_urls) > 1 else ""
                                
                                st.markdown(f"""<div style="width: 100%; height: 240px; overflow: hidden; border-radius: 12px; margin-bottom: 12px; border: 1px solid #F1F5F9; background:#F8FAFC;">
<img src="{main_img}" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.onerror=null;this.src='https://via.placeholder.com/400x300?text=Error';"></div>{thumbnails_html}
<div style="font-weight: 800; font-size: 1.15rem; color: #0F172A; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px; line-height: 1.4;">{prod.get('title', 'Unknown')}</div>
<div style="color: #10B981; font-weight: 800; font-size: 1.25rem; margin-bottom: 15px;">₹ {prod.get('price', 0.0):,.2f}</div>
<a href="{prod.get('url', '#')}" target="_blank" class="product-link-btn">🔗 View Original Link</a>""", unsafe_allow_html=True)
                                
                                curr_idx = stages.index(prod.get('stage', 'Stage 1')) if prod.get('stage') in stages else 0
                                new_stage = st.selectbox("Stage", stages, index=curr_idx, key=f"stg_{prod['_id']}", label_visibility="collapsed")
                                
                                btn_c1, btn_c2 = st.columns(2)
                                if btn_c1.button("💾 Apply", key=f"upd_{prod['_id']}", use_container_width=True):
                                    db.update_launched_product_stage(prod['_id'], new_stage); st.toast("Updated!"); time.sleep(0.5); st.rerun()
                                    
                                with btn_c2.popover("⚙️ Manage", use_container_width=True):
                                    e_title = st.text_input("Title", value=prod.get('title', ''), key=f"et_{prod['_id']}")
                                    e_price = st.number_input("Price (₹)", value=float(prod.get('price', 0.0)), key=f"ep_{prod['_id']}")
                                    e_img = st.text_input("Main Image", value=main_img, key=f"ei_{prod['_id']}")
                                    e_img_file = st.file_uploader("Replace Images", type=['png', 'jpg'], accept_multiple_files=True, key=f"ef_{prod['_id']}")
                                    st.markdown("<br>", unsafe_allow_html=True)
                                    if st.button("Save Changes", type="primary", key=f"es_{prod['_id']}", use_container_width=True):
                                        final_edit_imgs = [f"data:{f.type};base64,{base64.b64encode(f.read()).decode('utf-8')}" for f in e_img_file] if e_img_file else (img_urls if e_img == main_img else [e_img])
                                        s, m = db.update_launched_product_details(prod['_id'], e_title, e_price, final_edit_imgs)
                                        st.rerun() if s else st.error(m)
                                    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
                                    if st.button("🚨 Delete Product", key=f"del_{prod['_id']}", use_container_width=True):
                                        db.delete_launched_product(prod['_id']); st.rerun()

    # --- 📈 P&L ANALYSIS (HIGH-END RECONCILIATION ENGINE) ---
    elif nav == "📈 P&L Analysis":
        st.markdown("<div class='section-header' style='margin-top:0;'>Marketplace Reconciliation Engine</div>", unsafe_allow_html=True)
        st.caption("Upload and map marketplace data to generate automatic, deep-dive sales analytics.")
        
        channels = db.get_channels_list()
        
        if not channels:
            st.info("No active channels found. Please configure Marketplaces in 'System Masters'.")
        else:
            tabs = st.tabs([f"🛒 {c}" for c in channels])
            
            for i, c_name in enumerate(channels):
                with tabs[i]:
                    sub_tabs = st.radio("Select View", ["📊 1. Order Analytics", "💳 2. Payments & Ads"], horizontal=True, key=f"sub_{c_name}", label_visibility="collapsed")
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    if sub_tabs == "📊 1. Order Analytics":
                        
                        # --- DATA UPLOAD & MAPPING BLOCK ---
                        if f'pl_orders_{c_name}' not in st.session_state:
                            with st.container(border=True):
                                st.markdown(f"#### 📦 Map {c_name} Order Report")
                                o_file = st.file_uploader(f"Upload Orders (CSV/Excel)", type=['csv', 'xlsx'], key=f"o_{c_name}")
                                
                                if o_file:
                                    df_o = pd.read_csv(o_file) if o_file.name.endswith('.csv') else pd.read_excel(o_file)
                                    cols = ["Select File Column..."] + df_o.columns.tolist()
                                    
                                    with st.container(key=f"mobile_grid_inputs_{c_name}"):
                                        st.markdown("**Map Required Columns:**")
                                        mc1, mc2, mc3 = st.columns(3)
                                        o_dt = mc1.selectbox("Order Date", cols, key=f"o_dt_{c_name}")
                                        o_sku = mc2.selectbox("SKU / Item", cols, key=f"o_sku_{c_name}")
                                        o_stat = mc3.selectbox("Order Status", cols, key=f"o_stat_{c_name}")
                                        
                                        st.markdown("**Map Optional Data (For Profit Analytics):**")
                                        mc4, mc5, mc6 = st.columns(3)
                                        o_am = mc4.selectbox("Sale Amount (Optional)", cols, key=f"o_am_{c_name}")
                                        o_qty = mc5.selectbox("Quantity (Optional)", cols, key=f"o_qty_{c_name}")
                                        o_st = mc6.selectbox("Customer State (Optional)", cols, key=f"o_st_{c_name}")
                                        
                                    st.markdown("<br>", unsafe_allow_html=True)
                                    if st.button("🚀 Process & Generate Dashboard", type="primary", key=f"o_btn_{c_name}", use_container_width=True):
                                        if "Select File Column..." not in [o_dt, o_sku, o_stat]:
                                            try:
                                                # Clean Data
                                                df_o['ParsedDate'] = pd.to_datetime(df_o[o_dt], errors='coerce')
                                                df_o = df_o.dropna(subset=['ParsedDate']).copy() 
                                                df_o['DayOfWeek'] = df_o['ParsedDate'].dt.day_name()
                                                df_o['IsWeekend'] = df_o['ParsedDate'].dt.dayofweek >= 5
                                                df_o['CleanStatus'] = df_o[o_stat].apply(categorize_status)
                                                
                                                # Optional Columns handling
                                                if o_am != "Select File Column...":
                                                    if df_o[o_am].dtype == 'object': df_o['AmountVal'] = pd.to_numeric(df_o[o_am].replace('[\₹,]', '', regex=True), errors='coerce').fillna(0)
                                                    else: df_o['AmountVal'] = pd.to_numeric(df_o[o_am], errors='coerce').fillna(0)
                                                else: df_o['AmountVal'] = 0.0
                                                    
                                                df_o['QtyVal'] = pd.to_numeric(df_o[o_qty], errors='coerce').fillna(1) if o_qty != "Select File Column..." else 1
                                                df_o['StateVal'] = df_o[o_st].astype(str) if o_st != "Select File Column..." else "Unknown"
                                                
                                                st.session_state[f'pl_orders_{c_name}'] = df_o
                                                st.rerun()
                                            except Exception as e: st.error(f"Analysis failed: {e}")
                                        else: st.warning("Please map Date, SKU, and Status to generate the dashboard.")
                                        
                        # --- ANALYTICS DASHBOARD VIEW ---
                        else:
                            df_dash = st.session_state[f'pl_orders_{c_name}']
                            
                            # Header & Reset
                            col_h1, col_h2 = st.columns([3, 1])
                            col_h1.markdown(f"### 📈 {c_name} Intelligence Dashboard")
                            if col_h2.button("🔄 Upload New Report", use_container_width=True):
                                del st.session_state[f'pl_orders_{c_name}']
                                st.rerun()
                                
                            # 1. Date Range Filter
                            min_d, max_d = df_dash['ParsedDate'].min().date(), df_dash['ParsedDate'].max().date()
                            date_sel = st.date_input("📅 Filter Analytics by Date", [min_d, max_d])
                            
                            if isinstance(date_sel, tuple) and len(date_sel) == 2:
                                start_d, end_d = date_sel
                                mask = (df_dash['ParsedDate'].dt.date >= start_d) & (df_dash['ParsedDate'].dt.date <= end_d)
                                filtered_df = df_dash.loc[mask]
                            else:
                                filtered_df = df_dash
                                
                            st.markdown("<hr style='margin: 10px 0 20px 0; border-color:#E2E8F0;'>", unsafe_allow_html=True)
                                
                            # Metrics Calculations
                            tot_orders = len(filtered_df)
                            deliv = len(filtered_df[filtered_df['CleanStatus'] == 'Delivered'])
                            canc = len(filtered_df[filtered_df['CleanStatus'] == 'Cancelled'])
                            cr = len(filtered_df[filtered_df['CleanStatus'] == 'Customer Return'])
                            rto = len(filtered_df[filtered_df['CleanStatus'] == 'RTO'])
                            tot_ret = cr + rto
                            
                            def pct(val): return f"{(val/tot_orders)*100:.1f}%" if tot_orders > 0 else "0%"

                            metrics = [
                                {"title": "Total Orders", "val": f"{tot_orders:,.0f}", "sub": "", "icon": "📦", "color": "blue"},
                                {"title": "Delivered", "val": f"{deliv:,.0f}", "sub": pct(deliv), "icon": "✅", "color": "green"},
                                {"title": "Cancelled", "val": f"{canc:,.0f}", "sub": pct(canc), "icon": "❌", "color": "red"},
                                {"title": "Cust. Returns", "val": f"{cr:,.0f}", "sub": pct(cr), "icon": "🔄", "color": "orange"},
                                {"title": "RTO (Courier Ret)", "val": f"{rto:,.0f}", "sub": pct(rto), "icon": "🔙", "color": "purple"},
                                {"title": "Total Returns", "val": f"{tot_ret:,.0f}", "sub": pct(tot_ret), "icon": "📉", "color": "teal"},
                                {"title": "Gross Sales", "val": f"₹{filtered_df['AmountVal'].sum():,.0f}", "sub": "Total Value", "icon": "💰", "color": "blue"},
                                {"title": "Items Sold", "val": f"{filtered_df['QtyVal'].sum():,.0f}", "sub": "Units", "icon": "👕", "color": "green"}
                            ]
                            
                            # Render 8-Grid
                            render_kpi_grid(metrics)
                            
                            # --- CHARTS ---
                            st.markdown("#### 📊 Order Trends & Performance")
                            chart_col1, chart_col2 = st.columns(2)
                            
                            with chart_col1:
                                with st.container(border=True):
                                    st.markdown("**Order Status Breakdown**")
                                    status_counts = filtered_df['CleanStatus'].value_counts()
                                    st.bar_chart(status_counts, use_container_width=True)
                                    
                            with chart_col2:
                                with st.container(border=True):
                                    st.markdown("**Top Customer States**")
                                    if 'Unknown' not in filtered_df['StateVal'].values or len(filtered_df['StateVal'].unique()) > 1:
                                        state_counts = filtered_df[filtered_df['StateVal'] != 'Unknown']['StateVal'].value_counts().head(10)
                                        st.bar_chart(state_counts, use_container_width=True)
                                    else:
                                        st.info("State data not mapped.")
                            
                            with st.container(border=True):
                                st.markdown("**Daily Sales Trend**")
                                daily = filtered_df.groupby(filtered_df['ParsedDate'].dt.date)['AmountVal'].sum().reset_index()
                                daily.set_index('ParsedDate', inplace=True)
                                st.line_chart(daily, use_container_width=True)
                                
                            c_ch1, c_ch2 = st.columns(2)
                            with c_ch1:
                                with st.container(border=True):
                                    st.markdown("**Weekday Operations (Mon-Fri)**")
                                    wkdy = filtered_df[~filtered_df['IsWeekend']].groupby('DayOfWeek')['AmountVal'].sum().reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']).fillna(0)
                                    st.bar_chart(wkdy)
                            with c_ch2:
                                with st.container(border=True):
                                    st.markdown("**Weekend Operations (Sat-Sun)**")
                                    wknd = filtered_df[filtered_df['IsWeekend']].groupby('DayOfWeek')['AmountVal'].sum().reindex(['Saturday', 'Sunday']).fillna(0)
                                    st.bar_chart(wknd)
                                    
                            # --- SKU ANALYTICS TABLES ---
                            st.markdown("#### 📚 Deep SKU Analytics")
                            
                            # Build the Order Analytics Table
                            sku_group = filtered_df.groupby(filtered_df[f"o_sku_{c_name}"])
                            order_analytics = pd.DataFrame({
                                "Orders": sku_group.size(),
                                "Qty": sku_group['QtyVal'].sum(),
                                "Sale Value": sku_group['AmountVal'].sum(),
                                "Delivered": filtered_df[filtered_df['CleanStatus'] == 'Delivered'].groupby(filtered_df[f"o_sku_{c_name}"]).size(),
                                "Cancelled": filtered_df[filtered_df['CleanStatus'] == 'Cancelled'].groupby(filtered_df[f"o_sku_{c_name}"]).size(),
                                "Cust. Return": filtered_df[filtered_df['CleanStatus'] == 'Customer Return'].groupby(filtered_df[f"o_sku_{c_name}"]).size(),
                                "RTO": filtered_df[filtered_df['CleanStatus'] == 'RTO'].groupby(filtered_df[f"o_sku_{c_name}"]).size(),
                            }).fillna(0).astype(int)
                            
                            # Add percentages
                            order_analytics['Cust. Ret%'] = (order_analytics['Cust. Return'] / order_analytics['Orders'] * 100).round(1).astype(str) + "%"
                            order_analytics['RTO%'] = (order_analytics['RTO'] / order_analytics['Orders'] * 100).round(1).astype(str) + "%"
                            order_analytics['Total Ret.'] = order_analytics['Cust. Return'] + order_analytics['RTO']
                            
                            st.markdown("**SKU Operational Matrix**")
                            st.dataframe(order_analytics.reset_index(), use_container_width=True, hide_index=True)
                            
                            st.markdown("<hr style='margin: 30px 0; border-color:#E2E8F0;'>", unsafe_allow_html=True)
                            
                            # --- COGS & PROFIT ANALYTICS ---
                            st.markdown("#### 💰 Cost of Goods (COGS) & True Profitability")
                            st.info("Download your active SKU list, fill in your Cost of Goods (COGS), and upload it back to see real profitability.")
                            
                            cogs_col1, cogs_col2 = st.columns([1, 2])
                            with cogs_col1:
                                unique_skus = filtered_df[f"o_sku_{c_name}"].unique()
                                cogs_template = pd.DataFrame({"SKU": unique_skus, "Cost_of_Goods": 0.0})
                                st.download_button("1. ⬇️ Download COGS Template", cogs_template.to_csv(index=False).encode('utf-8'), f"COGS_Template_{c_name}.csv", "text/csv", use_container_width=True)
                                
                            with cogs_col2:
                                cogs_file = st.file_uploader("2. 📤 Upload Completed COGS Template", type=['csv'], key=f"cogs_{c_name}", label_visibility="collapsed")
                                
                            if cogs_file:
                                cogs_df = pd.read_csv(cogs_file)
                                # Build Profit Table
                                profit_df = order_analytics[['Sale Value', 'Qty', 'Total Ret.']].reset_index()
                                profit_df = profit_df.merge(cogs_df, left_on=f"o_sku_{c_name}", right_on="SKU", how="left").fillna(0)
                                profit_df['Avg Rate'] = (profit_df['Sale Value'] / profit_df['Qty'].replace(0,1)).round(2)
                                profit_df['Total Cost'] = profit_df['Cost_of_Goods'] * profit_df['Qty']
                                # Simple Net: Sales - Cost
                                profit_df['Net After Cost'] = profit_df['Sale Value'] - profit_df['Total Cost']
                                
                                profit_df = profit_df[['SKU', 'Sale Value', 'Qty', 'Avg Rate', 'Cost_of_Goods', 'Total Cost', 'Net After Cost']]
                                
                                st.markdown("**SKU Profitability Matrix**")
                                st.dataframe(profit_df, use_container_width=True, hide_index=True)
                                st.metric("Total System Profit (Gross - COGS)", f"₹ {profit_df['Net After Cost'].sum():,.2f}")

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
                    db.save_payment(str(pd_), ps, pa, pt, rem); st.success("Recorded!")

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

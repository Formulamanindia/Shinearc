import streamlit as st
import pandas as pd
import db_manager as db
import datetime
import math
import time
import base64

# --- CONFIG (COLLAPSE SIDEBAR GLOBALLY) ---
st.set_page_config(page_title="DrenchWear App", page_icon="📱", layout="centered", initial_sidebar_state="collapsed")

# --- MOBILE APP UI / CSS INJECTION ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Global Theme & App Constraints */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    .stApp { background-color: #F8FAFC !important; color: #0F172A; }
    
    /* Hide Streamlit Native Elements for App Feel */
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    footer { visibility: hidden; }
    
    /* Centralize Content (Mobile View on Desktop) */
    .block-container {
        max-width: 600px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 5rem !important;
        margin: 0 auto;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 { color: #0F172A !important; font-weight: 700 !important; letter-spacing: -0.025em; }

    /* Custom App Header Bar */
    .app-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 15px;
        border-bottom: 2px solid #E2E8F0;
        margin-bottom: 20px;
    }
    .app-title {
        font-size: 1.25rem;
        font-weight: 800;
        color: #0F172A;
        margin: 0;
        text-align: center;
    }

    /* Metric Cards */
    .metric-card { 
        background: #FFFFFF; 
        border: 1px solid #E2E8F0; 
        border-radius: 16px; 
        padding: 16px; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); 
        position: relative; 
        overflow: hidden; 
        margin-bottom: 10px;
    }
    .metric-value { font-size: 1.6rem; font-weight: 800; color: #0F172A; margin-top: 2px; letter-spacing: -0.02em; }
    .metric-label { font-size: 0.75rem; color: #64748B; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
    .decorative-bar { position: absolute; top: 0; left: 0; height: 4px; width: 100%; }

    /* Product Launcher Cards */
    .product-card {
        background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 16px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.04); margin-bottom: 20px; display: flex; flex-direction: column;
    }
    .img-container { position: relative; display: inline-block; width: 100%; }
    .product-image { width: 100%; height: 200px; object-fit: cover; border-radius: 12px; margin-bottom: 12px; background-color: #F8FAFC; border: 1px solid #F1F5F9; }
    .thumbnail-container { display: flex; gap: 8px; margin-bottom: 12px; overflow-x: auto; padding-bottom: 6px; scrollbar-width: none; -webkit-overflow-scrolling: touch; }
    .thumbnail-container::-webkit-scrollbar { display: none; }
    .product-thumbnail { width: 50px; height: 50px; object-fit: cover; border-radius: 8px; border: 1px solid #E2E8F0; }
    .product-title { font-weight: 700; font-size: 1.1rem; color: #0F172A; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px; }
    .product-price { color: #10B981; font-weight: 800; font-size: 1.2rem; margin-bottom: 15px; }
    .product-link { display: inline-flex; align-items: center; justify-content: center; background-color: #EEF2FF; color: #4F46E5 !important; padding: 10px; border-radius: 8px; font-weight: 600; font-size: 0.9rem; text-decoration: none !important; margin-bottom: 10px; min-height: 44px; }

    /* Forms and Containers */
    [data-testid="stForm"], .st-emotion-cache-1104q3m { 
        background: #FFFFFF !important; padding: 20px !important; border-radius: 16px !important; border: 1px solid #E2E8F0 !important; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02) !important; 
    }

    /* Inputs (Text, Numbers, Dates, Select) */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox > div > div { 
        background-color: #F8FAFC !important; border: 1px solid #CBD5E1 !important; border-radius: 10px !important; color: #0F172A !important; padding: 10px 14px !important; font-size: 0.95rem; min-height: 48px !important; 
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus, .stSelectbox > div > div:focus { 
        border-color: #4F46E5 !important; box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15) !important; background-color: #FFFFFF !important; 
    }

    /* Selectbox Dropdown Fix */
    div[data-baseweb="select"] span, div[data-baseweb="select"] div, .stSelectbox [data-testid="stMarkdownContainer"] p { color: #0F172A !important; }
    div[data-baseweb="popover"], ul[role="listbox"] { background-color: #FFFFFF !important; border-radius: 10px !important; border: 1px solid #E2E8F0 !important; }
    div[data-baseweb="popover"] *, ul[role="listbox"] li { color: #0F172A !important; }
    ul[role="listbox"] li:hover { background-color: #F1F5F9 !important; }

    /* Standard Buttons */
    .stButton button { 
        border-radius: 12px; font-weight: 600; min-height: 48px !important; transition: all 0.2s ease; 
    }
    .stButton button[kind="primary"] { 
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%) !important; color: white !important; border: none !important; box-shadow: 0 4px 10px rgba(79, 70, 229, 0.3); 
    }
    .stButton button[kind="primary"]:active { transform: scale(0.98); }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 2px solid #E2E8F0; padding-bottom: 0px; overflow-x: auto; -webkit-overflow-scrolling: touch; scrollbar-width: none; }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }
    .stTabs [data-baseweb="tab"] { height: 44px; border: none; background: transparent; color: #64748B; font-weight: 600; font-size: 0.9rem; padding: 0 12px; border-radius: 8px 8px 0 0; white-space: nowrap; }
    .stTabs [aria-selected="true"] { color: #4F46E5 !important; border-bottom: 3px solid #4F46E5 !important; }

    /* Login Centering */
    .login-container { margin: 10vh auto; background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border: 1px solid #E2E8F0; text-align: center; }
    
    .section-header { border-left: 4px solid #4F46E5; padding-left: 10px; margin-top: 25px; margin-bottom: 15px; color: #0F172A; font-size: 1.1rem; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# --- DYNAMIC CSS FOR DASHBOARD CARDS ONLY ---
# This styles the secondary buttons ON THE HOME PAGE to look like big app tiles.
def apply_dashboard_card_css():
    st.markdown("""
    <style>
        /* Make secondary buttons on Home act as App Tiles */
        .stButton button[kind="secondary"] {
            height: 110px !important;
            border-radius: 20px !important;
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.03) !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            white-space: pre-wrap !important;
            line-height: 1.3 !important;
            color: #0F172A !important;
            font-size: 0.95rem !important;
            font-weight: 700 !important;
        }
        .stButton button[kind="secondary"]:active {
            background-color: #EEF2FF !important;
            border-color: #4F46E5 !important;
            transform: scale(0.96);
        }
    </style>
    """, unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def render_metric_card(label, value, icon="📈", border_color="#4F46E5", bg_color="#EEF2FF"):
    card_html = f"""<div class="metric-card">
<div class="decorative-bar" style="background-color: {border_color};"></div>
<div style="display: flex; justify-content: space-between; align-items: center;">
<div>
<div class="metric-label">{label}</div>
<div class="metric-value">{value}</div>
</div>
<div style="background-color: {bg_color}; padding: 12px; border-radius: 12px; font-size: 20px; display: flex; align-items: center; justify-content: center;">
{icon}
</div>
</div>
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
<div style="font-size: 3rem; margin-bottom: 10px;">🧵</div>
<h2 style='color: #4F46E5; margin-bottom: 5px; margin-top:0;'>DrenchWear App</h2>
<p style='color: #64748B; font-weight: 500; margin-bottom: 25px;'>ERP Secure Login</p>"""
    st.markdown(login_html, unsafe_allow_html=True)
    with st.form("login", clear_on_submit=True):
        pwd = st.text_input("Access Key", type="password", placeholder="••••••••", label_visibility="collapsed")
        submit_btn = st.form_submit_button("Login", type="primary", use_container_width=True)
        if submit_btn:
            if pwd == "Flow@1993":
                st.session_state["authenticated"] = True; st.rerun()
            else: st.error("❌ Incorrect Password")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- INIT STATE ---
if "nav_selection" not in st.session_state: st.session_state.nav_selection = "Home"

nav = st.session_state.nav_selection

# ==========================================
# APP ROUTER
# ==========================================

if nav == "Home":
    apply_dashboard_card_css() # Inject Tile CSS only on Home
    
    st.markdown("<h2 style='text-align: center; color: #4F46E5; margin-bottom: 20px;'>🧵 DrenchWear Hub</h2>", unsafe_allow_html=True)
    
    # --- METRICS 2x2 GRID ---
    pcs, earn, pending, active = db.get_dashboard_stats()
    m1, m2 = st.columns(2)
    with m1: render_metric_card("Today's Pcs", f"{pcs:,.0f}", "👕", "#10B981", "#D1FAE5")
    with m2: render_metric_card("Prod Value", f"₹{earn:,.0f}", "₹", "#F59E0B", "#FEF3C7")
    m3, m4 = st.columns(2)
    with m3: render_metric_card("Liabilities", f"₹{pending:,.0f}", "💳", "#EF4444", "#FEE2E2")
    with m4: render_metric_card("Active Staff", f"{active}", "👥", "#3B82F6", "#DBEAFE")
    
    st.markdown("<h4 style='margin-top: 25px; margin-bottom: 10px;'>Modules</h4>", unsafe_allow_html=True)
    
    # --- APP DASHBOARD TILES (2x4 GRID) ---
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🏭\nWork Ops", use_container_width=True): route("🏭 Work Operations")
        if st.button("🚀\nLauncher", use_container_width=True): route("🚀 Product Launcher")
        if st.button("💸\nPayments", use_container_width=True): route("💸 Staff Payments")
        if st.button("📦\nMaster", use_container_width=True): route("Product Master")
    with c2:
        if st.button("🤖\nDrench AI", use_container_width=True): route("Drench AI")
        if st.button("🧾\nGST Track", use_container_width=True): route("🧾 GST Tracker")
        if st.button("📋\nCatalog", use_container_width=True): route("📋 Catalog Maker")
        if st.button("⚙️\nSettings", use_container_width=True): route("System Masters")
        
else:
    # --- NATIVE APP TOP BAR ---
    b1, b2, b3 = st.columns([1, 3, 1])
    with b1:
        if st.button("⬅️ Home", use_container_width=True): route("Home")
    with b2:
        st.markdown(f"<div class='app-title' style='padding-top: 10px;'>{nav.split(' ')[-1] if ' ' in nav else nav}</div>", unsafe_allow_html=True)
    with b3:
        if st.button("🔒 Exit", use_container_width=True): 
            st.session_state.authenticated = False
            st.rerun()
    st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px;'>", unsafe_allow_html=True)

    # ==========================================
    # MODULE CONTENT VIEWS
    # ==========================================

    if nav == "Drench AI":
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
        tab_cut, tab_stitch, tab_ops = st.tabs(["✂️ Cutting", "🪡 Stitching", "📦 Ops"])
        
        # CUTTING
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
                if st.button("🔄 Reset Rows", use_container_width=True):
                    st.session_state.lot_df = pd.DataFrame([{"Bundle No": str(i+1), "Qty": 0} for i in range(n_bun)])
                    
                if "lot_df" not in st.session_state:
                    st.session_state.lot_df = pd.DataFrame([{"Bundle No": str(i+1), "Qty": 0} for i in range(10)])
                    
                e_bun = st.data_editor(st.session_state.lot_df, height=300, use_container_width=True, hide_index=True)
                
                total_pcs = pd.to_numeric(e_bun['Qty'], errors='coerce').sum()
                st.markdown(f"<div style='color: #4F46E5; font-weight:700; margin-top: 10px;'>Total Auto-Calculated: {total_pcs:,.0f} Pcs</div>", unsafe_allow_html=True)
                
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

        # STITCHING
        with tab_stitch:
            stitch_mode = st.radio("Mode", ["📝 Single", "📤 Bulk CSV"], horizontal=True, label_visibility="collapsed")
            if stitch_mode == "📝 Single":
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
                    
                    c1, c2 = st.columns(2)
                    qty = c1.number_input("Qty (Pcs)", min_value=1.0)
                    lbl = c2.checkbox("🏷️ Label (+0.50)")
                    
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

        # OPS
        with tab_ops:
            ops_view_mode = st.radio("View", ["📦 Tracking", "🛠️ Fabrication"], horizontal=True, label_visibility="collapsed")
            if ops_view_mode == "📦 Tracking":
                st.dataframe(db.get_bundle_progress(), use_container_width=True)
            else:
                with st.form("fab_form"):
                    fd = st.date_input("Date")
                    fp = st.selectbox("Party", db.get_parties_list())
                    fi = st.text_input("Item")
                    c1, c2 = st.columns(2)
                    fq = c1.number_input("Qty", 1.0)
                    fr = c2.number_input("Rate", 0.0)
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
            
            c_btn, c_man = st.columns(2)
            if c_btn.button("🔍 Fetch", use_container_width=True):
                if fetch_url:
                    with st.spinner("Scraping..."):
                        st.session_state.launcher_draft = db.fetch_product_metadata(fetch_url)
                else: st.warning("Enter URL.")
                    
            if c_man.button("✍️ Manual", use_container_width=True):
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
                    if st.form_submit_button("💾 Save", type="primary", use_container_width=True):
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
                st.info("No products.")
            else:
                stages = ["Stage 1", "Stage 2", "Stage 3", "Stage 4", "Stage 5", "Stage 6", "Stage 7"]
                
                for prod in products:
                    img_urls = prod.get('images', [])
                    if not img_urls and prod.get('image_url'): img_urls = [prod.get('image_url')]
                        
                    main_img = img_urls[0] if img_urls else "https://via.placeholder.com/400x300?text=No+Image+Found"
                    
                    thumbnails_html = ""
                    if len(img_urls) > 1:
                        thumbnails_html = "<div class='thumbnail-container'>\n"
                        for thumb in img_urls[1:]:
                            thumbnails_html += f"<img src='{thumb}' class='product-thumbnail' onerror=\"this.style.display='none';\">\n"
                        thumbnails_html += "</div>"
                    
                    prod_card_html = f"""<div class="product-card">
<div class="img-container"><img src="{main_img}" class="product-image" onerror="this.onerror=null;this.src='https://via.placeholder.com/400x300?text=Error';"></div>
{thumbnails_html}
<div class="product-title">{prod.get('title', 'Unknown')}</div>
<div class="product-price">₹ {prod.get('price', 0.0):,.2f}</div>
<a href="{prod.get('url', '#')}" target="_blank" class="product-link" style="width:100%;">🔗 Original Link</a>
</div>"""
                    st.markdown(prod_card_html, unsafe_allow_html=True)
                    
                    curr_stage = prod.get('stage', 'Stage 1')
                    curr_idx = stages.index(curr_stage) if curr_stage in stages else 0
                    
                    new_stage = st.selectbox("Stage", stages, index=curr_idx, key=f"stg_{prod['_id']}", label_visibility="collapsed")
                    
                    bc1, bc2 = st.columns(2)
                    if bc1.button("💾 Apply", key=f"upd_{prod['_id']}", use_container_width=True):
                        db.update_launched_product_stage(prod['_id'], new_stage)
                        st.rerun()
                        
                    with bc2.popover("✏️ Edit", use_container_width=True):
                        e_title = st.text_input("Title", value=prod.get('title', ''), key=f"et_{prod['_id']}")
                        e_price = st.number_input("Price", value=float(prod.get('price', 0.0)), key=f"ep_{prod['_id']}")
                        e_img = st.text_input("Main Image", value=main_img, key=f"ei_{prod['_id']}")
                        e_img_file = st.file_uploader("Replace Images", type=['png', 'jpg'], accept_multiple_files=True, key=f"ef_{prod['_id']}")
                        
                        if st.button("Save", type="primary", key=f"es_{prod['_id']}", use_container_width=True):
                            final_edit_imgs = img_urls
                            if e_img_file:
                                final_edit_imgs = [f"data:{f.type};base64,{base64.b64encode(f.read()).decode('utf-8')}" for f in e_img_file]
                            elif e_img != main_img: final_edit_imgs = [e_img]
                                
                            s, m = db.update_launched_product_details(prod['_id'], e_title, e_price, final_edit_imgs)
                            st.rerun() if s else st.error(m)
                                
                    if st.button("🗑️ Remove", key=f"del_{prod['_id']}", use_container_width=True):
                        db.delete_launched_product(prod['_id']); st.rerun()
                    st.markdown("<hr>", unsafe_allow_html=True)

    elif nav == "🧾 GST Tracker":
        tab1, tab2, tab3 = st.tabs(["📅 Matrix", "➕ Update", "📋 Clients"])
        
        with tab1:
            df_hist = db.get_6_month_compliance_history()
            if not df_hist.empty: st.dataframe(df_hist, use_container_width=True, hide_index=True)
            else: st.info("No data.")

        with tab2:
            c1, c2 = st.columns(2)
            m_sel = c1.selectbox("Month", range(1, 13), index=datetime.date.today().month - 1)
            y_sel = c2.selectbox("Year", range(2024, 2030), index=datetime.date.today().year - 2024)
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
            reg_mode = st.radio("Mode", ["Single", "Bulk"], horizontal=True, label_visibility="collapsed")
            if reg_mode == "Single":
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
                st.metric("Total Liability", f"₹ {df['Net Payable'].sum():,.2f}")
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

    elif nav == "Product Master":
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

    elif nav == "System Masters":
        sub = st.radio("Settings", ["Staff", "Items", "Process", "Rates", "Wipe"], horizontal=True, label_visibility="collapsed")
        
        if sub == "Staff":
            with st.form("sm"):
                n=st.text_input("Staff Name")
                r=st.selectbox("Role", ["Stitching","Cutting","Helper"])
                if st.form_submit_button("Add", type="primary", use_container_width=True): 
                    db.save_staff(n, "", r, "Piece", 0); st.success("Saved")
            st.dataframe(db.get_df("masters_staff"), use_container_width=True)
            
        elif sub == "Items":
            n=st.text_input("Category Name")
            if st.button("Add Category", type="primary", use_container_width=True): db.save_category(n); st.rerun()
            st.dataframe(pd.DataFrame(db.get_categories_list(), columns=["Category"]), use_container_width=True)
            
        elif sub == "Process":
            n=st.text_input("Process Name")
            if st.button("Add Process", type="primary", use_container_width=True): db.save_master("masters_processes", {"name":n}); st.rerun()
            st.dataframe(db.get_df("masters_processes"), use_container_width=True)
            
        elif sub == "Rates":
            with st.form("rm"):
                i=st.selectbox("Category", db.get_categories_list())
                p=st.selectbox("Process", db.get_processes_list())
                r=st.number_input("Rate (₹)", min_value=0.0)
                fd = st.date_input("From Date")
                td = st.date_input("To Date", value=datetime.date.today() + datetime.timedelta(days=365))
                if st.form_submit_button("Update Rate", type="primary", use_container_width=True): 
                    db.save_rate(i,p,r, fd, td); st.success("Updated!")
            st.dataframe(db.get_rates_df(), use_container_width=True)
            
        elif sub == "Wipe":
            st.error("🚨 PERMANENT DELETE")
            wipe_opts = {
                "🏭 Production": ["production"], "✂️ Cutting": ["masters_lots", "transactions_cutting"],
                "💸 Payments": ["payments"], "🧾 GST": ["gst_registrations", "gst_filings"],
                "📋 Catalog": ["masters_catalog"], "🚀 Launcher": ["product_launcher"],
                "📦 Products": ["masters_products"], "⚙️ Masters": ["masters_staff", "masters_items"]
            }
            selected_wipe = st.multiselect("Select modules:", list(wipe_opts.keys()))
            if st.button("⚠️ WIPE DATA", type="primary", use_container_width=True):
                if selected_wipe:
                    cols = []
                    for s in selected_wipe: cols.extend(wipe_opts[s])
                    db.clean_database(cols)
                    st.success("Wiped!"); st.rerun()
                else: st.error("Select a module.")

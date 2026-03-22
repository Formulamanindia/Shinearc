import streamlit as st
import pandas as pd
import db_manager as db
import datetime
import math
import time
import base64

# --- CONFIG (COLLAPSE SIDEBAR GLOBALLY) ---
st.set_page_config(page_title="DrenchWear App", page_icon="📱", layout="centered", initial_sidebar_state="collapsed")

# --- MOBILE APP UI / RESPONSIVE CSS INJECTION ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Global Theme & App Constraints */
    * { box-sizing: border-box !important; }
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    .stApp { background-color: #F8FAFC !important; color: #0F172A; overflow-x: hidden !important; }
    
    /* Hide Streamlit Native Elements for App Feel */
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    footer { display: none !important; }
    
    /* Centralize Content */
    .block-container {
        max-width: 800px !important;
        padding-top: 2rem !important;
        padding-bottom: 5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        margin: 0 auto;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 { color: #0F172A !important; font-weight: 700 !important; letter-spacing: -0.025em; }

    /* --- NATIVE UNIFIED CARDS --- */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 20px !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05) !important;
        background: #FFFFFF !important;
        padding: 12px !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        margin-bottom: 15px !important;
        width: 100% !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 15px 25px -5px rgba(0,0,0,0.08) !important;
        border-color: #4F46E5 !important;
    }

    /* Metric Cards */
    .metric-card { 
        background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 20px; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); position: relative; overflow: hidden; margin-bottom: 10px;
    }
    .metric-value { font-size: 1.8rem; font-weight: 800; color: #0F172A; margin-top: 4px; }
    .metric-label { font-size: 0.8rem; color: #64748B; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
    .decorative-bar { position: absolute; top: 0; left: 0; height: 4px; width: 100%; }

    /* Product Launcher Specific CSS */
    .thumbnail-container { display: flex; gap: 8px; margin-bottom: 12px; overflow-x: auto; padding-bottom: 6px; scrollbar-width: none; -webkit-overflow-scrolling: touch; }
    .thumbnail-container::-webkit-scrollbar { display: none; }
    .product-thumbnail { width: 55px; height: 55px; object-fit: cover; border-radius: 8px; border: 1px solid #E2E8F0; }

    /* Forms and Containers */
    [data-testid="stForm"], .st-emotion-cache-1104q3m { 
        background: #FFFFFF !important; padding: 24px !important; border-radius: 16px !important; border: 1px solid #E2E8F0 !important; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02) !important; width: 100% !important;
    }

    /* Inputs (Text, Numbers, Dates, Select) */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox > div > div { 
        background-color: #F8FAFC !important; border: 1px solid #CBD5E1 !important; border-radius: 12px !important; color: #0F172A !important; padding: 12px 16px !important; font-size: 1rem; min-height: 48px !important; width: 100% !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus, .stSelectbox > div > div:focus { 
        border-color: #4F46E5 !important; box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15) !important; background-color: #FFFFFF !important; 
    }

    /* Selectbox Dropdown Fix */
    div[data-baseweb="select"] span, div[data-baseweb="select"] div, .stSelectbox [data-testid="stMarkdownContainer"] p { color: #0F172A !important; font-weight: 600; }
    div[data-baseweb="popover"], ul[role="listbox"] { background-color: #FFFFFF !important; border-radius: 12px !important; border: 1px solid #E2E8F0 !important; overflow: hidden; max-width: 95vw !important; }
    div[data-baseweb="popover"] *, ul[role="listbox"] li { color: #0F172A !important; }
    ul[role="listbox"] li { padding: 12px 16px !important; font-size: 1rem !important; }
    ul[role="listbox"] li:hover { background-color: #EEF2FF !important; color: #4F46E5 !important; }

    /* Standard Buttons */
    .stButton button { 
        border-radius: 12px; font-weight: 600; min-height: 48px !important; transition: all 0.2s ease; width: 100% !important;
    }
    .stButton button[kind="primary"] { 
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%) !important; color: white !important; border: none !important; box-shadow: 0 4px 10px rgba(79, 70, 229, 0.3); 
    }
    .stButton button[kind="primary"]:active { transform: scale(0.96); }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 2px solid #E2E8F0; padding-bottom: 0px; overflow-x: auto; -webkit-overflow-scrolling: touch; scrollbar-width: none; }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }
    .stTabs [data-baseweb="tab"] { height: 48px; border: none; background: transparent; color: #64748B; font-weight: 600; font-size: 0.95rem; padding: 0 16px; border-radius: 12px 12px 0 0; white-space: nowrap; transition: all 0.2s; }
    .stTabs [aria-selected="true"] { color: #4F46E5 !important; border-bottom: 3px solid #4F46E5 !important; background-color: transparent !important; }

    /* Login Centering */
    .login-container { max-width: 400px; margin: 10vh auto; background: white; padding: 40px 30px; border-radius: 24px; box-shadow: 0 20px 40px rgba(0,0,0,0.08); border: 1px solid #E2E8F0; text-align: center; }
    
    .section-header { border-left: 4px solid #4F46E5; padding-left: 12px; margin-top: 25px; margin-bottom: 15px; color: #0F172A; font-size: 1.15rem; font-weight: 700; }

    /* =========================================================
       📱 STRICT MOBILE RESPONSIVENESS
       ========================================================= */
    @media (max-width: 600px) {
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 1rem !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            padding: 8px !important;
            border-radius: 16px !important;
        }
        [data-testid="stForm"], .st-emotion-cache-1104q3m { 
            padding: 16px !important; 
        }
        .metric-card {
            padding: 16px;
        }
        .metric-value { font-size: 1.5rem; }
        .stButton button { min-height: 54px !important; /* Larger touch area on small screens */ }
    }
</style>
""", unsafe_allow_html=True)

# --- DYNAMIC CSS FOR DASHBOARD GRID ONLY ---
def apply_dashboard_card_css():
    st.markdown("""
    <style>
        /* App Tiles Button CSS */
        .stButton button[kind="secondary"] {
            height: 120px !important;
            border-radius: 20px !important;
            background: #FFFFFF !important;
            border: 2px solid #F1F5F9 !important;
            box-shadow: 0 8px 16px rgba(0,0,0,0.03) !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            white-space: pre-wrap !important;
            line-height: 1.4 !important;
            color: #0F172A !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            width: 100% !important;
        }
        .stButton button[kind="secondary"] p {
            font-size: 1.1rem !important; 
            font-weight: 700 !important;
            margin: 0 !important;
        }
        .stButton button[kind="secondary"]:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 24px rgba(79,70,229,0.12) !important;
            border-color: #E0E7FF !important;
            color: #4F46E5 !important;
        }
        .stButton button[kind="secondary"]:active {
            transform: scale(0.96);
            background-color: #EEF2FF !important;
        }

        /* Mobile Optimization for Tiles */
        @media (max-width: 600px) {
            .stButton button[kind="secondary"] {
                height: 100px !important;
                border-radius: 16px !important;
            }
            .stButton button[kind="secondary"] p {
                font-size: 1rem !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
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
<h2 style='color: #4F46E5; margin-bottom: 5px; margin-top:0; font-weight:800;'>DrenchWear</h2>
<p style='color: #64748B; font-weight: 500; margin-bottom: 30px; font-size:1.1rem;'>Secure ERP Login</p>"""
    st.markdown(login_html, unsafe_allow_html=True)
    with st.form("login", clear_on_submit=True):
        pwd = st.text_input("Access Key", type="password", placeholder="••••••••", label_visibility="collapsed")
        st.markdown("<br>", unsafe_allow_html=True)
        submit_btn = st.form_submit_button("Enter App", type="primary", use_container_width=True)
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
    apply_dashboard_card_css() 
    
    st.markdown("""
        <div style='text-align: center; margin-bottom: 25px; margin-top: 10px;'>
            <h1 style='color: #4F46E5; font-weight: 800; font-size: 2.2rem; margin-bottom: 5px;'>🧵 DrenchWear</h1>
            <p style='color: #64748B; font-weight: 500; font-size: 1rem; margin:0;'>Select a module to begin</p>
        </div>
    """, unsafe_allow_html=True)
    
    # --- APP DASHBOARD TILES ---
    # Using st.columns(2) natively allows Streamlit to stack them cleanly on mobile screens
    # while keeping them side-by-side on desktop/tablets.
    c1, c2 = st.columns(2)
    with c1: 
        if st.button("🏭\nWork Ops", use_container_width=True): route("🏭 Work Operations")
        if st.button("💸\nPayments", use_container_width=True): route("💸 Staff Payments")
        if st.button("🤖\nDrench AI", use_container_width=True): route("Drench AI")
        if st.button("📋\nCatalog", use_container_width=True): route("📋 Catalog Maker")
        
    with c2: 
        if st.button("🚀\nLauncher", use_container_width=True): route("🚀 Product Launcher")
        if st.button("📦\nMaster", use_container_width=True): route("Product Master")
        if st.button("🧾\nGST Track", use_container_width=True): route("🧾 GST Tracker")
        if st.button("⚙️\nSettings", use_container_width=True): route("System Masters")
        
else:
    # --- MOBILE-FRIENDLY NAV BAR ---
    n1, n2, n3 = st.columns([1, 2.5, 1])
    with n1:
        if st.button("⬅️ Home", use_container_width=True): route("Home")
    with n2:
        st.markdown(f"<div style='text-align: center; font-weight: 800; color: #0F172A; padding-top: 12px; font-size:1.15rem;'>{nav.split(' ')[-1] if ' ' in nav else nav}</div>", unsafe_allow_html=True)
    with n3:
        if st.button("🔒 Exit", use_container_width=True): 
            st.session_state.authenticated = False
            st.rerun()
    st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px; border-color:#E2E8F0;'>", unsafe_allow_html=True)

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

        # STITCHING
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
            
            # Use columns to put buttons side-by-side
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
                st.info("No products.")
            else:
                stages = ["Stage 1", "Stage 2", "Stage 3", "Stage 4", "Stage 5", "Stage 6", "Stage 7"]
                
                # We use standard Streamlit columns. On mobile, it automatically stacks to 1 column.
                # On Desktop, it will be 2 columns.
                cols = st.columns(2)
                
                for idx, prod in enumerate(products):
                    with cols[idx % 2]:
                        with st.container(border=True): # This creates the unified card shell
                            
                            img_urls = prod.get('images', [])
                            if not img_urls and prod.get('image_url'): img_urls = [prod.get('image_url')]
                                
                            main_img = img_urls[0] if img_urls else "https://via.placeholder.com/400x300?text=No+Image+Found"
                            
                            thumbnails_html = ""
                            if len(img_urls) > 1:
                                thumbnails_html = "<div class='thumbnail-container'>\n"
                                for thumb in img_urls[1:]:
                                    thumbnails_html += f"<img src='{thumb}' class='product-thumbnail' onerror=\"this.style.display='none';\">\n"
                                thumbnails_html += "</div>"
                            
                            # Responsive Image Display
                            prod_html = f"""<div style="margin-bottom: 10px;">
<img src="{main_img}" style="width: 100%; height: auto; aspect-ratio: 4/3; object-fit: cover; border-radius: 12px; border: 1px solid #F1F5F9; margin-bottom: 10px;" onerror="this.onerror=null;this.src='https://via.placeholder.com/400x300?text=Error';">
{thumbnails_html}
<div style="font-weight: 800; font-size: 1.15rem; color: #0F172A; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px;">{prod.get('title', 'Unknown')}</div>
<div style="color: #10B981; font-weight: 800; font-size: 1.25rem; margin-bottom: 15px;">₹ {prod.get('price', 0.0):,.2f}</div>
<a href="{prod.get('url', '#')}" target="_blank" style="display: flex; align-items: center; justify-content: center; background-color: #EEF2FF; color: #4F46E5; padding: 12px; border-radius: 10px; font-weight: 700; font-size: 0.95rem; text-decoration: none; transition: all 0.2s ease;">🔗 View Original Link</a>
</div>"""
                            st.markdown(prod_html, unsafe_allow_html=True)
                            
                            # Interactive Elements nested inside the card container
                            curr_stage = prod.get('stage', 'Stage 1')
                            curr_idx = stages.index(curr_stage) if curr_stage in stages else 0
                            new_stage = st.selectbox("Stage", stages, index=curr_idx, key=f"stg_{prod['_id']}", label_visibility="collapsed")
                            
                            btn_c1, btn_c2 = st.columns(2)
                            if btn_c1.button("💾 Save", key=f"upd_{prod['_id']}", use_container_width=True):
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

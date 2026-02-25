import streamlit as st
import pandas as pd
import db_manager as db
import datetime
import time
import re

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="DrenchWear.in", 
    page_icon="🧵", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. AUTHENTICATION ---
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<br><br><h1 style='text-align: center; color: #1F2937;'>🧵 DrenchWear.in</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #6B7280; font-weight:400;'>ERP Login</h3>", unsafe_allow_html=True)
        with st.form("login_form"):
            pwd = st.text_input("Password", type="password")
            submit_btn = st.form_submit_button("Sign In", use_container_width=True)
            if submit_btn:
                if pwd == "Flow@1993":
                    st.session_state["authenticated"] = True
                    st.rerun()
                else: st.error("❌ Incorrect Password")
    st.stop()

# --- 3. SESSION STATE ---
if "sale_cart" not in st.session_state: st.session_state.sale_cart = []
if "pur_cart" not in st.session_state: st.session_state.pur_cart = []
if "last_invoice_html" not in st.session_state: st.session_state.last_invoice_html = None
if "selected_staff_stat" not in st.session_state: st.session_state.selected_staff_stat = None
if "staff_search" not in st.session_state: st.session_state.staff_search = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [{"role": "assistant", "content": "👋 **Hello!**\n\nReady to work."}]
if "chat_mode" not in st.session_state: st.session_state.chat_mode = "menu"
if "chat_active" not in st.session_state: st.session_state.chat_active = False
if "nav_selection" not in st.session_state: st.session_state.nav_selection = "Dashboard"

# --- 4. CSS (BEAUTIFUL DESKTOP THEME) ---
st.markdown("""
<style>
    /* GLOBAL APP THEME */
    .stApp { background-color: #F9FAFB !important; font-family: 'Inter', sans-serif; color: #111827; }
    
    /* --- SIDEBAR STYLING --- */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E5E7EB;
        box-shadow: 4px 0 24px rgba(0,0,0,0.02);
    }
    
    /* Sidebar Title */
    section[data-testid="stSidebar"] h1 {
        color: #4F46E5 !important;
        font-weight: 800 !important;
        font-size: 28px !important;
        text-align: center;
        margin-top: 10px;
        margin-bottom: 30px;
        letter-spacing: -0.5px;
    }
    
    /* Navigation Radio Buttons (The Menu) */
    div[data-testid="stRadio"] > label {
        display: none; /* Hide label 'Navigation' */
    }
    div[role="radiogroup"] {
        gap: 8px;
    }
    div[role="radiogroup"] label {
        background-color: transparent !important;
        border: 1px solid transparent;
        padding: 10px 15px !important;
        border-radius: 10px !important;
        margin-bottom: 2px !important;
        transition: all 0.2s ease-in-out;
        color: #4B5563 !important;
        font-weight: 500 !important;
        font-size: 15px !important;
    }
    
    /* Hover State for Menu Items */
    div[role="radiogroup"] label:hover {
        background-color: #F3F4F6 !important;
        color: #111827 !important;
        transform: translateX(4px);
    }
    
    /* Active/Selected Menu Item */
    div[role="radiogroup"] label[data-checked="true"] {
        background-color: #EEF2FF !important; /* Light Indigo */
        color: #4F46E5 !important; /* Indigo Text */
        font-weight: 700 !important;
        border: 1px solid #E0E7FF !important;
        box-shadow: 0 1px 2px rgba(79, 70, 229, 0.05);
    }
    
    /* Sidebar Divider */
    hr { margin: 1.5rem 0 !important; border-color: #F3F4F6 !important; }
    
    /* Quick Action Buttons in Sidebar */
    section[data-testid="stSidebar"] .stButton button {
        background-color: #FFFFFF !important;
        color: #374151 !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 12px !important;
        padding: 0.6rem 1rem !important;
        font-weight: 600 !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        transition: all 0.2s;
        text-align: left;
        display: flex;
        align-items: center;
        justify-content: flex-start;
    }
    
    section[data-testid="stSidebar"] .stButton button:hover {
        border-color: #4F46E5 !important;
        color: #4F46E5 !important;
        background-color: #F9FAFB !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    /* Logout Button Specifics */
    section[data-testid="stSidebar"] .stButton button:last-child {
        color: #EF4444 !important;
        border-color: #FEE2E2 !important;
    }
    section[data-testid="stSidebar"] .stButton button:last-child:hover {
        background-color: #FEF2F2 !important;
    }

    /* --- MAIN CONTENT AREA --- */
    .block-container { padding-top: 2rem !important; padding-bottom: 4rem !important; max-width: 95% !important; }

    /* Cards */
    .metric-card {
        background-color: white;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
        transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05); }
    .metric-label { font-size: 0.85rem; color: #6B7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
    .metric-value { font-size: 2rem; font-weight: 800; color: #111827; letter-spacing: -0.025em; }

    /* Inputs */
    input, textarea, .stSelectbox > div > div {
        background-color: #FFFFFF !important;
        color: #111827 !important;
        border-color: #D1D5DB !important;
        border-radius: 8px !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { border-bottom: 2px solid #F3F4F6; gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        font-weight: 600;
        font-size: 15px;
        color: #6B7280;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        color: #4F46E5 !important;
        border-bottom: 2px solid #4F46E5 !important;
    }
    
    /* Tables */
    div[data-testid="stDataFrame"] {
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        overflow: hidden;
        background: white;
    }
    
    /* Chat Drawer */
    .chat-drawer {
        position: fixed; right: 0; top: 0; bottom: 0; width: 400px;
        background: white; border-left: 1px solid #E5E7EB;
        z-index: 99999; padding: 25px;
        box-shadow: -10px 0 30px rgba(0,0,0,0.05);
        display: flex; flex-direction: column;
    }
    .close-btn { position: absolute; top: 15px; right: 15px; cursor: pointer; font-size: 20px; color: #9CA3AF; }
    .close-btn:hover { color: #111827; }
</style>
""", unsafe_allow_html=True)

# --- 5. HELPER FUNCTIONS ---
def render_df(df, file_name="data"):
    if df.empty: st.info("No data available."); return
    st.dataframe(df, use_container_width=True, hide_index=True, height=450)

def render_html_table(df, cols):
    if df.empty: st.info("No Data"); return
    st.dataframe(df[cols], use_container_width=True, hide_index=True)

def render_metric_card(label, value, border_color="#E5E7EB"):
    st.markdown(f"""
    <div class="metric-card" style="border-left: 4px solid {border_color};">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# --- CHAT & QUICK ACTION LOGIC ---
def render_chat_system():
    with st.container():
        st.markdown('<div class="chat-drawer">', unsafe_allow_html=True)
        if st.button("❌ Close Panel", key="close_drawer_btn"): 
            st.session_state.chat_active = False
            st.rerun()
        st.markdown("---")

        mode = st.session_state.chat_mode
        if mode == "production":
            st.subheader("🏭 Production Entry")
            with st.form("q_prod"):
                s = st.selectbox("Worker", db.get_staff_list())
                l = st.selectbox("Lot No", db.get_active_lots())
                bun_opts = [f"{b['bundle_no']} | {b['item_name']} | {b['qty']} pcs" for b in db.get_detailed_bundles(l)] if l else []
                b_lbl = st.selectbox("Bundle", bun_opts)
                p = st.selectbox("Process", db.get_processes_list())
                q = st.number_input("Qty", 1.0)
                if st.form_submit_button("Save Record", type="primary"):
                    if l and b_lbl:
                        real_b = b_lbl.split(" | ")[0]
                        b_det = db.get_bundle_details(l, real_b)
                        r = db.get_rate(b_det['item_name'], p)
                        success, msg = db.save_production(str(datetime.date.today()), s, b_det['item_name'], p, q, r, l, real_b)
                        if success: st.success(msg)
                        else: st.error(msg)
        
        elif mode == "attendance":
            st.subheader("📅 Mark Attendance")
            a_staff = st.selectbox("Staff Member", [""] + db.get_staff_list())
            if a_staff:
                rec = db.get_attendance_record(str(datetime.date.today()), a_staff)
                if rec:
                    st.info(f"Current Status: {rec.get('status','Unknown')}")
                    if rec.get('in_time') and not rec.get('out_time'):
                        t_out = st.time_input("Out Time", datetime.datetime.now().time())
                        if st.button("🔴 Clock Out Now"):
                            db.save_attendance(str(datetime.date.today()), a_staff, "Present", in_time=None, out_time=t_out)
                            st.success("Clocked Out Successfully!")
                else:
                    t_in = st.time_input("In Time", datetime.time(9,0))
                    if st.button("🟢 Clock In"):
                        db.save_attendance(str(datetime.date.today()), a_staff, "Present", in_time=t_in)
                        st.success("Clocked In Successfully!")
        
        elif mode == "cashbook":
            st.subheader("💸 Cash Transaction")
            with st.form("q_cash"):
                ct = st.radio("Transaction Type", ["IN (Credit)", "OUT (Debit)"], horizontal=True)
                cp = st.selectbox("Party / Name", db.get_parties_list())
                ca = st.number_input("Amount (₹)", 1.0)
                cr = st.text_input("Remarks / Note")
                if st.form_submit_button("Save Transaction", type="primary"):
                    t_short = "IN" if "IN" in ct else "OUT"
                    db.save_cash_transaction(str(datetime.date.today()), t_short, ca, cp, "Cash", cr)
                    st.success("Transaction Saved!")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 6. SIDEBAR LAYOUT ---
with st.sidebar:
    st.title("🧵 DrenchWear.in")
    st.caption("Admin Dashboard")
    
    st.markdown("### Menu")
    nav_selection = st.radio(
        "Navigate",
        ["Dashboard", "Drench AI", "✂️ Cutting Dept", "Work Operations", "Product Master", "Staff Management", "System Masters"],
        label_visibility="collapsed"
    )
    st.session_state.nav_selection = nav_selection

    st.markdown("---")
    st.markdown("### ⚡ Actions")
    if st.button("🏭 Production", use_container_width=True): 
        st.session_state.chat_active = True
        st.session_state.chat_mode = "production"
        st.rerun()
    if st.button("📅 Attendance", use_container_width=True): 
        st.session_state.chat_active = True
        st.session_state.chat_mode = "attendance"
        st.rerun()
    if st.button("💸 Cashbook", use_container_width=True): 
        st.session_state.chat_active = True
        st.session_state.chat_mode = "cashbook"
        st.rerun()
        
    st.markdown("---")
    if st.button("🔒 Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

# --- 7. MAIN CONTENT RENDERER ---

if st.session_state.get("chat_active", False):
    render_chat_system()

# DASHBOARD
if st.session_state.nav_selection == "Dashboard":
    st.title("👋 Dashboard")
    st.markdown("Overview of your manufacturing unit.")
    
    pcs, earn, pending, active = db.get_dashboard_stats()
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: render_metric_card("Today's Output", f"{pcs:,.0f} Pcs", "#10B981") # Green
    with c2: render_metric_card("Production Value", f"₹ {earn:,.0f}", "#F59E0B") # Amber
    with c3: render_metric_card("Pending Payments", f"₹ {pending:,.0f}", "#EF4444") # Red
    with c4: render_metric_card("Active Workers", f"{active}", "#6366F1") # Indigo
    
    st.markdown("### 📉 Live Production Feed")
    recent_prod = db.get_df("production")
    if not recent_prod.empty:
        recent_prod['Time'] = pd.to_datetime(recent_prod['created_at']).dt.strftime('%H:%M')
        render_df(recent_prod[['Time', 'staff_name', 'item', 'process', 'qty']].head(15))
    else:
        st.info("No production data for today.")

# DRENCH AI
elif st.session_state.nav_selection == "Drench AI":
    st.title("🤖 Drench AI - Order Planner")
    
    tab1, tab2, tab3 = st.tabs(["📤 Upload Daily Orders", "📊 Order Summary", "✂️ Auto-Cutting Plan"])
    
    with tab1:
        st.info("Upload Daily Orders Excel. Columns Required: `Channel`, `Item`, `Category`, `Color`, `Size`, `Qty`")
        up_file = st.file_uploader("Upload Excel / CSV", type=['csv', 'xlsx'])
        if up_file:
            if st.button("Process & Upload", type="primary"):
                try:
                    if up_file.name.endswith('.csv'): df = pd.read_csv(up_file)
                    else: df = pd.read_excel(up_file)
                    success, msg = db.save_daily_orders(df)
                    if success: st.success(msg)
                    else: st.error(msg)
                except ImportError: st.error("⚠️ Library 'openpyxl' is missing. Run `pip install openpyxl` to fix Excel upload.")
                except Exception as e: st.error(f"Error: {e}")

    with tab2:
        st.markdown("#### 🔍 Filter Orders")
        c1, c2, c3, c4 = st.columns(4)
        f_item = c1.multiselect("Item", [""] + db.get_items_list())
        f_color = c2.multiselect("Color", [""] + db.get_colors_list())
        f_size = c3.multiselect("Size", [""] + db.get_sizes_list())
        f_chan = c4.multiselect("Channel", ["Flipkart", "Meesho", "Amazon", "Myntra"])
        
        filters = {}
        if f_item: filters['item'] = f_item
        if f_color: filters['color'] = f_color
        if f_size: filters['size'] = f_size
        if f_chan: filters['channel'] = f_chan
        
        render_df(db.get_daily_orders_df(filters))

    with tab3:
        st.markdown("#### ✂️ Weekly Job Generator")
        
        c1, c2, c3 = st.columns(3)
        d1 = c1.date_input("From Date", datetime.date.today() - datetime.timedelta(days=7))
        d2 = c2.date_input("To Date", datetime.date.today())
        max_lot_size = c3.number_input("Max Pcs per Lot", min_value=10, value=200)
        
        if st.button("Generate Matrix Plan", type="primary"):
            df_plan = db.get_cutting_matrix(str(d1), str(d2))
            
            if not df_plan.empty:
                st.success(f"Generated Plan for {len(df_plan)} Styles")
                # Add estimation
                df_plan['Est. Lots'] = df_plan['Total Pcs'].apply(lambda x: math.ceil(x / max_lot_size))
                st.dataframe(df_plan, use_container_width=True)
                csv = df_plan.to_csv(index=False).encode('utf-8')
                st.download_button("⬇️ Download Job Sheet (CSV)", csv, "cutting_plan_matrix.csv", "text/csv")
            else:
                st.warning("No orders found in range.")

# CUTTING DEPT (LOT MAKER)
elif st.session_state.nav_selection == "✂️ Cutting Dept":
    st.title("✂️ Cutting Department")
    lot_act = st.radio("Mode", ["Create New Lot", "View Lots", "Import Legacy CSV"], horizontal=True, label_visibility="collapsed")
    
    if lot_act == "Create New Lot":
        with st.container(border=True):
            st.subheader("1. Lot Header")
            c1, c2, c3 = st.columns(3)
            l_no = c1.text_input("Lot No (e.g. L-1001)")
            l_date = c2.date_input("Cut Date", datetime.date.today())
            l_sku = c3.selectbox("Style / SKU", [""] + db.get_child_skus_list())
            
            parts = l_sku.split('-') if l_sku else []
            def_gender = parts[0] if len(parts) > 0 else ""
            def_item = parts[2] if len(parts) > 2 else ""
            
            c4, c5 = st.columns(2)
            l_gen = c4.text_input("Gender", value=def_gender)
            l_item = c5.text_input("Item Category", value=def_item)

            st.markdown("---")
            st.subheader("2. Fabric Consumption")
            if "fab_df" not in st.session_state:
                st.session_state.fab_df = pd.DataFrame([{"Fabric Name": "", "Color": "", "Rolls": 0, "Weight (Kg)": 0.0}])
            
            edited_fab = st.data_editor(st.session_state.fab_df, num_rows="dynamic", use_container_width=True)
            
            st.markdown("---")
            st.subheader("3. Bundle Breakdown")
            
            bc1, bc2, bc3 = st.columns(3)
            n_buns = bc1.number_input("Number of Bundles", 1, 200, 10)
            def_col = bc2.selectbox("Default Color", db.get_colors_list())
            def_siz = bc3.selectbox("Default Size", db.get_sizes_list())
            
            if st.button("⚡ Generate Grid"):
                rows = [{"Bundle No": f"B-{i+1:02d}", "Color": def_col, "Size": def_siz, "Qty": 0} for i in range(n_buns)]
                st.session_state.lot_bundles = pd.DataFrame(rows)
            
            if "lot_bundles" in st.session_state:
                edited_bundles = st.data_editor(
                    st.session_state.lot_bundles,
                    column_config={
                        "Color": st.column_config.SelectboxColumn("Color", options=db.get_colors_list(), required=True),
                        "Size": st.column_config.SelectboxColumn("Size", options=db.get_sizes_list(), required=True),
                        "Qty": st.column_config.NumberColumn("Qty", min_value=1, required=True)
                    },
                    use_container_width=True, height=400
                )
                
                st.markdown("---")
                st.subheader("4. Authorization")
                ac1, ac2 = st.columns(2)
                cut_name = ac1.text_input("Cutter Name")
                sup_name = ac2.text_input("Supervisor Name")
                
                if st.button("💾 SAVE CUTTING LOT", type="primary"):
                    if l_no and l_sku:
                        header = {
                            "lot_no": l_no, "date": str(l_date), "sku": l_sku, 
                            "item_name": l_item, "category": l_item, 
                            "cutter": cut_name, "supervisor": sup_name
                        }
                        success, msg = db.save_full_lot(header, edited_fab, edited_bundles)
                        if success: st.success(msg)
                        else: st.error(msg)
                    else: st.error("Missing Header Info")

    elif lot_act == "Import Legacy CSV":
         st.markdown("##### 📦 Bulk Import Lots")
         up_file = st.file_uploader("Upload CSV", type=["csv"])
         if up_file and st.button("🚀 IMPORT", type="primary"):
            try:
                if db.save_bulk_lots(pd.read_csv(up_file)): st.success("Imported!")
            except: st.error("Error")

# PRODUCT MASTER
elif st.session_state.nav_selection == "Product Master":
    st.title("📦 Product Management")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Create Product", "📤 Bulk Import", "🔗 SKU Mapping", "📚 Catalog"])
    
    with tab1:
        c1, c2 = st.columns([1, 1])
        with c1:
            with st.container(border=True):
                st.subheader("1. Parent Product")
                with st.form("parent_form"):
                    p_name = st.text_input("Product Name")
                    c_a, c_b = st.columns(2)
                    p_gender = c_a.selectbox("Gender", ["Kids", "Men", "Women", "Boys", "Girls", "Unisex"])
                    p_cat = c_b.selectbox("Category", [""] + db.get_categories_list())
                    p_desc = st.text_area("Description")
                    if st.form_submit_button("Create Parent", type="primary"):
                        if p_name and p_gender and p_cat:
                            success, msg = db.save_product_parent(p_name, p_gender, p_cat, p_desc)
                            if success: st.success(msg)
                            else: st.error(msg)
                        else: st.error("Missing Fields")
        
        with c2:
            with st.container(border=True):
                st.subheader("2. Child Variant")
                parents = db.get_parent_products()
                if not parents:
                    st.warning("Create a Parent first.")
                else:
                    parent_opts = {f"{p.get('name','')} ({p.get('gender','')} {p.get('category','')})": p for p in parents}
                    sel_p_key = st.selectbox("Select Parent", list(parent_opts.keys()))
                    sel_parent = parent_opts[sel_p_key]
                    
                    with st.form("child_form"):
                        cc1, cc2 = st.columns(2)
                        c_color = cc1.selectbox("Color", db.get_colors_list())
                        c_size = cc2.selectbox("Size", db.get_sizes_list())
                        
                        p_gen = sel_parent.get('gender', 'Uni')
                        p_cat = sel_parent.get('category', 'Gen')
                        auto_sku = f"{p_gen}-{c_color}-{p_cat}-{c_size}".replace(" ", "")
                        
                        st.info(f"**SKU:** {auto_sku}")
                        c_rate = st.number_input("Piece Rate (₹)", 0.0)
                        
                        if st.form_submit_button("Create Variant", type="primary"):
                            success, msg = db.save_product_child(sel_parent['system_id'], auto_sku, c_color, c_size, c_rate)
                            if success: st.success(msg)
                            else: st.error(msg)

    with tab2:
        st.markdown("### 📤 Bulk Import")
        csv_data = "type,name,gender,category,description,parent_name,color,size,rate\nparent,Cherry Top,Kids,Crop Top,Best Seller,,,,\nchild,,,,,Cherry Top,Pink,M,150"
        st.download_button("⬇️ Download Template", csv_data, "products_template.csv", "text/csv")
        up_file = st.file_uploader("Upload CSV", type=["csv"])
        if up_file and st.button("Process Upload", type="primary"):
            try:
                df = pd.read_csv(up_file)
                count, errors = db.save_bulk_products(df)
                st.success(f"Processed {count} products!")
                if errors: st.write(errors)
            except Exception as e: st.error(str(e))

    with tab3:
        st.markdown("### 🔗 Marketplace Mapping")
        with st.form("map_form"):
            c1, c2, c3 = st.columns(3)
            int_sku = c1.selectbox("Internal SKU", [""] + db.get_child_skus_list())
            channel = c2.selectbox("Channel", ["Flipkart", "Meesho", "Amazon", "Myntra"])
            chan_sku = c3.text_input("Channel SKU ID")
            if st.form_submit_button("Link SKU", type="primary"):
                if int_sku and chan_sku:
                    db.save_sku_mapping(int_sku, channel, chan_sku)
                    st.success("Linked Successfully!")
        render_df(pd.DataFrame(db.get_mappings()))

    with tab4:
        st.markdown("### 📚 Product Catalog")
        render_df(pd.DataFrame(db.get_all_products_flat()))

# --- 9. WORK OPERATIONS ---
elif st.session_state.nav_selection == "Work Operations":
    st.title("🏭 Work Operations")
    
    tab_prod, tab_bundle, tab_fab, tab_sales, tab_pur, tab_fin = st.tabs([
        "Production", "Bundle Tracking", "Fabrication", "Sales", "Purchase", "Finance"
    ])
    
    with tab_prod:
        with st.container(border=True):
            st.subheader("Production Entry")
            c1, c2, c3 = st.columns(3)
            p_date = c1.date_input("Date", datetime.date.today())
            all_lots = db.get_active_lots()
            p_lot = c2.selectbox("Lot No.", [""] + all_lots)
            
            bun_opts = [f"{b['bundle_no']} | {b['item_name']} | {b['qty']} pcs" for b in db.get_detailed_bundles(p_lot)] if p_lot else []
            p_bundle_sel = c3.selectbox("Bundle", [""] + bun_opts)
            
            c4, c5, c6 = st.columns(3)
            p_staff = c4.selectbox("Worker", [""] + db.get_staff_list())
            p_process = c5.selectbox("Process", [""] + db.get_processes_list())
            p_qty = c6.number_input("Qty", min_value=0.0)
            
            if st.button("Save Production Record", type="primary"):
                if p_lot and p_bundle_sel and p_staff:
                    real_b = p_bundle_sel.split(" | ")[0]
                    b_det = db.get_bundle_details(p_lot, real_b)
                    r = db.get_rate(b_det['item_name'], p_process)
                    success, msg = db.save_production(str(p_date), p_staff, b_det['item_name'], p_process, p_qty, r, p_lot, real_b)
                    if success: st.success(msg)
                    else: st.error(msg)
                    
    with tab_bundle:
        st.subheader("📦 Bundle Tracking")
        c1, c2 = st.columns(2)
        f_lot = c1.selectbox("Filter by Lot", ["All"] + db.get_active_lots())
        bun_opts = ["All"] + (db.get_bundles_for_lot(f_lot) if f_lot != "All" else [])
        f_bun = c2.selectbox("Filter by Bundle", bun_opts)
        
        if f_lot != "All" and f_bun != "All":
            j_data, c_qty, h_qty = db.get_bundle_journey(f_lot, f_bun)
            m1, m2, m3 = st.columns(3)
            m1.metric("Created", f"{c_qty}")
            m2.metric("Current", f"{h_qty}")
            m3.progress(min(1.0, h_qty/c_qty) if c_qty > 0 else 0)
            render_html_table(pd.DataFrame(j_data), ["Date", "Process", "Issued To", "Issued Qty", "Status"])
        else:
            df = db.get_bundle_progress(f_lot, f_bun)
            render_df(df)

    with tab_fab:
        st.subheader("🛠️ Fabrication (Job Work)")
        with st.form("fab_form"):
            c1, c2, c3, c4 = st.columns(4)
            fd = c1.date_input("Date")
            fp = c2.selectbox("Party", db.get_parties_list())
            fi = c3.text_input("Item")
            fq = c4.number_input("Qty", 1.0)
            c5, c6 = st.columns(2)
            fr = c5.number_input("Rate", 0.0)
            fd = c6.text_input("Desc")
            if st.form_submit_button("Save Entry", type="primary"):
                db.save_fabrication(str(fd), fp, fi, fq, fr, fd)
                st.success("Saved")
        render_df(db.get_recent_fabrication())

    with tab_sales:
        st.info("Sales Module active.")
    with tab_pur:
        st.info("Purchase Module active.")
    with tab_fin: 
        st.subheader("Finance & Ledger")
        sel_party = st.selectbox("View Ledger For", [""] + db.get_parties_list())
        if sel_party:
            df = db.get_party_ledger(sel_party)
            if not df.empty:
                bal = df['debit'].sum() - df['credit'].sum()
                st.metric("Net Balance", f"₹ {bal:,.2f}")
                render_df(df)

# --- 10. STAFF ---
elif st.session_state.nav_selection == "Staff Management":
    st.title("👥 Staff & HR")
    tab1, tab2, tab3 = st.tabs(["Worker Stats", "Mark Attendance", "Payments"])
    
    with tab1:
        s = st.selectbox("Select Staff", [""] + db.get_staff_list())
        if s:
            e, p, bal, hist = db.get_worker_history(s)
            c1, c2, c3 = st.columns(3)
            c1.metric("Earned", f"₹{e:,.0f}")
            c2.metric("Paid", f"₹{p:,.0f}")
            c3.metric("Balance", f"₹{bal:,.0f}", delta_color="inverse")
            render_df(hist.head(20))
            
    with tab2:
        st.write("Use the **Quick Actions** sidebar for fast attendance.")
        
    with tab3:
        with st.form("pay_form"):
            c1, c2, c3 = st.columns(3)
            pd_ = c1.date_input("Date")
            ps = c2.selectbox("Staff", [""] + db.get_staff_list())
            pa = c3.number_input("Amount", 100)
            if st.form_submit_button("Record Payment", type="primary"):
                db.save_payment(str(pd_), ps, pa, "Salary", "Manual Entry")
                st.success("Recorded")

# --- 11. SYSTEM MASTERS ---
elif st.session_state.nav_selection == "System Masters":
    st.title("⚙️ System Masters")
    
    t1, t2, t3, t4, t5, t6, t7 = st.tabs(["Staff", "Parties", "Rates", "Processes", "Categories", "Colors/Sizes", "Admin"])
    
    with t1:
        with st.form("m_staff"):
            n = st.text_input("Name")
            r = st.selectbox("Role", ["Stitching", "Helper", "Cutting"])
            if st.form_submit_button("Add Staff", type="primary"): db.save_staff(n, "", r, "Piece Rate", 0); st.success("Saved")
        render_df(db.get_df("masters_staff"))
        
    with t2:
        with st.form("m_party"):
            n = st.text_input("Party Name")
            t = st.selectbox("Type", ["Customer", "Vendor", "Source"])
            if st.form_submit_button("Add Party", type="primary"): db.save_party(n, t); st.success("Saved")
    
    with t3:
        with st.form("m_rate"):
            c1, c2, c3 = st.columns(3)
            i = c1.selectbox("Item", db.get_items_list())
            p = c2.selectbox("Proc", db.get_processes_list())
            r = c3.number_input("Rate")
            if st.form_submit_button("Set Rate", type="primary"): db.save_rate(i, p, r); st.success("Saved")
        render_df(db.get_rates_df())

    with t4:
        n = st.text_input("New Process Name")
        if st.button("Add Process"): db.save_master("masters_processes", {"name":n}); st.rerun()
        render_df(db.get_df("masters_processes"))
        
    with t5:
        n = st.text_input("New Category")
        if st.button("Add Category"): db.save_master("masters_categories", {"name":n}); st.rerun()
        render_df(db.get_df("masters_categories"))
        
    with t6:
        c1, c2 = st.columns(2)
        with c1:
            n = st.text_input("New Color")
            if st.button("Add Color"): db.save_master("masters_colors", {"name":n}); st.rerun()
            render_df(db.get_df("masters_colors"))
        with c2:
            s = st.text_input("New Size")
            if st.button("Add Size"): db.save_master("masters_sizes", {"name":s}); st.rerun()
            render_df(db.get_df("masters_sizes"))

    with t7:
        if st.button("⚠️ CLEAN / WIPE DATA"):
            sel = st.multiselect("Select Tables", ["Staff", "Items", "Rates", "Process", "Colors", "Sizes", "Lots", "Data", "Pay", "Att", "Pur", "Cash", "Sales", "Parties", "GST", "Fabrication", "Products"])
            if sel:
                opts = {"Staff": "masters_staff", "Items": "masters_items", "Rates": "masters_rates", "Process": "masters_processes", "Colors": "masters_colors", "Sizes": "masters_sizes", "Lots": "masters_lots", "Data": "production", "Pay": "payments", "Att": "attendance", "Pur": "transactions_purchase", "Cash": "transactions_cashbook", "Sales": "transactions_sales", "Parties": "masters_parties", "GST": "masters_gst", "Fabrication": "transactions_fabrication", "Products": "masters_products"}
                db.clean_database([opts[x] for x in sel]); st.success("Wiped!")

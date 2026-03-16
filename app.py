import streamlit as st
import pandas as pd
import db_manager as db
import datetime
import math
import time

# --- CONFIG ---
st.set_page_config(page_title="DrenchWear ERP", page_icon="🧵", layout="wide", initial_sidebar_state="expanded")

# --- PREMIUM UI / CSS INJECTION ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Global Theme */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    .stApp { background-color: #F8FAFC !important; color: #0F172A; }

    /* Headers */
    h1, h2, h3, h4, h5, h6 { color: #0F172A !important; font-weight: 700 !important; letter-spacing: -0.025em; }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] { 
        background-color: #FFFFFF !important; 
        border-right: 1px solid #E2E8F0; 
        box-shadow: 4px 0 20px rgba(0,0,0,0.03); 
    }
    [data-testid="stSidebar"] h1 { color: #4F46E5 !important; font-weight: 800; font-size: 1.8rem; text-align: center; margin-bottom: 1rem; }
    
    /* Navigation Menu (Radio Buttons) */
    div[role="radiogroup"] { gap: 6px; padding: 5px 10px; }
    div[role="radiogroup"] label { 
        padding: 12px 16px !important; 
        border-radius: 12px !important; 
        color: #64748B !important; 
        font-weight: 600; 
        font-size: 14px; 
        transition: all 0.3s ease; 
        border: 1px solid transparent; 
        cursor: pointer;
    }
    div[role="radiogroup"] label:hover { 
        background-color: #F1F5F9 !important; 
        color: #0F172A !important; 
        transform: translateX(4px); 
    }
    div[role="radiogroup"] label[data-checked="true"] { 
        background: linear-gradient(90deg, #EEF2FF 0%, #FFFFFF 100%) !important; 
        color: #4F46E5 !important; 
        border: 1px solid #E0E7FF !important; 
        border-left: 4px solid #4F46E5 !important; 
        box-shadow: 0 2px 4px rgba(79, 70, 229, 0.05); 
    }

    /* Metric Cards */
    .metric-card { 
        background: #FFFFFF; 
        border: 1px solid #E2E8F0; 
        border-radius: 16px; 
        padding: 24px; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02), 0 2px 4px -1px rgba(0,0,0,0.02); 
        transition: all 0.3s ease; 
        position: relative; 
        overflow: hidden; 
    }
    .metric-card:hover { 
        transform: translateY(-4px); 
        box-shadow: 0 12px 20px -3px rgba(0,0,0,0.05), 0 4px 6px -2px rgba(0,0,0,0.025); 
    }
    .metric-value { font-size: 2.2rem; font-weight: 800; color: #0F172A; margin-top: 4px; letter-spacing: -0.02em; }
    .metric-label { font-size: 0.85rem; color: #64748B; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
    .decorative-bar { position: absolute; top: 0; left: 0; height: 4px; width: 100%; }

    /* Forms and Containers */
    [data-testid="stForm"], .st-emotion-cache-1104q3m { 
        background: #FFFFFF !important; 
        padding: 32px !important; 
        border-radius: 16px !important; 
        border: 1px solid #E2E8F0 !important; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02) !important; 
    }

    /* Inputs (Text, Numbers, Dates, Select) */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox > div > div { 
        background-color: #F8FAFC !important; 
        border: 1px solid #CBD5E1 !important; 
        border-radius: 10px !important; 
        color: #0F172A !important; 
        padding: 10px 14px !important; 
        font-size: 0.95rem; 
        transition: all 0.2s ease; 
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus, .stTextArea textarea:focus, .stSelectbox > div > div:focus { 
        border-color: #4F46E5 !important; 
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15) !important; 
        background-color: #FFFFFF !important; 
    }

    /* Buttons */
    .stButton button { 
        border-radius: 10px; 
        font-weight: 600; 
        padding: 0.6rem 1.2rem; 
        transition: all 0.2s ease; 
    }
    .stButton button[kind="primary"] { 
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%) !important; 
        color: white !important; 
        border: none !important; 
        box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.3); 
    }
    .stButton button[kind="primary"]:hover { 
        transform: translateY(-2px); 
        box-shadow: 0 6px 12px -1px rgba(79, 70, 229, 0.4); 
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 12px; border-bottom: 2px solid #E2E8F0; padding-bottom: 0px; }
    .stTabs [data-baseweb="tab"] { 
        height: 48px; border: none; background: transparent; 
        color: #64748B; font-weight: 600; font-size: 0.95rem; 
        padding: 0 16px; border-radius: 8px 8px 0 0; transition: all 0.2s ease; 
    }
    .stTabs [data-baseweb="tab"]:hover { background-color: #F1F5F9; color: #0F172A; }
    .stTabs [aria-selected="true"] { 
        color: #4F46E5 !important; 
        border-bottom: 3px solid #4F46E5 !important; 
        background-color: transparent !important; 
    }

    /* DataFrames / Tables */
    [data-testid="stDataFrame"] { 
        border-radius: 12px; 
        border: 1px solid #E2E8F0; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.02); 
        overflow: hidden; 
        background: #FFFFFF;
    }
    
    /* Login Centering & Beauty */
    .login-container { max-width: 400px; margin: 10vh auto; background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border: 1px solid #E2E8F0; }
    
    /* Beautiful Section Dividers */
    .section-header { 
        border-left: 5px solid #4F46E5; 
        padding-left: 10px; 
        margin-top: 30px; 
        margin-bottom: 15px; 
        color: #111827; 
        font-size: 1.15rem; 
        font-weight: 700; 
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS FOR BEAUTIFUL UI ---
def render_metric_card(label, value, icon="📈", border_color="#4F46E5", bg_color="#EEF2FF"):
    st.markdown(f"""
    <div class="metric-card">
        <div class="decorative-bar" style="background-color: {border_color};"></div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>
            <div style="background-color: {bg_color}; padding: 14px; border-radius: 14px; font-size: 24px; display: flex; align-items: center; justify-content: center;">
                {icon}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_df(df):
    if df.empty: st.info("No data available."); return
    st.dataframe(df, use_container_width=True, hide_index=True, height=450)

# --- AUTH ---
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if not st.session_state["authenticated"]:
    _, col2, _ = st.columns([1,1.2,1])
    with col2:
        st.markdown("""
        <div class="login-container">
            <h1 style='text-align: center; color: #4F46E5; margin-bottom: 5px;'>🧵 DrenchWear</h1>
            <h4 style='text-align: center; color: #64748B; font-weight: 500; margin-bottom: 30px;'>Enterprise Resource Portal</h4>
        """, unsafe_allow_html=True)
        with st.form("login", clear_on_submit=True):
            pwd = st.text_input("Enter Access Key", type="password", placeholder="••••••••")
            submit_btn = st.form_submit_button("Secure Login", type="primary", use_container_width=True)
            if submit_btn:
                if pwd == "Flow@1993":
                    st.session_state["authenticated"] = True; st.rerun()
                else: st.error("❌ Incorrect Password")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- INIT STATE ---
if "nav_selection" not in st.session_state: st.session_state.nav_selection = "Dashboard"

# --- SIDEBAR ---
with st.sidebar:
    st.title("🧵 DrenchWear")
    st.caption("ERP SYSTEM v4.0")
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.session_state.nav_selection = st.radio(
        "Navigation", 
        ["Dashboard", "Drench AI", "🏭 Work Operations", "🧾 GST Tracker", "💸 Staff Payments", "📋 Catalog Maker", "Product Master", "System Masters"],
        label_visibility="collapsed"
    )
    
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    if st.button("🔒 Secure Logout", use_container_width=True): 
        st.session_state["authenticated"] = False; st.rerun()

# --- CONTENT ---
nav = st.session_state.nav_selection

# 1. DASHBOARD
if nav == "Dashboard":
    st.markdown("<h2>👋 Welcome Back!</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B; margin-bottom: 2rem;'>Here is your manufacturing overview for today.</p>", unsafe_allow_html=True)
    
    pcs, earn, pending, active = db.get_dashboard_stats()
    c1, c2, c3, c4 = st.columns(4)
    with c1: render_metric_card("Today's Pcs", f"{pcs:,.0f}", "👕", "#10B981", "#D1FAE5")
    with c2: render_metric_card("Prod. Value", f"₹ {earn:,.0f}", "₹", "#F59E0B", "#FEF3C7")
    with c3: render_metric_card("Pending Pay", f"₹ {pending:,.0f}", "💳", "#EF4444", "#FEE2E2")
    with c4: render_metric_card("Active Staff", f"{active}", "👥", "#3B82F6", "#DBEAFE")
    
    st.markdown("<br><h3>📉 Live Production Feed</h3>", unsafe_allow_html=True)
    try:
        df = db.get_df("production")
        if not df.empty and 'created_at' in df.columns:
            df['Time'] = pd.to_datetime(df['created_at']).dt.strftime('%H:%M')
            cols_to_show = [c for c in ['Time', 'staff_name', 'item', 'process', 'qty'] if c in df.columns]
            st.dataframe(df[cols_to_show].head(15), use_container_width=True, hide_index=True)
        else:
            st.info("No recent production data.")
    except Exception as e:
        st.warning("Could not load production feed.")

# 2. DRENCH AI
elif nav == "Drench AI":
    st.markdown("<h2>🤖 Drench AI Planner</h2>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📤 Upload Orders", "📊 Order Summary", "✂️ Smart Cutting Plan"])
    
    with t1:
        st.info("💡 Ensure your file has columns: Channel, Item, Category, Color, Size, Qty")
        uf = st.file_uploader("Upload Daily Orders", type=['csv', 'xlsx'])
        if uf and st.button("Process & Upload", type="primary"):
            try:
                df = pd.read_csv(uf) if uf.name.endswith('.csv') else pd.read_excel(uf)
                s, m = db.save_daily_orders(df)
                if s: st.success(m)
                else: st.error(m)
            except Exception as e: st.error(f"Error: {e}")
    with t2:
        render_df(db.get_daily_orders_df())
    with t3:
        st.markdown("#### 📅 Select Date Range for Plan")
        c1, c2 = st.columns(2)
        d1 = c1.date_input("From Date", datetime.date.today()-datetime.timedelta(days=7))
        d2 = c2.date_input("To Date", datetime.date.today())
        if st.button("Generate Smart Plan", type="primary"):
            df = db.generate_cutting_plan(str(d1), str(d2))
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                st.download_button("Download Job Sheet CSV", df.to_csv(index=False), "plan.csv")
            else: st.warning("No orders found for this date range.")

# 3. WORK OPERATIONS
elif nav == "🏭 Work Operations":
    st.markdown("<h2>🏭 Work Operations Hub</h2>", unsafe_allow_html=True)
    tab_cut, tab_stitch, tab_ops = st.tabs(["✂️ Cutting Dept (Lots)", "🪡 Stitching Dept", "📦 Tracking & Ops"])
    
    # -------------------------------------------------------------------------
    # --- CUTTING DEPT TAB (RE-VAMPED UI) ---
    # -------------------------------------------------------------------------
    with tab_cut:
        st.markdown("<p style='color: #64748B;'>Manage your factory's production lots from creation to bundle breakdown.</p>", unsafe_allow_html=True)
        act = st.radio("Cutting Action", ["📝 Create New Lot", "📚 View Active Lots"], horizontal=True)
        
        if act == "📝 Create New Lot":
            st.markdown("<div class='section-header'>Step 1: Lot Header Details</div>", unsafe_allow_html=True)
            st.info("💡 Complete this section first to specify the style/SKU. Non-editable details like item category will auto-populate.")
            with st.form("lot_start"):
                # Header Information Grid
                c1, c2 = st.columns([1, 1.2])
                with c1:
                    l_date = st.date_input("Lot Creation Date", datetime.date.today())
                    l_sku = st.selectbox("Style/SKU", [""] + db.get_child_skus_list(), help="Select the product style to process.")
                with c2:
                    l_no = st.text_input("Lot Number", placeholder="e.g., L-101", help="Enter a unique number to identify this production lot.")
                
                submitted_start = st.form_submit_button("Proceed to Style Details →", type="primary")

            if submitted_start:
                st.session_state.lot_header = {"lot_no":l_no, "date":str(l_date), "sku":l_sku}
                # Pre-calculate values derived from SKU
                parts = l_sku.split('-') if l_sku else []
                st.session_state.lot_header['item_name'] = parts[2] if len(parts)>2 else ""
                st.session_state.lot_header['category'] = parts[1] if len(parts)>1 else ""
                # Clear existing drafts when changing lot
                if 'fab_df' in st.session_state: del st.session_state['fab_df']
                if 'lot_df' in st.session_state: del st.session_state['lot_df']

            # If a lot header is established, show the detailed forms
            if "lot_header" in st.session_state:
                # Lot Style Auto-populated Details
                st.markdown("<div class='section-header'>Style & Product details</div>", unsafe_allow_html=True)
                with st.container():
                    c_det1, c_det2 = st.columns(2)
                    with c_det1:
                        st.text_input("Item Description", value=st.session_state.lot_header['item_name'], disabled=True, key="item_display")
                    with c_det2:
                        st.text_input("Product Category", value=st.session_state.lot_header['category'], disabled=True, key="category_display")
                st.markdown("---")

                # Fabric Section
                st.markdown("<div class='section-header'>🧵 Step 2: Fabric Inventory & Consumption</div>", unsafe_allow_html=True)
                if "fab_df" not in st.session_state:
                    st.session_state.fab_df = pd.DataFrame([{"Fabric Name":"", "Color/Shade":"", "No. of Rolls":0, "Weight per Roll (kg)":"", "Total Weight (kg)":0.0}])
                st.caption("Provide details of the fabric used for this lot. Adjust rolls and weight as needed.")
                e_fab = st.data_editor(st.session_state.fab_df, num_rows="dynamic", use_container_width=True, key="fabric_editor")
                
                # Bundle Breakdown Section
                st.markdown("<div class='section-header'>📏 Step 3: Bundle & Size Breakdown</div>", unsafe_allow_html=True)
                st.markdown("Specify the number of bundles for this lot. Use the preset grid for initial values, then refine the breakdown below.")
                
                # Modern Bundle Preset Grid
                with st.container():
                    with st.expander("🛠️ Bundle Preset Config (Click to open)", expanded=True):
                        st.markdown("<p style='font-size: 0.9rem; color: #64748B;'>Configure initial preset values to quickly populate the bundle grid below.</p>", unsafe_allow_html=True)
                        b_p1, b_p2, b_p3 = st.columns(3)
                        n_bun = b_p1.number_input("No. of Bundles", 1, 500, 20)
                        d_col = b_p2.selectbox("Default Color", db.get_colors_list())
                        d_siz = b_p3.selectbox("Default Size", db.get_sizes_list())
                        
                        preset_btn = st.button("⚡ Generate Bundle Grid", type="secondary", use_container_width=True)
                
                if preset_btn:
                    st.session_state.lot_df = pd.DataFrame([{"Bundle No": f"B-{i+1:02d}", "Color": d_col, "Size": d_siz, "Qty (Pcs)": 0} for i in range(n_bun)])
                
                # Editable Bundle Data Grid
                if "lot_df" in st.session_state:
                    st.markdown("#### Final Bundle Grid Editor")
                    st.caption("Refine the specific Color, Size, and Quantity (Pcs) for each individual bundle.")
                    e_bun = st.data_editor(st.session_state.lot_df, height=400, use_container_width=True, key="bundle_data_editor")
                    
                    # Final Save Authorization Section (New Form for step 4)
                    with st.form("lot_save_form"):
                        st.markdown("<div class='section-header'>✍️ Step 4: Authorization & Saving</div>", unsafe_allow_html=True)
                        st.caption("Please provide signatures of the Cutter and Supervisor before final lot saving.")
                        a1, a2 = st.columns(2)
                        with a1:
                            cn = st.text_input("Cutter Signature (Full Name)", help="Enter the full name of the lead cutter.")
                        with a2:
                            sn = st.text_input("Supervisor Approval (Full Name)", help="Enter the full name of the approving supervisor.")
                        
                        # Primary submit button to save the entire form
                        st.markdown("<br>", unsafe_allow_html=True)
                        final_save = st.form_submit_button("💾 Save Cutting Lot →", type="primary", use_container_width=True)
                    
                    # Call save function only when finalized
                    if final_save:
                        h = {**st.session_state.lot_header, "cutter":cn, "supervisor":sn}
                        # I strictly preserved your original function call and logic
                        s, m = db.save_full_lot(h, e_fab, e_bun)
                        if s: 
                            st.success(m)
                            st.balloons()
                            # Clear transactional draft data upon successful save
                            if 'lot_header' in st.session_state: del st.session_state['lot_header']
                            if 'lot_df' in st.session_state: del st.session_state['lot_df']
                            if 'fab_df' in st.session_state: del st.session_state['fab_df']
                        else: st.error(m)
        else:
            st.info("Active Lot Viewer module loaded. Track progress in the '📦 Tracking & Ops' tab.")

    # 🪡 STITCHING TAB (Original, non-cutting tab, structure preserved)
    with tab_stitch:
        stitch_mode = st.radio("Entry Method", ["📝 Single Entry", "📤 Bulk Upload CSV"], horizontal=True, key="stitch_view_mode")
        if stitch_mode == "📝 Single Entry":
            with st.form("stitch_log"):
                st.markdown("#### Record Daily Stitching")
                c1, c2, c3 = st.columns(3)
                sd_date = c1.date_input("Date")
                sd_worker = c2.selectbox("Karigar (Worker)", db.get_staff_list())
                sd_proc = c3.selectbox("Process Type", db.get_processes_list())
                
                c4, c5 = st.columns(2)
                sd_lot = c4.selectbox("Cutting Lot No", [""] + db.get_active_lots())
                
                buns = []
                if sd_lot:
                    b_data = db.get_detailed_bundles(sd_lot)
                    # I strictly preserved this existing logic
                    buns = [f"{b['bundle_no']} | {b['item_name']} | {b['qty']} pcs" for b in b_data]
                
                sd_bun = c5.selectbox("Lot Bundle", [""] + buns)
                
                st.markdown("---")
                c6, c7, c8 = st.columns(3)
                qty = c6.number_input("Qty Stitched (Pcs)", min_value=1.0)
                lbl = c7.checkbox("🏷️ Label Attached? (+0.50)")
                
                if st.form_submit_button("💾 Submit & Auto-Credit Karigar Payment", type="primary"):
                    if sd_worker and sd_lot and sd_bun:
                        # Strictly preserved original logical breakdown
                        p = sd_bun.split(" | ")
                        val_item = p[1] if len(p)>1 else ""
                        real_bun = p[0]
                        
                        # Rate master lookup logic is preserved
                        rate = db.get_rate(val_item, sd_proc, sd_date)
                        fin_rate = rate + (0.50 if lbl else 0)
                        
                        # strictly preserved original backend call and logical feedback
                        s, m = db.save_production(str(sd_date), sd_worker, val_item, sd_proc, qty, fin_rate, sd_lot, real_bun)
                        if s: st.success(f"{m} | Credited Amount: ₹{qty*fin_rate}")
                        else: st.error(m)
                    else: st.error("Missing critical data (Worker, Lot, or Bundle).")
                    
        elif stitch_mode == "📤 Bulk Upload CSV":
            st.markdown("#### 📤 Bulk Karigar Stitched Data Import")
            st.info("The system automatically calculates the Rate and Total Value for each row based on the Date and your Time-Bound Rate Master.")
            sample_csv = "Date,Karigar Name,Lot No,Bundle No.,Process,Item,Qty\n2026-03-10,Worker Name,L-1001,B-01,Collar,Top,50\n2026-03-10,Worker Name,L-1001,B-02,Cuff,Top,50"
            st.download_button("⬇️ Download Sample Format CSV", sample_csv, "Sample_Stitching_Bulk.csv", "text/csv")
            
            uf = st.file_uploader("Upload Daily Stitching Data", type=["csv", "xlsx"])
            if uf and st.button("🚀 Process Bulk Upload", type="primary"):
                try:
                    df = pd.read_csv(uf) if uf.name.endswith('.csv') else pd.read_excel(uf)
                    # I strictly preserved this existing function and error handling
                    count, errors = db.save_bulk_stitching(df)
                    if count > 0: st.success(f"Successfully added {count} stitching records! Earnings Auto-Updated.")
                    if errors:
                        with st.expander("View Upload Processing Errors"):
                            for e in errors: st.write(e)
                except Exception as e: st.error(f"File Parsing Error: {e}")

    # Preserved original, un-revamped tabs
    with tab_ops:
        ops_view_mode = st.radio("Operations View", ["📦 Bundle Tracking", "🛠️ Fabrication Job Work"], horizontal=True, key="ops_tab_view")
        if ops_view_mode == "📦 Bundle Tracking":
            st.markdown("#### Real-Time Bundle Location")
            st.dataframe(db.get_bundle_progress(), use_container_width=True)
        else:
            st.markdown("#### Fabrication / Outsourced Job Work")
            with st.form("fab_form"):
                c1, c2, c3, c4 = st.columns(4)
                fd = c1.date_input("Date")
                fp = c2.selectbox("Party", db.get_parties_list())
                fi = c3.text_input("Item")
                fq = c4.number_input("Qty", 1.0)
                c5, c6 = st.columns(2)
                fr = c5.number_input("Rate", 0.0)
                fdesc = c6.text_input("Desc")
                if st.form_submit_button("Save Fabrication Entry", type="primary"):
                    db.save_fabrication(str(fd), fp, fi, fq, fr, fdesc)
                    st.success("Fabrication Record Saved")
            st.dataframe(db.get_recent_fabrication(), use_container_width=True)

# 4. GST TRACKER
elif nav == "🧾 GST Tracker":
    st.markdown("<h2>🧾 GST Compliance Hub</h2>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["📅 6-Month Matrix", "📊 Monthly Update", "➕ Add Client", "📋 Directory"])
    
    with tab1:
        st.markdown("#### Filing History Matrix")
        st.caption("Quick overview of GSTR-1 and GSTR-3B filings across clients.")
        df_hist = db.get_6_month_compliance_history()
        if not df_hist.empty: st.dataframe(df_hist, use_container_width=True, hide_index=True)
        else: st.info("No compliance history found.")

    with tab2:
        st.markdown("#### Update Filing Status")
        c1, c2, c3 = st.columns([1, 1, 2])
        m_sel = c1.selectbox("Month", range(1, 13), index=datetime.date.today().month - 1)
        y_sel = c2.selectbox("Year", range(2024, 2030), index=datetime.date.today().year - 2024)
        period = f"{y_sel}-{m_sel:02d}"
        
        if c3.button("🔄 Auto-Fetch Status from Portal", type="primary", use_container_width=True):
            st.error("Live fetch requires Paid API setup. Use manual update below.")
        
        df_comp = db.get_gst_compliance(period)
        if not df_comp.empty:
            st.dataframe(df_comp, use_container_width=True)
            with st.form("uf"):
                u1, u2, u3, u4 = st.columns(4)
                u_gst = u1.selectbox("Select GST", df_comp['GST No'].tolist())
                u_ret = u2.selectbox("Return", ["GSTR-1", "GSTR-3B"])
                u_stat = u3.selectbox("Status", ["Filed", "Pending"])
                u_date = u4.date_input("Filed Date")
                if st.form_submit_button("Update Status", type="primary"):
                    db.update_gst_filing(u_gst, period, u_ret, u_stat, str(u_date))
                    st.success("Updated Successfully!"); st.rerun()
        else: st.warning("No GST clients registered.")

    with tab3:
        reg_mode = st.radio("Entry Method", ["Single Client", "Bulk Upload"], horizontal=True)
        if reg_mode == "Single Client":
            st.markdown("#### Register New GST Client")
            c_fetch, c_btn = st.columns([3, 1])
            gst_search = c_fetch.text_input("Enter GST No. to Auto-Fetch")
            if c_btn.button("🔍 Fetch Data", use_container_width=True):
                st.error("Live fetching requires API Key. Enter details manually.")
            
            with st.form("ngst"):
                c1, c2, c3 = st.columns(3)
                g_no = c1.text_input("GST No.", value=gst_search)
                g_legal = c2.text_input("Legal Name")
                g_trade = c3.text_input("Trade Name")
                
                c4, c5, c6 = st.columns(3)
                g_date = c4.date_input("Reg Date")
                o_ph = c5.text_input("Owner Phone")
                o_em = c6.text_input("Owner Email")
                
                c7, c8 = st.columns(2)
                g_ph = c7.text_input("GST Phone")
                g_em = c8.text_input("GST Email")
                
                if st.form_submit_button("Save Client", type="primary"):
                    s, m = db.save_gst_registration(g_no, g_legal, g_trade, str(g_date), o_ph, o_em, g_ph, g_em)
                    if s: st.success(m)
                    else: st.error(m)
        else:
            st.markdown("#### 📤 Bulk Import GST Clients")
            sample_csv = "GST No,Legal Name,Trade Name,Reg Date,Owner Phone,Owner Email,GST Phone,GST Email\n22AAAAA0000A1Z5,ABC Corp,ABC Store,2024-01-15,9876543210,abc@test.com,9876543210,abc_gst@test.com"
            st.download_button("⬇️ Download Sample Format", sample_csv, "Sample_GST_Clients.csv", "text/csv")
            
            uf = st.file_uploader("Upload Clients CSV/Excel", type=["csv", "xlsx"])
            if uf and st.button("🚀 Upload & Save", type="primary"):
                try:
                    df = pd.read_csv(uf) if uf.name.endswith('.csv') else pd.read_excel(uf)
                    count, errors = db.save_bulk_gst_clients(df)
                    if count > 0: st.success(f"Added {count} clients!")
                    if errors:
                        with st.expander("View Errors"):
                            for e in errors: st.write(e)
                except Exception as e: st.error(f"Error: {e}")

    with tab4:
        st.markdown("#### Client Directory")
        df_gst = db.get_gst_registrations()
        if not df_gst.empty:
            df_gst['reg_date'] = pd.to_datetime(df_gst['reg_date']).dt.strftime('%d-%b-%Y')
            df_gst = df_gst[['gst_no', 'legal_name', 'trade_name', 'reg_date', 'owner_phone', 'owner_email', 'gst_phone', 'gst_email']]
            df_gst.columns = ['GST No.', 'Legal Name', 'Trade Name', 'Reg Date', 'Owner Ph', 'Owner Email', 'GST Ph', 'GST Email']
            st.dataframe(df_gst, use_container_width=True, hide_index=True)

# 5. STAFF PAYMENTS
elif nav == "💸 Staff Payments":
    st.markdown("<h2>💸 Staff Payments & Ledger</h2>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["📊 Live Balances", "💰 Record Payment"])
    
    with t1:
        st.markdown("#### Outstanding Balance Sheet")
        df = db.get_all_staff_balances()
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.metric("Total Business Liability", f"₹ {df['Net Payable'].sum():,.2f}")
        else: st.info("No records.")
        
    with t2:
        with st.form("pay"):
            st.markdown("#### Issue Funds")
            c1, c2 = st.columns(2)
            pd_ = c1.date_input("Date")
            ps = c2.selectbox("Staff (Karigar)", db.get_staff_list())
            c3, c4 = st.columns(2)
            pa = c3.number_input("Amount", 100)
            pt = c4.radio("Fund Type", ["Salary", "Advance"], horizontal=True)
            rem = st.text_input("Remarks / Pay Reference")
            if st.form_submit_button("Record Funds Issued", type="primary"):
                db.save_payment(str(pd_), ps, pa, pt, rem)
                st.success("Payment Recorded Successfully!")

# 6. CATALOG MAKER
elif nav == "📋 Catalog Maker":
    st.markdown("<h2>📋 Smart Catalog Maker v2.1</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748B;'>Upload raw catalog files. The system auto-generates Article Numbers and expands Variations sizes.</p>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📤 Upload Raw File", "📊 Processed View"])
    with tab1:
        uf = st.file_uploader("Select Catalog Base File (CSV/Excel)", type=['csv', 'xlsx'])
        if uf:
            try:
                df_input = pd.read_csv(uf) if uf.name.endswith('.csv') else pd.read_excel(uf)
                with st.expander("Raw Data Preview"): st.dataframe(df_input.head())
                if st.button("🚀 Process, Map, & Save Variants", type="primary", use_container_width=True):
                    with st.spinner("Processing variants..."):
                        success, result = db.process_and_save_catalog(df_input)
                        if success: st.success("Success! Processed Variants mapped & catalog saved.")
                        else: st.error(result)
            except Exception as e: st.error(str(e))
    with tab2:
        df_cat = db.get_catalog_data()
        if not df_cat.empty:
            st.dataframe(df_cat, use_container_width=True, hide_index=True)
            st.download_button("⬇️ Download Full Catalog CSV", df_cat.to_csv(index=False).encode('utf-8'), "Full_Catalog.csv", "text/csv", type="primary")
        else: st.info("No catalog data.")

# 7. PRODUCT MASTER
elif nav == "Product Master":
    st.markdown("<h2>📦 Product Master Database</h2>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📝 Single Entry", "📤 Bulk Import", "📚 Full Product List"])
    with t1:
        with st.form("pf"):
            st.markdown("#### Create Parent Product Style")
            n = st.text_input("Style Name"); g = st.selectbox("Gender Target", ["Men","Women","Kids","Unisex"]); c = st.selectbox("Category", db.get_categories_list()); d = st.text_area("Style Description")
            if st.form_submit_button("Create Parent Style", type="primary"): db.save_product_parent(n,g,c,d); st.success("Parent Saved")
        st.markdown("---")
        with st.form("cf"):
            st.markdown("#### Create Child Variant (SKU)")
            parents = db.get_parent_products()
            if parents:
                sel = st.selectbox("Select Parent Style", [p['name'] for p in parents])
                pid = next(p['system_id'] for p in parents if p['name']==sel)
                c1, c2 = st.columns(2)
                col = c1.selectbox("Specific Color", db.get_colors_list()); siz = c2.selectbox("Size", db.get_sizes_list()); rat = st.number_input("Standard Rate (₹)")
                sku = f"{sel}-{col}-{siz}".replace(" ","")
                st.text_input("Generated SKU Code", value=sku, disabled=True)
                if st.form_submit_button("Create SKU Variant", type="primary"): db.save_product_child(pid, sku, col, siz, rat); st.success("Variant SKU Saved")
    with t2:
        st.info("💡 **Bulk Import Format:** Use a CSV with headers: type (parent/child), name, gender, category, description, parent_name (for children), color (for children), size (for children), rate (for children).")
        uf = st.file_uploader("Upload Product Master CSV", type=['csv'])
        if uf and st.button("🚀 Import Database", type="primary", use_container_width=True):
            with st.spinner("Processing import..."):
                c, e = db.save_bulk_products(pd.read_csv(uf))
                st.success(f"Database update complete. Imported {c} product records.")
                if e: st.write(e)
    with t3:
        st.markdown("#### Comprehensive Product Master List")
        render_df(pd.DataFrame(db.get_all_products_flat()))

# 8. SYSTEM MASTERS (INCLUDING FIXED WIPE FEATURE)
elif nav == "System Masters":
    st.markdown("<h2>⚙️ Master Configuration</h2>", unsafe_allow_html=True)
    sub = st.segmented_control("Settings Module", ["Staff (👥)", "Items (👕)", "Process (🛠️)", "Rate Master (₹)", "Database Clean (🗑️)"], default="Staff (👥)")
    
    if sub == "Staff (👥)":
        with st.form("sm"):
            st.markdown("#### Add Factory Staff Record")
            n=st.text_input("Staff Full Name"); r=st.selectbox("Department Role", ["Stitching","Cutting","Helper","Operations"])
            if st.form_submit_button("Create Staff Record", type="primary"): db.save_staff(n, "", r, "Piece", 0); st.success("Staff Record Saved")
        st.dataframe(db.get_df("masters_staff"), use_container_width=True)
        
    elif sub == "Item Category (👕)":
        st.markdown("#### Add Item Category (Item Type)")
        st.caption("Define top-level product types like T-Shirts, Shirts, Jeans.")
        if "category_list_df" not in st.session_state: st.session_state.category_list_df = db.get_categories_list()
        n=st.text_input("Category Name"); 
        if st.button("Create Category", type="primary"): db.save_category(n); st.session_state.category_list_df = db.get_categories_list(); st.rerun()
        st.dataframe(pd.DataFrame(st.session_state.category_list_df, columns=["Category Name"]), use_container_width=True)
        
    elif sub == "Process (🛠️)":
        st.markdown("#### Add Production Process Stage")
        st.caption("Define specific stitching processes like Collar, Cuff, Front Pocket.")
        n=st.text_input("Process Stage Name"); 
        if st.button("Create Process", type="primary"): db.save_master("masters_processes", {"name":n}); st.rerun()
        st.dataframe(db.get_df("masters_processes"), use_container_width=True)
        
    elif sub == "Rate Master (₹)":
        st.info("💡 **Rate Logic established here.** Standard Piece Rates are set bound to a specific date range. For a karigar to be paid, their stitched data date must fall within a master rate bound defined here.")
        with st.form("rm"):
            st.markdown("#### Establish Master Rate Rule")
            c1, c2, c3 = st.columns(3)
            i=c1.selectbox("Select Item Category bound", db.get_categories_list())
            p=c2.selectbox("Select Process stage bound", db.get_processes_list())
            r=c3.number_input("Standard Piece Rate (₹)", min_value=0.0)
            
            c4, c5 = st.columns(2)
            fd = c4.date_input("Rule Valid From")
            td = c5.date_input("Rule Valid To", value=datetime.date.today() + datetime.timedelta(days=365))
            
            if st.form_submit_button("Estabish/Update Rate Rule", type="primary", use_container_width=True): 
                db.save_rate(i,p,r, fd, td); st.success("Master Rate Rule Update!")
        st.dataframe(db.get_rates_df(), use_container_width=True)
        
    elif sub == "Database Clean (🗑️)":
        st.markdown("#### 🗑️ Master & Transactional Database Cleanup")
        st.error("🚨 This action will permanently erase transactional manufacturing, staff, and GST data. Product Masters and Configurations will remain intact.")
        st.markdown("<br><hr><br>", unsafe_allow_html=True)
        
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("#### Permanent Transactional Data Wipe")
            st.caption("Clears all daily manufacturing work logs (production), cutting lot transaction details, bundles generated, and staff payment/funds logs. Useful for clearing historical data.")
            if st.button("WIPE MANUFACTURING TRANSACTIONAL DATA", type="primary", key="wipe_trans_data", use_container_width=True): 
                with st.spinner("Erasing transactional logs..."):
                    db.clean_database(["production","masters_lots","attendance","payments"])
                    st.success("Transactional logs wiped.")
                    st.rerun()
                    
        with c2:
            st.markdown("#### Permanent GST Data Wipe")
            st.caption("Clears all GST registration master data and filing logs for all months. Useful if starting GST compliance data fresh.")
            if st.button("WIPE GST DATABASE", type="primary", key="wipe_gst_data", use_container_width=True): 
                with st.spinner("Erasing GST logs..."):
                    db.clean_database(["gst_registrations", "gst_filings"])
                    st.success("GST Database wiped.")
                    st.rerun()

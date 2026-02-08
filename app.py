import streamlit as st
import pandas as pd
import db_manager as db
import datetime
import time
import re

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Sparsh 1.0", 
    page_icon="🧵", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. AUTHENTICATION ---
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<h1 style='text-align: center;'>🔒 Sparsh 1.0 Login</h1>", unsafe_allow_html=True)
    with st.form("login_form"):
        pwd = st.text_input("Enter Password", type="password")
        submit_btn = st.form_submit_button("Login")
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
    st.session_state.chat_messages = [{"role": "assistant", "content": "👋 **Hello!**\n\nI can help you record work or fix mistakes.\n\n*Try: \"Deepa 50 pcs Lot 101 Bundle 5\"*"}]
if "chat_mode" not in st.session_state: st.session_state.chat_mode = "menu"
if "chat_active" not in st.session_state: st.session_state.chat_active = False

# --- 4. CSS ---
st.markdown("""
<style>
    /* GLOBAL THEME */
    .stApp { background-color: #F8FAFC; font-family: 'Inter', sans-serif; }
    header[data-testid="stHeader"] { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }
    div.stSegmentedControl { position: sticky; top: 0; z-index: 9999; background-color: #F8FAFC; padding: 10px 0; margin-bottom: 10px; }
    
    .dashboard-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 20px; }
    @media (min-width: 768px) { .dashboard-grid { grid-template-columns: repeat(4, 1fr); } }
    
    /* CHAT UI */
    .chat-container { background-color: #EFEAE2; border-radius: 12px; padding: 20px; max-height: 500px; overflow-y: auto; border: 1px solid #D1D7DB; display: flex; flex-direction: column; gap: 8px; margin-bottom: 15px; }
    .chat-bubble { padding: 8px 12px; border-radius: 8px; font-size: 14px; line-height: 1.4; max-width: 80%; position: relative; box-shadow: 0 1px 1px rgba(0,0,0,0.1); word-wrap: break-word; }
    .user-bubble { align-self: flex-end; background-color: #D9FDD3; color: #111B21; border-top-right-radius: 0; }
    .bot-bubble { align-self: flex-start; background-color: #FFFFFF; color: #111B21; border-top-left-radius: 0; }
    .msg-time { font-size: 10px; color: #667781; text-align: right; margin-top: 4px; margin-bottom: -2px; }
    
    .stChatInput textarea { background-color: #FFFFFF !important; color: #000000 !important; border: 1px solid #E2E8F0 !important; border-radius: 20px !important; }
    
    /* FAB */
    div[data-testid="stPopover"] { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); z-index: 1000; }
    div[data-testid="stPopover"] button { width: 60px; height: 60px; border-radius: 50%; background-color: #4F46E5; color: white; box-shadow: 0 4px 12px rgba(0,0,0,0.3); font-size: 24px; border: 2px solid white; display: flex; align-items: center; justify-content: center; }
</style>
""", unsafe_allow_html=True)

# --- 5. HELPER FUNCTIONS ---
def render_df(df, file_name="data"):
    if df.empty: st.info("No data."); return
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(f"⬇️ CSV", csv, f"{file_name}.csv", "text/csv", key=f"dl_{file_name}")
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_html_table(df, cols):
    if df.empty: st.info("No Data"); return
    html = df[cols].to_html(classes='styled-table', index=False, escape=False)
    st.markdown(html, unsafe_allow_html=True)

# --- CHAT LOGIC ---
def process_chat_message(msg):
    msg_lower = msg.lower()
    staff_list = db.get_staff_list()
    found_staff = None
    for s in staff_list:
        if s.lower() in msg_lower: found_staff = s; break
    if not found_staff: return "❌ I couldn't find a staff member name in your message."

    # DELETE
    if any(x in msg_lower for x in ["delete", "remove", "cancel"]):
        if "attendance" in msg_lower:
            rec = db.get_last_attendance(found_staff)
            if rec:
                db.delete_record_by_id("attendance", rec['_id'])
                return f"🗑️ Deleted attendance for **{found_staff}**."
            else: return f"⚠️ No attendance found for {found_staff} today."
        elif "work" in msg_lower or "lot" in msg_lower or "pcs" in msg_lower:
            rec = db.get_last_production(found_staff)
            if rec:
                db.delete_record_by_id("production", rec['_id'])
                return f"🗑️ Deleted last work entry for **{found_staff}** ({rec['qty']} pcs - {rec['item']})."
            else: return f"⚠️ No recent work found for {found_staff}."

    # EDIT
    if any(x in msg_lower for x in ["change", "update", "edit", "correct"]):
        qty_match = re.search(r'(to|qty|quantity)\s+(\d+)', msg_lower)
        if qty_match:
            new_qty = float(qty_match.group(2))
            rec = db.get_last_production(found_staff)
            if rec:
                success = db.update_production_qty(rec['_id'], new_qty)
                if success: return f"✏️ Updated **{found_staff}'s** last work qty from {rec['qty']} to **{new_qty}**."
                else: return f"⚠️ **Error:** New Qty {new_qty} exceeds Bundle Size."
            else: return f"⚠️ No recent work found to update for {found_staff}."
        return "⚠️ Please specify quantity (e.g., 'Change to 100')."

    # ATTENDANCE
    if any(x in msg_lower for x in ["came", "reached", "clock in", "present"]) or re.search(r'\d{1,2}[:.]\d{2}', msg_lower):
        time_match = re.search(r'(\d{1,2})[:.](\d{2})\s*(am|pm)?', msg_lower)
        if time_match:
            hr, mn, period = time_match.groups()
            hr, mn = int(hr), int(mn)
            if period == 'pm' and hr != 12: hr += 12
            if period == 'am' and hr == 12: hr = 0
            in_time_obj = datetime.time(hr, mn)
            db.save_attendance(str(datetime.date.today()), found_staff, "Present", in_time=in_time_obj)
            return f"✅ **Attendance Marked!**\n{found_staff} clocked in at {in_time_obj.strftime('%I:%M %p')}."
        return "⚠️ Found name but couldn't understand time."

    # PRODUCTION
    if "lot" in msg_lower or "bundle" in msg_lower or "pcs" in msg_lower:
        qty_match = re.search(r'(\d+)\s*(?:pcs|pc|pieces)', msg_lower)
        qty = float(qty_match.group(1)) if qty_match else 0.0
        lot_match = re.search(r'lot\s*([a-zA-Z0-9-]+)', msg_lower)
        lot = lot_match.group(1) if lot_match else None
        bun_match = re.search(r'bundle\s*(?:no\.?)?\s*([a-zA-Z0-9-]+)', msg_lower)
        bundle = bun_match.group(1) if bun_match else None
        procs = db.get_processes_list()
        found_proc = "Stitching"
        for p in procs:
            if p.lower() in msg_lower: found_proc = p; break
        
        if lot and bundle and qty > 0:
            b_det = db.get_bundle_details(lot, bundle)
            if b_det:
                item_name = b_det.get('item_name', 'Unknown')
                rate = db.get_rate(item_name, found_proc)
                success, msg = db.save_production(str(datetime.date.today()), found_staff, item_name, found_proc, qty, rate, lot, bundle)
                return msg
            else: return "⚠️ Bundle not found in database."
        return "⚠️ Missing Lot/Bundle/Qty info."

    return "🤖 I didn't understand. Try 'Delete last work of Deepa' or 'Baba came at 9am'."

# --- CHAT RENDERER ---
def render_chat_system():
    st.markdown('<div class="chat-area-wrapper">', unsafe_allow_html=True)
    
    # History
    chat_html = '<div class="chat-container">'
    if "chat_history" in st.session_state and st.session_state.chat_history:
        for msg in st.session_state.chat_history:
            bubble_class = "user-bubble" if msg["role"] == "user" else "bot-bubble"
            align_class = "flex-end" if msg["role"] == "user" else "flex-start"
            content = msg["content"].replace("\n", "<br>")
            chat_html += f'<div style="display:flex; width:100%; justify-content:{align_class};"><div class="chat-bubble {bubble_class}">{content}<div class="msg-time">{datetime.datetime.now().strftime("%H:%M")}</div></div></div>'
    chat_html += '</div>'
    st.markdown(chat_html, unsafe_allow_html=True)
    
    # Forms
    mode = st.session_state.chat_mode
    if mode == "menu":
        c1, c2, c3 = st.columns(3)
        if c1.button("🏭 Prod"): st.session_state.chat_mode = "production"; st.rerun()
        if c2.button("📅 Attn"): st.session_state.chat_mode = "attendance"; st.rerun()
        if c3.button("💸 Cash"): st.session_state.chat_mode = "cashbook"; st.rerun()
        
    elif mode == "production":
        with st.form("cp"):
            s = st.selectbox("Staff", db.get_staff_list())
            l = st.selectbox("Lot", db.get_active_lots())
            bun_opts = [f"{b['bundle_no']} | {b['item_name']} | {b['qty']} pcs" for b in db.get_detailed_bundles(l)] if l else []
            b_lbl = st.selectbox("Bundle", bun_opts)
            p = st.selectbox("Proc", db.get_processes_list())
            q = st.number_input("Qty", 1.0)
            if st.form_submit_button("Save"):
                real_b = b_lbl.split(" | ")[0]
                b_det = db.get_bundle_details(l, real_b)
                success, msg = db.save_production(str(datetime.date.today()), s, b_det['item_name'], p, q, db.get_rate(b_det['item_name'], p), l, real_b)
                st.session_state.chat_history.append({"role": "assistant", "content": msg})
                st.session_state.chat_mode = "menu"; st.rerun()
        if st.button("Back"): st.session_state.chat_mode="menu"; st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    if prompt := st.chat_input("Command..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        resp = process_chat_message(prompt)
        st.session_state.chat_history.append({"role": "assistant", "content": resp})
        st.rerun()

# --- 6. NAVIGATION ---
nav_options = ["🏠 Home", "🏭 Work", "👥 Staff", "⚙️ Masters"]
selected_nav = st.segmented_control("Main Menu", nav_options, default="🏠 Home", label_visibility="collapsed")

if "last_nav" not in st.session_state: st.session_state.last_nav = "🏠 Home"
if selected_nav != st.session_state.last_nav:
    st.session_state.chat_active = False 
    st.session_state.last_nav = selected_nav

# --- 7. HOME ---
if selected_nav == "🏠 Home":
    # --- FLOATING FAB ---
    with st.popover("➕", use_container_width=False):
        st.markdown("### Quick Actions")
        if st.button("🏭 Production", use_container_width=True): st.session_state.chat_active=True; st.session_state.chat_mode="production"; st.rerun()
        if st.button("📅 Attendance", use_container_width=True): st.session_state.chat_active=True; st.session_state.chat_mode="attendance"; st.rerun()
        if st.button("💸 Cashbook", use_container_width=True): st.session_state.chat_active=True; st.session_state.chat_mode="cashbook"; st.rerun()

    if st.session_state.chat_active:
        if st.button("❌ Close"): st.session_state.chat_active=False; st.rerun()
        render_chat_system()
    else:
        st.markdown("##### 👋 Dashboard")
        
        # --- NEW BUTTONS: PRODUCT MASTER & SKU MAPPING ---
        c1, c2 = st.columns(2)
        if c1.button("📦 Product Master", use_container_width=True): 
             st.session_state.current_master_view = "Product Master"
             # We will handle redirection to Masters tab logic or just use a session state flag
             # For now, let's keep it simple: switch to Masters tab
             # But streamlit doesn't allow changing nav widget value easily.
             # So we will just show the content here or use a dedicated view.
             # Let's show it in a dialog for better UX.
             pass
             
        if c2.button("🔗 SKU Mapping", use_container_width=True): 
             pass

        # --- PRODUCT MASTER DIALOGS ---
        @st.dialog("📦 Product Master (Base.com Style)")
        def show_product_master():
            tab1, tab2 = st.tabs(["Create Parent", "Create Child"])
            with tab1:
                with st.form("parent_form"):
                    p_name = st.text_input("Product Name (e.g. Cotton Shirt)")
                    p_sku = st.text_input("Parent SKU (e.g. SHIRT-COT)")
                    p_cat = st.selectbox("Category", ["Apparel", "Home", "Accessories"])
                    p_desc = st.text_area("Description")
                    if st.form_submit_button("Create Parent"):
                        success, msg = db.save_product_parent(p_name, p_sku, p_cat, p_desc)
                        if success: st.success(msg)
                        else: st.error(msg)
            
            with tab2:
                parents = db.get_parent_products()
                if not parents: st.info("Create a Parent Product first."); st.stop()
                
                sel_p = st.selectbox("Select Parent", [p['sku'] for p in parents])
                # Find system id
                p_sys_id = next(p['system_id'] for p in parents if p['sku'] == sel_p)
                
                with st.form("child_form"):
                    c1, c2 = st.columns(2)
                    c_color = c1.selectbox("Color", db.get_colors_list())
                    c_size = c2.selectbox("Size", db.get_sizes_list())
                    c_sku = st.text_input("Child SKU", value=f"{sel_p}-{c_color}-{c_size}")
                    c_rate = st.number_input("Rate", 0.0)
                    if st.form_submit_button("Create Variant"):
                         success, msg = db.save_product_child(p_sys_id, c_sku, c_color, c_size, c_rate)
                         if success: st.success(msg)
                         else: st.error(msg)
                         
                st.markdown("---")
                st.markdown("**Existing Variants:**")
                children = db.get_children_for_parent(p_sys_id)
                if children:
                    st.dataframe(pd.DataFrame(children)[['sku', 'color', 'size', 'rate']], hide_index=True)

        @st.dialog("🔗 Picklist / SKU Mapping")
        def show_sku_mapping():
            st.info("Map your Sparsh SKUs to Marketplace SKUs for easy excel uploads.")
            with st.form("map_form"):
                sparsh_sku = st.selectbox("Internal SKU", db.get_child_skus_list())
                channel = st.selectbox("Channel", ["Flipkart", "Meesho", "Amazon", "Myntra"])
                chan_sku = st.text_input("Channel SKU ID")
                if st.form_submit_button("Save Mapping"):
                    db.save_sku_mapping(sparsh_sku, channel, chan_sku)
                    st.success("Mapped!")
            
            st.markdown("##### Current Mappings")
            df_map = pd.DataFrame(db.get_sku_mappings())
            if not df_map.empty:
                st.dataframe(df_map, hide_index=True)

        if c1.button("📦 Open Product Master", key="pm_btn"): show_product_master()
        if c2.button("🔗 Open SKU Mapping", key="sm_btn"): show_sku_mapping()
        
        # ... (Rest of Dashboard Stats) ...
        pcs, earn, pending, active = db.get_dashboard_stats()
        st.markdown(f"""
        <div class="dashboard-grid">
            <div class="stat-tile-html" style="border-bottom: 4px solid #10B981;"><div class="stat-num-html">{pcs:,.0f}</div><div class="stat-desc-html">Today Pcs</div></div>
            <div class="stat-tile-html" style="border-bottom: 4px solid #F59E0B;"><div class="stat-num-html">₹{earn:,.0f}</div><div class="stat-desc-html">Prod. Value</div></div>
            <div class="stat-tile-html" style="border-bottom: 4px solid #EF4444;"><div class="stat-num-html">₹{pending:,.0f}</div><div class="stat-desc-html">Pending Pay</div></div>
            <div class="stat-tile-html" style="border-bottom: 4px solid #6366F1;"><div class="stat-num-html">{active}</div><div class="stat-desc-html">Active Staff</div></div>
        </div>
        """, unsafe_allow_html=True)

# --- 8. WORK ---
elif "Work" in selected_nav:
    work_nav = st.segmented_control("Work Section", ["Production", "Bundle Progress", "Fabrication", "Sales", "Purchase", "Ledger", "Cashbook", "Lots", "Log"], default="Production")
    
    if work_nav == "Production":
        with st.container(border=True):
            st.markdown("**Production Entry**")
            p_date = st.date_input("Date", datetime.date.today())
            all_lots = db.get_active_lots()
            c_lot, c_bun = st.columns(2)
            p_lot = c_lot.selectbox("Lot No.", [""] + all_lots)
            bun_opts = [f"{b['bundle_no']} | {b['item_name']} | {b['qty']} pcs" for b in db.get_detailed_bundles(p_lot)] if p_lot else []
            p_bundle_sel = c_bun.selectbox("Bundle", [""] + bun_opts)
            c_staff, c_item = st.columns(2)
            p_staff = c_staff.selectbox("Worker", [""] + db.get_staff_list())
            p_item = c_item.text_input("Item", disabled=True, value=p_bundle_sel.split(" | ")[1] if p_bundle_sel else "")
            c_proc, c_qty = st.columns(2)
            p_process = c_proc.selectbox("Process", [""] + db.get_processes_list())
            p_qty = c_qty.number_input("Qty", min_value=0.0)
            
            if st.button("CONFIRM WORK", type="primary"):
                if p_lot and p_bundle_sel and p_staff:
                    real_b = p_bundle_sel.split(" | ")[0]
                    r = db.get_rate(p_item, p_process)
                    success, msg = db.save_production(str(p_date), p_staff, p_item, p_process, p_qty, r, p_lot, real_b)
                    if success: st.success(msg)
                    else: st.error(msg)
                else: st.error("Missing Data")
                
    elif work_nav == "Bundle Progress":
        st.markdown("##### 📊 Bundle Progress Tracker")
        
        # FILTERS FOR BUNDLE PROGRESS
        f_lot = st.selectbox("Filter Lot", ["All"] + db.get_active_lots())
        
        bun_opts = ["All"]
        if f_lot != "All":
            bun_opts += db.get_bundles_for_lot(f_lot)
        f_bun = st.selectbox("Filter Bundle", bun_opts)
        
        # --- NEW LOGIC: SHOW JOURNEY IF SPECIFIC BUNDLE SELECTED ---
        if f_lot != "All" and f_bun != "All":
            journey_data, created_qty, current_qty = db.get_bundle_journey(f_lot, f_bun)
            
            # 1. Metrics
            c1, c2 = st.columns(2)
            c1.metric("Initial Created", f"{created_qty} pcs")
            c2.metric("Current Handover", f"{current_qty} pcs")
            
            # 2. Timeline Table
            st.caption("📦 **Full Journey Timeline**")
            if journey_data:
                df_j = pd.DataFrame(journey_data)
                # Ensure correct column order
                cols = ["Date", "Process", "Issued To", "Issued Qty", "Status"]
                render_html_table(df_j, cols)
            else:
                st.warning("No journey data found.")
                
        else:
            # --- DEFAULT VIEW: SUMMARY TABLE ---
            df_prog = db.get_bundle_progress(f_lot, f_bun)
            if not df_prog.empty:
                st.dataframe(
                    df_prog,
                    column_config={
                        "Current Stage": st.column_config.TextColumn("Stage"),
                        "Pcs": st.column_config.NumberColumn("Current Qty"),
                    },
                    use_container_width=True
                )
            else:
                st.info("No Lots Found")

    elif work_nav == "Fabrication":
        st.markdown("##### 🛠️ Fabrication")
        with st.container(border=True):
            c1, c2 = st.columns(2)
            f_d = c1.date_input("Date", datetime.date.today())
            f_p = c2.selectbox("Party", db.get_parties_list())
            c3, c4 = st.columns(2)
            f_i = c3.text_input("Item")
            f_q = c4.number_input("Qty", 1.0)
            c5, c6 = st.columns(2)
            f_r = c5.number_input("Rate", 0.0)
            f_desc = c6.text_input("Desc")
            if st.button("SAVE FABRICATION"):
                if f_p and f_i: db.save_fabrication(str(f_d), f_p, f_i, f_q, f_r, f_desc); st.success("Saved!")
                
    # ... (Rest of Work tabs same as before) ...
    elif work_nav == "Log": render_df(db.get_df("production"), "log")
    
# --- 9. STAFF ---
elif "Staff" in selected_nav:
    staff_view = st.segmented_control("View", ["📊 Stats", "📅 Attendance", "💸 Payments"], default="📊 Stats")
    if staff_view == "📊 Stats":
        s = st.selectbox("Staff", [""] + db.get_staff_list())
        if s:
            e, p, bal, hist = db.get_worker_history(s)
            st.markdown(f"### Balance: ₹ {bal:,.0f}")
            
            # Date Filter
            c1, c2 = st.columns(2)
            d1 = c1.date_input("From", datetime.date.today().replace(day=1))
            d2 = c2.date_input("To", datetime.date.today())
            
            er, pr, df_r = db.get_staff_range_stats(s, str(d1), str(d2))
            st.markdown(f"**Period Earned:** ₹{er} | **Paid:** ₹{pr}")
            st.dataframe(df_r, use_container_width=True)

# --- 10. MASTERS ---
elif "Masters" in selected_nav:
    sub = st.segmented_control("Master", ["Staff", "Party", "Item", "Proc", "Rate", "Clean"], default="Staff")
    if sub == "Item":
        n = st.text_input("Item Name")
        procs = st.multiselect("Processes", db.get_processes_list())
        if st.button("Save Item"): db.save_item(n, procs); st.success("Saved")
        render_df(db.get_df("masters_items"))
    elif sub == "Rate":
        c1, c2, c3 = st.columns(3)
        i = c1.selectbox("Item", db.get_items_list())
        p = c2.selectbox("Proc", db.get_processes_list())
        r = c3.number_input("Rate")
        if st.button("Update Rate"): db.save_rate(i, p, r); st.success("Saved")
        render_df(db.get_rates_df())

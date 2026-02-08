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
    st.markdown("<h1 style='text-align: center; color: #1F2937;'>🔒 Sparsh 1.0 Login</h1>", unsafe_allow_html=True)
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

# --- 4. CSS (VISIBILITY FIX) ---
st.markdown("""
<style>
    /* --- FORCE LIGHT MODE & VISIBILITY --- */
    
    /* Main Background */
    .stApp { background-color: #F8FAFC !important; color: #1F2937 !important; font-family: 'Inter', sans-serif; }
    
    /* Hide Header */
    header[data-testid="stHeader"] { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }

    /* --- INPUT FIELDS (Fix Black/Invisible Issue) --- */
    
    /* Text Inputs, Number Inputs, Date Inputs */
    input[type="text"], input[type="number"], input[type="password"], input.stDateInput {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 8px !important;
    }
    
    /* Selectboxes / Dropdowns */
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 8px !important;
    }
    
    /* Dropdown Text Color (Selected Value) */
    div[data-baseweb="select"] span {
        color: #000000 !important;
    }

    /* Dropdown Options Menu (The list that pops up) */
    ul[data-baseweb="menu"] {
        background-color: #FFFFFF !important;
    }
    ul[data-baseweb="menu"] li {
        color: #000000 !important;
    }
    
    /* Labels for Inputs */
    label, .stMarkdown p {
        color: #374151 !important;
        font-weight: 500;
    }
    
    /* --- BUTTONS --- */
    .stButton button {
        background-color: #4F46E5 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
    }
    .stButton button:hover {
        background-color: #4338CA !important;
    }
    
    /* Secondary/Ghost Buttons */
    button[kind="secondary"] {
        background-color: #FFFFFF !important;
        color: #374151 !important;
        border: 1px solid #D1D5DB !important;
    }

    /* --- TABLES --- */
    div[data-testid="stDataFrame"] {
        background-color: white !important;
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    /* --- NAVIGATION --- */
    div.stSegmentedControl {
        background-color: #F8FAFC !important;
        padding: 10px 0;
        position: sticky; top: 0; z-index: 99;
    }
    div.stSegmentedControl button {
        background-color: #FFFFFF !important;
        color: #4B5563 !important;
        border: 1px solid #E5E7EB !important;
    }
    div.stSegmentedControl button[aria-selected="true"] {
        background-color: #4F46E5 !important;
        color: white !important;
    }

    /* --- CHAT UI --- */
    .chat-area-wrapper {
        background-color: #EFEAE2; /* Beige */
        border: 1px solid #D1D7DB;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
    }
    
    .chat-container {
        max-height: 300px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-bottom: 10px;
    }
    
    .chat-bubble {
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 14px;
        line-height: 1.4;
        max-width: 85%;
        position: relative;
        box-shadow: 0 1px 1px rgba(0,0,0,0.1);
        word-wrap: break-word;
    }
    
    .user-bubble {
        align-self: flex-end;
        background-color: #D9FDD3; /* Green */
        color: #111B21;
        border-top-right-radius: 0;
    }
    
    .bot-bubble {
        align-self: flex-start;
        background-color: #FFFFFF;
        color: #111B21;
        border-top-left-radius: 0;
    }
    
    .msg-time {
        font-size: 9px;
        color: #667781;
        text-align: right;
        margin-top: 4px;
        margin-bottom: -2px;
    }

    /* CHAT INPUT FIX */
    .stChatInput textarea {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 20px !important;
    }
    
    /* FORM CONTAINER INSIDE CHAT */
    .chat-form-container {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-top: 10px;
        border: 1px solid #E5E7EB;
    }
    
    /* DASHBOARD CARDS */
    .stat-tile-html {
        background: white;
        border-radius: 12px;
        padding: 15px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        text-align: center;
    }
    .stat-num-html { font-size: 24px; font-weight: 700; color: #111827; }
    .stat-desc-html { font-size: 12px; color: #6B7280; font-weight: 500; text-transform: uppercase; margin-top: 4px; }
    
    /* FLOATING CHAT - RIGHT MIDDLE */
    div[data-testid="stPopover"] {
        position: fixed;
        top: 50%;
        right: 20px;
        bottom: auto;
        left: auto;
        transform: translateY(-50%);
        z-index: 9999;
    }
    div[data-testid="stPopover"] button {
        width: 60px; height: 60px; border-radius: 50%;
        background-color: #4F46E5 !important; color: white !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        font-size: 24px; display: flex; align-items: center; justify-content: center;
        border: 2px solid white !important;
    }
    
    /* HTML TABLE STYLING */
    .styled-table { border-collapse: collapse; margin: 15px 0; font-size: 13px; font-family: 'Inter', sans-serif; width: 100%; box-shadow: 0 0 20px rgba(0, 0, 0, 0.05); border-radius: 10px; overflow: hidden; background-color: white; }
    .styled-table thead tr { background-color: #4F46E5; color: white; text-align: left; }
    .styled-table th, .styled-table td { padding: 10px 15px; color: #374151; }
    .styled-table tbody tr { border-bottom: 1px solid #dddddd; }
    .styled-table tbody tr:nth-of-type(even) { background-color: #F9FAFB; }
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

def generate_invoice_html(type_label, bill_no, date, party, items_df, sub_total, tax_amt, grand_total):
    items_html = ""
    for _, row in items_df.iterrows():
        items_html += f"""<tr style="border-bottom: 1px solid #eee;"><td style="padding: 8px;">{row['item']}</td><td style="padding: 8px; text-align: center;">{row['qty']}</td><td style="padding: 8px; text-align: right;">{row['rate']}</td><td style="padding: 8px; text-align: right;">{row['qty'] * row['rate']:,.0f}</td></tr>"""
    return f"""<div style="background: white; padding: 30px; border: 1px solid #ddd; font-family: sans-serif; max-width: 800px; margin: auto; color:black;"><div style="display: flex; justify-content: space-between; border-bottom: 2px solid #4F46E5; padding-bottom: 20px;"><div><h1 style="margin: 0; color: #4F46E5;">INVOICE</h1><p style="margin: 5px 0; font-weight: bold;">{type_label}</p></div><div style="text-align: right;"><h3 style="margin: 0;"># {bill_no}</h3><p style="margin: 5px 0; color: #666;">Date: {date}</p></div></div><div style="margin: 20px 0;"><p style="margin: 0; font-size: 12px; color: #888; text-transform: uppercase;">Bill To</p><h3 style="margin: 5px 0;">{party}</h3></div><table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;"><thead><tr style="background: #f8f9fa; text-align: left;"><th style="padding: 10px; border-bottom: 2px solid #ddd;">Item</th><th style="padding: 10px; border-bottom: 2px solid #ddd; text-align: center;">Qty</th><th style="padding: 10px; border-bottom: 2px solid #ddd; text-align: right;">Rate</th><th style="padding: 10px; border-bottom: 2px solid #ddd; text-align: right;">Total</th></tr></thead><tbody>{items_html}</tbody></table><div style="display: flex; justify-content: flex-end;"><div style="width: 250px;"><div style="display: flex; justify-content: space-between; padding: 5px 0;"><span>Sub Total:</span><span>₹ {sub_total:,.2f}</span></div><div style="display: flex; justify-content: space-between; padding: 5px 0; color: #666;"><span>Tax:</span><span>₹ {tax_amt:,.2f}</span></div><div style="display: flex; justify-content: space-between; padding: 10px 0; border-top: 2px solid #4F46E5; font-weight: bold; font-size: 18px;"><span>Total:</span><span>₹ {grand_total:,.0f}</span></div></div></div></div>"""

# --- CHAT LOGIC ---
def process_chat_message(msg):
    msg_lower = msg.lower()
    staff_list = db.get_staff_list()
    found_staff = None
    for s in staff_list:
        if s.lower() in msg_lower:
            found_staff = s; break
    if not found_staff: return "❌ I couldn't find a staff member name."

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
                return f"🗑️ Deleted last work for **{found_staff}** ({rec['qty']} pcs)."
            else: return f"⚠️ No recent work found."

    # EDIT
    if any(x in msg_lower for x in ["change", "update", "edit", "correct"]):
        qty_match = re.search(r'(to|qty|quantity)\s+(\d+)', msg_lower)
        if qty_match:
            new_qty = float(qty_match.group(2))
            rec = db.get_last_production(found_staff)
            if rec:
                success = db.update_production_qty(rec['_id'], new_qty)
                if success: return f"✏️ Updated **{found_staff}'s** last work qty to **{new_qty}**."
                else: return f"⚠️ Error: Qty {new_qty} exceeds Bundle Size."
            else: return f"⚠️ No recent work found."
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
            return f"✅ **Attendance Marked!**\n{found_staff} at {in_time_obj.strftime('%I:%M %p')}."
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
        st.markdown('<div class="chat-form-container">', unsafe_allow_html=True)
        st.caption("🏭 **New Production Entry**")
        with st.form("chat_prod"):
            cp_staff = st.selectbox("Worker", db.get_staff_list())
            cp_lot = st.selectbox("Lot No", db.get_active_lots())
            
            bun_opts = [f"{b['bundle_no']} | {b['item_name']} | {b['qty']} pcs" for b in db.get_detailed_bundles(cp_lot)] if cp_lot else []
            cp_bun_label = st.selectbox("Bundle", bun_opts)
            cp_proc = st.selectbox("Process", db.get_processes_list())
            cp_qty = st.number_input("Qty", min_value=1.0)
            
            c_b, c_s = st.columns([1,2])
            if c_b.form_submit_button("Back"):
                st.session_state.chat_mode = "menu"; st.rerun()
            
            if c_s.form_submit_button("✅ Save", type="primary"):
                if cp_staff and cp_lot and cp_bun_label:
                    real_bun = cp_bun_label.split(" | ")[0]
                    b_det = db.get_bundle_details(cp_lot, real_bun)
                    i_name = b_det.get('item_name', 'Unknown')
                    rate = db.get_rate(i_name, cp_proc)
                    
                    success, msg = db.save_production(str(datetime.date.today()), cp_staff, i_name, cp_proc, cp_qty, rate, cp_lot, real_bun)
                    
                    st.session_state.chat_history.append({"role": "user", "content": f"Production: {cp_staff}, {cp_qty} pcs"})
                    st.session_state.chat_history.append({"role": "assistant", "content": msg})
                    st.session_state.chat_mode = "menu"
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif mode == "attendance":
        st.markdown('<div class="chat-form-container">', unsafe_allow_html=True)
        st.caption("📅 **Mark Attendance**")
        
        ca_staff = st.selectbox("Select Staff", db.get_staff_list(), key="ca_att_s")
        if ca_staff:
            rec = db.get_attendance_record(str(datetime.date.today()), ca_staff)
            status_txt = "Not Marked"
            if rec:
                if rec.get('out_time'): status_txt = "Completed"
                elif rec.get('in_time'): status_txt = f"In at {rec['in_time']}"
            st.info(f"Status: {status_txt}")
            
            if rec and rec.get('in_time') and not rec.get('out_time'):
                t_out = st.time_input("Out Time", datetime.datetime.now().time())
                if st.button("🔴 Clock Out"):
                    db.save_attendance(str(datetime.date.today()), ca_staff, "Present", in_time=None, out_time=t_out)
                    st.session_state.chat_history.append({"role": "assistant", "content": f"✅ {ca_staff} Clocked Out."})
                    st.session_state.chat_mode = "menu"
                    st.rerun()
            elif not rec:
                c1, c2 = st.columns(2)
                t_in = st.time_input("In Time", datetime.time(9,0))
                if c1.button("🟢 Clock In"):
                    db.save_attendance(str(datetime.date.today()), ca_staff, "Present", in_time=t_in)
                    st.session_state.chat_history.append({"role": "assistant", "content": f"✅ {ca_staff} Clocked In."})
                    st.session_state.chat_mode = "menu"
                    st.rerun()
        
        if st.button("Back"):
            st.session_state.chat_mode = "menu"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    elif mode == "cashbook":
        st.markdown('<div class="chat-form-container">', unsafe_allow_html=True)
        st.caption("💸 **Cash Entry**")
        with st.form("cc_form"):
            cc_type = st.radio("Type", ["IN", "OUT"], horizontal=True)
            cc_party = st.selectbox("Party", db.get_parties_list())
            cc_amt = st.number_input("Amount", min_value=1.0)
            cc_rem = st.text_input("Note")
            
            c_b, c_s = st.columns([1,2])
            if c_b.form_submit_button("Back"):
                st.session_state.chat_mode = "menu"; st.rerun()
            if c_s.form_submit_button("Save"):
                db.save_cash_transaction(str(datetime.date.today()), cc_type, cc_amt, cc_party, "Cash", cc_rem)
                st.session_state.chat_history.append({"role": "assistant", "content": "✅ Cash Transaction Saved."})
                st.session_state.chat_mode = "menu"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

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
        if c1.button("📦 Open Product Master", key="pm_btn"): 
             @st.dialog("📦 Product Master")
             def show_product_master():
                tab1, tab2 = st.tabs(["Create Parent", "Create Child"])
                with tab1:
                    with st.form("parent_form"):
                        p_name = st.text_input("Product Name")
                        p_sku = st.text_input("Parent SKU")
                        p_cat = st.selectbox("Category", ["Apparel", "Home", "Accessories"])
                        p_desc = st.text_area("Description")
                        if st.form_submit_button("Create Parent"):
                            success, msg = db.save_product_parent(p_name, p_sku, p_cat, p_desc)
                            if success: st.success(msg)
                            else: st.error(msg)
                with tab2:
                    parents = db.get_parent_products()
                    if not parents: st.info("Create a Parent first."); st.stop()
                    sel_p = st.selectbox("Select Parent", [p['sku'] for p in parents])
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
                    if children: st.dataframe(pd.DataFrame(children)[['sku', 'color', 'size', 'rate']], hide_index=True)
             show_product_master()

        if c2.button("🔗 Open SKU Mapping", key="sm_btn"): 
             @st.dialog("🔗 Picklist Mapping")
             def show_sku_mapping():
                st.info("Map Internal SKUs to Marketplace SKUs")
                with st.form("map_form"):
                    sparsh_sku = st.selectbox("Internal SKU", db.get_child_skus_list())
                    channel = st.selectbox("Channel", ["Flipkart", "Meesho", "Amazon", "Myntra"])
                    chan_sku = st.text_input("Channel SKU ID")
                    if st.form_submit_button("Save Mapping"):
                        db.save_sku_mapping(sparsh_sku, channel, chan_sku)
                        st.success("Mapped!")
                st.markdown("##### Current Mappings")
                df_map = pd.DataFrame(db.get_mappings())
                if not df_map.empty: st.dataframe(df_map, hide_index=True)
             show_sku_mapping()
        
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
        f_lot = st.selectbox("Filter Lot", ["All"] + db.get_active_lots())
        bun_opts = ["All"] + (db.get_bundles_for_lot(f_lot) if f_lot != "All" else [])
        f_bun = st.selectbox("Filter Bundle", bun_opts)
        
        if f_lot != "All" and f_bun != "All":
            journey_data, created_qty, current_qty = db.get_bundle_journey(f_lot, f_bun)
            c1, c2 = st.columns(2)
            c1.metric("Initial Created", f"{created_qty} pcs")
            c2.metric("Current Handover", f"{current_qty} pcs")
            st.caption("📦 **Full Journey Timeline**")
            if journey_data: render_html_table(pd.DataFrame(journey_data), ["Date", "Process", "Issued To", "Issued Qty", "Status"])
            else: st.warning("No journey data found.")
        else:
            df_prog = db.get_bundle_progress(f_lot, f_bun)
            if not df_prog.empty: st.dataframe(df_prog, column_config={"Current Stage": st.column_config.TextColumn("Stage"), "Pcs": st.column_config.NumberColumn("Current Qty")}, use_container_width=True)
            else: st.info("No Lots Found")

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
        st.caption("Recent Fabrication Entries")
        df_fab = db.get_recent_fabrication()
        if not df_fab.empty:
            df_fab['date'] = pd.to_datetime(df_fab['date']).dt.strftime('%d-%b')
            render_html_table(df_fab, ['date', 'party', 'item', 'total_value'])
                
    elif work_nav == "Sales":
        # ... (Sales Logic) ...
        pass
    
    elif work_nav == "Purchase":
        # ... (Purchase Logic) ...
        pass

    elif work_nav == "Ledger":
        st.markdown("##### 📒 Party Ledger")
        sel_party = st.selectbox("Select Party", [""] + db.get_parties_list())
        if sel_party:
            df_ledg = db.get_party_ledger(sel_party)
            if not df_ledg.empty:
                balance = df_ledg['debit'].sum() - df_ledg['credit'].sum()
                st.markdown(f"#### Net Balance: <span style='color:{'red' if balance < 0 else 'green'}'>₹ {balance:,.0f}</span>", unsafe_allow_html=True)
                df_ledg['Date'] = df_ledg['date'].dt.strftime('%d-%b')
                render_html_table(df_ledg, ['Date', 'description', 'debit', 'credit'])

    elif work_nav == "Cashbook":
        # ... (Cashbook Logic) ...
        pass

    elif work_nav == "Lots":
        st.markdown("##### 📦 Lot Management")
        up_file = st.file_uploader("Upload CSV", type=["csv"])
        if up_file and st.button("🚀 IMPORT"):
            try:
                if db.save_bulk_lots(pd.read_csv(up_file)): st.success("Imported!")
            except: st.error("Error")
        df_lots = db.get_df("masters_lots")
        if not df_lots.empty: render_df(df_lots, "lots_data")
        
    elif work_nav == "Log": render_df(db.get_df("production"), "log")
    
# --- 9. STAFF ---
elif "Staff" in selected_nav:
    staff_view = st.segmented_control("View", ["📊 Stats", "📅 Attendance", "💸 Payments"], default="📊 Stats")
    if staff_view == "📊 Stats":
        s = st.selectbox("Staff", [""] + db.get_staff_list())
        if s:
            e, p, bal, hist = db.get_worker_history(s)
            st.markdown(f"### Balance: ₹ {bal:,.0f}")
            c1, c2 = st.columns(2)
            d1 = c1.date_input("From", datetime.date.today().replace(day=1))
            d2 = c2.date_input("To", datetime.date.today())
            er, pr, df_r = db.get_staff_range_stats(s, str(d1), str(d2))
            st.markdown(f"**Period:** Earned ₹{er:,.0f} | Paid ₹{pr:,.0f}")
            if not df_r.empty:
                df_r['Date'] = pd.to_datetime(df_r['date']).dt.strftime('%d-%b')
                if 'item' in df_r.columns: render_html_table(df_r, ['Date', 'item', 'amount'])
                else: render_html_table(df_r, ['Date', 'status', 'daily_earnings'])

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

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
def check_password():
    if st.session_state["password_input"] == "Flow@1993":
        st.session_state["authenticated"] = True
        del st.session_state["password_input"]
    else: st.error("❌ Incorrect Password")

if not st.session_state["authenticated"]:
    st.markdown("<h1 style='text-align: center;'>🔒 Sparsh 1.0 Login</h1>", unsafe_allow_html=True)
    st.text_input("Enter Password", type="password", key="password_input", on_change=check_password)
    st.stop()

# --- 3. SESSION STATE INITIALIZATION (MOVED TO TOP) ---
if "sale_cart" not in st.session_state: st.session_state.sale_cart = []
if "pur_cart" not in st.session_state: st.session_state.pur_cart = []
if "last_invoice_html" not in st.session_state: st.session_state.last_invoice_html = None
if "selected_staff_stat" not in st.session_state: st.session_state.selected_staff_stat = None
if "staff_search" not in st.session_state: st.session_state.staff_search = None
# Initialize Chat State EARLY to prevent Attribute Errors
if "chat_history" not in st.session_state: 
    st.session_state.chat_history = [{"role": "assistant", "content": "👋 **Hi! Select an option below or type a command.**"}]
if "chat_mode" not in st.session_state: st.session_state.chat_mode = "menu"
if "chat_active" not in st.session_state: st.session_state.chat_active = False

# --- 4. CSS ---
st.markdown("""
<style>
    /* GLOBAL THEME */
    .stApp { background-color: #F8FAFC; font-family: 'Inter', sans-serif; }
    header[data-testid="stHeader"] { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }
    
    /* NAVIGATION */
    div.stSegmentedControl { position: sticky; top: 0; z-index: 9999; background-color: #F8FAFC; padding: 10px 0; margin-bottom: 10px; }
    
    /* DASHBOARD GRID */
    .dashboard-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 20px; }
    @media (min-width: 768px) { .dashboard-grid { grid-template-columns: repeat(4, 1fr); } }
    
    /* STAFF GRID */
    .staff-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 10px; }
    @media (min-width: 768px) { .staff-grid { grid-template-columns: repeat(4, 1fr); } }
    
    /* STAFF CARDS */
    .staff-card-pretty {
        background: linear-gradient(135deg, #ffffff 0%, #f3f4f6 100%);
        border-radius: 16px; padding: 15px; border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); text-align: center; height: 100%;
    }
    .card-name { font-size: 16px; font-weight: 700; color: #1F2937; margin-bottom: 5px; }
    .card-stat-row { display: flex; justify-content: space-between; font-size: 12px; margin-top: 8px; color: #6B7280; }
    .card-val { font-weight: 700; color: #4F46E5; }
    
    /* --- WHATSAPP CHAT UI --- */
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

    /* ACTION BUTTONS IN CHAT */
    .chat-actions {
        display: flex;
        gap: 5px;
        justify-content: space-around;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid #D1D7DB;
    }

    /* FORM CONTAINER INSIDE CHAT */
    .chat-form-container {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-top: 10px;
    }

    /* FIX CHAT INPUT VISIBILITY */
    .stChatInput textarea {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 20px !important;
    }
    
    /* TABLES & INPUTS */
    .styled-table { border-collapse: collapse; margin: 15px 0; font-size: 13px; font-family: 'Inter', sans-serif; width: 100%; box-shadow: 0 0 20px rgba(0, 0, 0, 0.05); border-radius: 10px; overflow: hidden; background-color: white; }
    .styled-table thead tr { background-color: #4F46E5; color: white; text-align: left; }
    .styled-table th, .styled-table td { padding: 10px 15px; }
    .styled-table tbody tr { border-bottom: 1px solid #dddddd; }
    .styled-table tbody tr:nth-of-type(even) { background-color: #F9FAFB; }
    
    .stTextInput input, .stNumberInput input, .stDateInput input { background-color: white !important; border: 1px solid #E2E8F0 !important; border-radius: 12px !important; min-height: 48px !important; font-size: 15px !important; color: #1E293B !important; }
    div[data-baseweb="select"] > div { background-color: white !important; border: 1px solid #E2E8F0 !important; border-radius: 12px !important; min-height: 48px !important; color: #1E293B !important; }
    .stButton button { width: 100%; min-height: 48px; border-radius: 12px; font-weight: 600; background-color: #4F46E5; color: white; border: none; }
    
    /* BUTTON CARDS */
    div[data-testid="stColumn"] button { width: 100%; border-radius: 12px; height: auto; padding: 15px 5px; background-color: white; border: 1px solid #E2E8F0; color: #1F2937; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    div[data-testid="stColumn"] button:hover { border-color: #4F46E5; color: #4F46E5; transform: translateY(-2px); transition: 0.2s; }
</style>
""", unsafe_allow_html=True)

# --- 5. HELPER FUNCTIONS ---
def render_mobile_card(title, subtitle, metric_label, metric_value):
    st.markdown(f"""
    <div class="mobile-card">
        <div style="font-weight:700; font-size:15px; color:#111827; margin-bottom:4px;">{title}</div>
        <div style="font-size:12px; color:#6B7280; margin-bottom:8px;">{subtitle}</div>
        <div class="card-row">
            <span style="font-size:11px; color:#9CA3AF; font-weight:500;">{metric_label}</span>
            <span style="font-size:13px; font-weight:700; color:#4F46E5; background:#EEF2FF; padding:4px 10px; border-radius:8px;">{metric_value}</span>
        </div>
    </div>""", unsafe_allow_html=True)

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
    return f"""<div style="background: white; padding: 30px; border: 1px solid #ddd; font-family: sans-serif; max-width: 800px; margin: auto;"><div style="display: flex; justify-content: space-between; border-bottom: 2px solid #4F46E5; padding-bottom: 20px;"><div><h1 style="margin: 0; color: #4F46E5;">INVOICE</h1><p style="margin: 5px 0; font-weight: bold;">{type_label}</p></div><div style="text-align: right;"><h3 style="margin: 0;"># {bill_no}</h3><p style="margin: 5px 0; color: #666;">Date: {date}</p></div></div><div style="margin: 20px 0;"><p style="margin: 0; font-size: 12px; color: #888; text-transform: uppercase;">Bill To</p><h3 style="margin: 5px 0;">{party}</h3></div><table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;"><thead><tr style="background: #f8f9fa; text-align: left;"><th style="padding: 10px; border-bottom: 2px solid #ddd;">Item</th><th style="padding: 10px; border-bottom: 2px solid #ddd; text-align: center;">Qty</th><th style="padding: 10px; border-bottom: 2px solid #ddd; text-align: right;">Rate</th><th style="padding: 10px; border-bottom: 2px solid #ddd; text-align: right;">Total</th></tr></thead><tbody>{items_html}</tbody></table><div style="display: flex; justify-content: flex-end;"><div style="width: 250px;"><div style="display: flex; justify-content: space-between; padding: 5px 0;"><span>Sub Total:</span><span>₹ {sub_total:,.2f}</span></div><div style="display: flex; justify-content: space-between; padding: 5px 0; color: #666;"><span>Tax:</span><span>₹ {tax_amt:,.2f}</span></div><div style="display: flex; justify-content: space-between; padding: 10px 0; border-top: 2px solid #4F46E5; font-weight: bold; font-size: 18px;"><span>Total:</span><span>₹ {grand_total:,.0f}</span></div></div></div></div>"""

# --- CHAT NLP LOGIC ---
def process_text_command(msg):
    msg_lower = msg.lower()
    staff_list = db.get_staff_list()
    found_staff = None
    for s in staff_list:
        if s.lower() in msg_lower: found_staff = s; break
    
    if not found_staff: return "❌ I couldn't find a staff name in your message."

    # Delete
    if any(x in msg_lower for x in ["delete", "remove"]):
        if "work" in msg_lower:
            rec = db.get_last_production(found_staff)
            if rec: db.delete_record_by_id("production", rec['_id']); return f"🗑️ Deleted last work for {found_staff}."
            return "⚠️ No work found."
    
    # Edit
    if "change" in msg_lower and "qty" in msg_lower:
        qty_match = re.search(r'(\d+)', msg_lower)
        if qty_match:
            rec = db.get_last_production(found_staff)
            if rec: db.update_production_qty(rec['_id'], float(qty_match.group(1))); return f"✏️ Updated qty to {qty_match.group(1)}."

    return "🤖 I didn't understand. Use the buttons above for entry."

# --- CHAT RENDERER ---
def render_chat_system():
    # 1. Chat Container (History)
    st.markdown('<div class="chat-area-wrapper">', unsafe_allow_html=True)
    
    # History
    chat_html = '<div class="chat-container">'
    # Safe access to chat_history
    if "chat_history" in st.session_state and st.session_state.chat_history:
        for msg in st.session_state.chat_history:
            bubble_class = "user-bubble" if msg["role"] == "user" else "bot-bubble"
            align_class = "flex-end" if msg["role"] == "user" else "flex-start"
            content = msg["content"].replace("\n", "<br>")
            chat_html += f'<div style="display:flex; width:100%; justify-content:{align_class};"><div class="chat-bubble {bubble_class}">{content}<div class="msg-time">{datetime.datetime.now().strftime("%H:%M")}</div></div></div>'
    else:
         st.session_state.chat_history = [{"role": "assistant", "content": "👋 **Hi! Select an option below.**"}]
         
    chat_html += '</div>'
    st.markdown(chat_html, unsafe_allow_html=True)
    
    # 2. Interactive Forms Area
    mode = st.session_state.chat_mode
    
    if mode == "menu":
        c1, c2, c3 = st.columns(3)
        if c1.button("🏭 Production", use_container_width=True):
            st.session_state.chat_mode = "production"
            st.rerun()
        if c2.button("📅 Attendance", use_container_width=True):
            st.session_state.chat_mode = "attendance"
            st.rerun()
        if c3.button("💸 Cashbook", use_container_width=True):
            st.session_state.chat_mode = "cashbook"
            st.rerun()
            
    elif mode == "production":
        st.markdown('<div class="chat-form-container">', unsafe_allow_html=True)
        st.caption("🏭 **New Production Entry**")
        with st.form("chat_prod"):
            cp_staff = st.selectbox("Worker", db.get_staff_list())
            cp_lot = st.selectbox("Lot No", db.get_active_lots())
            
            bun_opts = []
            if cp_lot:
                bundles = db.get_detailed_bundles(cp_lot)
                bun_opts = [f"{b['bundle_no']} | {b['item_name']} | {b['qty']} pcs" for b in bundles]
            
            cp_bun_label = st.selectbox("Bundle", bun_opts)
            cp_proc = st.selectbox("Process", db.get_processes_list())
            cp_qty = st.number_input("Qty", min_value=1.0)
            
            c_b, c_s = st.columns([1,2])
            if c_b.form_submit_button("Cancel"):
                st.session_state.chat_mode = "menu"; st.rerun()
            
            if c_s.form_submit_button("✅ Save", type="primary"):
                if cp_staff and cp_lot and cp_bun_label:
                    real_bun = cp_bun_label.split(" | ")[0]
                    b_det = db.get_bundle_details(cp_lot, real_bun)
                    i_name = b_det.get('item_name', 'Unknown')
                    rate = db.get_rate(i_name, cp_proc)
                    db.save_production(str(datetime.date.today()), cp_staff, i_name, cp_proc, cp_qty, rate, cp_lot, real_bun)
                    
                    st.session_state.chat_history.append({"role": "user", "content": f"Production: {cp_staff}, {cp_qty} pcs"})
                    st.session_state.chat_history.append({"role": "assistant", "content": f"✅ **Saved!** Amt: ₹{cp_qty*rate}"})
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
        
        if st.button("Cancel"):
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
            if c_b.form_submit_button("Cancel"):
                st.session_state.chat_mode = "menu"; st.rerun()
            if c_s.form_submit_button("Save"):
                db.save_cash_transaction(str(datetime.date.today()), cc_type, cc_amt, cc_party, "Cash", cc_rem)
                st.session_state.chat_history.append({"role": "assistant", "content": "✅ Cash Transaction Saved."})
                st.session_state.chat_mode = "menu"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True) # End Wrapper

    # 3. Text Input (Always available for commands)
    if prompt := st.chat_input("Type a command (e.g. 'Delete last work of Deepa')"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        resp = process_text_command(prompt)
        st.session_state.chat_history.append({"role": "assistant", "content": resp})
        st.rerun()

# --- 6. NAVIGATION ---
nav_options = ["🏠 Home", "🏭 Work", "👥 Staff", "⚙️ Masters"]
selected_nav = st.segmented_control("Main Menu", nav_options, default="🏠 Home", label_visibility="collapsed")

# --- RESET CHAT SESSION ON NAV CHANGE ---
if "last_nav" not in st.session_state: st.session_state.last_nav = "🏠 Home"
if selected_nav != st.session_state.last_nav:
    if st.session_state.get("chat_active", False):
        st.session_state.chat_history = [{"role": "assistant", "content": "👋 **Hi! Select an option below.**"}]
        st.session_state.chat_mode = "menu"
        st.session_state.chat_active = False 
    st.session_state.last_nav = selected_nav

# --- 7. PAGE: DASHBOARD (HOME) ---
if selected_nav == "🏠 Home":
    
    # --- CHAT MODE ---
    if st.session_state.get("chat_active", False):
        st.markdown(f"""
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:5px;">
            <h3 style="margin:0;">💬 Sparsh AI</h3>
            <div style="font-size:12px; color:grey;">Interactive Mode</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("❌ Close Assistant", use_container_width=True):
            st.session_state.chat_active = False
            st.rerun()
            
        render_chat_system()

    else:
        # --- HOME DASHBOARD ---
        st.markdown("##### 👋 Dashboard")
        
        # MAIN CHAT TRIGGER BUTTON
        if st.button("💬 Open AI Assistant", use_container_width=True, type="primary"):
            st.session_state.chat_active = True
            st.rerun()

        # FLOATING CHAT BUTTON (RIGHT MIDDLE)
        with st.popover("💬", use_container_width=False):
            st.markdown("### 🤖 Sparsh AI Assistant")
            
            # Simple Chat inside popover
            chat_html = '<div class="chat-container" style="height:250px;">'
            # Safe Slice (Prevent Error if empty)
            if "chat_history" in st.session_state and st.session_state.chat_history:
                msgs_to_show = st.session_state.chat_history[-4:]
                for msg in msgs_to_show:
                    bubble_class = "user-bubble" if msg["role"] == "user" else "bot-bubble"
                    align_class = "flex-end" if msg["role"] == "user" else "flex-start"
                    content = msg["content"].replace("\n", "<br>")
                    chat_html += f'<div style="display:flex; width:100%; justify-content:{align_class};"><div class="chat-bubble {bubble_class}">{content}</div></div>'
            else:
                 chat_html += '<div style="display:flex; width:100%; justify-content:flex-start;"><div class="chat-bubble bot-bubble">Hi!</div></div>'
                 
            chat_html += '</div>'
            st.markdown(chat_html, unsafe_allow_html=True)
            
            if prompt := st.chat_input("Quick Chat..."):
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                response = process_text_command(prompt)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()

        pcs, earn, pending, active = db.get_dashboard_stats()
        
        st.markdown(f"""
        <div class="dashboard-grid">
            <div class="stat-tile-html" style="border-bottom: 4px solid #10B981;">
                <div class="stat-num-html">{pcs:,.0f}</div>
                <div class="stat-desc-html">Today Pcs</div>
            </div>
            <div class="stat-tile-html" style="border-bottom: 4px solid #F59E0B;">
                <div class="stat-num-html">₹{earn:,.0f}</div>
                <div class="stat-desc-html">Prod. Value</div>
            </div>
            <div class="stat-tile-html" style="border-bottom: 4px solid #EF4444;">
                <div class="stat-num-html">₹{pending:,.0f}</div>
                <div class="stat-desc-html">Pending Pay</div>
            </div>
            <div class="stat-tile-html" style="border-bottom: 4px solid #6366F1;">
                <div class="stat-num-html">{active}</div>
                <div class="stat-desc-html">Active Staff</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("⚡ **Quick Work Entry**", expanded=False):
            with st.container(border=True):
                p_date = st.date_input("Date", datetime.date.today())
                all_lots = db.get_active_lots()
                c_lot, c_bun = st.columns(2)
                p_lot = c_lot.selectbox("Lot No.", [""] + all_lots, key="home_lot")
                
                bun_options = []
                bun_map = {}
                if p_lot:
                    bundles = db.get_detailed_bundles(p_lot)
                    for b in bundles:
                        label = f"{b['bundle_no']} | {b['item_name']} | {b['color']} | {b['size']} | {b['qty']} pcs"
                        bun_options.append(label)
                        bun_map[label] = b
                
                p_bundle_sel = c_bun.selectbox("Bundle No (Detail)", [""] + bun_options, key="home_bun")
                
                auto_item, auto_qty = "", 0.0
                real_bundle_no = ""
                
                if p_bundle_sel and p_lot:
                    sel_data = bun_map[p_bundle_sel]
                    real_bundle_no = sel_data['bundle_no']
                    auto_item = sel_data.get('item_name', '')
                    auto_qty = float(sel_data.get('qty', 0))
                    st.caption(f"Selected: **{auto_item}** | Default Qty: {auto_qty}")
                
                c_staff, c_item = st.columns(2)
                p_staff = c_staff.selectbox("Worker", [""] + db.get_staff_list())
                item_list = db.get_items_list()
                idx_item = item_list.index(auto_item) if auto_item in item_list else 0
                p_item = c_item.selectbox("Item", [""] + item_list, index=idx_item+1 if auto_item else 0)
                
                c_proc, c_qty = st.columns(2)
                p_process = c_proc.selectbox("Process", [""] + db.get_processes_list())
                p_qty = c_qty.number_input("Qty", min_value=0.0, value=auto_qty, step=1.0)
                
                if st.button("SAVE ENTRY"):
                    if not p_lot or not p_bundle_sel or not p_staff or not p_item: st.error("⚠️ Missing Fields")
                    else:
                        auto_rate = db.get_rate(p_item, p_process)
                        db.save_production(str(p_date), p_staff, p_item, p_process, p_qty, auto_rate, p_lot, real_bundle_no)
                        st.success(f"✅ Saved! Rate: ₹{auto_rate}")

# --- 8. PAGE: WORK ---
elif "Work" in selected_nav:
    st.markdown("##### 🏭 Work Management")
    work_opts = ["Production", "Bundle Progress", "Sales", "Purchase", "Ledger", "Cashbook", "Lots", "Log"]
    work_nav = st.segmented_control("Work Section", work_opts, default="Production")
    
    if work_nav == "Production":
        with st.container(border=True):
            st.markdown("**Production Entry**")
            p_date = st.date_input("Date", datetime.date.today(), key="w_date")
            all_lots = db.get_active_lots()
            c_lot, c_bun = st.columns(2)
            p_lot = c_lot.selectbox("Lot No.", [""] + all_lots, key="w_lot")
            
            bun_options = []
            bun_map = {}
            if p_lot:
                bundles = db.get_detailed_bundles(p_lot)
                for b in bundles:
                    label = f"{b['bundle_no']} | {b['item_name']} | {b['color']} | {b['size']} | {b['qty']} pcs"
                    bun_options.append(label)
                    bun_map[label] = b
            
            p_bundle_sel = c_bun.selectbox("Bundle No (Detail)", [""] + bun_options, key="w_bun")
            
            auto_item, auto_qty = "", 0.0
            real_bundle_no = ""
            if p_bundle_sel and p_lot:
                sel_data = bun_map[p_bundle_sel]
                real_bundle_no = sel_data['bundle_no']
                auto_item = sel_data.get('item_name', '')
                auto_qty = float(sel_data.get('qty', 0))
            
            c_staff, c_item = st.columns(2)
            p_staff = c_staff.selectbox("Worker", [""] + db.get_staff_list(), key="w_staff")
            item_list = db.get_items_list()
            idx_item = item_list.index(auto_item) if auto_item in item_list else 0
            p_item = c_item.selectbox("Item", [""] + item_list, index=idx_item+1 if auto_item else 0, key="w_item")
            
            c_proc, c_qty = st.columns(2)
            p_process = c_proc.selectbox("Process", [""] + db.get_processes_list(), key="w_proc")
            p_qty = c_qty.number_input("Qty", min_value=0.0, value=auto_qty, step=1.0, key="w_qty")
            
            if st.button("CONFIRM WORK", type="primary"):
                if p_lot and p_bundle_sel and p_staff and p_item:
                    auto_rate = db.get_rate(p_item, p_process)
                    db.save_production(str(p_date), p_staff, p_item, p_process, p_qty, auto_rate, p_lot, real_bundle_no)
                    st.success(f"✅ Recorded! Rate: ₹{auto_rate}")
                else: st.error("Missing Data")
                
    elif work_nav == "Bundle Progress":
        st.markdown("##### 📊 Bundle Progress Tracker")
        df_prog = db.get_bundle_progress()
        if not df_prog.empty:
            st.dataframe(
                df_prog,
                column_config={
                    "Done": st.column_config.ProgressColumn("Progress", min_value=0, max_value=100, format="%f"),
                },
                use_container_width=True
            )
        else:
            st.info("No Lots Found")
    
    elif work_nav == "Sales":
        if st.session_state.last_invoice_html:
            with st.expander("📄 **Generated Invoice (Click to View)**", expanded=True):
                st.markdown(st.session_state.last_invoice_html, unsafe_allow_html=True)
                if st.button("❌ Close Invoice"):
                    st.session_state.last_invoice_html = None
                    st.rerun()
            st.markdown("---")

        mode = st.radio("Mode", ["New Invoice", "Edit Invoice"], horizontal=True, label_visibility="collapsed")
        
        if mode == "New Invoice":
            with st.container(border=True):
                st.markdown("**New Sale Invoice**")
                c1, c2, c3, c4 = st.columns(4)
                pd_ = c1.date_input("Date", datetime.date.today(), key="sale_date")
                s_party = c2.selectbox("Customer", [""] + db.get_parties_list(), key="s_party")
                s_bill = c3.text_input("Bill No", key="s_bill")
                s_gst = c4.selectbox("GST %", [0.0] + db.get_gst_list(), key="s_gst")
                
                with st.form("s_line"):
                    c_i, c_q, c_r = st.columns(3)
                    li_item = c_i.text_input("Item")
                    li_qty = c_q.number_input("Qty", min_value=1.0, step=1.0)
                    li_rate = c_r.number_input("Rate", min_value=0.0)
                    if st.form_submit_button("Add Item"):
                        st.session_state.sale_cart.append({"item": li_item, "qty": li_qty, "rate": li_rate})
                        st.rerun()
                
                if st.session_state.sale_cart:
                    st.markdown("###### Items in Cart")
                    df_cart = pd.DataFrame(st.session_state.sale_cart)
                    df_cart['Amount'] = df_cart['qty'] * df_cart['rate']
                    st.dataframe(df_cart, hide_index=True)
                    
                    sub_total = df_cart['Amount'].sum()
                    tax_amt = sub_total * (s_gst / 100.0)
                    grand_total = sub_total + tax_amt
                    
                    st.markdown(f"""
                    <div style='background:#F8FAFC; padding:15px; border-radius:10px; border:1px solid #E2E8F0;'>
                        <div style='display:flex; justify-content:space-between;'><span>Sub Total:</span> <b>₹ {sub_total:,.2f}</b></div>
                        <div style='display:flex; justify-content:space-between; color:#EF4444;'><span>Tax ({s_gst}%):</span> <b>+ ₹ {tax_amt:,.2f}</b></div>
                        <hr style='margin:5px 0;'>
                        <div style='display:flex; justify-content:space-between; font-size:18px;'><span>Grand Total:</span> <b>₹ {grand_total:,.0f}</b></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("✅ FINALIZE & PRINT INVOICE", type="primary"):
                        if s_party and s_bill:
                            db.save_sale_invoice(str(pd_), s_party, s_bill, st.session_state.sale_cart, s_gst)
                            inv_html = generate_invoice_html("SALES INVOICE", s_bill, str(pd_), s_party, df_cart, sub_total, tax_amt, grand_total)
                            st.session_state.last_invoice_html = inv_html
                            st.session_state.sale_cart = []
                            st.success("Invoice Saved!")
                            st.rerun()
                        else: st.error("Missing Party or Bill No")
        else:
            st.warning("✏️ Edit Mode")
            txs = db.get_recent_transactions("transactions_sales")
            if txs:
                tx_map = {f"{t['date'].strftime('%d-%b')} | Bill: {t['bill_no']} | {t['item']} (₹{t['grand_total']})": t for t in txs}
                sel_tx = st.selectbox("Select Transaction", list(tx_map.keys()))
                if sel_tx:
                    d = tx_map[sel_tx]
                    if st.button("🗑️ Delete"):
                        db.delete_transaction("transactions_sales", d['_id']); st.rerun()
    
    elif work_nav == "Purchase":
        if st.session_state.last_invoice_html:
            with st.expander("📄 **Generated Invoice (Click to View)**", expanded=True):
                st.markdown(st.session_state.last_invoice_html, unsafe_allow_html=True)
                if st.button("❌ Close Invoice"):
                    st.session_state.last_invoice_html = None
                    st.rerun()
            st.markdown("---")

        mode = st.radio("Mode", ["New Invoice", "Edit Invoice"], horizontal=True, label_visibility="collapsed")
        
        if mode == "New Invoice":
            with st.container(border=True):
                st.markdown("**New Purchase Invoice**")
                p_type = st.radio("Entry Type", ["Purchase", "Purchase Return"], horizontal=True, key="p_type_sel")
                
                c1, c2, c3, c4 = st.columns(4)
                pd_ = c1.date_input("Date", datetime.date.today(), key="pur_date")
                p_vend = c2.selectbox("Vendor", [""] + db.get_parties_list(), key="p_vend")
                p_bill = c3.text_input("Bill No", key="p_bill")
                p_gst = c4.selectbox("GST %", [0.0] + db.get_gst_list(), key="p_gst")
                
                with st.form("p_line"):
                    c_i, c_q, c_r = st.columns(3)
                    li_item = c_i.text_input("Item")
                    li_qty = c_q.number_input("Qty", min_value=1.0, step=1.0)
                    li_rate = c_r.number_input("Rate", min_value=0.0)
                    if st.form_submit_button("Add Item"):
                        st.session_state.pur_cart.append({"item": li_item, "qty": li_qty, "rate": li_rate})
                        st.rerun()
                
                if st.session_state.pur_cart:
                    st.markdown("###### Items in Cart")
                    df_cart = pd.DataFrame(st.session_state.pur_cart)
                    df_cart['Amount'] = df_cart['qty'] * df_cart['rate']
                    st.dataframe(df_cart, hide_index=True)
                    
                    sub_total = df_cart['Amount'].sum()
                    tax_amt = sub_total * (p_gst / 100.0)
                    grand_total = sub_total + tax_amt
                    
                    st.markdown(f"""
                    <div style='background:#F8FAFC; padding:15px; border-radius:10px; border:1px solid #E2E8F0;'>
                        <div style='display:flex; justify-content:space-between;'><span>Sub Total:</span> <b>₹ {sub_total:,.2f}</b></div>
                        <div style='display:flex; justify-content:space-between; color:#EF4444;'><span>Tax ({p_gst}%):</span> <b>+ ₹ {tax_amt:,.2f}</b></div>
                        <hr style='margin:5px 0;'>
                        <div style='display:flex; justify-content:space-between; font-size:18px;'><span>Grand Total:</span> <b>₹ {grand_total:,.0f}</b></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("✅ FINALIZE & PRINT", type="primary"):
                        if p_vend and p_bill:
                            db.save_purchase_invoice(str(pd_), p_vend, p_type, p_bill, st.session_state.pur_cart, p_gst)
                            inv_html = generate_invoice_html(f"{p_type.upper()} INVOICE", p_bill, str(pd_), p_vend, df_cart, sub_total, tax_amt, grand_total)
                            st.session_state.last_invoice_html = inv_html
                            st.session_state.pur_cart = []
                            st.success(f"{p_type} Saved!")
                            st.rerun()
                        else: st.error("Missing Vendor or Bill No")

            st.caption("Recent Invoices")
            df_bills = db.get_recent_purchase_bills()
            if not df_bills.empty:
                df_bills['date'] = pd.to_datetime(df_bills['date']).dt.strftime('%d-%b')
                df_bills['Total'] = df_bills['total_amount'].apply(lambda x: f"₹{x:,.0f}")
                render_html_table(df_bills, ['date', 'type', 'bill_no', 'vendor', 'Total'])
            else: st.info("No recent invoices.")
        
        else:
            st.warning("✏️ Edit Mode")
            txs = db.get_recent_transactions("transactions_purchase")
            if txs:
                tx_map = {f"{t['date'].strftime('%d-%b')} | {t.get('type','Pur')} | {t['item']} (₹{t['grand_total']})": t for t in txs}
                sel_tx = st.selectbox("Select Transaction", list(tx_map.keys()))
                if sel_tx:
                    d = tx_map[sel_tx]
                    if st.button("🗑️ Delete"):
                        db.delete_transaction("transactions_purchase", d['_id']); st.rerun()

    elif work_nav == "Ledger":
        st.markdown("##### 📒 Party Ledger")
        sel_party = st.selectbox("Select Party", [""] + db.get_parties_list(), key="ledg_party")
        view_type = st.radio("View Mode", ["Bill & Item Wise", "Bill Wise"], horizontal=True, label_visibility="collapsed")
        
        if sel_party:
            df_ledg = db.get_party_ledger(sel_party)
            if not df_ledg.empty:
                df_ledg['debit'] = df_ledg['debit'].fillna(0.0)
                df_ledg['credit'] = df_ledg['credit'].fillna(0.0)
                
                if view_type == "Bill Wise":
                    mask_bill = (df_ledg['bill_no'] != "-") & (df_ledg['bill_no'].notna())
                    df_bills = df_ledg[mask_bill]
                    df_others = df_ledg[~mask_bill]
                    if not df_bills.empty:
                        df_grouped = df_bills.groupby(['bill_no', 'date', 'type']).agg({
                            'description': lambda x: f"Bill #{x.iloc[0]} (Consolidated)",
                            'debit': 'sum', 'credit': 'sum'
                        }).reset_index()
                        df_ledg = pd.concat([df_grouped, df_others], ignore_index=True)
                    else: df_ledg = df_others
                    df_ledg = df_ledg.sort_values(by='date')

                df_ledg['Date'] = df_ledg['date'].dt.strftime('%d-%b-%Y')
                df_ledg['Debit (+)'] = df_ledg['debit'].apply(lambda x: f"₹{x:,.0f}" if x>0 else "-")
                df_ledg['Credit (-)'] = df_ledg['credit'].apply(lambda x: f"₹{x:,.0f}" if x>0 else "-")
                
                balance = df_ledg['debit'].sum() - df_ledg['credit'].sum()
                bal_color = "money-neg" if balance < 0 else "money-pos"
                st.markdown(f"#### Net Balance: <span class='{bal_color}'>₹ {balance:,.0f}</span>", unsafe_allow_html=True)
                render_html_table(df_ledg, ['Date', 'description', 'Debit (+)', 'Credit (-)'])
            else: st.info("No transactions found.")

    elif work_nav == "Cashbook":
        mode = st.radio("Mode", ["New Entry", "Edit Entry"], horizontal=True, label_visibility="collapsed")
        if mode == "New Entry":
            with st.container(border=True):
                st.markdown("**Cashbook Entry**")
                tx_type = st.radio("Type", ["Money In (Income)", "Money Out (Expense)"], horizontal=True)
                c1, c2 = st.columns(2)
                cb_date = c1.date_input("Date", datetime.date.today(), key="cb_date")
                cb_amt = c2.number_input("Amount (₹)", min_value=1.0)
                c3, c4 = st.columns(2)
                cb_party = c3.selectbox("Party", [""] + db.get_parties_list(), key="cb_party")
                cb_acc = c4.text_input("Account (Bank/Cash)")
                cb_rem = st.text_input("Remarks")
                if st.button("SAVE TRANSACTION"):
                    if cb_amt and cb_party:
                        t_short = "IN" if "In" in tx_type else "OUT"
                        db.save_cash_transaction(str(cb_date), t_short, cb_amt, cb_party, cb_acc, cb_rem)
                        st.success("Saved!")
                    else: st.error("Missing Info")
            
            st.caption("Recent Transactions")
            df_cb = db.get_df("transactions_cashbook")
            if not df_cb.empty:
                df_cb['date'] = pd.to_datetime(df_cb['date']).dt.strftime('%d-%b')
                def fmt_cb(row):
                    col = "money-pos" if row['type'] == "IN" else "money-neg"
                    return f"<span class='{col}'>₹ {row['amount']:,.0f}</span><br><span style='font-size:10px; color:#666;'>{row['party']}</span>"
                df_cb['Detail'] = df_cb.apply(fmt_cb, axis=1)
                render_html_table(df_cb, ['date', 'type', 'Detail', 'account'])
        else:
            st.warning("✏️ Edit Mode")
            txs = db.get_recent_transactions("transactions_cashbook")
            if txs:
                tx_map = {f"{t['date'].strftime('%d-%b')} | {t['type']} | ₹{t['amount']} ({t['party']})": t for t in txs}
                sel_tx = st.selectbox("Select Transaction", list(tx_map.keys()))
                if sel_tx:
                    d = tx_map[sel_tx]
                    with st.form("edit_cash"):
                        e_amt = st.number_input("Amount", value=float(d['amount']))
                        e_party = st.text_input("Party", value=d['party'])
                        if st.form_submit_button("Update"):
                            if db.update_transaction("transactions_cashbook", d['_id'], {"amount": e_amt, "party": e_party}):
                                st.success("Updated"); st.rerun()
                    if st.button("🗑️ Delete"):
                        if db.delete_transaction("transactions_cashbook", d['_id']): st.success("Deleted"); st.rerun()

    elif work_nav == "Lots":
        st.markdown("##### 📦 Lot Management")
        csv_temp = "date,Lot No,Item name,Bundle no.,Color Name,Size,Qty\n2023-10-25,L-101,Shirt,B-01,Blue,M,10"
        st.download_button("📥 Template", csv_temp, "lot_temp.csv", "text/csv")
        up_file = st.file_uploader("Upload CSV", type=["csv"])
        if up_file and st.button("🚀 IMPORT"):
            try:
                if db.save_bulk_lots(pd.read_csv(up_file)): st.success("Imported!")
            except: st.error("Error")
        df_lots = db.get_df("masters_lots")
        if not df_lots.empty: render_df(df_lots, "lots_data")
        
    elif work_nav == "Log":
        df_prod = db.get_df("production")
        if not df_prod.empty:
            df_prod['date'] = pd.to_datetime(df_prod['date'])
            df_prod = df_prod.sort_values(by="date", ascending=False)
            df_disp = df_prod[['date', 'staff_name', 'qty', 'amount', 'lot_no']].copy()
            df_disp['date'] = df_disp['date'].dt.strftime('%d-%b')
            render_df(df_disp, "work_log")

# --- 9. PAGE: STAFF ---
elif "Staff" in selected_nav:
    st.markdown("##### 👥 Staff Management")
    staff_view = st.segmented_control("Staff View", ["📊 Stats", "📅 Attendance", "💸 Payments"], default="📊 Stats")
    
    if staff_view == "📊 Stats":
        st.markdown("##### 📊 Staff Statistics")
        staff_list = db.get_staff_list()
        
        # --- DROPDOWN NAVIGATION ONLY ---
        if "selected_staff_stat" not in st.session_state:
             st.session_state.selected_staff_stat = None

        index_val = 0
        if st.session_state.selected_staff_stat in staff_list:
            index_val = staff_list.index(st.session_state.selected_staff_stat) + 1

        search = st.selectbox("Select Staff Member", [""] + staff_list, index=index_val, key="staff_search_box")
        
        if search:
            st.session_state.selected_staff_stat = search
        
        if st.session_state.selected_staff_stat:
            target = st.session_state.selected_staff_stat
            details = db.get_staff_details(target)
            role = details.get('role', '-')
            sal_type = details.get('salary_type', 'Piece Rate')
            m_sal = details.get('monthly_salary', 0)
            e, p, bal, hist_df = db.get_worker_history(target)
            bal_color = "#EF4444" if bal < 0 else "#10B981"
            
            st.markdown(f"""
            <div style="background:white; padding:20px; border-radius:16px; border:1px solid #E5E7EB; text-align:center; margin-bottom:20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                <h3 style="color:#1F2937; margin:0;">{target}</h3>
                <div style="color:#6B7280; font-size:12px; font-weight:600; margin-bottom:10px;">{role.upper()} • {sal_type.upper()}</div>
                <div style="font-size:32px; font-weight:800; color:{bal_color}; margin: 5px 0;">₹ {abs(bal):,.0f}</div>
                <div style="font-size:12px; font-weight:700; color:{bal_color}; letter-spacing: 1px;">{'ADVANCE TAKEN' if bal < 0 else 'PAYABLE AMOUNT'}</div>
            </div>""", unsafe_allow_html=True)
            
            st.markdown("##### 📅 Monthly Summary")
            is_salaried = (sal_type == "Salaried")
            # LIMIT TO 2 MONTHS
            df_sum = db.get_monthly_summary(target, is_salaried, m_sal, limit=2)
            
            df_sum['Earned'] = df_sum['Earned'].apply(lambda x: f"₹ {x:,.0f}")
            df_sum['Paid'] = df_sum['Paid'].apply(lambda x: f"₹ {x:,.0f}")
            df_sum['Balance'] = df_sum['Balance'].apply(lambda x: f"<span class='money-neg'>₹ {x:,.0f}</span>" if x < 0 else f"<span class='money-pos'>₹ {x:,.0f}</span>")
            render_html_table(df_sum, ['Month', 'Earned', 'Paid', 'Balance'])
            
            st.markdown("##### 📜 Activity Filter")
            c1, c2 = st.columns(2)
            start_d = c1.date_input("From", datetime.date.today().replace(day=1))
            end_d = c2.date_input("To", datetime.date.today())
            
            earned_range, paid_range, df_range = db.get_staff_range_stats(target, str(start_d), str(end_d))
            
            st.markdown(f"""
            <div style="padding:10px; background:#F3F4F6; border-radius:8px; margin-bottom:10px; display:flex; justify-content:space-between;">
                <span><b>Earned:</b> ₹{earned_range:,.0f}</span>
                <span><b>Paid:</b> ₹{paid_range:,.0f}</span>
                <span><b>Net:</b> <span style="color:{'green' if (earned_range-paid_range)>0 else 'red'}">₹{earned_range-paid_range:,.0f}</span></span>
            </div>""", unsafe_allow_html=True)
            
            if not df_range.empty:
                df_range['date'] = pd.to_datetime(df_range['date'])
                df_range['Date'] = df_range['date'].dt.strftime('%d-%b')
                
                if 'item' in df_range.columns: # Production
                     df_range['Detail'] = df_range['item'] + " (" + df_range['qty'].astype(str) + ")"
                     render_html_table(df_range, ['Date', 'Detail', 'amount'])
                else: # Attendance
                     render_html_table(df_range, ['Date', 'status', 'daily_earnings'])
            else:
                st.info("No records in selected range.")
            
            st.markdown("---")
            st.caption("Recent 10 Entries (Default View)")
            if not hist_df.empty:
                hist_df = hist_df.head(10)
                hist_df['date'] = pd.to_datetime(hist_df['date'])
                hist_df['Date'] = hist_df['date'].dt.strftime('%d-%b')
                if 'item' in hist_df.columns:
                     hist_df['Detail'] = hist_df['item']
                     render_html_table(hist_df, ['Date', 'Detail', 'amount'])
                else:
                     render_html_table(hist_df, ['Date', 'status', 'daily_earnings'])

    elif staff_view == "📅 Attendance":
        with st.container(border=True):
            st.markdown("**Mark Attendance**")
            a_date = st.date_input("Date", datetime.date.today(), key="a_date")
            a_staff = st.selectbox("Staff", [""] + db.get_staff_list(), key="a_staff")
            
            # --- DYNAMIC ATTENDANCE LOGIC ---
            record = None
            if a_staff:
                record = db.get_attendance_record(str(a_date), a_staff)
            
            is_checked_in = record and record.get('in_time') and not record.get('out_time')
            is_completed = record and record.get('out_time')
            
            if is_completed:
                st.info(f"✅ Attendance Completed for {a_date.strftime('%d-%b')}")
                st.write(f"In: {record['in_time']} | Out: {record['out_time']}")
                st.write(f"Worked: {record.get('worked_hours',0)} hrs | Pay: ₹{record.get('daily_earnings',0)}")
            elif is_checked_in:
                st.success(f"🟢 Clocked In at {record['in_time']}")
                t_out = st.time_input("Out Time", datetime.datetime.now().time())
                if st.button("🔴 CLOCK OUT"):
                    db.save_attendance(str(a_date), a_staff, "Present", in_time=None, out_time=t_out)
                    st.success("Clocked Out!")
                    st.rerun()
            else:
                status = st.radio("Status", ["Present", "Absent", "Half Day"], horizontal=True)
                if status == "Present":
                    t_in = st.time_input("In Time", datetime.time(9, 0))
                    if st.button("🟢 CLOCK IN"):
                        db.save_attendance(str(a_date), a_staff, "Present", in_time=t_in, out_time=None)
                        st.success("Clocked In!")
                        st.rerun()
                else:
                    if st.button(f"Mark {status}"):
                        db.save_attendance(str(a_date), a_staff, status, in_time=None, out_time=None)
                        st.success("Saved!")
                        st.rerun()

        st.markdown("---")
        st.subheader("📋 Logs")
        df_att = db.get_df("attendance")
        if not df_att.empty:
            df_att['date'] = pd.to_datetime(df_att['date'])
            df_att = df_att.sort_values(by="date", ascending=False)
            df_att['Date'] = df_att['date'].dt.strftime('%d-%b')
            def fmt_status(row):
                s = row['status']
                col = "status-present" if s=="Present" else "status-absent"
                html = f'<span class="{col}">{s}</span>'
                if s == "Present":
                    times = f"<br><span style='font-size:10px; color:#666;'>{row.get('in_time','-')} - {row.get('out_time','?')}</span>"
                    return html + times
                return html
            df_att['Info'] = df_att.apply(fmt_status, axis=1)
            render_html_table(df_att, ['Date', 'staff_name', 'Info'])

    elif staff_view == "💸 Payments":
        mode = st.radio("Mode", ["New Pay", "Edit Pay"], horizontal=True, label_visibility="collapsed")
        
        if mode == "New Pay":
            with st.container(border=True):
                pay_mode = st.radio("Type", ["Salary", "Advance"], horizontal=True)
                pd_ = st.date_input("Date", datetime.date.today(), key="pay_date")
                ps = st.selectbox("Staff", [""] + db.get_staff_list(), key="pay_staff")
                if ps:
                    _, _, bal, _ = db.get_worker_history(ps)
                    st.caption(f"Current Balance: ₹{bal:,.0f}")
                amt = st.number_input("Amount", min_value=1)
                rem = st.text_input("Note", pay_mode)
                if st.button("PAY"):
                    if ps and amt: db.save_payment(str(pd_), ps, amt, pay_mode, rem); st.success("Saved!")
            df_pay = db.get_df("payments")
            if not df_pay.empty:
                df_pay = df_pay.sort_values(by="created_at", ascending=False).head(5)
                for _, r in df_pay.iterrows():
                    render_mobile_card(r['staff_name'], r['type'], "Paid", f"₹{r['amount']:,.0f}")
        else:
            st.warning("✏️ Edit Staff Payment")
            txs = db.get_recent_transactions("payments")
            if txs:
                tx_map = {f"{t['date'].strftime('%d-%b')} | {t['staff_name']} | ₹{t['amount']}": t for t in txs}
                sel_tx = st.selectbox("Select Payment", list(tx_map.keys()))
                if sel_tx:
                    d = tx_map[sel_tx]
                    with st.form("edit_pay"):
                        e_amt = st.number_input("Amount", value=float(d['amount']))
                        e_rem = st.text_input("Note", value=d.get('remarks', ''))
                        if st.form_submit_button("Update"):
                            if db.update_transaction("payments", d['_id'], {"amount": e_amt, "remarks": e_rem}):
                                st.success("Updated"); st.rerun()
                    if st.button("🗑️ Delete"):
                        if db.delete_transaction("payments", d['_id']): st.success("Deleted"); st.rerun()

# --- 10. MASTERS ---
elif "Masters" in selected_nav:
    st.markdown("##### ⚙️ Setup")
    
    t_list = ["Staff", "Party", "Item", "Color", "Size", "Proc", "Rate", "GST", "Clean"]
    sub_nav = st.segmented_control("Type", t_list, default="Staff") 
    
    if not sub_nav: sub_nav = "Staff"

    if sub_nav == "Staff":
        with st.container(border=True):
            n = st.text_input("Name")
            p = st.text_input("Phone")
            r = st.selectbox("Role", ["Stitching", "Helper", "Cutting"])
            s_type = st.radio("Pay Type", ["Piece Rate", "Salaried"], horizontal=True)
            m_sal = 0.0
            if s_type == "Salaried": m_sal = st.number_input("Monthly Salary", step=500.0)
            if st.button("Save Staff", type="primary"):
                if n: db.save_staff(n, p, r, s_type, m_sal); st.success("Saved!")
                else: st.error("Name Required")
        df_s = db.get_df("masters_staff")
        if not df_s.empty and 'name' in df_s.columns:
            cols = [c for c in ['name', 'role', 'salary_type', 'monthly_salary'] if c in df_s.columns]
            render_df(df_s[cols], "staff")

    elif sub_nav == "Party":
        with st.container(border=True):
            p_name = st.text_input("Party Name")
            p_type = st.selectbox("Type", ["Customer", "Vendor", "Source"])
            if st.button("Add Party"):
                if p_name: db.save_party(p_name, p_type); st.success("Saved")
        render_df(db.get_df("masters_parties"), "parties")

    elif sub_nav == "Item":
        n = st.text_input("Name")
        if st.button("Save"): db.save_master("masters_items", {"name":n}); st.success("Saved")
        render_df(db.get_df("masters_items"), "items")

    elif sub_nav == "Rate":
        c1, c2, c3 = st.columns(3)
        i = c1.selectbox("Item", db.get_items_list())
        p = c2.selectbox("Proc", db.get_processes_list())
        r = c3.number_input("Rate", 0.0)
        if st.button("Update Rate"): db.save_rate(i, p, r); st.success("Updated")
        render_df(db.get_rates_df(), "rates")
    
    elif sub_nav == "Proc":
        n = st.text_input("Process")
        if st.button("Save"): db.save_master("masters_processes", {"name":n}); st.success("Saved")
        render_df(db.get_df("masters_processes"), "procs")
        
    elif sub_nav == "Color":
        n = st.text_input("Color Name")
        if st.button("Add Color"): db.save_master("masters_colors", {"name":n}); st.success("Added")
        render_df(db.get_df("masters_colors"), "colors")
        
    elif sub_nav == "Size":
        n = st.text_input("Size")
        if st.button("Add Size"): db.save_master("masters_sizes", {"name":n}); success("Added")
        render_df(db.get_df("masters_sizes"), "sizes")
        
    elif sub_nav == "GST":
        n = st.number_input("GST % Rate", min_value=0.0, step=1.0)
        if st.button("Add Slab"): db.save_master("masters_gst", {"rate":n}); st.success("Added")
        render_df(db.get_df("masters_gst"), "gst")
    
    elif sub_nav == "Clean":
        st.warning("⚠️ **DANGER ZONE**")
        opts = {"Staff": "masters_staff", "Items": "masters_items", "Rates": "masters_rates", "Process": "masters_processes", "Colors": "masters_colors", "Sizes": "masters_sizes", "Lots": "masters_lots", "Data": "production", "Pay": "payments", "Att": "attendance", "Pur": "transactions_purchase", "Cash": "transactions_cashbook", "Sales": "transactions_sales", "Parties": "masters_parties", "GST": "masters_gst"}
        sel = st.multiselect("Select Tables", list(opts.keys()))
        if sel and st.button("🗑️ WIPE", type="primary"):
            status, wiped = db.clean_database([opts[x] for x in sel])
            if status:
                st.success(f"Successfully wiped: {', '.join(wiped)}")
                time.sleep(2)
                st.rerun()
            else:
                st.error("Wipe Failed.")

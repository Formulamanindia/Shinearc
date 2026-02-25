import streamlit as st
import pymongo
import pandas as pd
import datetime
import random
import string
from bson.objectid import ObjectId
from dateutil.relativedelta import relativedelta

# --- CONNECT TO DATABASE ---
try:
    client = pymongo.MongoClient(st.secrets["MONGO_URI"])
    db = client['shine_arc_new_db']
except Exception as e:
    st.error(f"Database Connection Error: {e}")

# ==========================================
# 1. FETCHERS
# ==========================================
def get_staff_list(): return sorted([s['name'] for s in db.masters_staff.find({}, {'_id':0, 'name':1})])
def get_staff_details(name): return db.masters_staff.find_one({"name": name})
def get_items_list(): return sorted([i['name'] for i in db.masters_items.find({}, {'_id':0, 'name':1})])
def get_colors_list(): return sorted([c['name'] for c in db.masters_colors.find({}, {'_id':0, 'name':1})])
def get_sizes_list(): return sorted([s['name'] for s in db.masters_sizes.find({}, {'_id':0, 'name':1})])
def get_categories_list(): return sorted([c['name'] for c in db.masters_categories.find({}, {'_id':0, 'name':1})])
def get_processes_list(): return sorted([p['name'] for p in db.masters_processes.find({}, {'_id':0, 'name':1})])
def get_parties_list(): return sorted([p['name'] for p in db.masters_parties.find({}, {'_id':0, 'name':1})])
def get_gst_list(): return sorted([g['rate'] for g in db.masters_gst.find({}, {'_id':0, 'rate':1})])
def get_vendors_list(): return sorted([v['name'] for v in db.masters_vendors.find({}, {'_id':0, 'name':1})])
def get_sources_list(): return sorted([s['name'] for s in db.masters_sources.find({}, {'_id':0, 'name':1})])

def get_rate(item, process):
    res = db.masters_rates.find_one({"item": item, "process": process})
    return float(res['rate']) if res else 0.0

# --- PRODUCT MASTER ---
def generate_id(prefix):
    nums = ''.join(random.choices(string.digits, k=6))
    return f"{prefix}-{nums}"

def save_product_parent(name, gender, category, description):
    if db.masters_products.find_one({"name": name, "gender": gender, "type": "parent"}):
        return False, "Parent Product already exists"
    pid = generate_id("P")
    db.masters_products.insert_one({
        "type": "parent", "system_id": pid, "name": name, 
        "gender": gender, "category": category, "description": description,
        "created_at": datetime.datetime.now()
    })
    return True, "Parent Created"

def save_product_child(parent_sys_id, sku, color, size, rate):
    if db.masters_products.find_one({"sku": sku}):
        return False, f"SKU '{sku}' already exists"
    parent = db.masters_products.find_one({"system_id": parent_sys_id})
    if not parent: return False, "Parent not found"
    cid = generate_id("C")
    db.masters_products.insert_one({
        "type": "child", "system_id": cid, "parent_id": parent_sys_id,
        "parent_name": parent['name'], "parent_category": parent['category'], 
        "parent_gender": parent['gender'],
        "sku": sku, "color": color, "size": size, "rate": float(rate),
        "created_at": datetime.datetime.now()
    })
    return True, "Child Variant Created"

def save_bulk_products(df):
    success_count = 0
    errors = []
    for _, row in df.iterrows():
        try:
            p_type = str(row.get('type', '')).lower().strip()
            if p_type == 'parent':
                status, msg = save_product_parent(str(row.get('name', '')), str(row.get('gender', '')), str(row.get('category', '')), str(row.get('description', '')))
                if status: success_count += 1
                else: errors.append(f"Row {_}: {msg}")
            elif p_type == 'child':
                p_name = str(row.get('parent_name', ''))
                parent = db.masters_products.find_one({"name": p_name, "type": "parent"})
                if parent:
                    sku = f"{parent.get('gender','')}-{row.get('color','')}-{parent.get('category','')}-{row.get('size','')}".replace(" ", "")
                    status, msg = save_product_child(parent['system_id'], sku, str(row.get('color', '')), str(row.get('size', '')), float(row.get('rate', 0)))
                    if status: success_count += 1
                    else: errors.append(f"Row {_}: {msg}")
                else: errors.append(f"Row {_}: Parent '{p_name}' not found")
        except Exception as e: errors.append(f"Row {_}: {str(e)}")
    return success_count, errors

def get_parent_products(): return list(db.masters_products.find({"type": "parent"}))
def get_children_for_parent(parent_sys_id): return list(db.masters_products.find({"parent_id": parent_sys_id}))
def get_all_products_flat(): return list(db.masters_products.find({}))
def get_child_skus_list(): return sorted(db.masters_products.distinct("sku", {"type": "child"}))

# --- MARKETPLACE MAPPING ---
def save_sku_mapping(sparsh_sku, channel, channel_sku):
    key = {"internal_sku": sparsh_sku, "channel": channel}
    db.masters_mappings.update_one(key, {"$set": {"internal_sku": sparsh_sku, "channel": channel, "channel_sku": channel_sku, "updated_at": datetime.datetime.now()}}, upsert=True)
    return True
def get_mappings(sparsh_sku=None):
    q = {}
    if sparsh_sku: q['internal_sku'] = sparsh_sku
    return list(db.masters_mappings.find(q))

# --- LOTS & BUNDLES (NEW LOT MAKER) ---
def get_active_lots(): return sorted(db.masters_lots.distinct("lot_no"))
def get_bundles_for_lot(lot_no): return sorted(db.masters_lots.distinct("bundle_no", {"lot_no": lot_no}))
def get_detailed_bundles(lot_no): return list(db.masters_lots.find({"lot_no": lot_no}, {'_id':0}))
def get_bundle_details(lot_no, bundle_no): return db.masters_lots.find_one({"lot_no": lot_no, "bundle_no": bundle_no}, {'_id':0})

def save_full_lot(header_data, fabric_df, bundle_df):
    """
    Saves the Lot Header to 'transactions_cutting'
    Saves individual bundles to 'masters_lots'
    """
    try:
        # 1. Save Header / Cutting Transaction
        lot_no = header_data['lot_no']
        if db.transactions_cutting.find_one({"lot_no": lot_no}):
            return False, f"Lot No {lot_no} already exists!"
        
        # Prepare Fabric Data
        fabrics = fabric_df.to_dict('records')
        
        # Calculate totals
        total_pcs = bundle_df['Qty'].sum()
        
        header_doc = {
            "lot_no": lot_no,
            "date": pd.to_datetime(header_data['date']),
            "style_sku": header_data['sku'],
            "item_name": header_data['item_name'],
            "category": header_data['category'],
            "fabric_consumption": fabrics,
            "total_pcs": float(total_pcs),
            "created_at": datetime.datetime.now()
        }
        db.transactions_cutting.insert_one(header_doc)
        
        # 2. Save Bundles to Masters Lots
        # Columns in DF: Bundle No, Color, Size, Qty
        bundles = []
        for _, row in bundle_df.iterrows():
            bundles.append({
                "date": pd.to_datetime(header_data['date']),
                "lot_no": lot_no,
                "bundle_no": row['Bundle No'],
                "item_name": header_data['item_name'], # Or SKU? Usually item name for easy reading
                "item_sku": header_data['sku'],
                "color": row['Color'],
                "size": row['Size'],
                "qty": float(row['Qty']),
                "created_at": datetime.datetime.now()
            })
            
        if bundles:
            db.masters_lots.insert_many(bundles)
            
        return True, f"Lot {lot_no} Created with {len(bundles)} Bundles!"
        
    except Exception as e:
        return False, str(e)

def get_bundle_progress(lot_filter=None, bundle_filter=None):
    query = {}
    if lot_filter and lot_filter != "All": query["lot_no"] = lot_filter
    if bundle_filter and bundle_filter != "All": query["bundle_no"] = bundle_filter
    lots = list(db.masters_lots.find(query, {'_id':0}))
    if not lots: return pd.DataFrame()
    pipeline = [{"$sort": {"created_at": 1}}, {"$group": {"_id": {"lot": "$lot_no", "bun": "$bundle_no"}, "last_process": {"$last": "$process"}, "last_qty": {"$last": "$qty"}}}]
    prod_data = list(db.production.aggregate(pipeline))
    status_map = { (p['_id']['lot'], p['_id']['bun']): {'proc': p['last_process'], 'qty': p['last_qty']} for p in prod_data }
    data = []
    for r in lots:
        key = (r.get('lot_no'), r.get('bundle_no'))
        curr_proc = "🆕 Created"
        curr_qty = float(r.get('qty', 0))
        if key in status_map:
            curr_proc = status_map[key]['proc']
            curr_qty = status_map[key]['qty']
        data.append({
            "Lot": r.get('lot_no'), "Bundle": r.get('bundle_no'), "Item": f"{r.get('item_name')} ({r.get('color')}-{r.get('size')})",
            "Current Stage": curr_proc, "Pcs": curr_qty, "Initial Qty": float(r.get('qty', 0))
        })
    return pd.DataFrame(data)

def get_bundle_journey(lot_no, bundle_no):
    master = db.masters_lots.find_one({"lot_no": lot_no, "bundle_no": bundle_no})
    if not master: return [], 0, 0
    created_qty = float(master.get('qty', 0))
    created_date = master.get('date', master.get('created_at'))
    journey = [{"Date": pd.to_datetime(created_date).strftime('%d-%b-%Y'), "Issued To": "System", "Process": "Bundle Created", "Issued Qty": created_qty, "Status": "✅ Generated"}]
    prod_recs = list(db.production.find({"lot_no": lot_no, "bundle_no": bundle_no}).sort("created_at", 1))
    current_handover = created_qty
    for p in prod_recs:
        journey.append({"Date": p['date'].strftime('%d-%b-%Y'), "Issued To": p['staff_name'], "Process": p['process'], "Issued Qty": p['qty'], "Status": "✅ Completed"})
        current_handover = p['qty']
    return journey, created_qty, current_handover

# --- CHAT / SMART EDIT FUNCTIONS ---
def get_last_production(staff_name): return db.production.find_one({"staff_name": staff_name}, sort=[("created_at", -1)])
def get_last_attendance(staff_name):
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return db.attendance.find_one({"staff_name": staff_name, "date": {"$gte": today}})
def delete_record_by_id(collection, record_id):
    try: db[collection].delete_one({"_id": record_id}); return True
    except: return False
def update_production_qty(record_id, new_qty):
    try:
        rec = db.production.find_one({"_id": record_id})
        if rec:
            b_det = db.masters_lots.find_one({"lot_no": rec['lot_no'], "bundle_no": rec['bundle_no']})
            if b_det:
                max_q = float(b_det.get('qty', 0))
                if float(new_qty) > max_q: return False
            new_amount = float(new_qty) * float(rec['rate'])
            db.production.update_one({"_id": record_id}, {"$set": {"qty": float(new_qty), "amount": new_amount}})
            return True
    except: return False
    return False

# --- TRANSACTIONS ---
def get_recent_transactions(collection_name, limit=50):
    data = list(db[collection_name].find().sort("created_at", -1).limit(limit))
    for d in data: d['_id'] = str(d['_id']) 
    return data
def update_transaction(collection_name, doc_id, update_data):
    try: db[collection_name].update_one({"_id": ObjectId(doc_id)}, {"$set": update_data}); return True
    except: return False
def delete_transaction(collection_name, doc_id):
    try: db[collection_name].delete_one({"_id": ObjectId(doc_id)}); return True
    except: return False
def get_recent_purchase_bills(limit=10):
    pipeline = [{"$group": {"_id": {"bill_no": "$bill_no", "vendor": "$vendor", "type": "$type"}, "date": {"$first": "$date"}, "total_amount": {"$sum": "$grand_total"}, "created_at": {"$max": "$created_at"}}}, {"$sort": {"created_at": -1}}, {"$limit": limit}, {"$project": {"bill_no": "$_id.bill_no", "vendor": "$_id.vendor", "type": "$_id.type", "date": 1, "total_amount": 1, "_id": 0}}]
    return pd.DataFrame(list(db.transactions_purchase.aggregate(pipeline)))

# --- FABRICATION ---
def save_fabrication(date, party, item, qty, rate, description):
    total = float(qty) * float(rate)
    db.transactions_fabrication.insert_one({"date": pd.to_datetime(date), "party": party, "item": item, "qty": float(qty), "rate": float(rate), "total_value": total, "description": description, "created_at": datetime.datetime.now()})
    return True
def get_recent_fabrication(limit=20): return pd.DataFrame(list(db.transactions_fabrication.find().sort("created_at", -1).limit(limit)))

# --- LEDGER ---
def get_party_ledger(party_name):
    transactions = []
    sales = list(db.transactions_sales.find({"party": party_name}))
    for s in sales: transactions.append({"date": s['date'], "bill_no": s.get('bill_no', '-'), "description": f"Sale: {s['item']}", "debit": s['grand_total'], "credit": 0.0, "type": "SALE"})
    purchases = list(db.transactions_purchase.find({"vendor": party_name}))
    for p in purchases:
        d_type = "Debit" if p.get('type') == "Purchase Return" else "Credit"
        transactions.append({"date": p['date'], "bill_no": p.get('bill_no','-'), "description": p['item'], "debit": p['grand_total'] if d_type=="Debit" else 0.0, "credit": p['grand_total'] if d_type=="Credit" else 0.0, "type": "PURCHASE"})
    cash = list(db.transactions_cashbook.find({"party": party_name}))
    for c in cash:
        if c['type'] == "IN": transactions.append({"date": c['date'], "bill_no": "-", "description": "Payment In", "debit": 0.0, "credit": c['amount'], "type": "PAY_IN"})
        else: transactions.append({"date": c['date'], "bill_no": "-", "description": "Payment Out", "debit": c['amount'], "credit": 0.0, "type": "PAY_OUT"})
    fab = list(db.transactions_fabrication.find({"party": party_name}))
    for f in fab:
        transactions.append({"date": f['date'], "bill_no": "-", "description": f"Fab: {f['item']} ({f['qty']}@{f['rate']})", "debit": 0.0, "credit": f['total_value'], "type": "FABRICATION"})
    if not transactions: return pd.DataFrame()
    df = pd.DataFrame(transactions)
    df['date'] = pd.to_datetime(df['date'])
    return df.sort_values(by='date')

# --- DASHBOARD & STATS ---
def get_dashboard_stats():
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    month = datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    pcs = list(db.production.aggregate([{"$match": {"date": {"$gte": today}}}, {"$group": {"_id": None, "total": {"$sum": "$qty"}}}]))
    earn = list(db.production.aggregate([{"$match": {"date": {"$gte": today}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
    m_earn_prod = list(db.production.aggregate([{"$match": {"date": {"$gte": month}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
    m_earn_sal = list(db.attendance.aggregate([{"$match": {"date": {"$gte": month}}}, {"$group": {"_id": None, "total": {"$sum": "$daily_earnings"}}}]))
    total_earned = (m_earn_prod[0]['total'] if m_earn_prod else 0) + (m_earn_sal[0]['total'] if m_earn_sal else 0)
    m_paid = list(db.payments.aggregate([{"$match": {"date": {"$gte": month}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
    total_paid = m_paid[0]['total'] if m_paid else 0
    active = len(db.production.distinct("staff_name", {"date": {"$gte": today}}))
    return (pcs[0]['total'] if pcs else 0), (earn[0]['total'] if earn else 0), (total_earned - total_paid), active

def get_staff_current_month_stats(staff_name):
    month = datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    s_det = get_staff_details(staff_name)
    is_sal = s_det.get('salary_type') == 'Salaried' if s_det else False
    if is_sal: e = list(db.attendance.aggregate([{"$match": {"staff_name": staff_name, "date": {"$gte": month}}}, {"$group": {"_id": None, "total": {"$sum": "$daily_earnings"}}}]))
    else: e = list(db.production.aggregate([{"$match": {"staff_name": staff_name, "date": {"$gte": month}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
    p = list(db.payments.aggregate([{"$match": {"staff_name": staff_name, "date": {"$gte": month}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
    _, _, bal, _ = get_worker_history(staff_name)
    return (e[0]['total'] if e else 0), (p[0]['total'] if p else 0), bal

def get_worker_history(staff_name):
    s_det = get_staff_details(staff_name)
    is_sal = s_det.get('salary_type') == 'Salaried' if s_det else False
    if is_sal:
        e = list(db.attendance.aggregate([{"$match": {"staff_name": staff_name}}, {"$group": {"_id": None, "total": {"$sum": "$daily_earnings"}}}]))
        hist = list(db.attendance.find({"staff_name": staff_name}).sort("date", -1))
    else:
        e = list(db.production.aggregate([{"$match": {"staff_name": staff_name}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
        hist = list(db.production.find({"staff_name": staff_name}).sort("date", -1))
    p = list(db.payments.aggregate([{"$match": {"staff_name": staff_name}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
    earned_val = e[0]['total'] if e else 0
    paid_val = p[0]['total'] if p else 0
    return earned_val, paid_val, (earned_val - paid_val), pd.DataFrame(hist)

def get_staff_range_stats(staff_name, start_date, end_date):
    s_date = pd.to_datetime(start_date)
    e_date = pd.to_datetime(end_date) + datetime.timedelta(days=1)
    s_det = get_staff_details(staff_name)
    is_sal = s_det.get('salary_type') == 'Salaried' if s_det else False
    earned, paid = 0.0, 0.0
    if is_sal:
        agg = list(db.attendance.aggregate([{"$match": {"staff_name": staff_name, "date": {"$gte": s_date, "$lt": e_date}}}, {"$group": {"_id": None, "total": {"$sum": "$daily_earnings"}}}]))
        earned = agg[0]['total'] if agg else 0.0
        hist_data = list(db.attendance.find({"staff_name": staff_name, "date": {"$gte": s_date, "$lt": e_date}}).sort("date", -1))
    else:
        agg = list(db.production.aggregate([{"$match": {"staff_name": staff_name, "date": {"$gte": s_date, "$lt": e_date}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
        earned = agg[0]['total'] if agg else 0.0
        hist_data = list(db.production.find({"staff_name": staff_name, "date": {"$gte": s_date, "$lt": e_date}}).sort("date", -1))
    agg_p = list(db.payments.aggregate([{"$match": {"staff_name": staff_name, "date": {"$gte": s_date, "$lt": e_date}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
    paid = agg_p[0]['total'] if agg_p else 0.0
    return earned, paid, pd.DataFrame(hist_data)

def get_attendance_history(staff_name): return pd.DataFrame(list(db.attendance.find({"staff_name": staff_name}).sort("date", -1)))

def get_monthly_summary(staff_name, is_salaried, monthly_salary=0, limit=2):
    summary = []
    curr = datetime.datetime.now()
    for i in range(limit):
        start = (curr - relativedelta(months=i)).replace(day=1, hour=0, minute=0, second=0)
        end = start + relativedelta(months=1)
        p = list(db.payments.aggregate([{"$match": {"staff_name": staff_name, "date": {"$gte": start, "$lt": end}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
        paid = p[0]['total'] if p else 0
        if is_salaried: e = list(db.attendance.aggregate([{"$match": {"staff_name": staff_name, "date": {"$gte": start, "$lt": end}}}, {"$group": {"_id": None, "total": {"$sum": "$daily_earnings"}}}]))
        else: e = list(db.production.aggregate([{"$match": {"staff_name": staff_name, "date": {"$gte": start, "$lt": end}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
        earned = e[0]['total'] if e else 0
        summary.append({"Month": start.strftime("%B %Y"), "Earned": earned, "Paid": paid, "Balance": earned - paid})
    return pd.DataFrame(summary)

# ==========================================
# 2. SAVERS
# ==========================================
def save_master(collection, data):
    key = "rate" if collection == "masters_gst" else "name"
    try: db[collection].update_one({key: data[key]}, {"$set": data}, upsert=True); return True
    except: return False

def save_party(name, type_): db.masters_parties.update_one({"name": name}, {"$set": {"name": name, "type": type_}}, upsert=True)
def save_staff(name, phone, role, salary_type, monthly_salary): db.masters_staff.update_one({"name": name}, {"$set": {"name": name, "phone": phone, "role": role, "salary_type": salary_type, "monthly_salary": monthly_salary}}, upsert=True)
def save_item(name, processes_list): db.masters_items.update_one({"name": name}, {"$set": {"name": name, "processes": processes_list}}, upsert=True)
def save_category(name): db.masters_categories.update_one({"name": name}, {"$set": {"name": name}}, upsert=True)
def save_rate(item, process, rate): db.masters_rates.update_one({"item": item, "process": process}, {"$set": {"rate": float(rate)}}, upsert=True)
def save_payment(date, staff, amount, p_type, remarks): db.payments.insert_one({"date": pd.to_datetime(date), "staff_name": staff, "amount": float(amount), "type": p_type, "remarks": remarks, "created_at": datetime.datetime.now()})

def save_production(date, staff, item, process, qty, rate, lot_no, bundle_no):
    b_det = db.masters_lots.find_one({"lot_no": lot_no, "bundle_no": bundle_no})
    if b_det:
        max_q = float(b_det.get('qty', 0))
        if float(qty) > max_q: return False, f"⚠️ Error: Cannot enter {qty}. Max Bundle Qty is {max_q}."
    total = float(qty) * float(rate)
    db.production.insert_one({"date": pd.to_datetime(date), "staff_name": staff, "item": item, "process": process, "qty": float(qty), "rate": float(rate), "amount": total, "lot_no": lot_no, "bundle_no": bundle_no, "created_at": datetime.datetime.now()})
    return True, "✅ Saved Successfully"

def save_attendance(date_str, staff, status, in_time=None, out_time=None, note=""):
    s_det = get_staff_details(staff)
    m_sal = float(s_det.get('monthly_salary', 0)) if s_det else 0
    daily_rate = m_sal / 30.0 if m_sal else 0.0
    hourly_rate = daily_rate / 10.0
    date_obj = pd.to_datetime(date_str)
    update = {"status": status, "note": note, "updated_at": datetime.datetime.now()}
    if in_time: update["in_time"] = str(in_time)
    if out_time: update["out_time"] = str(out_time)
    if status == "Present" and out_time:
        t_in_str = str(in_time) if in_time else ""
        if not in_time:
             curr = db.attendance.find_one({"date": date_obj, "staff_name": staff})
             t_in_str = curr.get('in_time', '') if curr else ''
        if t_in_str:
            try:
                h, m = map(int, t_in_str.split(':')[:2])
                t1 = datetime.datetime.combine(date_obj, datetime.time(h, m))
                t2 = datetime.datetime.combine(date_obj, out_time)
                hours = round((t2-t1).total_seconds()/3600, 2)
                std = 7.5 if date_obj.weekday() == 6 else 10
                pay = daily_rate * 2 if date_obj.weekday() == 6 else daily_rate
                if hours > std: pay += (hours - std) * hourly_rate
                update["worked_hours"] = hours
                update["daily_earnings"] = round(pay, 2)
            except: pass
    elif status == "Half Day": update["daily_earnings"] = round(daily_rate * 0.5, 2)
    db.attendance.update_one({"date": date_obj, "staff_name": staff}, {"$set": update}, upsert=True)

def save_bulk_lots(df):
    clean = []
    for r in df.to_dict('records'):
        clean.append({"date": pd.to_datetime(r.get('date', datetime.datetime.now())), "lot_no": str(r.get('Lot No', '')), "item_name": str(r.get('Item name', '')), "bundle_no": str(r.get('Bundle no.', '')), "color": str(r.get('Color Name', '')), "size": str(r.get('Size', '')), "qty": float(r.get('Qty', 0)), "created_at": datetime.datetime.now()})
    if clean: db.masters_lots.insert_many(clean); return True
    return False

def save_purchase_invoice(date, vendor, p_type, bill_no, cart_items, global_gst):
    records = []
    for item in cart_items:
        base = float(item['qty']) * float(item['rate'])
        tax = base * (float(global_gst) / 100.0)
        records.append({"date": pd.to_datetime(date), "vendor": vendor, "type": p_type, "item": item['item'], "qty": float(item['qty']), "rate": float(item['rate']), "gst_rate": float(global_gst), "base_amount": base, "tax_amount": tax, "grand_total": base+tax, "bill_no": bill_no, "created_at": datetime.datetime.now()})
    if records: db.transactions_purchase.insert_many(records); return True
    return False

def save_sale_invoice(date, party, bill_no, cart_items, global_gst):
    records = []
    for item in cart_items:
        base = float(item['qty']) * float(item['rate'])
        tax = base * (float(global_gst) / 100.0)
        records.append({"date": pd.to_datetime(date), "party": party, "item": item['item'], "qty": float(item['qty']), "rate": float(item['rate']), "gst_rate": float(global_gst), "base_amount": base, "tax_amount": tax, "grand_total": base+tax, "bill_no": bill_no, "created_at": datetime.datetime.now()})
    if records: db.transactions_sales.insert_many(records); return True
    return False

def save_cash_transaction(date, type_, amount, party, account, remarks):
    db.transactions_cashbook.insert_one({"date": pd.to_datetime(date), "type": type_, "amount": float(amount), "party": party, "account": account, "remarks": remarks, "created_at": datetime.datetime.now()})

def clean_database(selected_collections, start_date=None, end_date=None):
    final_targets = set(selected_collections)
    deleted_summary = {}
    try:
        for col_name in final_targets:
            query = {}
            if start_date and end_date:
                s_date = pd.to_datetime(start_date)
                e_date = pd.to_datetime(end_date) + datetime.timedelta(days=1)
                
                # Collections using 'date' field
                if col_name in ["production", "attendance", "payments", "transactions_cashbook", "transactions_sales", "transactions_purchase", "transactions_fabrication", "masters_lots", "transactions_cutting", "transactions_daily_orders"]:
                     query = {"date": {"$gte": s_date, "$lt": e_date}}
                     if col_name == "transactions_daily_orders": query = {"upload_date": {"$gte": s_date, "$lt": e_date}}
                elif col_name in ["masters_products", "masters_staff", "masters_parties", "masters_items"]:
                     query = {"created_at": {"$gte": s_date, "$lt": e_date}}
                else: continue 
            
            result = db[col_name].delete_many(query)
            if result.deleted_count > 0: deleted_summary[col_name] = result.deleted_count
        
        return True, deleted_summary
    except Exception as e:
        return False, str(e)

def get_df(collection_name): return pd.DataFrame(list(db[collection_name].find({}, {'_id':0})))
def get_rates_df(): return pd.DataFrame(list(db.masters_rates.find({}, {'_id':0})))

import streamlit as st
import pymongo
import pandas as pd
import datetime
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
def get_processes_list(): return sorted([p['name'] for p in db.masters_processes.find({}, {'_id':0, 'name':1})])

def get_parties_list(): return sorted([p['name'] for p in db.masters_parties.find({}, {'_id':0, 'name':1})])
def get_gst_list(): return sorted([g['rate'] for g in db.masters_gst.find({}, {'_id':0, 'rate':1})])
def get_vendors_list(): return sorted([v['name'] for v in db.masters_vendors.find({}, {'_id':0, 'name':1})])
def get_sources_list(): return sorted([s['name'] for s in db.masters_sources.find({}, {'_id':0, 'name':1})])

def get_rate(item, process):
    res = db.masters_rates.find_one({"item": item, "process": process})
    return float(res['rate']) if res else 0.0

# --- LOTS & BUNDLES ---
def get_active_lots(): return sorted(db.masters_lots.distinct("lot_no"))
def get_bundles_for_lot(lot_no): return sorted(db.masters_lots.distinct("bundle_no", {"lot_no": lot_no}))
def get_detailed_bundles(lot_no): return list(db.masters_lots.find({"lot_no": lot_no}, {'_id':0}))
def get_bundle_details(lot_no, bundle_no): return db.masters_lots.find_one({"lot_no": lot_no, "bundle_no": bundle_no}, {'_id':0})

# --- BUNDLE TRACKING (SUMMARY) ---
def get_bundle_progress(lot_filter=None, bundle_filter=None):
    query = {}
    if lot_filter and lot_filter != "All": query["lot_no"] = lot_filter
    if bundle_filter and bundle_filter != "All": query["bundle_no"] = bundle_filter
    lots = list(db.masters_lots.find(query, {'_id':0}))
    if not lots: return pd.DataFrame()
    
    # Get Production Data Summary
    pipeline = [
        {"$sort": {"created_at": 1}},
        {"$group": {"_id": {"lot": "$lot_no", "bun": "$bundle_no"}, "last_process": {"$last": "$process"}, "last_qty": {"$last": "$qty"}}}
    ]
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

# --- BUNDLE JOURNEY (DETAILED) ---
def get_bundle_journey(lot_no, bundle_no):
    # 1. Master Data
    master = db.masters_lots.find_one({"lot_no": lot_no, "bundle_no": bundle_no})
    if not master: return [], 0, 0
    
    created_qty = float(master.get('qty', 0))
    created_date = master.get('date', master.get('created_at'))
    
    # 2. Journey Log
    journey = []
    
    # Step 0: Creation
    journey.append({
        "Date": pd.to_datetime(created_date).strftime('%d-%b-%Y'),
        "Issued To": "System",
        "Process": "Bundle Created",
        "Issued Qty": created_qty,
        "Status": "✅ Generated"
    })
    
    # Step 1...N: Production
    prod_recs = list(db.production.find({"lot_no": lot_no, "bundle_no": bundle_no}).sort("created_at", 1))
    
    current_handover = created_qty
    for p in prod_recs:
        journey.append({
            "Date": p['date'].strftime('%d-%b-%Y'),
            "Issued To": p['staff_name'],
            "Process": p['process'],
            "Issued Qty": p['qty'],
            "Status": "✅ Completed"
        })
        current_handover = p['qty'] # Update to latest
        
    return journey, created_qty, current_handover

# --- CHAT / SMART EDIT FUNCTIONS ---
def get_last_production(staff_name):
    return db.production.find_one({"staff_name": staff_name}, sort=[("created_at", -1)])

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
    db.transactions_fabrication.insert_one({
        "date": pd.to_datetime(date), "party": party, "item": item,
        "qty": float(qty), "rate": float(rate), "total_value": total,
        "description": description, "created_at": datetime.datetime.now()
    })
    return True

def get_recent_fabrication(limit=20):
    data = list(db.transactions_fabrication.find().sort("created_at", -1).limit(limit))
    return pd.DataFrame(data)

# --- LEDGER ---
def get_party_ledger(party_name):
    transactions = []
    # Sales
    sales = list(db.transactions_sales.find({"party": party_name}))
    for s in sales: transactions.append({"date": s['date'], "bill_no": s.get('bill_no', '-'), "description": f"Sale: {s['item']}", "debit": s['grand_total'], "credit": 0.0, "type": "SALE"})
    # Purchases
    purchases = list(db.transactions_purchase.find({"vendor": party_name}))
    for p in purchases:
        d_type = "Debit" if p.get('type') == "Purchase Return" else "Credit"
        transactions.append({"date": p['date'], "bill_no": p.get('bill_no','-'), "description": p['item'], "debit": p['grand_total'] if d_type=="Debit" else 0.0, "credit": p['grand_total'] if d_type=="Credit" else 0.0, "type": "PURCHASE"})
    # Cash
    cash = list(db.transactions_cashbook.find({"party": party_name}))
    for c in cash:
        if c['type'] == "IN": transactions.append({"date": c['date'], "bill_no": "-", "description": "Payment In", "debit": 0.0, "credit": c['amount'], "type": "PAY_IN"})
        else: transactions.append({"date": c['date'], "bill_no": "-", "description": "Payment Out", "debit": c['amount'], "credit": 0.0, "type": "PAY_OUT"})
    # Fabrication
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
    
    if is_sal:
        e = list(db.attendance.aggregate([{"$match": {"staff_name": staff_name, "date": {"$gte": month}}}, {"$group": {"_id": None, "total": {"$sum": "$daily_earnings"}}}]))
    else:
        e = list(db.production.aggregate([{"$match": {"staff_name": staff_name, "date": {"$gte": month}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
    
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
    
    earned = 0.0
    paid = 0.0
    
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

def get_attendance_history(staff_name):
    return pd.DataFrame(list(db.attendance.find({"staff_name": staff_name}).sort("date", -1)))

def get_monthly_summary(staff_name, is_salaried, monthly_salary=0, limit=2):
    summary = []
    curr = datetime.datetime.now()
    for i in range(limit):
        start = (curr - relativedelta(months=i)).replace(day=1, hour=0, minute=0, second=0)
        end = start + relativedelta(months=1)
        p = list(db.payments.aggregate([{"$match": {"staff_name": staff_name, "date": {"$gte": start, "$lt": end}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
        paid = p[0]['total'] if p else 0
        
        if is_salaried:
            e = list(db.attendance.aggregate([{"$match": {"staff_name": staff_name, "date": {"$gte": start, "$lt": end}}}, {"$group": {"_id": None, "total": {"$sum": "$daily_earnings"}}}]))
        else:
            e = list(db.production.aggregate([{"$match": {"staff_name": staff_name, "date": {"$gte": start, "$lt": end}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
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
def save_rate(item, process, rate): db.masters_rates.update_one({"item": item, "process": process}, {"$set": {"rate": float(rate)}}, upsert=True)
def save_payment(date, staff, amount, p_type, remarks): db.payments.insert_one({"date": pd.to_datetime(date), "staff_name": staff, "amount": float(amount), "type": p_type, "remarks": remarks, "created_at": datetime.datetime.now()})
def save_production(date, staff, item, process, qty, rate, lot_no, bundle_no): db.production.insert_one({"date": pd.to_datetime(date), "staff_name": staff, "item": item, "process": process, "qty": float(qty), "rate": float(rate), "amount": float(qty)*float(rate), "lot_no": lot_no, "bundle_no": bundle_no, "created_at": datetime.datetime.now()})

def get_attendance_record(date_str, staff_name): return db.attendance.find_one({"date": pd.to_datetime(date_str), "staff_name": staff_name})

def save_attendance(date_str, staff, status, in_time=None, out_time=None, note=""):
    s_det = get_staff_details(staff)
    m_sal = float(s_det.get('monthly_salary', 0)) if s_det else 0
    daily_rate = m_sal / 30.0 if m_sal else 0.0
    hourly_rate = daily_rate / 10.0
    date_obj = pd.to_datetime(date_str)
    
    update = {"status": status, "note": note, "updated_at": datetime.datetime.now()}
    if in_time: update["in_time"] = str(in_time)
    if out_time: update["out_time"] = str(out_time)
    
    if status == "Present":
        if out_time:
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
    elif status == "Half Day":
        update["daily_earnings"] = round(daily_rate * 0.5, 2)

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

def clean_database(selected_collections):
    final_targets = set(selected_collections)
    if "masters_staff" in final_targets: final_targets.update(["production", "payments", "attendance"])
    try:
        for col in final_targets: db[col].delete_many({})
        return True, list(final_targets)
    except: return False, []

def get_df(collection_name): return pd.DataFrame(list(db[collection_name].find({}, {'_id':0})))
def get_rates_df(): return pd.DataFrame(list(db.masters_rates.find({}, {'_id':0})))

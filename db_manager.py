import streamlit as st
import pymongo
import pandas as pd
import datetime
import random
import string
import math
from bson.objectid import ObjectId

# --- CONNECT TO DATABASE ---
try:
    client = pymongo.MongoClient(st.secrets["MONGO_URI"])
    db = client['shine_arc_new_db']
except Exception as e:
    st.error(f"Database Connection Error: {e}")
    db = None

# ==========================================
# 1. FETCHERS
# ==========================================
def get_staff_list(): return sorted([s['name'] for s in db.masters_staff.find({}, {'_id':0, 'name':1})]) if db is not None else []
def get_items_list(): return sorted([i['name'] for i in db.masters_items.find({}, {'_id':0, 'name':1})]) if db is not None else []
def get_colors_list(): return sorted([c['name'] for c in db.masters_colors.find({}, {'_id':0, 'name':1})]) if db is not None else []
def get_sizes_list(): return sorted([s['name'] for s in db.masters_sizes.find({}, {'_id':0, 'name':1})]) if db is not None else []
def get_categories_list(): return sorted([c['name'] for c in db.masters_categories.find({}, {'_id':0, 'name':1})]) if db is not None else []
def get_processes_list(): return sorted([p['name'] for p in db.masters_processes.find({}, {'_id':0, 'name':1})]) if db is not None else []
def get_parties_list(): return sorted([p['name'] for p in db.masters_parties.find({}, {'_id':0, 'name':1})]) if db is not None else []

def get_staff_details(name):
    if db is None: return {}
    return db.masters_staff.find_one({"name": name})

def get_rate(item, process):
    if db is None: return 0.0
    res = db.masters_rates.find_one({"item": item, "process": process})
    return float(res['rate']) if res else 0.0

def get_child_skus_list(): return sorted(db.masters_products.distinct("sku", {"type": "child"})) if db is not None else []
def get_parent_products(): return list(db.masters_products.find({"type": "parent"})) if db is not None else []
def get_all_products_flat(): return list(db.masters_products.find({})) if db is not None else []
def get_mappings(): return list(db.masters_mappings.find({})) if db is not None else []

# --- DASHBOARD STATS ---
def get_dashboard_stats():
    if db is None: return 0, 0, 0, 0
    try:
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        month = datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        pcs_agg = list(db.production.aggregate([{"$match": {"date": {"$gte": today}}}, {"$group": {"_id": None, "total": {"$sum": "$qty"}}}]))
        pcs = pcs_agg[0]['total'] if pcs_agg else 0
        
        earn_agg = list(db.production.aggregate([{"$match": {"date": {"$gte": today}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
        earn = earn_agg[0]['total'] if earn_agg else 0
        
        # Monthly Stats
        m_prod = list(db.production.aggregate([{"$match": {"date": {"$gte": month}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
        m_sal = list(db.attendance.aggregate([{"$match": {"date": {"$gte": month}}}, {"$group": {"_id": None, "total": {"$sum": "$daily_earnings"}}}]))
        total_earned = (m_prod[0]['total'] if m_prod else 0) + (m_sal[0]['total'] if m_sal else 0)
        
        m_paid = list(db.payments.aggregate([{"$match": {"date": {"$gte": month}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
        total_paid = m_paid[0]['total'] if m_paid else 0
        
        active = len(db.production.distinct("staff_name", {"date": {"$gte": today}}))
        return pcs, earn, (total_earned - total_paid), active
    except: return 0, 0, 0, 0

# --- STAFF BALANCE SUMMARY & HISTORY (FIXED) ---
def get_worker_history(staff_name):
    """Returns: earned, paid, balance, history_df"""
    if db is None: return 0.0, 0.0, 0.0, pd.DataFrame()
    
    s_det = get_staff_details(staff_name)
    is_sal = s_det.get('salary_type') == 'Salaried' if s_det else False
    
    if is_sal:
        e = list(db.attendance.aggregate([{"$match": {"staff_name": staff_name}}, {"$group": {"_id": None, "total": {"$sum": "$daily_earnings"}}}]))
        hist = list(db.attendance.find({"staff_name": staff_name}).sort("date", -1))
    else:
        e = list(db.production.aggregate([{"$match": {"staff_name": staff_name}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
        hist = list(db.production.find({"staff_name": staff_name}).sort("date", -1))
        
    p = list(db.payments.aggregate([{"$match": {"staff_name": staff_name}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
    
    earned_val = e[0]['total'] if e else 0.0
    paid_val = p[0]['total'] if p else 0.0
    return earned_val, paid_val, (earned_val - paid_val), pd.DataFrame(hist)

def get_all_staff_balances():
    if db is None: return pd.DataFrame()
    
    # 1. Production
    prod_map = {i['_id']: i['t'] for i in db.production.aggregate([{"$group": {"_id": "$staff_name", "t": {"$sum": "$amount"}}}])}
    # 2. Attendance
    att_map = {i['_id']: i['t'] for i in db.attendance.aggregate([{"$group": {"_id": "$staff_name", "t": {"$sum": "$daily_earnings"}}}])}
    # 3. Payments
    pay_map = {i['_id']: i['t'] for i in db.payments.aggregate([{"$group": {"_id": "$staff_name", "t": {"$sum": "$amount"}}}])}
    
    data = []
    for s in get_staff_list():
        earned = prod_map.get(s, 0.0) + att_map.get(s, 0.0)
        paid = pay_map.get(s, 0.0)
        data.append({"Staff Name": s, "Total Earned": earned, "Total Paid": paid, "Net Payable": earned - paid})
    return pd.DataFrame(data)

# --- DRENCH AI ---
def save_daily_orders(df):
    if db is None: return False, "DB Error"
    records = []
    batch = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    df.columns = [c.strip().title() for c in df.columns]
    req = {'Channel', 'Item', 'Category', 'Color', 'Size', 'Qty'}
    if not req.issubset(df.columns): return False, f"Missing: {req}"
    for _, r in df.iterrows():
        records.append({"upload_id": batch, "upload_date": datetime.datetime.now(), "channel": str(r['Channel']), "item": str(r['Item']), "category": str(r['Category']), "color": str(r['Color']), "size": str(r['Size']), "qty": float(r['Qty'])})
    db.transactions_daily_orders.insert_many(records)
    return True, f"Uploaded {len(records)} orders."

def get_daily_orders_df(filters=None):
    if db is None: return pd.DataFrame()
    q = {}
    if filters:
        if filters.get('item'): q['item'] = {"$in": filters['item']}
        if filters.get('color'): q['color'] = {"$in": filters['color']}
    return pd.DataFrame(list(db.transactions_daily_orders.find(q, {'_id':0}).sort("upload_date", -1)))

def generate_cutting_plan(start, end):
    if db is None: return pd.DataFrame()
    s = pd.to_datetime(start); e = pd.to_datetime(end) + datetime.timedelta(days=1)
    res = list(db.transactions_daily_orders.aggregate([
        {"$match": {"upload_date": {"$gte": s, "$lt": e}}},
        {"$group": {"_id": {"item": "$item", "color": "$color", "size": "$size"}, "qty": {"$sum": "$qty"}}}
    ]))
    if not res: return pd.DataFrame()
    df = pd.DataFrame([{"Item": r['_id']['item'], "Color": r['_id']['color'], "Size": r['_id']['size'], "Qty": r['qty']} for r in res])
    pivot = df.pivot_table(index=['Item', 'Color'], columns='Size', values='Qty', aggfunc='sum', fill_value=0)
    pivot['Total'] = pivot.sum(axis=1)
    return pivot.reset_index()

# --- PRODUCT MASTER ---
def generate_id(prefix): return f"{prefix}-{''.join(random.choices(string.digits, k=6))}"
def save_product_parent(n, g, c, d):
    if db.masters_products.find_one({"name": n, "gender": g, "type": "parent"}): return False, "Exists"
    db.masters_products.insert_one({"type": "parent", "system_id": generate_id("P"), "name": n, "gender": g, "category": c, "description": d, "created_at": datetime.datetime.now()})
    return True, "Created"
def save_product_child(pid, sku, c, s, r):
    if db.masters_products.find_one({"sku": sku}): return False, "SKU Exists"
    p = db.masters_products.find_one({"system_id": pid})
    db.masters_products.insert_one({"type": "child", "system_id": generate_id("C"), "parent_id": pid, "parent_name": p['name'], "parent_category": p['category'], "parent_gender": p['gender'], "sku": sku, "color": c, "size": s, "rate": float(r), "created_at": datetime.datetime.now()})
    return True, "Created"

def save_bulk_products(df):
    c = 0; err = []
    for _, r in df.iterrows():
        try:
            if r.get('type') == 'parent':
                s, m = save_product_parent(r.get('name'), r.get('gender'), r.get('category'), r.get('description'))
                if s: c+=1
            elif r.get('type') == 'child':
                p = db.masters_products.find_one({"name": r.get('parent_name'), "type": "parent"})
                if p:
                    sku = f"{p.get('gender')}-{r.get('color')}-{p.get('category')}-{r.get('size')}".replace(" ", "")
                    save_product_child(p['system_id'], sku, r.get('color'), r.get('size'), r.get('rate'))
                    c+=1
        except: pass
    return c, err

def save_sku_mapping(i, c, k): db.masters_mappings.update_one({"internal_sku": i, "channel": c}, {"$set": {"channel_sku": k, "updated_at": datetime.datetime.now()}}, upsert=True)

# --- LOTS & CUTTING ---
def get_active_lots(): return sorted(db.masters_lots.distinct("lot_no")) if db is not None else []
def get_detailed_bundles(lot): return list(db.masters_lots.find({"lot_no": lot}, {'_id':0})) if db is not None else []
def get_bundle_details(lot, bun): return db.masters_lots.find_one({"lot_no": lot, "bundle_no": bun}, {'_id':0}) if db is not None else None

def save_full_lot(header, fabric_df, bundle_df):
    if db is None: return False, "DB Error"
    if db.transactions_cutting.find_one({"lot_no": header['lot_no']}): return False, "Lot Exists"
    
    db.transactions_cutting.insert_one({
        **header, "fabric_consumption": fabric_df.to_dict('records'), 
        "total_pcs": float(bundle_df['Qty'].sum()), "created_at": datetime.datetime.now()
    })
    
    bundles = []
    for _, r in bundle_df.iterrows():
        bundles.append({
            "date": pd.to_datetime(header['date']), "lot_no": header['lot_no'],
            "bundle_no": r['Bundle No'], "item_name": header['item_name'], "item_sku": header['sku'],
            "color": r['Color'], "size": r['Size'], "qty": float(r['Qty']), "created_at": datetime.datetime.now()
        })
    if bundles: db.masters_lots.insert_many(bundles)
    return True, "Lot Saved Successfully"

def get_bundle_progress(lot=None, bun=None):
    if db is None: return pd.DataFrame()
    q = {}
    if lot and lot != "All": q["lot_no"] = lot
    if bun and bun != "All": q["bundle_no"] = bun
    lots = list(db.masters_lots.find(q, {'_id':0}))
    if not lots: return pd.DataFrame()
    
    pipeline = [{"$group": {"_id": {"lot": "$lot_no", "bun": "$bundle_no"}, "proc": {"$last": "$process"}, "qty": {"$last": "$qty"}}}]
    prod_map = { (p['_id']['lot'], p['_id']['bun']): p for p in list(db.production.aggregate(pipeline)) }
    
    data = []
    for r in lots:
        k = (r.get('lot_no'), r.get('bundle_no'))
        info = prod_map.get(k, {})
        data.append({
            "Lot": r.get('lot_no'), "Bundle": r.get('bundle_no'), "Item": f"{r.get('item_name')} ({r.get('color')}-{r.get('size')})",
            "Current Stage": info.get('proc', '🆕 Created'), "Pcs": info.get('qty', r.get('qty'))
        })
    return pd.DataFrame(data)

def get_bundle_journey(lot, bun):
    if db is None: return [], 0, 0
    created = db.masters_lots.find_one({"lot_no": lot, "bundle_no": bun})
    if not created: return [], 0, 0
    qty = float(created.get('qty', 0))
    journey = [{"Date": pd.to_datetime(created.get('date')).strftime('%d-%b'), "Process": "Created", "Worker": "System", "Qty": qty}]
    prods = list(db.production.find({"lot_no": lot, "bundle_no": bun}).sort("created_at", 1))
    for p in prods:
        journey.append({"Date": p['date'].strftime('%d-%b'), "Process": p['process'], "Worker": p['staff_name'], "Qty": p['qty']})
    return journey, qty, (prods[-1]['qty'] if prods else qty)

# --- PRODUCTION / MASTERS ---
def save_production(d, s, i, p, q, r, l, b):
    if db is None: return False, "DB Error"
    db.production.insert_one({"date": pd.to_datetime(d), "staff_name": s, "item": i, "process": p, "qty": q, "rate": r, "amount": q*r, "lot_no": l, "bundle_no": b, "created_at": datetime.datetime.now()})
    return True, "Entry Saved & Payment Updated"

def save_attendance(d, s, st, ti=None, to=None): db.attendance.update_one({"date": pd.to_datetime(d), "staff_name": s}, {"$set": {"status": st, "in_time": str(ti), "out_time": str(to)}}, upsert=True)
def get_attendance_record(d, s): return db.attendance.find_one({"date": pd.to_datetime(d), "staff_name": s})

def save_staff(n, p, r, st, ms): db.masters_staff.update_one({"name": n}, {"$set": {"name":n, "phone":p, "role":r, "salary_type":st, "monthly_salary":ms}}, upsert=True)
def save_party(n, t): db.masters_parties.update_one({"name": n}, {"$set": {"name":n, "type":t}}, upsert=True)
def save_item(n, p): db.masters_items.update_one({"name": n}, {"$set": {"name":n, "processes":p}}, upsert=True)
def save_category(n): db.masters_categories.update_one({"name": n}, {"$set": {"name": n}}, upsert=True)
def save_rate(i, p, r): db.masters_rates.update_one({"item": i, "process": p}, {"$set": {"rate": float(r)}}, upsert=True)
def save_master(col, data): db[col].update_one({"name": data.get("name") or data.get("rate")}, {"$set": data}, upsert=True)
def save_payment(d, s, a, t, r): db.payments.insert_one({"date": pd.to_datetime(d), "staff_name": s, "amount": float(a), "type": t, "remarks": r, "created_at": datetime.datetime.now()})
def save_cash_transaction(d, t, a, p, ac, r): db.transactions_cashbook.insert_one({"date": pd.to_datetime(d), "type": t, "amount": float(a), "party": p, "account": ac, "remarks": r, "created_at": datetime.datetime.now()})
def save_fabrication(d, p, i, q, r, ds): db.transactions_fabrication.insert_one({"date": pd.to_datetime(d), "party": p, "item": i, "qty": q, "rate": r, "description": ds, "created_at": datetime.datetime.now()})

def clean_database(cols, s_date=None, e_date=None):
    if not db: return False, "DB Error"
    res = {}
    for c in cols:
        q = {}
        if s_date and e_date:
            sd = pd.to_datetime(s_date); ed = pd.to_datetime(e_date) + datetime.timedelta(days=1)
            date_field = "created_at" if "masters" in c else "date"
            if c == "transactions_daily_orders": date_field = "upload_date"
            q[date_field] = {"$gte": sd, "$lt": ed}
        r = db[c].delete_many(q)
        if r.deleted_count > 0: res[c] = r.deleted_count
    return True, res

def get_df(col): return pd.DataFrame(list(db[col].find({}, {'_id':0}))) if db is not None else pd.DataFrame()
def get_rates_df(): return pd.DataFrame(list(db.masters_rates.find({}, {'_id':0}))) if db is not None else pd.DataFrame()
def get_recent_fabrication(): return get_df("transactions_fabrication")
def get_party_ledger(party):
    recs = []
    for x in db.transactions_sales.find({"party": party}): recs.append({"date": x['date'], "desc": "Sale", "debit": x['grand_total'], "credit": 0})
    for x in db.transactions_purchase.find({"vendor": party}): recs.append({"date": x['date'], "desc": "Purchase", "debit": 0, "credit": x['grand_total']})
    for x in db.transactions_cashbook.find({"party": party}): 
        if x['type'] == "IN": recs.append({"date": x['date'], "desc": "Payment In", "debit": 0, "credit": x['amount']})
        else: recs.append({"date": x['date'], "desc": "Payment Out", "debit": x['amount'], "credit": 0})
    return pd.DataFrame(recs)
def save_purchase_invoice(d, v, t, b, items, gst): db.transactions_purchase.insert_many([{"date": pd.to_datetime(d), "vendor": v, "type": t, "bill_no": b, "item": i['item'], "qty": i['qty'], "rate": i['rate'], "grand_total": i['qty']*i['rate']*(1+gst/100), "created_at": datetime.datetime.now()} for i in items])
def save_sale_invoice(d, p, b, items, gst): db.transactions_sales.insert_many([{"date": pd.to_datetime(d), "party": p, "bill_no": b, "item": i['item'], "qty": i['qty'], "rate": i['rate'], "grand_total": i['qty']*i['rate']*(1+gst/100), "created_at": datetime.datetime.now()} for i in items])
def get_recent_transactions(col): return list(db[col].find().sort("created_at", -1).limit(50))
def delete_transaction(col, _id): db[col].delete_one({"_id": ObjectId(_id)})

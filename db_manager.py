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

# ==========================================
# 1. FETCHERS & CALCULATIONS
# ==========================================
def get_staff_list(): return sorted([s['name'] for s in db.masters_staff.find({}, {'_id':0, 'name':1})])
def get_items_list(): return sorted([i['name'] for i in db.masters_items.find({}, {'_id':0, 'name':1})])
def get_colors_list(): return sorted([c['name'] for c in db.masters_colors.find({}, {'_id':0, 'name':1})])
def get_sizes_list(): return sorted([s['name'] for s in db.masters_sizes.find({}, {'_id':0, 'name':1})])
def get_categories_list(): return sorted([c['name'] for c in db.masters_categories.find({}, {'_id':0, 'name':1})])
def get_processes_list(): return sorted([p['name'] for p in db.masters_processes.find({}, {'_id':0, 'name':1})])
def get_parties_list(): return sorted([p['name'] for p in db.masters_parties.find({}, {'_id':0, 'name':1})])

def get_rate(item, process):
    res = db.masters_rates.find_one({"item": item, "process": process})
    return float(res['rate']) if res else 0.0

def get_child_skus_list(): return sorted(db.masters_products.distinct("sku", {"type": "child"}))
def get_parent_products(): return list(db.masters_products.find({"type": "parent"}))
def get_all_products_flat(): return list(db.masters_products.find({}))
def get_mappings(): return list(db.masters_mappings.find({}))

# --- STAFF BALANCE SUMMARY (NEW) ---
def get_all_staff_balances():
    """
    Aggregates Earnings (Production + Attendance) vs Payments (Salary + Advance)
    Returns a DataFrame for the Payment Tab.
    """
    # 1. Production Earnings
    prod_agg = list(db.production.aggregate([
        {"$group": {"_id": "$staff_name", "prod_total": {"$sum": "$amount"}}}
    ]))
    prod_map = {i['_id']: i['prod_total'] for i in prod_agg}
    
    # 2. Attendance Earnings (For Salaried)
    att_agg = list(db.attendance.aggregate([
        {"$group": {"_id": "$staff_name", "att_total": {"$sum": "$daily_earnings"}}}
    ]))
    att_map = {i['_id']: i['att_total'] for i in att_agg}
    
    # 3. Payments Made
    pay_agg = list(db.payments.aggregate([
        {"$group": {"_id": "$staff_name", "pay_total": {"$sum": "$amount"}}}
    ]))
    pay_map = {i['_id']: i['pay_total'] for i in pay_agg}
    
    # 4. Combine
    all_staff = get_staff_list()
    data = []
    for s in all_staff:
        earned = prod_map.get(s, 0.0) + att_map.get(s, 0.0)
        paid = pay_map.get(s, 0.0)
        bal = earned - paid
        data.append({
            "Staff Name": s,
            "Total Earned": earned,
            "Total Paid/Adv": paid,
            "Net Balance": bal
        })
    
    return pd.DataFrame(data)

# --- DRENCH AI (ORDERS) ---
def save_daily_orders(df):
    records = []
    batch_date = datetime.datetime.now().replace(microsecond=0)
    upload_batch_id = batch_date.strftime("%Y%m%d%H%M%S")
    
    df.columns = [c.strip().title() for c in df.columns]
    required_cols = {'Channel', 'Item', 'Category', 'Color', 'Size', 'Qty'}
    if not required_cols.issubset(df.columns): return False, f"Missing columns. Required: {required_cols}"
        
    for _, row in df.iterrows():
        records.append({
            "upload_id": upload_batch_id, "upload_date": batch_date,
            "channel": str(row['Channel']), "item": str(row['Item']),
            "category": str(row['Category']), "color": str(row['Color']),
            "size": str(row['Size']), "qty": float(row['Qty'])
        })
    if records:
        db.transactions_daily_orders.insert_many(records)
        return True, f"Uploaded {len(records)} orders."
    return False, "No data."

def get_daily_orders_df(filters=None):
    query = {}
    if filters:
        if filters.get('item'): query['item'] = {"$in": filters['item']}
        if filters.get('color'): query['color'] = {"$in": filters['color']}
    data = list(db.transactions_daily_orders.find(query, {'_id':0}).sort("upload_date", -1))
    return pd.DataFrame(data)

def generate_cutting_plan(start_date, end_date):
    s_date = pd.to_datetime(start_date)
    e_date = pd.to_datetime(end_date) + datetime.timedelta(days=1)
    pipeline = [
        {"$match": {"upload_date": {"$gte": s_date, "$lt": e_date}}},
        {"$group": {
            "_id": {
                "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$upload_date"}},
                "item": "$item", "color": "$color", "size": "$size"
            },
            "qty": {"$sum": "$qty"}
        }}
    ]
    data = list(db.transactions_daily_orders.aggregate(pipeline))
    if not data: return pd.DataFrame()
    
    flat = []
    for d in data:
        flat.append({"Date": d['_id']['date'], "Item": d['_id']['item'], "Color": d['_id']['color'], "Size": d['_id']['size'], "Qty": d['qty']})
    
    df = pd.DataFrame(flat)
    pivot = df.pivot_table(index=['Date', 'Item', 'Color'], columns='Size', values='Qty', aggfunc='sum', fill_value=0)
    pivot['Total Pcs'] = pivot.sum(axis=1)
    return pivot.reset_index()

# --- PRODUCT MASTER ---
def generate_id(prefix): return f"{prefix}-{''.join(random.choices(string.digits, k=6))}"

def save_product_parent(name, gender, category, description):
    if db.masters_products.find_one({"name": name, "gender": gender, "type": "parent"}): return False, "Exists"
    db.masters_products.insert_one({"type": "parent", "system_id": generate_id("P"), "name": name, "gender": gender, "category": category, "description": description, "created_at": datetime.datetime.now()})
    return True, "Created"

def save_product_child(parent_sys_id, sku, color, size, rate):
    if db.masters_products.find_one({"sku": sku}): return False, "SKU Exists"
    parent = db.masters_products.find_one({"system_id": parent_sys_id})
    if not parent: return False, "Parent not found"
    db.masters_products.insert_one({"type": "child", "system_id": generate_id("C"), "parent_id": parent_sys_id, "parent_name": parent['name'], "parent_category": parent['category'], "parent_gender": parent['gender'], "sku": sku, "color": color, "size": size, "rate": float(rate), "created_at": datetime.datetime.now()})
    return True, "Created"

def save_bulk_products(df):
    c = 0; err = []
    for _, r in df.iterrows():
        try:
            if r.get('type') == 'parent':
                s, m = save_product_parent(r.get('name'), r.get('gender'), r.get('category'), r.get('description'))
                if s: c+=1
                else: err.append(m)
            elif r.get('type') == 'child':
                p = db.masters_products.find_one({"name": r.get('parent_name'), "type": "parent"})
                if p:
                    sku = f"{p.get('gender')}-{r.get('color')}-{p.get('category')}-{r.get('size')}".replace(" ", "")
                    s, m = save_product_child(p['system_id'], sku, r.get('color'), r.get('size'), r.get('rate'))
                    if s: c+=1
                    else: err.append(m)
        except Exception as e: err.append(str(e))
    return c, err

def save_sku_mapping(int_sku, ch, ch_sku):
    db.masters_mappings.update_one({"internal_sku": int_sku, "channel": ch}, {"$set": {"channel_sku": ch_sku, "updated_at": datetime.datetime.now()}}, upsert=True)
    return True

# --- LOTS (UPDATED FOR PDF LOGIC) ---
def get_active_lots(): return sorted(db.masters_lots.distinct("lot_no"))
def get_detailed_bundles(lot_no): return list(db.masters_lots.find({"lot_no": lot_no}, {'_id':0}))
def get_bundle_details(lot_no, bundle_no): return db.masters_lots.find_one({"lot_no": lot_no, "bundle_no": bundle_no}, {'_id':0})

def save_full_lot(header_data, fabric_df, bundle_df):
    try:
        lot_no = header_data['lot_no']
        if db.transactions_cutting.find_one({"lot_no": lot_no}): return False, f"Lot {lot_no} exists!"
        
        # Save Header
        fabrics = fabric_df.to_dict('records')
        total_pcs = bundle_df['Qty'].sum()
        db.transactions_cutting.insert_one({
            "lot_no": lot_no, "date": pd.to_datetime(header_data['date']),
            "sku": header_data['sku'], "item_name": header_data['item_name'], "category": header_data['category'],
            "fabric_consumption": fabrics, "total_pcs": float(total_pcs), 
            "cutter": header_data.get('cutter'), "supervisor": header_data.get('supervisor'),
            "created_at": datetime.datetime.now()
        })
        
        # Save Bundles
        bundles = []
        for _, row in bundle_df.iterrows():
            bundles.append({
                "date": pd.to_datetime(header_data['date']), "lot_no": lot_no,
                "bundle_no": row['Bundle No'], "item_name": header_data['item_name'], "item_sku": header_data['sku'],
                "color": row['Color'], "size": row['Size'], "qty": float(row['Qty']),
                "created_at": datetime.datetime.now()
            })
        if bundles: db.masters_lots.insert_many(bundles)
        return True, f"Lot {lot_no} Generated!"
    except Exception as e: return False, str(e)

def get_bundle_progress(lot=None, bun=None):
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
    created = db.masters_lots.find_one({"lot_no": lot, "bundle_no": bun})
    if not created: return [], 0, 0
    qty = float(created.get('qty', 0))
    journey = [{"Date": pd.to_datetime(created.get('date')).strftime('%d-%b'), "Process": "Created", "Worker": "System", "Qty": qty}]
    prods = list(db.production.find({"lot_no": lot, "bundle_no": bun}).sort("created_at", 1))
    for p in prods:
        journey.append({"Date": p['date'].strftime('%d-%b'), "Process": p['process'], "Worker": p['staff_name'], "Qty": p['qty']})
    return journey, qty, (prods[-1]['qty'] if prods else qty)

# --- PRODUCTION & ATTENDANCE ---
def save_production(date, staff, item, process, qty, rate, lot, bun):
    total = float(qty) * float(rate)
    db.production.insert_one({
        "date": pd.to_datetime(date), "staff_name": staff, "item": item, "process": process,
        "qty": float(qty), "rate": float(rate), "amount": total, "lot_no": lot, "bundle_no": bun,
        "created_at": datetime.datetime.now()
    })
    return True, "Saved"

def save_attendance(date, staff, status, t_in=None, t_out=None):
    upd = {"status": status, "updated_at": datetime.datetime.now()}
    if t_in: upd["in_time"] = str(t_in)
    if t_out: upd["out_time"] = str(t_out)
    if status=="Present" and t_out:
        # Simple hours calc could go here
        pass
    db.attendance.update_one({"date": pd.to_datetime(date), "staff_name": staff}, {"$set": upd}, upsert=True)

def get_attendance_record(date, staff):
    return db.attendance.find_one({"date": pd.to_datetime(date), "staff_name": staff})

# --- MASTERS GENERIC ---
def save_master(col, data): db[col].update_one({"name": data.get("name") or data.get("rate")}, {"$set": data}, upsert=True)
def save_staff(n, p, r, st, ms): db.masters_staff.update_one({"name": n}, {"$set": {"name":n, "phone":p, "role":r, "salary_type":st, "monthly_salary":ms}}, upsert=True)
def save_party(n, t): db.masters_parties.update_one({"name": n}, {"$set": {"name":n, "type":t}}, upsert=True)
def save_item(n, p): db.masters_items.update_one({"name": n}, {"$set": {"name":n, "processes":p}}, upsert=True)
def save_rate(i, p, r): db.masters_rates.update_one({"item": i, "process": p}, {"$set": {"rate": float(r)}}, upsert=True)
def save_payment(d, s, a, t, r): db.payments.insert_one({"date": pd.to_datetime(d), "staff_name": s, "amount": float(a), "type": t, "remarks": r, "created_at": datetime.datetime.now()})
def save_cash_transaction(d, t, a, p, ac, r): db.transactions_cashbook.insert_one({"date": pd.to_datetime(d), "type": t, "amount": float(a), "party": p, "account": ac, "remarks": r, "created_at": datetime.datetime.now()})
def save_fabrication(d, p, i, q, r, ds): db.transactions_fabrication.insert_one({"date": pd.to_datetime(d), "party": p, "item": i, "qty": q, "rate": r, "description": ds, "created_at": datetime.datetime.now()})

def clean_database(cols, s_date=None, e_date=None):
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

def get_recent_transactions(col, limit=50): 
    res = list(db[col].find().sort("created_at", -1).limit(limit))
    for r in res: r['_id'] = str(r['_id'])
    return res

def delete_transaction(col, _id):
    db[col].delete_one({"_id": ObjectId(_id)})
    return True

def get_df(col): return pd.DataFrame(list(db[col].find({}, {'_id':0})))
def get_rates_df(): return pd.DataFrame(list(db.masters_rates.find({}, {'_id':0})))
def get_recent_fabrication(): return get_df("transactions_fabrication")
def get_party_ledger(party):
    # Simplified ledger for speed
    recs = []
    for x in db.transactions_sales.find({"party": party}): recs.append({"date": x['date'], "desc": "Sale", "debit": x['grand_total'], "credit": 0})
    for x in db.transactions_purchase.find({"vendor": party}): recs.append({"date": x['date'], "desc": "Purchase", "debit": 0, "credit": x['grand_total']})
    for x in db.transactions_cashbook.find({"party": party}): 
        if x['type'] == "IN": recs.append({"date": x['date'], "desc": "Payment In", "debit": 0, "credit": x['amount']})
        else: recs.append({"date": x['date'], "desc": "Payment Out", "debit": x['amount'], "credit": 0})
    return pd.DataFrame(recs)
def save_purchase_invoice(d, v, t, b, items, gst): db.transactions_purchase.insert_many([{"date": pd.to_datetime(d), "vendor": v, "type": t, "bill_no": b, "item": i['item'], "qty": i['qty'], "rate": i['rate'], "grand_total": i['qty']*i['rate']*(1+gst/100), "created_at": datetime.datetime.now()} for i in items])
def save_sale_invoice(d, p, b, items, gst): db.transactions_sales.insert_many([{"date": pd.to_datetime(d), "party": p, "bill_no": b, "item": i['item'], "qty": i['qty'], "rate": i['rate'], "grand_total": i['qty']*i['rate']*(1+gst/100), "created_at": datetime.datetime.now()} for i in items])

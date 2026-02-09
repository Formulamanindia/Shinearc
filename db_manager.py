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

def save_product_parent(name, sku, category, description):
    if db.masters_products.find_one({"sku": sku, "type": "parent"}):
        return False, "Parent SKU already exists"
    
    pid = generate_id("P")
    db.masters_products.insert_one({
        "type": "parent", "system_id": pid, "name": name, 
        "sku": sku, "category": category, "description": description,
        "created_at": datetime.datetime.now()
    })
    return True, "Parent Created"

def save_product_child(parent_sys_id, sku, color, size, rate):
    if db.masters_products.find_one({"sku": sku}):
        return False, "SKU already exists"
    
    parent = db.masters_products.find_one({"system_id": parent_sys_id})
    if not parent: return False, "Parent not found"

    cid = generate_id("C")
    db.masters_products.insert_one({
        "type": "child", "system_id": cid, "parent_id": parent_sys_id,
        "parent_name": parent['name'], "parent_sku": parent['sku'],
        "sku": sku, "color": color, "size": size, "rate": float(rate),
        "created_at": datetime.datetime.now()
    })
    return True, "Child Variant Created"

def save_bulk_products(df):
    """
    Expects DataFrame cols: type, name, sku, category, description, color, size, rate, parent_sku
    """
    success_count = 0
    errors = []
    
    for _, row in df.iterrows():
        try:
            p_type = str(row.get('type', '')).lower().strip()
            
            if p_type == 'parent':
                # Create Parent
                status, msg = save_product_parent(
                    str(row.get('name', '')), str(row.get('sku', '')), 
                    str(row.get('category', '')), str(row.get('description', ''))
                )
                if status: success_count += 1
                else: errors.append(f"Row {_}: {msg}")
                
            elif p_type == 'child':
                # Create Child
                p_sku = str(row.get('parent_sku', ''))
                # Find parent ID by SKU
                parent = db.masters_products.find_one({"sku": p_sku, "type": "parent"})
                if parent:
                    status, msg = save_product_child(
                        parent['system_id'], str(row.get('sku', '')), 
                        str(row.get('color', '')), str(row.get('size', '')), 
                        float(row.get('rate', 0))
                    )
                    if status: success_count += 1
                    else: errors.append(f"Row {_}: {msg}")
                else:
                    errors.append(f"Row {_}: Parent SKU '{p_sku}' not found")
        except Exception as e:
            errors.append(f"Row {_}: {str(e)}")
            
    return success_count, errors

def get_parent_products():
    return list(db.masters_products.find({"type": "parent"}))

def get_children_for_parent(parent_sys_id):
    return list(db.masters_products.find({"parent_id": parent_sys_id}))

def get_all_products_flat():
    return list(db.masters_products.find({}))

def get_child_skus_list():
    return sorted(db.masters_products.distinct("sku", {"type": "child"}))

# --- MARKETPLACE MAPPING ---
def save_sku_mapping(sparsh_sku, channel, channel_sku):
    key = {"internal_sku": sparsh_sku, "channel": channel}
    db.masters_mappings.update_one(key, {"$set": {
        "internal_sku": sparsh_sku, "channel": channel, 
        "channel_sku": channel_sku, "updated_at": datetime.datetime.now()
    }}, upsert=True)
    return True

def get_mappings(sparsh_sku=None):
    q = {}
    if sparsh_sku: q['internal_sku'] = sparsh_sku
    return list(db.masters_mappings.find(q))

# --- LOTS & BUNDLES ---
def get_active_lots(): return sorted(db.masters_lots.distinct("lot_no"))
def get_bundles_for_lot(lot_no): return sorted(db.masters_lots.distinct("bundle_no", {"lot_no": lot_no}))
def get_detailed_bundles(lot_no): return list(db.masters_lots.find({"lot_no": lot_no}, {'_id':0}))
def get_bundle_details(lot_no, bundle_no): return db.masters_lots.find_one({"lot_no": lot_no, "bundle_no": bundle_no}, {'_id':0})

def get_bundle_progress(lot_filter=None, bundle_filter=None):
    query = {}
    if lot_filter and lot_filter != "All": query["lot_no"] = lot_filter
    if bundle_filter and bundle_filter != "All": query["bundle_no"] = bundle_filter
    lots = list(db.masters_lots.find(query, {'_id':0}))
    if not lots: return pd.DataFrame()
    
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
                max_q = float(b_det.get

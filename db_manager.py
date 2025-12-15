import streamlit as st
import pymongo
import pandas as pd
import datetime
import re

# --- CONNECT TO DATABASE ---
try:
    MONGO_URI = st.secrets["MONGO_URI"]
except:
    st.error("MongoDB Connection String not found in secrets!")
    st.stop()

@st.cache_resource
def get_db():
    client = pymongo.MongoClient(MONGO_URI)
    return client['shine_arc_mes_db']

db = get_db()

# ==========================================
# 1. DASHBOARD STATS (FIX FOR CRASH)
# ==========================================
def get_dashboard_stats():
    # 1. Product Stats
    active = db.lots.count_documents({"status": "Active"})
    completed = db.lots.count_documents({"status": "Completed"})
    
    # 2. Purchase Stats
    total_rolls = db.fabric_rolls.count_documents({"status": "Available"})
    total_accessories = db.accessories.count_documents({"quantity": {"$gt": 0}})
    
    # 3. Pending List (Active Lots) - Projection to limit data size
    pending_lots = list(db.lots.find(
        {"status": "Active"}, 
        {"_id": 0, "lot_no": 1, "item_name": 1, "total_qty": 1, "color": 1, "date_created": 1}
    ))
    
    # Ensure date is string for display
    for p in pending_lots:
        if isinstance(p.get('date_created'), datetime.datetime):
            p['date_created'] = p['date_created'].strftime("%Y-%m-%d")
    
    return {
        "active_lots": active,
        "completed_lots": completed,
        "fabric_rolls": total_rolls,
        "accessories_count": total_accessories,
        "pending_list": pending_lots
    }

# ==========================================
# 2. LOT & PRODUCTION TRACKING
# ==========================================
def get_next_lot_no():
    last_lot = db.lots.find_one(sort=[("date_created", -1)])
    if not last_lot: return "DRCLOT001"
    match = re.search(r'(\d+)$', last_lot['lot_no'])
    return f"DRCLOT{int(match.group(1)) + 1:03d}" if match else "DRCLOT001"

def create_lot(lot_data, all_selected_roll_ids):
    total_qty = sum(int(q) for q in lot_data['size_breakdown'].values())
    initial_stage = f"Cutting - {lot_data['created_by']}"
    
    lot_doc = {
        "lot_no": lot_data['lot_no'],
        "item_name": lot_data['item_name'],
        "item_code": lot_data['item_code'],
        "color": lot_data['color'],
        "created_by": lot_data['created_by'],
        "fabrics_consumed": lot_data.get('fabrics_consumed', []),
        "total_fabric_weight": lot_data.get('total_fabric_weight', 0),
        "date_created": datetime.datetime.now(),
        "total_qty": total_qty,
        "size_breakdown": lot_data['size_breakdown'],
        "current_stage_stock": {initial_stage: lot_data['size_breakdown']},
        "status": "Active"
    }
    
    try:
        db.lots.insert_one(lot_doc)
        if all_selected_roll_ids:
            db.fabric_rolls.update_many(
                {"_id": {"$in": all_selected_roll_ids}}, 
                {"$set": {"status": "Consumed", "used_in_lot": lot_data['lot_no']}}
            )
        return True, "Lot Created Successfully"
    except pymongo.errors.DuplicateKeyError:
        return False, "Lot No already exists!"

def get_active_lots(): return list(db.lots.find({"status": "Active"}))
def get_lot_details(lot_no): return db.lots.find_one({"lot_no": lot_no})
def get_all_lot_numbers(): return [l['lot_no'] for l in db.lots.find({}, {"lot_no": 1})]

def move_lot_stage(tx_data):
    lot_no, from_s, to_k = tx_data['lot_no'], tx_data['from_stage'], tx_data['to_stage_key']
    comp_k, qty = tx_data['size_key'], int(tx_data['qty'])
    
    log = {
        "lot_no": lot_no, "from_stage": from_s, "to_stage": to_k,
        "karigar": tx_data['karigar'], "machine": tx_data.get('machine', 'N/A'),
        "variant": comp_k, "qty": qty, "timestamp": datetime.datetime.now()
    }
    db.transactions.insert_one(log)
    
    db.lots.update_one({"lot_no": lot_no}, {"$inc": {f"current_stage_stock.{from_s}.{comp_k}": -qty}})
    db.lots.update_one({"lot_no": lot_no}, {"$inc": {f"current_stage_stock.{to_k}.{comp_k}": qty}})
    return True

def get_lot_transactions(lot_no):
    return list(db.transactions.find({"lot_no": lot_no}).sort("timestamp", -1))

# ==========================================
# 3. INVENTORY
# ==========================================
def add_fabric_rolls_batch(fabric_name, color, rolls_data, uom):
    batch_id = datetime.datetime.now().strftime("%Y%m%d%H%M")
    docs = [{
        "fabric_name": fabric_name, "color": color, "batch_id": batch_id,
        "roll_no": f"{batch_id}-{i+1}", "quantity": float(q), "uom": uom,
        "status": "Available", "date_added": datetime.datetime.now()
    } for i, q in enumerate(rolls_data)]
    if docs: db.fabric_rolls.insert_many(docs)

def get_available_rolls(name, color):
    return list(db.fabric_rolls.find({"fabric_name": name, "color": color, "status": "Available"}))

def get_all_fabric_stock_summary():
    pipeline = [
        {"$match": {"status": "Available"}},
        {"$group": {"_id": {"name": "$fabric_name", "color": "$color", "uom": "$uom"}, "total_rolls": {"$sum": 1}, "total_qty": {"$sum": "$quantity"}}}
    ]
    return list(db.fabric_rolls.aggregate(pipeline))

def update_accessory_stock(name, txn_type, qty, uom, remarks=""):
    db.accessory_logs.insert_one({
        "name": name, "type": txn_type, "qty": float(qty), "uom": uom, "remarks": remarks, "date": datetime.datetime.now()
    })
    change = float(qty) if txn_type == "Inward" else -float(qty)
    db.accessories.update_one({"name": name}, {"$inc": {"quantity": change}, "$set": {"uom": uom, "last_updated": datetime.datetime.now()}}, upsert=True)
    return True

def get_accessory_stock(): return list(db.accessories.find())
def get_accessory_names(): return [a['name'] for a in list(db.accessories.find({}, {"name": 1}))]

# ==========================================
# 4. MASTERS (ITEM UPDATED)
# ==========================================
def add_item_master(name, code, color, fabrics_list):
    if db.items.find_one({"item_code": code}): return False, "Exists!"
    clean_fabrics = [f for f in fabrics_list if f and f.strip() != ""]
    db.items.insert_one({
        "item_name": name, "item_code": code, "item_color": color, 
        "required_fabrics": clean_fabrics, "date_added": datetime.datetime.now()
    })
    return True, "Added"

def get_all_items(): return pd.DataFrame(list(db.items.find()))
def get_unique_item_names(): return sorted(list(db.items.distinct("item_name")))
def get_codes_by_item_name(name): return [i['item_code'] for i in db.items.find({"item_name": name}, {"item_code": 1})]
def get_item_details_by_code(code): return db.items.find_one({"item_code": code})

def add_process(name):
    if not db.processes.find_one({"name": name}): db.processes.insert_one({"name": name})
def get_all_processes():
    p = list(db.processes.find({}, {"name": 1}))
    return [x['name'] for x in p] if p else ["Singer", "Overlock", "Flat", "Kansai", "Iron", "Table", "Cutting", "Thread Cutting", "Outsource"]

def add_staff(name, role): db.staff.insert_one({"name": name, "role": role, "date_added": datetime.datetime.now()})
def get_staff_by_role(role): return [s['name'] for s in db.staff.find({"role": role}, {"name": 1})]
def get_all_staff_names(): return [s['name'] for s in db.staff.find({}, {"name": 1})]
def get_all_staff(): return pd.DataFrame(list(db.staff.find()))

def add_material(name, hsn, img=None): db.materials.insert_one({"name": name, "hsn": hsn, "image": img})
def get_materials(): return pd.DataFrame(list(db.materials.find()))
def get_material_names(): return sorted(list(db.materials.distinct("name")))

def add_size(name): 
    if not db.sizes.find_one({"name": name}): db.sizes.insert_one({"name": name})
def get_sizes(): return [x['name'] for x in db.sizes.find()]

def add_color(name): 
    if not db.colors.find_one({"name": name}): db.colors.insert_one({"name": name})
def get_colors(): return list(db.colors.distinct("name"))

# ==========================================
# 5. RATES & PAY
# ==========================================
def add_piece_rate(i, c, m, r, d): db.rates.insert_one({"item_name": i, "item_code": c, "machine": m, "rate": float(r), "valid_from": pd.to_datetime(d)})
def get_rate_master(): return pd.DataFrame(list(db.rates.find()))
def get_applicable_rate(i, m):
    r = db.rates.find_one({"item_name": i, "machine": m}, sort=[("valid_from", -1)])
    return r['rate'] if r else 0.0

def get_staff_productivity(month, year):
    start, end = datetime.datetime(year, month, 1), datetime.datetime(year + 1 if month==12 else year, 1 if month==12 else month+1, 1)
    pipeline = [
        {"$match": {"timestamp": {"$gte": start, "$lt": end}, "karigar": {"$ne": None}}},
        {"$lookup": {"from": "lots", "localField": "lot_no", "foreignField": "lot_no", "as": "lot"}},
        {"$unwind": "$lot"},
        {"$group": {"_id": {"s": "$karigar", "i": "$lot.item_name", "p": "$machine"}, "qty": {"$sum": "$qty"}}}
    ]
    data = list(db.transactions.aggregate(pipeline))
    att_pipeline = [{"$match": {"date": {"$gte": start, "$lt": end}}}, {"$group": {"_id": "$staff_name", "days": {"$sum": 1}, "hours": {"$sum": "$hours_worked"}}}]
    att_data = list(db.attendance.aggregate(att_pipeline))
    att_map = {x['_id']: x for x in att_data}
    report = []
    for row in data:
        rate = get_applicable_rate(row['_id']['i'], row['_id']['p'])
        ad = att_map.get(row['_id']['s'], {"days": 0, "hours": 0})
        report.append({
            "Staff": row['_id']['s'], "Process": row['_id']['p'], "Item": row['_id']['i'],
            "Qty": row['qty'], "Rate": rate, "Earnings": row['qty'] * rate, "Days Present": ad['days']
        })
    return pd.DataFrame(report)

# ==========================================
# 6. HELPERS
# ==========================================
def mark_attendance(staff_name, date, in_time, out_time, status, remarks):
    hours = 0.0
    if in_time and out_time:
        d = datetime.date(2000, 1, 1)
        hours = (datetime.datetime.combine(d, out_time) - datetime.datetime.combine(d, in_time)).total_seconds() / 3600
    db.attendance.update_one(
        {"staff_name": staff_name, "date": pd.to_datetime(date)},
        {"$set": {"in_time": str(in_time), "out_time": str(out_time), "hours_worked": round(hours, 2), "status": status, "remarks": remarks}}, upsert=True)

def get_attendance_records(date=None):
    q = {"date": {"$gte": pd.to_datetime(date), "$lt": pd.to_datetime(date) + datetime.timedelta(days=1)}} if date else {}
    return list(db.attendance.find(q).sort("date", -1))

def get_karigar_performance():
    return list(db.transactions.aggregate([{"$match": {"karigar": {"$ne": None}}}, {"$group": {"_id": "$karigar", "total_pcs": {"$sum": "$qty"}}}, {"$sort": {"total_pcs": -1}}]))

def get_stages_for_item(i): return ["Stitching", "Washing", "Finishing", "Packing", "Outsource"]

def clean_database():
    for c in db.list_collection_names(): db[c].drop()
    return True

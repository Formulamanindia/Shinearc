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
# 1. LOT & PRODUCTION TRACKING
# ==========================================
def get_next_lot_no():
    """Auto-generates the next Lot Number (DRCLOT001, DRCLOT002...)"""
    last_lot = db.lots.find_one(sort=[("date_created", -1)])
    
    if not last_lot:
        return "DRCLOT001"
    
    # Extract number from "DRCLOT005" -> 5
    last_code = last_lot['lot_no']
    match = re.search(r'(\d+)$', last_code)
    
    if match:
        next_num = int(match.group(1)) + 1
        return f"DRCLOT{next_num:03d}"
    
    return "DRCLOT001" # Fallback

def create_lot(lot_data, selected_rolls_ids):
    """
    Creates Lot and Consumes Fabric Rolls.
    """
    total_qty = sum(int(q) for q in lot_data['size_breakdown'].values())
    initial_stage = f"Cutting - {lot_data['created_by']}"
    
    lot_doc = {
        "lot_no": lot_data['lot_no'],
        "item_name": lot_data['item_name'],
        "item_code": lot_data['item_code'],
        "color": lot_data['color'],
        "created_by": lot_data['created_by'],
        "fabric_name": lot_data['fabric_name'],
        "rolls_used_ids": selected_rolls_ids, # List of Roll IDs
        "total_fabric_weight": lot_data['total_fabric_weight'],
        "date_created": datetime.datetime.now(),
        "total_qty": total_qty,
        "size_breakdown": lot_data['size_breakdown'],
        "current_stage_stock": {initial_stage: lot_data['size_breakdown']},
        "status": "Active"
    }
    
    try:
        # 1. Create Lot
        db.lots.insert_one(lot_doc)
        
        # 2. Consume Rolls (Mark as Used)
        if selected_rolls_ids:
            db.fabric_rolls.update_many(
                {"_id": {"$in": selected_rolls_ids}},
                {"$set": {"status": "Consumed", "used_in_lot": lot_data['lot_no']}}
            )
            
        return True, "Lot Created Successfully"
    except pymongo.errors.DuplicateKeyError:
        return False, "Lot No already exists!"

def get_active_lots():
    return list(db.lots.find({"status": "Active"}))

def get_lot_details(lot_no):
    return db.lots.find_one({"lot_no": lot_no})

def move_lot_stage(tx_data):
    lot_no = tx_data['lot_no']
    from_stage = tx_data['from_stage']
    to_stage_key = tx_data['to_stage_key']
    composite_key = tx_data['size_key'] 
    qty = int(tx_data['qty'])
    
    log = {
        "lot_no": lot_no,
        "from_stage": from_stage,
        "to_stage": to_stage_key,
        "karigar": tx_data['karigar'],
        "machine": tx_data.get('machine', 'N/A'),
        "variant": composite_key,
        "qty": qty,
        "timestamp": datetime.datetime.now()
    }
    db.transactions.insert_one(log)
    
    db.lots.update_one({"lot_no": lot_no}, {"$inc": {f"current_stage_stock.{from_stage}.{composite_key}": -qty}})
    db.lots.update_one({"lot_no": lot_no}, {"$inc": {f"current_stage_stock.{to_stage_key}.{composite_key}": qty}})
    return True

def get_lot_transactions(lot_no):
    return list(db.transactions.find({"lot_no": lot_no}).sort("timestamp", -1))

# ==========================================
# 2. FABRIC INVENTORY (ROLL LEVEL)
# ==========================================
def add_fabric_rolls_batch(fabric_name, color, rolls_data, uom):
    """
    rolls_data = [25.5, 26.0, 24.0] (List of weights)
    """
    batch_id = datetime.datetime.now().strftime("%Y%m%d%H%M")
    
    docs = []
    for idx, qty in enumerate(rolls_data):
        docs.append({
            "fabric_name": fabric_name,
            "color": color,
            "batch_id": batch_id,
            "roll_no": f"{batch_id}-{idx+1}",
            "quantity": float(qty),
            "uom": uom,
            "status": "Available", # Available, Consumed
            "date_added": datetime.datetime.now()
        })
    
    if docs:
        db.fabric_rolls.insert_many(docs)

def get_available_rolls(fabric_name, color):
    return list(db.fabric_rolls.find(
        {"fabric_name": fabric_name, "color": color, "status": "Available"}
    ))

def get_all_fabric_stock_summary():
    pipeline = [
        {"$match": {"status": "Available"}},
        {"$group": {
            "_id": {"name": "$fabric_name", "color": "$color", "uom": "$uom"},
            "total_rolls": {"$sum": 1},
            "total_qty": {"$sum": "$quantity"}
        }}
    ]
    return list(db.fabric_rolls.aggregate(pipeline))

# ==========================================
# 3. MASTERS & RATES
# ==========================================
def add_staff(name, role):
    db.staff.insert_one({"name": name, "role": role, "date_added": datetime.datetime.now()})

def get_staff_by_role(role):
    staff = list(db.staff.find({"role": role}, {"name": 1}))
    return [s['name'] for s in staff]

def get_all_staff():
    return pd.DataFrame(list(db.staff.find()))

def add_piece_rate(item_name, item_code, machine, rate, valid_from):
    db.rates.insert_one({
        "item_name": item_name, "item_code": item_code, "machine": machine,
        "rate": float(rate), "valid_from": pd.to_datetime(valid_from),
        "created_at": datetime.datetime.now()
    })

def get_rate_master():
    return pd.DataFrame(list(db.rates.find()))

def get_applicable_rate(item_name, machine):
    rate_doc = db.rates.find_one(
        {"item_name": item_name, "machine": machine},
        sort=[("valid_from", -1)]
    )
    return rate_doc['rate'] if rate_doc else 0.0

# ==========================================
# 4. PRODUCTIVITY & ANALYTICS
# ==========================================
def get_staff_productivity(month_num, year):
    """
    Calculates work done by staff in a specific month + Lot Creation credit for Cutters.
    """
    start_date = datetime.datetime(year, month_num, 1)
    if month_num == 12:
        end_date = datetime.datetime(year + 1, 1, 1)
    else:
        end_date = datetime.datetime(year, month_num + 1, 1)

    # 1. MOVEMENT TRANSACTIONS (Stitching, Ironing, etc.)
    pipeline = [
        {"$match": {
            "timestamp": {"$gte": start_date, "$lt": end_date},
            "karigar": {"$ne": None}
        }},
        {"$lookup": {
            "from": "lots", "localField": "lot_no", "foreignField": "lot_no", "as": "lot_info"
        }},
        {"$unwind": "$lot_info"},
        {"$group": {
            "_id": {"staff": "$karigar", "item": "$lot_info.item_name", "process": "$machine"},
            "total_qty": {"$sum": "$qty"}
        }}
    ]
    
    data = list(db.transactions.aggregate(pipeline))
    
    # 2. CUTTING TRANSACTIONS (From Lots created)
    # Cutters don't always appear in 'transactions' collection, they appear in 'lots' collection
    cutting_pipeline = [
        {"$match": {
            "date_created": {"$gte": start_date, "$lt": end_date}
        }},
        {"$group": {
            "_id": {"staff": "$created_by", "item": "$item_name", "process": "Cutting"},
            "total_qty": {"$sum": "$total_qty"}
        }}
    ]
    cutting_data = list(db.lots.aggregate(cutting_pipeline))
    
    # Combine Data
    full_data = data + cutting_data
    
    report = []
    for row in full_data:
        staff = row['_id']['staff']
        item = row['_id']['item']
        process = row['_id']['process']
        qty = row['total_qty']
        
        rate = get_applicable_rate(item, process)
        
        report.append({
            "Staff": staff,
            "Role/Process": process,
            "Item": item,
            "Total Qty": qty,
            "Rate": rate,
            "Earnings": qty * rate
        })
        
    return pd.DataFrame(report)

def get_dashboard_stats():
    active = db.lots.count_documents({"status": "Active"})
    pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total_qty"}}}]
    res = list(db.lots.aggregate(pipeline))
    pcs = res[0]['total'] if res else 0
    return active, pcs

def get_karigar_performance():
    pipeline = [
        {"$match": {"karigar": {"$ne": None}}},
        {"$group": {"_id": "$karigar", "total_pcs": {"$sum": "$qty"}}},
        {"$sort": {"total_pcs": -1}}
    ]
    return list(db.transactions.aggregate(pipeline))

# --- HELPERS ---
def get_stages_for_item(item_name):
    return ["Stitching", "Washing", "Finishing", "Packing", "Outsource"]
def get_colors():
    c = list(db.fabric_rolls.distinct("color"))
    return c if c else []
def get_fabric_names():
    f = list(db.fabric_rolls.distinct("fabric_name"))
    return f if f else []
def get_sizes():
    s = list(db.sizes.find())
    return [x['name'] for x in s]

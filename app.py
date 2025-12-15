import streamlit as st
import pymongo
import pandas as pd
import datetime

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
def create_lot(lot_data):
    """
    Creates a new production Lot with Multi-Color support.
    lot_data['size_breakdown'] will now look like:
    {'Red_S': 10, 'Red_M': 20, 'Blue_S': 10}
    """
    total_qty = sum(int(q) for q in lot_data['size_breakdown'].values())
    
    # Construct the detailed stage name
    initial_stage = f"Cutting - {lot_data['created_by']}"
    
    lot_doc = {
        "lot_no": lot_data['lot_no'],
        "item_name": lot_data['item_name'],
        "item_code": lot_data['item_code'],
        "created_by": lot_data['created_by'],
        "date_created": datetime.datetime.now(),
        "total_qty": total_qty,
        "is_multicolor": True, # Flag for UI handling
        "size_breakdown": lot_data['size_breakdown'],
        
        # Stock starts at Cutting
        "current_stage_stock": {
            initial_stage: lot_data['size_breakdown']
        },
        "status": "Active"
    }
    try:
        db.lots.insert_one(lot_doc)
        return True, "Lot Created Successfully"
    except pymongo.errors.DuplicateKeyError:
        return False, "Lot No already exists!"

def get_active_lots():
    return list(db.lots.find({"status": "Active"}))

def get_all_lot_numbers():
    lots = list(db.lots.find({}, {"lot_no": 1}))
    return [l['lot_no'] for l in lots]

def get_lot_details(lot_no):
    return db.lots.find_one({"lot_no": lot_no})

def move_lot_stage(tx_data):
    lot_no = tx_data['lot_no']
    from_stage = tx_data['from_stage']
    to_stage_key = tx_data['to_stage_key']
    
    # 'size' here will actually be 'Color_Size' (e.g. Red_S)
    composite_key = tx_data['size_key'] 
    qty = int(tx_data['qty'])
    
    # Log Transaction
    log = {
        "lot_no": lot_no,
        "from_stage": from_stage,
        "to_stage": to_stage_key,
        "karigar": tx_data['karigar'],
        "machine": tx_data.get('machine', 'N/A'),
        "variant": composite_key, # Stores 'Red_S'
        "qty": qty,
        "timestamp": datetime.datetime.now()
    }
    db.transactions.insert_one(log)
    
    # Update Stock
    db.lots.update_one({"lot_no": lot_no}, {"$inc": {f"current_stage_stock.{from_stage}.{composite_key}": -qty}})
    db.lots.update_one({"lot_no": lot_no}, {"$inc": {f"current_stage_stock.{to_stage_key}.{composite_key}": qty}})
    return True

def get_lot_transactions(lot_no):
    return list(db.transactions.find({"lot_no": lot_no}).sort("timestamp", -1))

# ==========================================
# 2. STAFF & RATES
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
        "item_name": item_name,
        "item_code": item_code,
        "machine": machine,
        "rate": float(rate),
        "valid_from": pd.to_datetime(valid_from),
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
# 3. ANALYTICS & REPORTS
# ==========================================
def get_staff_production_summary():
    pipeline = [
        {"$match": {"karigar": {"$ne": None}, "machine": {"$ne": "N/A"}}},
        {"$lookup": {
            "from": "lots",
            "localField": "lot_no",
            "foreignField": "lot_no",
            "as": "lot_info"
        }},
        {"$unwind": "$lot_info"},
        {"$group": {
            "_id": {
                "karigar": "$karigar",
                "item_name": "$lot_info.item_name",
                "machine": "$machine"
            },
            "total_qty": {"$sum": "$qty"}
        }}
    ]
    
    data = list(db.transactions.aggregate(pipeline))
    report = []
    for row in data:
        karigar = row['_id']['karigar']
        item = row['_id']['item_name']
        machine = row['_id']['machine']
        qty = row['total_qty']
        rate = get_applicable_rate(item, machine)
        report.append({
            "Staff Name": karigar,
            "Item": item,
            "Machine": machine,
            "Total Qty": qty,
            "Rate": rate,
            "Total Amount": qty * rate
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

def get_stages_for_item(item_name):
    return ["Stitching", "Washing", "Finishing", "Packing", "Outsource"]

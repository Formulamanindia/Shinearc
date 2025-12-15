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
    total_qty = sum(int(q) for q in lot_data['size_breakdown'].values())
    lot_doc = {
        "lot_no": lot_data['lot_no'],
        "item_name": lot_data['item_name'],
        "item_code": lot_data['item_code'],
        "color": lot_data['color'],
        "created_by": lot_data['created_by'],
        "date_created": datetime.datetime.now(),
        "total_qty": total_qty,
        "size_breakdown": lot_data['size_breakdown'],
        "current_stage_stock": {"Cutting": lot_data['size_breakdown']},
        "status": "Active"
    }
    try:
        db.lots.insert_one(lot_doc)
        return True, "Lot Created Successfully"
    except pymongo.errors.DuplicateKeyError:
        return False, "Lot No already exists!"

def get_active_lots():
    """Returns a list of all active lot dictionaries"""
    return list(db.lots.find({"status": "Active"}))

def get_all_lot_numbers():
    """Returns just a list of strings for Dropdowns"""
    lots = list(db.lots.find({}, {"lot_no": 1}))
    return [l['lot_no'] for l in lots]

def get_lot_details(lot_no):
    return db.lots.find_one({"lot_no": lot_no})

def move_lot_stage(tx_data):
    lot_no = tx_data['lot_no']
    from_stage = tx_data['from_stage']
    to_stage = tx_data['to_stage']
    size = tx_data['size']
    qty = int(tx_data['qty'])
    
    log = {
        "lot_no": lot_no,
        "from_stage": from_stage,
        "to_stage": to_stage,
        "karigar": tx_data['karigar'],
        "machine": tx_data.get('machine', 'N/A'),
        "size": size,
        "qty": qty,
        "timestamp": datetime.datetime.now()
    }
    db.transactions.insert_one(log)
    
    db.lots.update_one({"lot_no": lot_no}, {"$inc": {f"current_stage_stock.{from_stage}.{size}": -qty}})
    db.lots.update_one({"lot_no": lot_no}, {"$inc": {f"current_stage_stock.{to_stage}.{size}": qty}})
    return True

def get_lot_transactions(lot_no):
    return list(db.transactions.find({"lot_no": lot_no}).sort("timestamp", -1))

# ==========================================
# 2. STAFF MANAGEMENT (NEW)
# ==========================================
def add_staff(name, role):
    db.staff.insert_one({
        "name": name,
        "role": role,
        "date_added": datetime.datetime.now()
    })

def get_staff_by_role(role):
    """
    Returns a list of names for a specific role.
    e.g., role="Cutting Master" -> ["Ramesh", "Suresh"]
    """
    staff = list(db.staff.find({"role": role}, {"name": 1}))
    return [s['name'] for s in staff]

def get_all_staff():
    return pd.DataFrame(list(db.staff.find()))

# ==========================================
# 3. ANALYTICS & HELPERS
# ==========================================
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
    # Default stages
    return ["Cutting", "Fusing", "Stitching", "Washing", "Finishing", "Packing"]

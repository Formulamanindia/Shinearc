import streamlit as st
import pymongo
import pandas as pd
import datetime
from bson.objectid import ObjectId

# --- CONNECT TO DATABASE ---
try:
    MONGO_URI = st.secrets["MONGO_URI"]
except:
    st.error("MongoDB Connection String not found in secrets!")
    st.stop()

@st.cache_resource
def get_db():
    client = pymongo.MongoClient(MONGO_URI)
    return client['shine_arc_mes_db'] # New MES Database

db = get_db()

# ==========================================
# 1. WORKFLOW & CONFIGURATION
# ==========================================
def save_workflow(item_name, stages, is_outsource=False):
    """
    Saves the journey of an item (e.g., Shirt: Cutting -> Fusing -> Stitching -> Packing)
    """
    db.workflows.update_one(
        {"item_name": item_name},
        {"$set": {"stages": stages, "is_outsource": is_outsource, "updated_at": datetime.datetime.now()}},
        upsert=True
    )

def get_workflows():
    return list(db.workflows.find())

def get_stages_for_item(item_name):
    wf = db.workflows.find_one({"item_name": item_name})
    if wf:
        return wf['stages']
    # Default Fallback Journey
    return ["Cutting", "Stitching (Overlock)", "Stitching (Flat)", "Finishing", "Packing"]

# ==========================================
# 2. LOT MANAGEMENT (CUTTING FLOOR)
# ==========================================
def create_lot(lot_data):
    """
    Creates a new Lot in the system starting at 'Cutting' stage.
    lot_data includes: lot_no, item_name, sizes (dict of qty), color, item_code, cutter_name
    """
    # Calculate Total Qty
    total_qty = sum(int(q) for q in lot_data['size_breakdown'].values())
    
    lot_doc = {
        "lot_no": lot_data['lot_no'],
        "item_name": lot_data['item_name'],
        "item_code": lot_data['item_code'],
        "color": lot_data['color'],
        "created_by": lot_data['created_by'],
        "date_created": datetime.datetime.now(),
        "total_qty": total_qty,
        "size_breakdown": lot_data['size_breakdown'], # {'S': 10, 'M': 20}
        
        # CURRENT STATUS (Where is the stock?)
        # Initially, all stock is sitting in "Cutting"
        "current_stage_stock": {
            "Cutting": lot_data['size_breakdown'] 
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

def get_lot_details(lot_no):
    return db.lots.find_one({"lot_no": lot_no})

# ==========================================
# 3. PRODUCTION MOVEMENT (ISSUANCE)
# ==========================================
def move_lot_stage(transaction_data):
    """
    Moves pieces from one stage to another (e.g., Cutting -> Overlock).
    """
    lot_no = transaction_data['lot_no']
    from_stage = transaction_data['from_stage'] # e.g., "Cutting"
    to_stage = transaction_data['to_stage']     # e.g., "Stitching (Overlock)"
    size = transaction_data['size']
    qty = int(transaction_data['qty'])
    
    # 1. RECORD TRANSACTION LOG
    log = {
        "lot_no": lot_no,
        "from_stage": from_stage,
        "to_stage": to_stage,
        "karigar": transaction_data['karigar'],
        "machine": transaction_data['machine'],
        "size": size,
        "qty": qty,
        "timestamp": datetime.datetime.now()
    }
    db.transactions.insert_one(log)
    
    # 2. UPDATE LOT STOCK LEVELS
    # Decrement from 'from_stage'
    db.lots.update_one(
        {"lot_no": lot_no},
        {"$inc": {f"current_stage_stock.{from_stage}.{size}": -qty}}
    )
    
    # Increment to 'to_stage'
    db.lots.update_one(
        {"lot_no": lot_no},
        {"$inc": {f"current_stage_stock.{to_stage}.{size}": qty}}
    )
    
    return True

def get_lot_transactions(lot_no):
    return list(db.transactions.find({"lot_no": lot_no}).sort("timestamp", -1))

# ==========================================
# 4. ANALYTICS
# ==========================================
def get_dashboard_stats():
    # Total Active Lots
    active_lots = db.lots.count_documents({"status": "Active"})
    
    # Total Pieces in Production
    pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$total_qty"}}}
    ]
    res = list(db.lots.aggregate(pipeline))
    total_pieces = res[0]['total'] if res else 0
    
    return active_lots, total_pieces

def get_karigar_performance():
    # Group transactions by Karigar to see who did how much
    pipeline = [
        {"$match": {"karigar": {"$ne": "N/A"}}}, # Ignore non-karigar moves
        {"$group": {"_id": "$karigar", "total_pcs": {"$sum": "$qty"}}},
        {"$sort": {"total_pcs": -1}}
    ]
    return list(db.transactions.aggregate(pipeline))

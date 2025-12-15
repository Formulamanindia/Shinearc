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
    Creates a new production Lot.
    Expected keys: lot_no, item_name, item_code, color, created_by, size_breakdown
    """
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
        # Initial Stock Location: All in 'Cutting'
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

def move_lot_stage(tx_data):
    """
    Moves stock from one stage to another.
    """
    lot_no = tx_data['lot_no']
    from_stage = tx_data['from_stage']
    to_stage = tx_data['to_stage']
    size = tx_data['size']
    qty = int(tx_data['qty'])
    
    # 1. Log Transaction
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
    
    # 2. Update Stock (Decrement Source, Increment Destination)
    db.lots.update_one(
        {"lot_no": lot_no},
        {"$inc": {f"current_stage_stock.{from_stage}.{size}": -qty}}
    )
    db.lots.update_one(
        {"lot_no": lot_no},
        {"$inc": {f"current_stage_stock.{to_stage}.{size}": qty}}
    )
    return True

def get_lot_transactions(lot_no):
    return list(db.transactions.find({"lot_no": lot_no}).sort("timestamp", -1))

# ==========================================
# 2. CONFIG & HELPERS
# ==========================================
def save_workflow(item_name, stages, is_outsource=False):
    db.workflows.update_one(
        {"item_name": item_name},
        {"$set": {"stages": stages, "is_outsource": is_outsource}},
        upsert=True
    )

def get_stages_for_item(item_name):
    # Try to find specific workflow, else return default
    wf = db.workflows.find_one({"item_name": item_name})
    if wf: return wf['stages']
    return ["Cutting", "Stitching", "Washing", "Finishing", "Packing"]

# ==========================================
# 3. ANALYTICS
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

# ==========================================
# 4. BASIC INVENTORY (Legacy Support)
# ==========================================
def add_product(product_data):
    # For Design Catalog
    if 'stock_qty' not in product_data: product_data['stock_qty'] = 0
    if 'sell_price' not in product_data: product_data['sell_price'] = 0.0
    db.inventory.insert_one(product_data)

def get_inventory():
    return pd.DataFrame(list(db.inventory.find()))

def get_orders():
    # Placeholder for sales data
    return pd.DataFrame(list(db.sales.find()))

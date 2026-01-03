import streamlit as st
import pymongo
import pandas as pd
import datetime
import re
from bson.objectid import ObjectId

# --- DATABASE CONNECTION ---
try:
    MONGO_URI = st.secrets["MONGO_URI"]
except:
    st.error("MongoDB Secrets Missing!")
    st.stop()

@st.cache_resource
def get_db():
    client = pymongo.MongoClient(MONGO_URI)
    return client['shine_arc_mes_db']

db = get_db()

# ==========================================
# 1. SMART WORKFLOWS
# ==========================================
def process_smart_purchase(data):
    try:
        # 1. ADD LEDGER ENTRY (BILL)
        db.supplier_ledger.insert_one({
            "supplier": data['supplier'],
            "date": pd.to_datetime(data['date']),
            "type": "Bill",
            "amount": data['grand_total'],
            "reference": data['bill_no'],
            "remarks": f"Smart Entry | Stock: {data['stock_type']} | Tax: {data['tax_slab']}%",
            "items": data['items'],
            "created_at": datetime.datetime.now()
        })

        # 2. ADD STOCK (IF APPLICABLE)
        if data['stock_type'] == 'Fabric' and data['stock_data']:
            batch_id = datetime.datetime.now().strftime("%Y%m%d%H%M")
            fabric_docs = []
            for i, roll_wt in enumerate(data['stock_data'].get('rolls', [])):
                fabric_docs.append({
                    "fabric_name": data['stock_data']['name'],
                    "color": data['stock_data']['color'],
                    "batch_id": batch_id,
                    "roll_no": f"{batch_id}-{i+1}",
                    "quantity": float(roll_wt),
                    "uom": "Kg",
                    "supplier": data['supplier'],
                    "bill_no": data['bill_no'],
                    "status": "Available",
                    "date_added": datetime.datetime.now()
                })
            if fabric_docs: db.fabric_rolls.insert_many(fabric_docs)

        elif data['stock_type'] == 'Accessory' and data['stock_data']:
            db.accessories.update_one(
                {"name": data['stock_data']['name']},
                {"$inc": {"quantity": float(data['stock_data']['qty'])}},
                upsert=True
            )
            db.accessory_logs.insert_one({
                "name": data['stock_data']['name'],
                "type": "Inward",
                "qty": float(data['stock_data']['qty']),
                "uom": data['stock_data']['uom'],
                "remarks": f"Bill {data['bill_no']}",
                "date": datetime.datetime.now()
            })

        # 3. ADD PAYMENT (IF APPLICABLE)
        if data['payment'] and data['payment']['amount'] > 0:
            pay_ref = generate_payment_id()
            db.supplier_ledger.insert_one({
                "supplier": data['supplier'],
                "date": pd.to_datetime(data['date']),
                "type": "Payment",
                "amount": float(data['payment']['amount']),
                "reference": pay_ref,
                "remarks": f"Auto-Payment for Bill {data['bill_no']} ({data['payment']['mode']})",
                "created_at": datetime.datetime.now()
            })

        return True, "Transaction Successful"
    except Exception as e:
        return False, str(e)

# ==========================================
# 2. BASIC HELPERS
# ==========================================
def generate_payment_id(prefix="PAY"):
    today = datetime.datetime.now().strftime("%Y%m%d")
    start_of_day = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    count = db.supplier_ledger.count_documents({"type": {"$in": ["Payment", "Debit Note"]}, "created_at": {"$gte": start_of_day}})
    return f"{prefix}-{today}-{count+1:03d}"

def get_dashboard_stats():
    return {
        "active_lots": db.lots.count_documents({"status": "Active"}),
        "rolls": db.fabric_rolls.count_documents({"status": "Available"}),
        "accessories_count": db.accessories.count_documents({"quantity": {"$gt": 0}})
    }

# ==========================================
# 3. LEDGER & PAYMENTS
# ==========================================
def get_supplier_ledger(name):
    data = list(db.supplier_ledger.find({"supplier": name}).sort("date", 1))
    if not data: return pd.DataFrame()
    
    res = []; bal = 0
    for row in data:
        cr = row['amount'] if row['type'] == 'Bill' else 0
        dr = row['amount'] if row['type'] in ['Payment', 'Debit Note'] else 0
        bal += (cr - dr)
        res.append({
            "ID": str(row['_id']),
            "Date": row['date'].strftime("%d-%b-%y"),
            "Type": row['type'],
            "Ref": row.get('reference', '-'),
            "Credit": cr, "Debit": dr, "Balance": bal,
            "Remarks": row.get('remarks', '')
        })
    return pd.DataFrame(res)

def add_simple_payment(sup, date, amt, mode, note):
    ref = generate_payment_id()
    db.supplier_ledger.insert_one({
        "supplier": sup, "date": pd.to_datetime(date), "type": "Payment",
        "amount": amt, "reference": ref, "remarks": f"{mode} - {note}",
        "created_at": datetime.datetime.now()
    })
    return ref

# ==========================================
# 4. INVENTORY FUNCTIONS
# ==========================================
def get_all_fabric_stock_summary():
    return list(db.fabric_rolls.aggregate([
        {"$match": {"status": "Available"}},
        {"$group": {"_id": {"name": "$fabric_name", "color": "$color"}, "total_qty": {"$sum": "$quantity"}}}
    ]))

def update_accessory_stock(name, txn_type, qty, uom):
    change = float(qty) if txn_type == "Inward" else -float(qty)
    db.accessories.update_one(
        {"name": name}, 
        {"$inc": {"quantity": change}, "$set": {"uom": uom}}, 
        upsert=True
    )

def get_accessory_stock():
    return list(db.accessories.find({}, {"_id": 0, "name": 1, "quantity": 1, "uom": 1}))

def get_acc_names():
    return sorted(db.accessories.distinct("name"))

# ==========================================
# 5. PRODUCTION (SIMPLIFIED)
# ==========================================
def get_next_lot_no():
    last = db.lots.find_one(sort=[("date_created", -1)])
    if not last: return "LOT001"
    try:
        num = int(re.search(r'\d+', last['lot_no']).group()) + 1
        return f"LOT{num:03d}"
    except:
        return "LOT001"

def create_lot(lot_no, item, code, color, size_brk, rolls):
    total = sum(size_brk.values())
    db.lots.insert_one({
        "lot_no": lot_no, "item_name": item, "item_code": code, "color": color,
        "total_qty": total, "size_breakdown": size_brk,
        "current_stage_stock": {"Cutting": size_brk}, "status": "Active",
        "consumed_rolls": rolls, "date_created": datetime.datetime.now()
    })
    if rolls: db.fabric_rolls.update_many({"_id": {"$in": rolls}}, {"$set": {"status": "Consumed"}})
    return True

def move_lot(lot_no, from_s, to_s, karigar, qty, size):
    db.transactions.insert_one({
        "lot_no": lot_no, "from": from_s, "to": to_s, "karigar": karigar,
        "qty": qty, "size": size, "timestamp": datetime.datetime.now()
    })
    db.lots.update_one({"lot_no": lot_no}, {
        "$inc": {f"current_stage_stock.{from_s}.{size}": -qty, f"current_stage_stock.{to_s}.{size}": qty}
    })

# ==========================================
# 6. DATA FETCHERS & MASTERS
# ==========================================
def get_supplier_names(): return sorted(db.suppliers.distinct("name"))
def get_item_names(): return sorted(db.items.distinct("item_name"))
def get_active_lots(): return [l['lot_no'] for l in db.lots.find({"status": "Active"})]
def get_lot_info(lot): return db.lots.find_one({"lot_no": lot})
def get_materials(): return sorted(db.materials.distinct("name"))
def get_colors(): return sorted(db.colors.distinct("name"))
def get_staff(role): return [s['name'] for s in db.staff.find({"role": role})]

def add_supplier(n, g, c, a): db.suppliers.insert_one({"name":n,"gst":g,"contact":c,"address":a})

# UPDATED: Added color and fabrics list
def add_item(n, c, col, fabs): 
    db.items.insert_one({
        "item_name": n, 
        "item_code": c, 
        "color": col, 
        "fabrics": fabs,
        "date_added": datetime.datetime.now()
    })

def add_fabric(n): db.materials.insert_one({"name":n})
def add_staff(n, r): db.staff.insert_one({"name":n,"role":r})

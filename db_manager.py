import streamlit as st
import pymongo
import pandas as pd
import datetime
import re
from bson.objectid import ObjectId
import io

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
# 1. CATALOG & LISTING GENERATOR (NEW)
# ==========================================
def add_catalog_product(sku, name, category, fabric, color, size, mrp, sp, hsn, stock):
    db.catalog.update_one(
        {"sku": sku},
        {"$set": {
            "name": name, "category": category, "fabric": fabric, "color": color, 
            "size": size, "mrp": float(mrp), "selling_price": float(sp), 
            "hsn": hsn, "stock": int(stock), "last_updated": datetime.datetime.now()
        }},
        upsert=True
    )

def bulk_upload_catalog(df):
    """Expects standard columns in DF and saves to DB"""
    # Normalize headers to lowercase for safer matching
    df.columns = [c.lower().strip() for c in df.columns]
    
    count = 0
    for _, row in df.iterrows():
        # flexible column matching
        sku = row.get('sku') or row.get('item code') or row.get('design no')
        if sku:
            db.catalog.update_one(
                {"sku": str(sku)},
                {"$set": {
                    "name": row.get('name') or row.get('title') or "",
                    "category": row.get('category') or "Apparel",
                    "fabric": row.get('fabric') or "",
                    "color": row.get('color') or "",
                    "size": row.get('size') or "",
                    "mrp": float(row.get('mrp', 0)),
                    "selling_price": float(row.get('selling price', 0) or row.get('sp', 0)),
                    "hsn": str(row.get('hsn', '')),
                    "stock": int(row.get('stock', 0) or row.get('qty', 0)),
                    "last_updated": datetime.datetime.now()
                }},
                upsert=True
            )
            count += 1
    return count

def get_catalog_df():
    return pd.DataFrame(list(db.catalog.find({}, {"_id": 0})))

def generate_marketplace_file(platform):
    """
    Transforms the Master Catalog into Platform Specific CSV formats.
    """
    catalog = list(db.catalog.find({}, {"_id": 0}))
    if not catalog: return None
    
    df = pd.DataFrame(catalog)
    
    if platform == "Amazon":
        # Amazon Template Logic
        export_df = pd.DataFrame()
        export_df['item_sku'] = df['sku']
        export_df['item_name'] = df['name']
        export_df['external_product_id'] = "" # GTIN
        export_df['external_product_id_type'] = "EAN"
        export_df['brand_name'] = "Shine Arc"
        export_df['standard_price'] = df['selling_price']
        export_df['quantity'] = df['stock']
        export_df['main_image_url'] = ""
        export_df['other_image_url1'] = ""
        
    elif platform == "Flipkart":
        # Flipkart Template Logic
        export_df = pd.DataFrame()
        export_df['Seller_SKU'] = df['sku']
        export_df['Listing_Status'] = "Active"
        export_df['MRP'] = df['mrp']
        export_df['Your_Selling_Price'] = df['selling_price']
        export_df['Procurement_SLA'] = 2
        export_df['Stock'] = df['stock']
        export_df['HSN'] = df['hsn']
        export_df['Tax_Code'] = "GST_12" # Assumption
        
    elif platform == "Meesho":
        # Meesho Template Logic
        export_df = pd.DataFrame()
        export_df['Style ID'] = df['sku']
        export_df['Product Name'] = df['name']
        export_df['Category'] = df['category']
        export_df['MRP'] = df['mrp']
        export_df['Meesho Price'] = df['selling_price']
        export_df['Wrong/Defective Return Price'] = df['selling_price'] * 0.9 # Slightly lower
        export_df['Size'] = df['size']
        export_df['Inventory'] = df['stock']
        export_df['HSN Code'] = df['hsn']
        export_df['GST Percentage'] = 12

    elif platform == "Myntra":
        export_df = pd.DataFrame()
        export_df['Supplier SKU'] = df['sku']
        export_df['Brand'] = "Shine Arc"
        export_df['Article Type'] = df['category']
        export_df['Gender'] = "Women"
        export_df['Base Colour'] = df['color']
        export_df['Size'] = df['size']
        export_df['MRP'] = df['mrp']
        
    elif platform == "Ajio":
        export_df = pd.DataFrame()
        export_df['Seller SKU'] = df['sku']
        export_df['EAN/UPC'] = ""
        export_df['Model'] = df['name']
        export_df['Brand'] = "Shine Arc"
        export_df['Color'] = df['color']
        export_df['Size'] = df['size']
        export_df['MRP'] = df['mrp']
        export_df['Selling Price'] = df['selling_price']

    else:
        return df # Raw dump if no platform matched

    return export_df

# ==========================================
# 2. SMART WORKFLOWS
# ==========================================
def process_smart_purchase(data):
    try:
        # Save Bill
        db.supplier_ledger.insert_one({
            "supplier": data['supplier'],
            "date": pd.to_datetime(data['date']),
            "type": "Bill",
            "amount": data['grand_total'],
            "reference": data['bill_no'],
            "remarks": f"Smart Entry | Stock: {data['stock_type']}",
            "items": data['items'],
            "created_at": datetime.datetime.now()
        })

        # Save Stock (Fabric)
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

        # Save Stock (Accessories)
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

        # Save Payment
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
# 3. BASIC HELPERS
# ==========================================
def generate_payment_id(prefix="PAY"):
    today = datetime.datetime.now().strftime("%Y%m%d")
    start_of_day = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    count = db.supplier_ledger.count_documents({"type": {"$in": ["Payment", "Debit Note"]}, "created_at": {"$gte": start_of_day}})
    return f"{prefix}-{today}-{count+1:03d}"

def get_dashboard_stats():
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    present = db.attendance.count_documents({"date": today, "in_time": {"$ne": None}})
    return {
        "active_lots": db.lots.count_documents({"status": "Active"}),
        "rolls": db.fabric_rolls.count_documents({"status": "Available"}),
        "staff_present": present
    }

# ==========================================
# 4. LEDGER
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
# 5. INVENTORY & PRODUCTION
# ==========================================
def get_all_fabric_stock_summary():
    return list(db.fabric_rolls.aggregate([
        {"$match": {"status": "Available"}},
        {"$group": {"_id": {"name": "$fabric_name", "color": "$color"}, "total_qty": {"$sum": "$quantity"}}}
    ]))

def add_fabric_rolls_batch(fabric_name, color, rolls_data, uom, supplier, bill_no):
    batch_id = datetime.datetime.now().strftime("%Y%m%d%H%M")
    docs = []
    for i, q in enumerate(rolls_data):
        docs.append({
            "fabric_name": fabric_name, "color": color, "batch_id": batch_id, "roll_no": f"{batch_id}-{i+1}", 
            "quantity": float(q), "uom": uom, "supplier": supplier, "bill_no": bill_no, 
            "status": "Available", "date_added": datetime.datetime.now()
        })
    if docs: db.fabric_rolls.insert_many(docs)

def update_accessory_stock(name, txn_type, qty, uom):
    change = float(qty) if txn_type == "Inward" else -float(qty)
    db.accessories.update_one({"name": name}, {"$inc": {"quantity": change}, "$set": {"uom": uom}}, upsert=True)

def get_accessory_stock(): return list(db.accessories.find({}, {"_id": 0, "name": 1, "quantity": 1, "uom": 1}))

def get_next_lot_no():
    last = db.lots.find_one(sort=[("date_created", -1)])
    if not last: return "LOT001"
    try: return f"LOT{int(re.search(r'\d+', last['lot_no']).group()) + 1:03d}"
    except: return "LOT001"

def create_lot(lot_no, item, code, color, size_brk, rolls, cm):
    total = sum(size_brk.values())
    db.lots.insert_one({
        "lot_no": lot_no, "item_name": item, "item_code": code, "color": color,
        "total_qty": total, "size_breakdown": size_brk,
        "current_stage_stock": {"Cutting": size_brk}, "status": "Active",
        "created_by": cm, "consumed_rolls": rolls, "date_created": datetime.datetime.now()
    })
    if rolls: db.fabric_rolls.update_many({"_id": {"$in": rolls}}, {"$set": {"status": "Consumed"}})

def move_lot(lot_no, from_s, to_s, karigar, qty, size):
    db.transactions.insert_one({
        "lot_no": lot_no, "from_stage": from_s, "to_stage": to_s, "karigar": karigar,
        "qty": qty, "variant": size, "timestamp": datetime.datetime.now()
    })
    db.lots.update_one({"lot_no": lot_no}, {
        "$inc": {f"current_stage_stock.{from_s}.{size}": -qty, f"current_stage_stock.{to_s}.{size}": qty}
    })

def get_lot_transactions(lot_no): return list(db.transactions.find({"lot_no": lot_no}).sort("timestamp", -1))

# ==========================================
# 6. HR & MASTERS
# ==========================================
def add_piece_rate(item, process, rate):
    db.rates.update_one({"item": item, "process": process}, {"$set": {"rate": float(rate)}}, upsert=True)

def get_rate_master_df():
    return pd.DataFrame(list(db.rates.find({}, {"_id": 0, "item": 1, "process": 1, "rate": 1})))

def mark_attendance(staff_name, action):
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    now_time = datetime.datetime.now().strftime("%H:%M")
    if action == "In": db.attendance.update_one({"staff": staff_name, "date": today}, {"$set": {"in_time": now_time, "status": "Present"}}, upsert=True)
    elif action == "Out": db.attendance.update_one({"staff": staff_name, "date": today}, {"$set": {"out_time": now_time}})

def get_today_attendance():
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return list(db.attendance.find({"date": today}))

def get_staff_payout(month, year):
    start = datetime.datetime(year, month, 1)
    if month == 12: end = datetime.datetime(year + 1, 1, 1)
    else: end = datetime.datetime(year, month + 1, 1)
    
    prod_data = list(db.transactions.aggregate([
        {"$match": {"timestamp": {"$gte": start, "$lt": end}}},
        {"$group": {"_id": {"karigar": "$karigar", "lot": "$lot_no", "stage": "$to_stage"}, "total_qty": {"$sum": "$qty"}}}
    ]))
    
    report = []
    for p in prod_data:
        k = p['_id']['karigar']; lot = p['_id']['lot']; stage_raw = p['_id']['stage'].split(' - ')[0]; qty = p['total_qty']
        l_info = db.lots.find_one({"lot_no": lot}); item = l_info['item_name'] if l_info else "Unknown"
        r_doc = db.rates.find_one({"item": item, "process": stage_raw}); rate = r_doc['rate'] if r_doc else 0.0
        earning = qty * rate
        report.append({"Staff": k, "Item": item, "Process": stage_raw, "Qty": qty, "Rate": rate, "Total Pay": earning})
    return pd.DataFrame(report)

# FETCHERS
def get_supplier_names(): return sorted(db.suppliers.distinct("name"))
def get_item_names(): return sorted(db.items.distinct("item_name"))
def get_codes_by_item_name(item_name): return sorted(db.items.distinct("item_code", {"item_name": item_name}))
def get_colors_by_item_code(item_code): return sorted(db.items.distinct("color", {"item_code": item_code}))
def get_item_details_by_code(code): return db.items.find_one({"item_code": code})
def get_materials(): return sorted(db.materials.distinct("name"))
def get_colors(): return sorted(db.colors.distinct("name"))
def get_staff(role): return [s['name'] for s in db.staff.find({"role": role})]
def get_all_staff_names(): return sorted(db.staff.distinct("name"))
def get_all_processes(): return sorted(db.processes.distinct("name"))
def get_sizes(): return sorted(db.sizes.distinct("name"))
def get_acc_names(): return sorted(db.accessories.distinct("name"))
def get_active_lots(): return [l['lot_no'] for l in db.lots.find({"status": "Active"})]
def get_all_lot_numbers(): return [l['lot_no'] for l in db.lots.find({}, {"lot_no": 1})]
def get_lot_info(lot): return db.lots.find_one({"lot_no": lot})
def get_available_rolls(name, color): return list(db.fabric_rolls.find({"fabric_name": name, "color": color, "status": "Available"}))

def get_suppliers_df(): return pd.DataFrame(list(db.suppliers.find({}, {"_id": 0, "name": 1, "gst": 1, "contact": 1})))
def get_items_df(): return pd.DataFrame(list(db.items.find({}, {"_id": 0, "item_name": 1, "item_code": 1, "color": 1})))
def get_staff_df(): return pd.DataFrame(list(db.staff.find({}, {"_id": 0, "name": 1, "role": 1})))
def get_fabrics_df(): return pd.DataFrame(list(db.materials.find({}, {"_id": 0, "name": 1})))
def get_colors_df(): return pd.DataFrame(list(db.colors.find({}, {"_id": 0, "name": 1})))
def get_processes_df(): return pd.DataFrame(list(db.processes.find({}, {"_id": 0, "name": 1})))
def get_sizes_df(): return pd.DataFrame(list(db.sizes.find({}, {"_id": 0, "name": 1})))

def add_supplier(n, g, c, a): db.suppliers.insert_one({"name":n,"gst":g,"contact":c,"address":a})
def add_item(n, c, col, fabs): db.items.insert_one({"item_name":n, "item_code":c, "color":col, "fabrics":fabs})
def add_fabric(n): db.materials.insert_one({"name":n})
def add_color(n): db.colors.insert_one({"name":n})
def add_staff(n, r): db.staff.insert_one({"name":n,"role":r})
def add_process(n): db.processes.insert_one({"name":n})
def add_size(n): db.sizes.insert_one({"name":n})

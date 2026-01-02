import streamlit as st
import pymongo
import pandas as pd
import datetime
import re
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
    return client['shine_arc_mes_db']

db = get_db()

# ==========================================
# 1. BULK UPLOAD HANDLERS (NEW)
# ==========================================
def bulk_add_items(df):
    """Expects: Item Name, Code, Color, Fabrics (comma sep)"""
    success = 0; errors = 0
    for _, row in df.iterrows():
        try:
            name = str(row.get('Item Name', '')).strip()
            code = str(row.get('Code', '')).strip()
            color = str(row.get('Color', '')).strip()
            fabs = str(row.get('Fabrics', '')).split(',')
            
            if name and code:
                if not db.items.find_one({"item_code": code}):
                    db.items.insert_one({
                        "item_name": name, "item_code": code, "item_color": color,
                        "required_fabrics": [f.strip() for f in fabs if f.strip()],
                        "date_added": datetime.datetime.now()
                    })
                    success += 1
                else: errors += 1 # Duplicate
        except: errors += 1
    return success, errors

def bulk_add_staff(df):
    """Expects: Name, Role"""
    success = 0
    for _, row in df.iterrows():
        name = str(row.get('Name', '')).strip()
        role = str(row.get('Role', 'Helper')).strip()
        if name:
            db.staff.insert_one({"name": name, "role": role, "date_added": datetime.datetime.now()})
            success += 1
    return success

def bulk_add_fabric_rolls(df):
    """Expects: Fabric Name, Color, Quantity, UOM, Supplier, Bill No"""
    count = 0
    batch_id = datetime.datetime.now().strftime("%Y%m%d%H%M")
    docs = []
    
    for i, row in df.iterrows():
        qty = float(row.get('Quantity', 0))
        if qty > 0:
            docs.append({
                "fabric_name": str(row.get('Fabric Name', 'Unknown')),
                "color": str(row.get('Color', 'Mix')),
                "batch_id": batch_id,
                "roll_no": f"{batch_id}-{i+1}",
                "quantity": qty,
                "uom": str(row.get('UOM', 'Kg')),
                "supplier": str(row.get('Supplier', '')),
                "bill_no": str(row.get('Bill No', '')),
                "status": "Available",
                "date_added": datetime.datetime.now()
            })
            count += 1
    
    if docs: db.fabric_rolls.insert_many(docs)
    return count

def bulk_add_supplier_txns(df):
    """Expects: Supplier, Date, Type, Amount, Reference, Remarks"""
    count = 0
    for _, row in df.iterrows():
        sup = str(row.get('Supplier', '')).strip()
        amt = float(row.get('Amount', 0))
        if sup and amt > 0:
            db.supplier_ledger.insert_one({
                "supplier": sup,
                "date": pd.to_datetime(row.get('Date', datetime.datetime.now())),
                "type": str(row.get('Type', 'Bill')), # Bill or Payment
                "amount": amt,
                "reference": str(row.get('Reference', '')),
                "remarks": str(row.get('Remarks', 'Bulk Upload')),
                "created_at": datetime.datetime.now()
            })
            count += 1
    return count

# ==========================================
# 2. DASHBOARD
# ==========================================
def get_dashboard_stats():
    active = db.lots.count_documents({"status": "Active"})
    completed = db.lots.count_documents({"status": "Completed"})
    total_rolls = db.fabric_rolls.count_documents({"status": "Available"})
    total_accessories = db.accessories.count_documents({"quantity": {"$gt": 0}})
    
    pending_lots = list(db.lots.find(
        {"status": "Active"}, 
        {"_id": 0, "lot_no": 1, "item_name": 1, "total_qty": 1, "color": 1, "date_created": 1}
    ))
    
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
# 3. SUPPLIER LEDGER
# ==========================================
def add_supplier(name, gst="", contact="", address=""):
    if not db.suppliers.find_one({"name": name}):
        db.suppliers.insert_one({
            "name": name, "gst": gst, "contact": contact, "address": address,
            "date_added": datetime.datetime.now()
        })
        return True
    return False

def get_supplier_names():
    return [s['name'] for s in db.suppliers.find().sort("name")]

def get_supplier_details_df():
    return pd.DataFrame(list(db.suppliers.find({}, {"_id": 0, "name": 1, "gst": 1, "contact": 1, "address": 1})))

def generate_payment_id():
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    start_of_day = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    count = db.supplier_ledger.count_documents({"type": "Payment", "created_at": {"$gte": start_of_day}})
    return f"PAY-{today_str}-{count+1:03d}"

def add_supplier_txn(supplier, txn_date, txn_type, amount, ref, remark, attachment_name=None, items=None):
    final_ref = ref
    if txn_type == "Payment" and not final_ref:
        final_ref = generate_payment_id()

    doc = {
        "supplier": supplier,
        "date": pd.to_datetime(txn_date),
        "type": txn_type,
        "amount": float(amount),
        "reference": final_ref,
        "remarks": remark,
        "attachment": attachment_name, 
        "created_at": datetime.datetime.now()
    }
    if items: doc["items"] = items
    db.supplier_ledger.insert_one(doc)
    return final_ref

def get_supplier_ledger(supplier_name):
    txns = list(db.supplier_ledger.find({"supplier": supplier_name}).sort("date", 1))
    if not txns: return pd.DataFrame()
    
    data = []
    balance = 0.0
    for t in txns:
        credit = t['amount'] if t['type'] == 'Bill' else 0
        debit = t['amount'] if t['type'] == 'Payment' else 0
        balance += (credit - debit)
        
        data.append({
            "ID": str(t['_id']),
            "Date": t['date'].strftime("%Y-%m-%d"),
            "Type": t['type'],
            "Reference": t.get('reference', '-'),
            "Debit (Paid)": debit,
            "Credit (Bill)": credit,
            "Balance": balance,
            "Remarks": t.get('remarks', ''),
            "Attachment": t.get('attachment', 'No')
        })
    return pd.DataFrame(data)

def get_supplier_summary(supplier_name):
    pipeline = [
        {"$match": {"supplier": supplier_name}},
        {"$group": {
            "_id": {"date": "$date"},
            "total_bill": {"$sum": {"$cond": [{"$eq": ["$type", "Bill"]}, "$amount", 0]}},
            "total_paid": {"$sum": {"$cond": [{"$eq": ["$type", "Payment"]}, "$amount", 0]}}
        }},
        {"$sort": {"_id.date": 1}}
    ]
    summary = list(db.supplier_ledger.aggregate(pipeline))
    
    data = []
    running_bal = 0.0
    for s in summary:
        bill = s['total_bill']
        paid = s['total_paid']
        running_bal += (bill - paid)
        data.append({
            "Date": s['_id']['date'].strftime("%Y-%m-%d"),
            "Total Purchase": bill,
            "Total Payment": paid,
            "Closing Balance": running_bal
        })
    return pd.DataFrame(data)

def delete_supplier_txn(txn_id):
    try: db.supplier_ledger.delete_one({"_id": ObjectId(txn_id)}); return True
    except: return False

def update_supplier_txn(txn_id, date, amount, ref, remark):
    try:
        db.supplier_ledger.update_one({"_id": ObjectId(txn_id)}, {"$set": {"date": pd.to_datetime(date), "amount": float(amount), "reference": ref, "remarks": remark}})
        return True
    except: return False

# ==========================================
# 4. BOM (BILL OF MATERIALS)
# ==========================================
def create_bom(item_name, components, notes=""):
    if db.boms.find_one({"item_name": item_name}): return False, "Exists"
    db.boms.insert_one({
        "item_name": item_name, "components": components, "notes": notes,
        "created_at": datetime.datetime.now()
    })
    return True, "Created"

def get_all_boms(): return pd.DataFrame(list(db.boms.find({}, {"_id": 0}).sort("item_name", 1)))
def delete_bom(item_name): db.boms.delete_one({"item_name": item_name}); return True

# ==========================================
# 5. MCPL & INVENTORY
# ==========================================
def mcpl_add_product(sku, name, category, base_price, image_url=""):
    if db.mcpl_products.find_one({"sku": sku}): return False, "SKU Exists"
    db.mcpl_products.insert_one({"sku": sku, "name": name, "category": category, "base_price": float(base_price), "image_url": image_url, "channel_prices": {}, "status": "Draft", "created_at": datetime.datetime.now()})
    return True, "Added"

def mcpl_bulk_upload(df):
    count = 0; errors = 0
    for _, row in df.iterrows():
        sku = str(row.get('SKU', '')).strip()
        if sku:
            db.mcpl_products.update_one({"sku": sku}, {"$set": {"name": row.get('Name',''), "category": row.get('Category',''), "base_price": float(row.get('Price',0)), "image_url": row.get('Image URL', ''), "last_updated": datetime.datetime.now()}}, upsert=True)
            count += 1
        else: errors += 1
    return count, errors

def mcpl_update_channel_price(sku, channel, price):
    db.mcpl_products.update_one({"sku": sku}, {"$set": {f"channel_prices.{channel}": float(price)}})

def get_mcpl_catalog(): return pd.DataFrame(list(db.mcpl_products.find({}, {"_id": 0})))

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

def get_available_rolls(name, color): return list(db.fabric_rolls.find({"fabric_name": name, "color": color, "status": "Available"}))

def get_all_fabric_stock_summary():
    return list(db.fabric_rolls.aggregate([{"$match": {"status": "Available"}}, {"$group": {"_id": {"name": "$fabric_name", "color": "$color", "uom": "$uom"}, "total_rolls": {"$sum": 1}, "total_qty": {"$sum": "$quantity"}}}]))

def update_accessory_stock(name, txn_type, qty, uom, remarks=""):
    db.accessory_logs.insert_one({"name": name, "type": txn_type, "qty": float(qty), "uom": uom, "remarks": remarks, "date": datetime.datetime.now()})
    change = float(qty) if txn_type == "Inward" else -float(qty)
    db.accessories.update_one({"name": name}, {"$inc": {"quantity": change}, "$set": {"uom": uom, "last_updated": datetime.datetime.now()}}, upsert=True)
    return True

def get_accessory_stock(): return list(db.accessories.find())
def get_accessory_names(): return [a['name'] for a in list(db.accessories.find({}, {"name": 1}))]

# ==========================================
# 6. MASTERS & PRODUCTION
# ==========================================
def add_item_master(name, code, color, fabrics_list):
    if db.items.find_one({"item_code": code}): return False, "Exists!"
    valid = [f for f in fabrics_list if f and f.strip()!=""]
    db.items.insert_one({"item_name": name, "item_code": code, "item_color": color, "required_fabrics": valid, "date_added": datetime.datetime.now()})
    return True, "Added"

def get_all_items(): return pd.DataFrame(list(db.items.find()))
def get_unique_item_names(): return sorted(list(db.items.distinct("item_name")))
def get_codes_by_item_name(name): return [i['item_code'] for i in db.items.find({"item_name": name}, {"item_code": 1})]
def get_item_details_by_code(code): return db.items.find_one({"item_code": code})
def add_process(name): 
    if not db.processes.find_one({"name": name}): db.processes.insert_one({"name": name})
def get_all_processes(): p = list(db.processes.find({}, {"name": 1})); return [x['name'] for x in p] if p else ["Singer", "Overlock"]
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
# 7. LOT LOGIC
# ==========================================
def get_next_lot_no():
    last = db.lots.find_one(sort=[("date_created", -1)])
    if not last: return "DRCLOT001"
    match = re.search(r'(\d+)$', last['lot_no'])
    return f"DRCLOT{int(match.group(1)) + 1:03d}" if match else "DRCLOT001"

def create_lot(lot_data, all_selected_roll_ids):
    total = sum(int(q) for q in lot_data['size_breakdown'].values())
    lot_doc = {
        "lot_no": lot_data['lot_no'], "item_name": lot_data['item_name'], "item_code": lot_data['item_code'],
        "color": lot_data['color'], "created_by": lot_data['created_by'], "fabrics_consumed": lot_data.get('fabrics_consumed', []),
        "total_fabric_weight": lot_data.get('total_fabric_weight', 0), "date_created": datetime.datetime.now(), "total_qty": total,
        "size_breakdown": lot_data['size_breakdown'], "current_stage_stock": {f"Cutting - {lot_data['created_by']}": lot_data['size_breakdown']}, "status": "Active"
    }
    try:
        db.lots.insert_one(lot_doc)
        if all_selected_roll_ids: db.fabric_rolls.update_many({"_id": {"$in": all_selected_roll_ids}}, {"$set": {"status": "Consumed", "used_in_lot": lot_data['lot_no']}})
        return True, "Created"
    except pymongo.errors.DuplicateKeyError: return False, "Exists"

def get_active_lots(): return list(db.lots.find({"status": "Active"}))
def get_lot_details(lot_no): return db.lots.find_one({"lot_no": lot_no})
def get_all_lot_numbers(): return [l['lot_no'] for l in db.lots.find({}, {"lot_no": 1})]

def move_lot_stage(tx_data):
    db.transactions.insert_one({
        "lot_no": tx_data['lot_no'], "from_stage": tx_data['from_stage'], "to_stage": tx_data['to_stage_key'],
        "karigar": tx_data['karigar'], "machine": tx_data.get('machine', 'N/A'), "variant": tx_data['size_key'], "qty": int(tx_data['qty']), "timestamp": datetime.datetime.now()
    })
    db.lots.update_one({"lot_no": tx_data['lot_no']}, {"$inc": {f"current_stage_stock.{tx_data['from_stage']}.{tx_data['size_key']}": -int(tx_data['qty'])}})
    db.lots.update_one({"lot_no": tx_data['lot_no']}, {"$inc": {f"current_stage_stock.{tx_data['to_stage_key']}.{tx_data['size_key']}": int(tx_data['qty'])}})
    return True

# ==========================================
# 8. HELPERS
# ==========================================
def add_piece_rate(i, c, m, r, d): db.rates.insert_one({"item_name": i, "item_code": c, "machine": m, "rate": float(r), "valid_from": pd.to_datetime(d)})
def get_rate_master(): return pd.DataFrame(list(db.rates.find()))
def get_applicable_rate(i, m): r = db.rates.find_one({"item_name": i, "machine": m}, sort=[("valid_from", -1)]); return r['rate'] if r else 0.0

def get_staff_productivity(month, year):
    start, end = datetime.datetime(year, month, 1), datetime.datetime(year + 1 if month==12 else year, 1 if month==12 else month+1, 1)
    data = list(db.transactions.aggregate([{"$match": {"timestamp": {"$gte": start, "$lt": end}, "karigar": {"$ne": None}}}, {"$lookup": {"from": "lots", "localField": "lot_no", "foreignField": "lot_no", "as": "lot"}}, {"$unwind": "$lot"}, {"$group": {"_id": {"s": "$karigar", "i": "$lot.item_name", "p": "$machine"}, "qty": {"$sum": "$qty"}}}]))
    att_map = {x['_id']: x for x in list(db.attendance.aggregate([{"$match": {"date": {"$gte": start, "$lt": end}}}, {"$group": {"_id": "$staff_name", "days": {"$sum": 1}, "hours": {"$sum": "$hours_worked"}}}]))}
    report = []
    for row in data:
        rate = get_applicable_rate(row['_id']['i'], row['_id']['p'])
        ad = att_map.get(row['_id']['s'], {"days": 0, "hours": 0})
        report.append({"Staff": row['_id']['s'], "Process": row['_id']['p'], "Item": row['_id']['i'], "Qty": row['qty'], "Rate": rate, "Earnings": row['qty'] * rate, "Days Present": ad['days']})
    return pd.DataFrame(report)

def mark_attendance(staff_name, date, in_time, out_time, status, remarks):
    hours = 0.0
    if in_time and out_time:
        d = datetime.date(2000, 1, 1)
        hours = (datetime.datetime.combine(d, out_time) - datetime.datetime.combine(d, in_time)).total_seconds() / 3600
    db.attendance.update_one({"staff_name": staff_name, "date": pd.to_datetime(date)}, {"$set": {"in_time": str(in_time), "out_time": str(out_time), "hours_worked": round(hours, 2), "status": status, "remarks": remarks}}, upsert=True)

def get_attendance_records(date=None):
    q = {"date": {"$gte": pd.to_datetime(date), "$lt": pd.to_datetime(date) + datetime.timedelta(days=1)}} if date else {}
    return list(db.attendance.find(q).sort("date", -1))

def get_stages_for_item(i): return ["Stitching", "Washing", "Finishing", "Packing", "Outsource"]
def clean_database(): 
    for c in db.list_collection_names(): db[c].drop()
    return True

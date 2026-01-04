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
# 1. DATA CLEANING HELPERS (PREVENTS CRASHES)
# ==========================================
def safe_float(val):
    """Safely converts string/object to float. Handles '12%', '1,000', empty strings."""
    try:
        if pd.isna(val) or str(val).strip() == "":
            return 0.0
        # Remove % and , and currency symbols
        clean_val = str(val).replace("%", "").replace(",", "").replace("₹", "").strip()
        return float(clean_val)
    except:
        return 0.0

def safe_int(val):
    """Safely converts string/object to int."""
    try:
        if pd.isna(val) or str(val).strip() == "":
            return 0
        clean_val = str(val).replace(",", "").split(".")[0].strip()
        return int(clean_val)
    except:
        return 0

# ==========================================
# 2. CATALOG & SMART UPLOAD
# ==========================================
def get_next_drc_number():
    last_prod = db.catalog.find_one(sort=[("sort_index", -1)])
    if not last_prod: return 101
    try:
        last_group = last_prod.get('group_id', '')
        if last_group.startswith('DRC'):
            return int(last_group.replace('DRC', '')) + 1
        return 101
    except: return 101

def bulk_upload_catalog(df):
    """Smart Uploader with robustness against bad data."""
    # Clean headers: lowercase, strip spaces, replace space/dot with underscore
    df.columns = [str(c).strip().lower().replace(" ", "_").replace(".", "").replace("%", "") for c in df.columns]
    
    current_num = get_next_drc_number()
    processed_count = 0
    
    for _, row in df.iterrows():
        group_id = f"DRC{current_num}"
        
        # Handle Variations (Size Exploder)
        raw_vars = str(row.get('variation', '')).split(',')
        variations = [v.strip() for v in raw_vars if v.strip()]
        if not variations: variations = ["Free"]
            
        for size in variations:
            sku = f"{group_id}-{size}"
            
            # SAFE DATA EXTRACTION
            product_doc = {
                "sku": sku,
                "group_id": group_id,
                "sort_index": current_num,
                
                # Core Info
                "product_name": str(row.get('product_name', '')),
                "variation": size,
                "color": str(row.get('color', '')),
                "fabric": str(row.get('fabric', '')),
                "category": str(row.get('categories', 'Apparel')),
                "brand_name": str(row.get('brand_name', 'Shine Arc')),
                
                # Financials (Using Safe Helpers)
                "mrp": safe_float(row.get('mrp')),
                "selling_price": safe_float(row.get('selling_price')),
                "gst_rate": safe_float(row.get('gst_rate')), # Matches cleaned header 'gst_rate'
                "hsn": str(row.get('hsn', '')),
                "stock": safe_int(row.get('stock')),
                
                # Attributes
                "product_weight": str(row.get('product_weight', '')),
                "ideal_for": str(row.get('ideal_for', '')),
                "kids_weight": str(row.get('kids_weight', '')),
                "description": str(row.get('product_description', '')),
                "length": str(row.get('length', '')),
                "fit_type": str(row.get('fit_type', '')),
                "neck_type": str(row.get('neck_type', '')),
                "occasion": str(row.get('occasion', '')),
                "pattern": str(row.get('pattern', '')),
                "sleeve_length": str(row.get('sleeve_length', '')),
                "pack_of": str(row.get('pack_of', '1')),
                
                # Images
                "image_link_1": str(row.get('image_link_1', '')) if pd.notnull(row.get('image_link_1')) else '',
                "image_link_2": str(row.get('image_link_2', '')) if pd.notnull(row.get('image_link_2')) else '',
                "image_link_3": str(row.get('image_link_3', '')) if pd.notnull(row.get('image_link_3')) else '',
                "image_link_4": str(row.get('image_link_4', '')) if pd.notnull(row.get('image_link_4')) else '',

                # Fixed Fields
                "country_origin": "India",
                "manufacturer_name": "BnB Industries",
                "manufacturer_address": "Siraspur, Delhi",
                "manufacturer_pincode": "110042",
                
                "last_updated": datetime.datetime.now()
            }
            
            db.catalog.update_one({"sku": sku}, {"$set": product_doc}, upsert=True)
            processed_count += 1
            
        current_num += 1
        
    return processed_count

def add_catalog_product(sku, name, category, fabric, color, size, mrp, sp, hsn, stock, img_link):
    db.catalog.update_one(
        {"sku": sku},
        {"$set": {
            "sku": sku, "product_name": name, "category": category, "fabric": fabric, "color": color, 
            "variation": size, "mrp": float(mrp), "selling_price": float(sp), 
            "hsn": hsn, "stock": int(stock), "image_link_1": img_link,
            "country_origin": "India", "manufacturer_name": "BnB Industries",
            "manufacturer_address": "Siraspur, Delhi", "manufacturer_pincode": "110042",
            "last_updated": datetime.datetime.now()
        }},
        upsert=True
    )

def get_catalog_df():
    data = list(db.catalog.find({}, {"_id": 0}))
    return pd.DataFrame(data) if data else pd.DataFrame()

def generate_marketplace_file(platform):
    catalog = list(db.catalog.find({}, {"_id": 0}))
    if not catalog: return None
    df = pd.DataFrame(catalog)
    cols = ['sku', 'product_name', 'mrp', 'selling_price', 'stock', 'description', 'image_link_1', 'variation', 'group_id', 'color', 'fabric']
    for c in cols:
        if c not in df.columns: df[c] = ""

    if platform == "Amazon":
        export_df = pd.DataFrame()
        export_df['item_sku'] = df['sku']
        export_df['item_name'] = df['product_name']
        export_df['brand_name'] = "Shine Arc"
        export_df['standard_price'] = df['selling_price']
        export_df['quantity'] = df['stock']
        export_df['main_image_url'] = df['image_link_1']
    elif platform == "Flipkart":
        export_df = pd.DataFrame()
        export_df['Seller_SKU'] = df['sku']
        export_df['Group_ID'] = df['group_id']
        export_df['MRP'] = df['mrp']
        export_df['Your_Selling_Price'] = df['selling_price']
        export_df['Stock'] = df['stock']
        export_df['Size'] = df['variation']
        export_df['Color'] = df['color']
        export_df['Main_Img_URL'] = df['image_link_1']
    elif platform == "Meesho":
        export_df = pd.DataFrame()
        export_df['Style ID'] = df['group_id']
        export_df['SKU'] = df['sku']
        export_df['Product Name'] = df['product_name']
        export_df['MRP'] = df['mrp']
        export_df['Meesho Price'] = df['selling_price']
        export_df['Size'] = df['variation']
        export_df['Color'] = df['color']
        export_df['Fabric'] = df['fabric']
    elif platform == "Myntra":
        export_df = pd.DataFrame()
        export_df['Supplier SKU'] = df['sku']
        export_df['Style ID'] = df['group_id']
        export_df['Brand'] = "Shine Arc"
        export_df['MRP'] = df['mrp']
        export_df['Size'] = df['variation']
    elif platform == "Ajio":
        export_df = pd.DataFrame()
        export_df['Seller SKU'] = df['sku']
        export_df['Style Group'] = df['group_id']
        export_df['Brand'] = "Shine Arc"
        export_df['MRP'] = df['mrp']
        export_df['Selling Price'] = df['selling_price']
        export_df['Size'] = df['variation']
    else: return df 
    return export_df

# ==========================================
# 3. SMART WORKFLOWS
# ==========================================
def process_smart_purchase(data):
    try:
        db.supplier_ledger.insert_one({
            "supplier": data['supplier'], "date": pd.to_datetime(data['date']),
            "type": "Bill", "amount": data['grand_total'], "reference": data['bill_no'],
            "remarks": f"Smart Entry | Stock: {data['stock_type']}", "items": data['items'],
            "created_at": datetime.datetime.now()
        })
        if data['stock_type'] == 'Fabric' and data['stock_data']:
            batch_id = datetime.datetime.now().strftime("%Y%m%d%H%M")
            fabric_docs = []
            for i, roll_wt in enumerate(data['stock_data'].get('rolls', [])):
                fabric_docs.append({
                    "fabric_name": data['stock_data']['name'], "color": data['stock_data']['color'],
                    "batch_id": batch_id, "roll_no": f"{batch_id}-{i+1}", "quantity": float(roll_wt),
                    "uom": "Kg", "supplier": data['supplier'], "bill_no": data['bill_no'],
                    "status": "Available", "date_added": datetime.datetime.now()
                })
            if fabric_docs: db.fabric_rolls.insert_many(fabric_docs)
        elif data['stock_type'] == 'Accessory' and data['stock_data']:
            db.accessories.update_one({"name": data['stock_data']['name']}, {"$inc": {"quantity": float(data['stock_data']['qty'])}}, upsert=True)
            db.accessory_logs.insert_one({"name": data['stock_data']['name'], "type": "Inward", "qty": float(data['stock_data']['qty']), "uom": data['stock_data']['uom'], "remarks": f"Bill {data['bill_no']}", "date": datetime.datetime.now()})
        if data['payment'] and data['payment']['amount'] > 0:
            pay_ref = generate_payment_id()
            db.supplier_ledger.insert_one({"supplier": data['supplier'], "date": pd.to_datetime(data['date']), "type": "Payment", "amount": float(data['payment']['amount']), "reference": pay_ref, "remarks": f"Auto-Payment for Bill {data['bill_no']} ({data['payment']['mode']})", "created_at": datetime.datetime.now()})
        return True, "Transaction Successful"
    except Exception as e: return False, str(e)

# ==========================================
# 4. HELPERS
# ==========================================
def generate_payment_id(prefix="PAY"):
    today = datetime.datetime.now().strftime("%Y%m%d")
    count = db.supplier_ledger.count_documents({"type": {"$in": ["Payment", "Debit Note"]}, "created_at": {"$gte": datetime.datetime.now().replace(hour=0,minute=0)}})
    return f"{prefix}-{today}-{count+1:03d}"

def get_dashboard_stats():
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    present = db.attendance.count_documents({"date": today, "in_time": {"$ne": None}})
    return {"active_lots": db.lots.count_documents({"status": "Active"}), "rolls": db.fabric_rolls.count_documents({"status": "Available"}), "staff_present": present}

def get_supplier_ledger(name):
    data = list(db.supplier_ledger.find({"supplier": name}).sort("date", 1)); res = []; bal = 0
    if not data: return pd.DataFrame()
    for row in data:
        cr = row['amount'] if row['type'] == 'Bill' else 0; dr = row['amount'] if row['type'] in ['Payment', 'Debit Note'] else 0; bal += (cr - dr)
        res.append({"ID": str(row['_id']), "Date": row['date'].strftime("%d-%b-%y"), "Type": row['type'], "Ref": row.get('reference', '-'), "Credit": cr, "Debit": dr, "Balance": bal, "Remarks": row.get('remarks', '')})
    return pd.DataFrame(res)

def add_simple_payment(sup, date, amt, mode, note):
    ref = generate_payment_id()
    db.supplier_ledger.insert_one({"supplier": sup, "date": pd.to_datetime(date), "type": "Payment", "amount": amt, "reference": ref, "remarks": f"{mode} - {note}", "created_at": datetime.datetime.now()})

# ==========================================
# 5. INVENTORY & PRODUCTION
# ==========================================
def get_all_fabric_stock_summary(): return list(db.fabric_rolls.aggregate([{"$match": {"status": "Available"}}, {"$group": {"_id": {"name": "$fabric_name", "color": "$color"}, "total_qty": {"$sum": "$quantity"}}}]))
def add_fabric_rolls_batch(fabric_name, color, rolls_data, uom, supplier, bill_no):
    batch_id = datetime.datetime.now().strftime("%Y%m%d%H%M"); docs = [{"fabric_name": fabric_name, "color": color, "batch_id": batch_id, "roll_no": f"{batch_id}-{i+1}", "quantity": float(q), "uom": uom, "supplier": supplier, "bill_no": bill_no, "status": "Available", "date_added": datetime.datetime.now()} for i, q in enumerate(rolls_data)]
    if docs: db.fabric_rolls.insert_many(docs)
def update_accessory_stock(name, txn_type, qty, uom): db.accessories.update_one({"name": name}, {"$inc": {"quantity": float(qty) if txn_type == "Inward" else -float(qty)}, "$set": {"uom": uom}}, upsert=True)
def get_accessory_stock(): return list(db.accessories.find({}, {"_id": 0, "name": 1, "quantity": 1, "uom": 1}))
def get_next_lot_no():
    last = db.lots.find_one(sort=[("date_created", -1)])
    if not last: return "LOT001"
    try: return f"LOT{int(re.search(r'\d+', last['lot_no']).group()) + 1:03d}"
    except: return "LOT001"
def create_lot(lot_no, item, code, color, size_brk, rolls, cm):
    total = sum(size_brk.values()); db.lots.insert_one({"lot_no": lot_no, "item_name": item, "item_code": code, "color": color, "total_qty": total, "size_breakdown": size_brk, "current_stage_stock": {"Cutting": size_brk}, "status": "Active", "created_by": cm, "consumed_rolls": rolls, "date_created": datetime.datetime.now()})
    if rolls: db.fabric_rolls.update_many({"_id": {"$in": rolls}}, {"$set": {"status": "Consumed"}})
def move_lot(lot_no, from_s, to_s, karigar, qty, size):
    db.transactions.insert_one({"lot_no": lot_no, "from_stage": from_s, "to_stage": to_s, "karigar": karigar, "qty": qty, "variant": size, "timestamp": datetime.datetime.now()})
    db.lots.update_one({"lot_no": lot_no}, {"$inc": {f"current_stage_stock.{from_s}.{size}": -qty, f"current_stage_stock.{to_s}.{size}": qty}})
def get_lot_transactions(lot_no): return list(db.transactions.find({"lot_no": lot_no}).sort("timestamp", -1))

# ==========================================
# 6. HR & MASTERS
# ==========================================
def add_piece_rate(item, process, rate): db.rates.update_one({"item": item, "process": process}, {"$set": {"rate": float(rate)}}, upsert=True)
def get_rate_master_df(): return pd.DataFrame(list(db.rates.find({}, {"_id": 0, "item": 1, "process": 1, "rate": 1})))
def mark_attendance(staff_name, action):
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0); now_time = datetime.datetime.now().strftime("%H:%M")
    if action == "In": db.attendance.update_one({"staff": staff_name, "date": today}, {"$set": {"in_time": now_time, "status": "Present"}}, upsert=True)
    elif action == "Out": db.attendance.update_one({"staff": staff_name, "date": today}, {"$set": {"out_time": now_time}})
def get_today_attendance(): return list(db.attendance.find({"date": datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)}))
def get_staff_payout(month, year):
    start = datetime.datetime(year, month, 1); end = datetime.datetime(year + 1, 1, 1) if month == 12 else datetime.datetime(year, month + 1, 1)
    prod_data = list(db.transactions.aggregate([{"$match": {"timestamp": {"$gte": start, "$lt": end}}}, {"$group": {"_id": {"karigar": "$karigar", "lot": "$lot_no", "stage": "$to_stage"}, "total_qty": {"$sum": "$qty"}}}]))
    report = []
    for p in prod_data:
        k = p['_id']['karigar']; lot = p['_id']['lot']; stage_raw = p['_id']['stage'].split(' - ')[0]; qty = p['total_qty']
        l_info = db.lots.find_one({"lot_no": lot}); item = l_info['item_name'] if l_info else "Unknown"
        r_doc = db.rates.find_one({"item": item, "process": stage_raw}); rate = r_doc['rate'] if r_doc else 0.0
        report.append({"Staff": k, "Item": item, "Process": stage_raw, "Qty": qty, "Rate": rate, "Total Pay": qty * rate})
    return pd.DataFrame(report)

# GST
def get_gst_slabs(): 
    slabs = list(db.gst_slabs.find({}, {"_id": 0, "rate": 1}).sort("rate", 1))
    return [s['rate'] for s in slabs] if slabs else [0, 2.5, 3, 5, 12, 18, 28]
def add_gst_slab(rate): db.gst_slabs.update_one({"rate": float(rate)}, {"$set": {"rate": float(rate)}}, upsert=True)
def get_gst_df(): return pd.DataFrame(list(db.gst_slabs.find({}, {"_id": 0, "rate": 1}).sort("rate", 1)))

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

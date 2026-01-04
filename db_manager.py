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
# 1. CATALOG & SMART UPLOAD
# ==========================================

# --- SAFE CONVERSION HELPERS ---
def safe_float(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0.0
        clean_val = str(val).replace("%", "").replace(",", "").replace("₹", "").strip()
        return float(clean_val)
    except: return 0.0

def safe_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        clean_val = str(val).replace(",", "").split(".")[0].strip()
        return int(clean_val)
    except: return 0

def get_next_free_drc_number(reserved_indices=set()):
    """
    Finds the first available gap in the sequence to recycle numbers.
    Ex: If 101, 103 exist, it returns 102.
    """
    # Get all currently used sort_indices from DB
    used_indices = set(db.catalog.distinct("sort_index"))
    
    # Combine with indices reserved during this specific upload session
    all_unavailable = used_indices.union(reserved_indices)
    
    num = 101
    while True:
        if num not in all_unavailable:
            return num
        num += 1

def bulk_upload_catalog(df):
    """
    Smart Uploader with Duplicate Check, Updates, Deletions, and ID Recycling.
    Returns: (success_count, error_df)
    """
    # Clean headers
    df.columns = [str(c).strip().lower().replace(" ", "_").replace(".", "").replace("%", "") for c in df.columns]
    
    success_count = 0
    errors = []
    reserved_ids_this_session = set() # To track IDs generated within this loop
    
    for index, row in df.iterrows():
        action = str(row.get('action', '')).strip().lower()
        
        # Normalize SKU Logic
        csv_sku = str(row.get('sku_code', '')).strip()
        if not csv_sku or csv_sku.lower() == 'nan': csv_sku = None
        
        # Existing Product Check
        existing_doc = None
        if csv_sku:
            existing_doc = db.catalog.find_one({"sku": csv_sku})

        # --- LOGIC BRANCHING ---

        # 1. DELETE ACTION
        if action == 'delete':
            if existing_doc:
                db.catalog.delete_one({"sku": csv_sku})
                success_count += 1
            else:
                errors.append({"Row": index+2, "SKU": csv_sku, "Error": "Cannot Delete: SKU not found"})
            continue

        # 2. UPDATE ACTION
        elif action == 'update':
            if existing_doc:
                # Prepare update payload (Partial Update supported)
                update_fields = {"last_updated": datetime.datetime.now()}
                
                # Only update fields that are not empty in the CSV
                # Map CSV columns to DB keys
                field_map = {
                    'product_name': 'product_name', 'mrp': 'mrp', 'selling_price': 'selling_price',
                    'stock': 'stock', 'image_link_1': 'image_link_1', 'gst_rate': 'gst_rate',
                    'variation': 'variation', 'color': 'color', 'fabric': 'fabric', 'hsn': 'hsn'
                    # Add others as needed, keeping it lightweight for speed
                }
                
                for csv_key, db_key in field_map.items():
                    val = row.get(csv_key)
                    if pd.notnull(val) and str(val).strip() != "":
                        if db_key in ['mrp', 'selling_price', 'gst_rate']:
                            update_fields[db_key] = safe_float(val)
                        elif db_key == 'stock':
                            update_fields[db_key] = safe_int(val)
                        else:
                            update_fields[db_key] = str(val)

                db.catalog.update_one({"sku": csv_sku}, {"$set": update_fields})
                success_count += 1
            else:
                errors.append({"Row": index+2, "SKU": csv_sku, "Error": "Cannot Update: SKU not found"})
            continue

        # 3. NEW UPLOAD (No Action Specified)
        else:
            # Check for Duplicate
            if existing_doc:
                errors.append({"Row": index+2, "SKU": csv_sku, "Error": "Duplicate Product. Use 'Update' in Action column to modify."})
                continue
            
            # --- NEW PRODUCT CREATION LOGIC ---
            
            # Image Check
            img1 = str(row.get('image_link_1', ''))
            if not img1 or img1.lower() == 'nan':
                errors.append({"Row": index+2, "SKU": "New", "Error": "Image Link 1 is Mandatory"})
                continue

            # Generate Group ID (Recycled)
            user_group = str(row.get('group_id', '')).strip()
            
            # If user didn't provide Group ID, we need to generate one
            # We must be careful: If this row belongs to a variation set in the CSV, they need the SAME ID.
            # Ideally, the user provides Group ID. If not, we generate based on recycling.
            
            if user_group and user_group.lower() != 'nan':
                group_id = user_group
                current_sort_index = 0 # Not a primary parent
            else:
                # Get recycled number
                current_sort_index = get_next_free_drc_number(reserved_indices=reserved_ids_this_session)
                group_id = f"DRC{current_sort_index}"
                reserved_ids_this_session.add(current_sort_index)

            # Variations Exploder
            raw_vars = str(row.get('variation', '')).split(',')
            variations = [v.strip() for v in raw_vars if v.strip()]
            if not variations: variations = ["Free"]
            
            for size in variations:
                # SKU Generation
                if csv_sku:
                    final_sku = f"{csv_sku}-{size}" if len(variations) > 1 else csv_sku
                else:
                    final_sku = f"{group_id}-{size}"
                
                # Double check if this specific generated SKU exists (Collision check)
                if db.catalog.find_one({"sku": final_sku}):
                    errors.append({"Row": index+2, "SKU": final_sku, "Error": "Generated SKU already exists"})
                    continue

                product_doc = {
                    "sku": final_sku,
                    "group_id": group_id,
                    "sort_index": current_sort_index,
                    
                    # Core
                    "product_name": str(row.get('product_name', '')),
                    "image_link_1": img1,
                    "image_link_2": str(row.get('image_link_2', '')),
                    "image_link_3": str(row.get('image_link_3', '')),
                    "image_link_4": str(row.get('image_link_4', '')),
                    "color": str(row.get('color', '')),
                    "variation": size,
                    "gst_rate": safe_float(row.get('gst_rate')),
                    "hsn": str(row.get('hsn', '')),
                    "product_weight": str(row.get('product_weight', '')),
                    "fabric": str(row.get('fabric', '')),
                    "category": str(row.get('categories', 'Apparel')),
                    "ideal_for": str(row.get('ideal_for', '')),
                    "kids_weight": str(row.get('kids_weight', '')),
                    "brand_name": str(row.get('brand_name', 'Shine Arc')),
                    
                    # Attributes
                    "description": str(row.get('product_description', '')),
                    "length": str(row.get('length', '')),
                    "fit_type": str(row.get('fit_type', '')),
                    "neck_type": str(row.get('neck_type', '')),
                    "occasion": str(row.get('occasion', '')),
                    "pattern": str(row.get('pattern', '')),
                    "sleeve_length": str(row.get('sleeve_length', '')),
                    "pack_of": str(row.get('pack_of', '1')),
                    
                    # Financials
                    "mrp": safe_float(row.get('mrp')),
                    "selling_price": safe_float(row.get('selling_price')),
                    "stock": safe_int(row.get('stock')),

                    # Fixed
                    "country_origin": "India",
                    "manufacturer_name": "BnB Industries",
                    "manufacturer_address": "Siraspur, Delhi",
                    "manufacturer_pincode": "110042",
                    "last_updated": datetime.datetime.now()
                }
                
                db.catalog.insert_one(product_doc)
                success_count += 1

    return success_count, pd.DataFrame(errors)

def get_catalog_df():
    data = list(db.catalog.find({}, {"_id": 0}))
    return pd.DataFrame(data) if data else pd.DataFrame()

def generate_marketplace_file(platform):
    catalog = list(db.catalog.find({}, {"_id": 0}))
    if not catalog: return None
    df = pd.DataFrame(catalog)
    for col in ['sku', 'product_name', 'mrp', 'selling_price', 'stock']:
        if col not in df.columns: df[col] = ""

    if platform == "Meesho":
        export_df = pd.DataFrame()
        export_df['Image Link 1'] = df.get('image_link_1', '')
        export_df['Image Link 2'] = df.get('image_link_2', '')
        export_df['Image Link 3'] = df.get('image_link_3', '')
        export_df['Image Link 4'] = df.get('image_link_4', '')
        export_df['Sku Code'] = df.get('sku', '')
        export_df['Product Name'] = df.get('product_name', '')
        export_df['Color'] = df.get('color', '')
        export_df['Variation'] = df.get('variation', '')
        export_df['GST Rate'] = df.get('gst_rate', '')
        export_df['HSN'] = df.get('hsn', '')
        export_df['Product Weight'] = df.get('product_weight', '')
        export_df['Fabric'] = df.get('fabric', '')
        export_df['Categories'] = df.get('category', '')
        export_df['Ideal For'] = df.get('ideal_for', '')
        export_df['Kids Weight'] = df.get('kids_weight', '')
        export_df['Brand Name'] = df.get('brand_name', 'Shine Arc')
        export_df['Group Id'] = df.get('group_id', '')
        export_df['Product Description'] = df.get('description', '')
        export_df['Length'] = df.get('length', '')
        export_df['Fit Type'] = df.get('fit_type', '')
        export_df['Neck Type'] = df.get('neck_type', '')
        export_df['Occasion'] = df.get('occasion', '')
        export_df['Pattern'] = df.get('pattern', '')
        export_df['Sleeve Length'] = df.get('sleeve_length', '')
        export_df['Pack Of'] = df.get('pack_of', '')
        export_df['Country Origin'] = "India"
        export_df['Manufacturer Name'] = "BnB Industries"
        export_df['Manufacturer Address'] = "Siraspur, Delhi"
        export_df['Manufacturer Pin Code'] = "110042"
        export_df['MRP'] = df.get('mrp', 0)
        export_df['Selling Price'] = df.get('selling_price', 0)
        
    elif platform == "Flipkart":
        export_df = pd.DataFrame()
        export_df['Seller_SKU'] = df['sku']
        export_df['Group_ID'] = df.get('group_id', '')
        export_df['MRP'] = df['mrp']
        export_df['Your_Selling_Price'] = df['selling_price']
        export_df['Stock'] = df['stock']
        export_df['Main_Img_URL'] = df.get('image_link_1', '')
        
    elif platform == "Amazon":
        export_df = pd.DataFrame()
        export_df['item_sku'] = df['sku']
        export_df['item_name'] = df['product_name']
        export_df['standard_price'] = df['selling_price']
        export_df['quantity'] = df['stock']
        export_df['main_image_url'] = df.get('image_link_1', '')

    else: return df 
    return export_df

# ==========================================
# 2. SMART WORKFLOWS (BILLING & STOCK)
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
# 3. HELPERS
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
# 4. INVENTORY & PRODUCTION
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
# 5. HR, MASTERS & GST
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

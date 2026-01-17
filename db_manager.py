import streamlit as st
import pymongo
import pandas as pd
import datetime
import re
from bson.objectid import ObjectId
import io
import base64
import requests

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
# 1. PRODUCT MANAGEMENT (CRUD)
# ==========================================
def get_all_skus():
    return sorted(db.catalog.distinct("sku"))

def get_product_by_sku(sku):
    return db.catalog.find_one({"sku": sku}, {"_id": 0})

def update_catalog_product(sku, update_data):
    update_data['last_updated'] = datetime.datetime.now()
    db.catalog.update_one({"sku": sku}, {"$set": update_data})

def delete_catalog_product(sku):
    db.catalog.delete_one({"sku": sku})
    db.launches.delete_many({"sku": sku})

# ==========================================
# 2. LAUNCHER & IMAGE UTILS
# ==========================================
def fetch_image_from_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            match = re.search(r'<meta property="og:image" content="([^"]+)"', response.text)
            if match: return match.group(1)
    except: return None
    return None

def image_to_base64(uploaded_file):
    try:
        bytes_data = uploaded_file.getvalue()
        b64_str = base64.b64encode(bytes_data).decode()
        return f"data:{uploaded_file.type};base64,{b64_str}"
    except: return ""

def add_launch_entry(sku, platform, link, sizes, price, status, image_url):
    db.launches.update_one(
        {"sku": sku, "platform": platform},
        {"$set": {
            "sku": sku, "platform": platform, "product_link": link,
            "sizes_launched": sizes, "launch_price": float(price),
            "status": status, "image_url": image_url,
            "last_updated": datetime.datetime.now()
        }},
        upsert=True
    )

def create_and_launch_product(sku, name, platform, link, sizes, price, status, image_url):
    db.catalog.update_one(
        {"sku": sku},
        {"$set": {
            "sku": sku, "product_name": name, "image_link_1": image_url,
            "variation": sizes, "selling_price": float(price),
            "group_id": sku.split('-')[0], 
            "sort_index": int(re.search(r'\d+', sku).group()) if re.search(r'\d+', sku) else 0,
            "last_updated": datetime.datetime.now(),
            "country_origin": "India", "manufacturer_name": "BnB Industries",
            "manufacturer_address": "Siraspur, Delhi", "manufacturer_pincode": "110042"
        }},
        upsert=True
    )
    add_launch_entry(sku, platform, link, sizes, price, status, image_url)

def get_launch_data():
    data = list(db.launches.find({}, {"_id": 0}))
    return pd.DataFrame(data) if data else pd.DataFrame()

# ==========================================
# 3. CATALOG HELPERS
# ==========================================
def get_next_free_drc_number(reserved_indices=set()):
    used_indices = set(db.catalog.distinct("sort_index"))
    all_unavailable = used_indices.union(reserved_indices)
    num = 101
    while True:
        if num not in all_unavailable: return num
        num += 1

def get_next_sku():
    num = get_next_free_drc_number()
    return f"DRC{num}"

def safe_float(val):
    try: return float(str(val).replace("%", "").replace(",", "").replace("₹", "").strip()) if pd.notnull(val) and str(val).strip() else 0.0
    except: return 0.0

def safe_int(val):
    try: return int(str(val).replace(",", "").split(".")[0].strip()) if pd.notnull(val) and str(val).strip() else 0
    except: return 0

# ==========================================
# 4. BULK UPLOAD
# ==========================================
def bulk_upload_catalog(df):
    df.columns = [str(c).strip().lower().replace(" ", "_").replace(".", "").replace("%", "") for c in df.columns]
    success_count = 0; errors = []; reserved_ids = set()
    
    for index, row in df.iterrows():
        action = str(row.get('action', '')).strip().lower()
        csv_sku = str(row.get('sku_code', '')).strip()
        if not csv_sku or csv_sku.lower() == 'nan': csv_sku = None
        existing = db.catalog.find_one({"sku": csv_sku}) if csv_sku else None

        if action == 'delete':
            if existing: db.catalog.delete_one({"sku": csv_sku}); success_count += 1
            else: errors.append({"Row": index+2, "SKU": csv_sku, "Error": "Not Found"})
        elif action == 'update':
            if existing:
                update_fields = {"last_updated": datetime.datetime.now()}
                field_map = {'product_name': 'product_name', 'mrp': 'mrp', 'selling_price': 'selling_price', 'stock': 'stock', 'image_link_1': 'image_link_1', 'gst_rate': 'gst_rate', 'variation': 'variation', 'color': 'color', 'fabric': 'fabric', 'hsn': 'hsn'}
                for csv_k, db_k in field_map.items():
                    val = row.get(csv_k)
                    if pd.notnull(val) and str(val).strip() != "":
                        if db_k in ['mrp', 'selling_price', 'gst_rate']: update_fields[db_k] = safe_float(val)
                        elif db_k == 'stock': update_fields[db_k] = safe_int(val)
                        else: update_fields[db_k] = str(val)
                db.catalog.update_one({"sku": csv_sku}, {"$set": update_fields}); success_count += 1
            else: errors.append({"Row": index+2, "SKU": csv_sku, "Error": "Not Found"})
        else:
            if existing: errors.append({"Row": index+2, "SKU": csv_sku, "Error": "Duplicate"}); continue
            img1 = str(row.get('image_link_1', ''))
            if not img1 or img1.lower() == 'nan': errors.append({"Row": index+2, "SKU": "New", "Error": "Image Missing"}); continue
            
            user_group = str(row.get('group_id', '')).strip()
            if user_group and user_group.lower() != 'nan': group_id = user_group; current_sort = 0
            else: current_sort = get_next_free_drc_number(reserved_ids); group_id = f"DRC{current_sort}"; reserved_ids.add(current_sort)

            raw_vars = str(row.get('variation', '')).split(',')
            variations = [v.strip() for v in raw_vars if v.strip()] or ["Free"]
            
            for size in variations:
                final_sku = f"{csv_sku}-{size}" if csv_sku and len(variations) > 1 else (csv_sku if csv_sku else f"{group_id}-{size}")
                if db.catalog.find_one({"sku": final_sku}): errors.append({"Row": index+2, "SKU": final_sku, "Error": "SKU Exists"}); continue
                
                db.catalog.insert_one({
                    "sku": final_sku, "group_id": group_id, "sort_index": current_sort,
                    "product_name": str(row.get('product_name', '')), "image_link_1": img1,
                    "image_link_2": str(row.get('image_link_2', '')), "image_link_3": str(row.get('image_link_3', '')), "image_link_4": str(row.get('image_link_4', '')),
                    "color": str(row.get('color', '')), "variation": size,
                    "gst_rate": safe_float(row.get('gst_rate')), "hsn": str(row.get('hsn', '')),
                    "product_weight": str(row.get('product_weight', '')), "fabric": str(row.get('fabric', '')),
                    "category": str(row.get('categories', 'Apparel')), "ideal_for": str(row.get('ideal_for', '')),
                    "kids_weight": str(row.get('kids_weight', '')), "brand_name": str(row.get('brand_name', 'Shine Arc')),
                    "description": str(row.get('product_description', '')), "length": str(row.get('length', '')),
                    "fit_type": str(row.get('fit_type', '')), "neck_type": str(row.get('neck_type', '')),
                    "occasion": str(row.get('occasion', '')), "pattern": str(row.get('pattern', '')),
                    "sleeve_length": str(row.get('sleeve_length', '')), "pack_of": str(row.get('pack_of', '1')),
                    "mrp": safe_float(row.get('mrp')), "selling_price": safe_float(row.get('selling_price')), "stock": safe_int(row.get('stock')),
                    "country_origin": "India", "manufacturer_name": "BnB Industries", "manufacturer_address": "Siraspur, Delhi", "manufacturer_pincode": "110042",
                    "last_updated": datetime.datetime.now()
                }); success_count += 1
    return success_count, pd.DataFrame(errors)

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
# 5. BASIC FUNCTIONS
# ==========================================
def process_smart_purchase(data):
    try:
        db.supplier_ledger.insert_one({"supplier": data['supplier'], "date": pd.to_datetime(data['date']), "type": "Bill", "amount": data['grand_total'], "reference": data['bill_no'], "remarks": f"Smart Entry | Stock: {data['stock_type']}", "items": data['items'], "created_at": datetime.datetime.now()})
        if data['stock_type'] == 'Fabric' and data['stock_data']:
            batch_id = datetime.datetime.now().strftime("%Y%m%d%H%M")
            docs = [{"fabric_name": data['stock_data']['name'], "color": data['stock_data']['color'], "batch_id": batch_id, "roll_no": f"{batch_id}-{i+1}", "quantity": float(q), "uom": "Kg", "supplier": data['supplier'], "bill_no": data['bill_no'], "status": "Available", "date_added": datetime.datetime.now()} for i, q in enumerate(data['stock_data'].get('rolls', []))]
            if docs: db.fabric_rolls.insert_many(docs)
        elif data['stock_type'] == 'Accessory':
            db.accessories.update_one({"name": data['stock_data']['name']}, {"$inc": {"quantity": float(data['stock_data']['qty'])}}, upsert=True)
        if data['payment'] and data['payment']['amount'] > 0:
            db.supplier_ledger.insert_one({"supplier": data['supplier'], "date": pd.to_datetime(data['date']), "type": "Payment", "amount": float(data['payment']['amount']), "reference": generate_payment_id(), "remarks": f"Auto-Payment for Bill {data['bill_no']}", "created_at": datetime.datetime.now()})
        return True, "Success"
    except Exception as e: return False, str(e)

def generate_payment_id(): return f"PAY-{datetime.datetime.now().strftime('%Y%m%d')}-{db.supplier_ledger.count_documents({'type': 'Payment'})+1:03d}"
def get_dashboard_stats(): return {"active_lots": db.lots.count_documents({"status": "Active"}), "rolls": db.fabric_rolls.count_documents({"status": "Available"}), "staff_present": db.attendance.count_documents({"date": datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0), "in_time": {"$ne": None}})}
def get_supplier_ledger(name):
    data = list(db.supplier_ledger.find({"supplier": name}).sort("date", 1)); res = []; bal = 0
    for r in data:
        bal += (r['amount'] if r['type']=='Bill' else -r['amount']); res.append({"Date": r['date'], "Particulars": r.get('remarks',''), "Ref": r.get('reference',''), "Credit": r['amount'] if r['type']=='Bill' else 0, "Debit": r['amount'] if r['type']!='Bill' else 0, "Balance": bal})
    return pd.DataFrame(res)
def add_simple_payment(sup, date, amt, mode, note): db.supplier_ledger.insert_one({"supplier": sup, "date": pd.to_datetime(date), "type": "Payment", "amount": amt, "reference": generate_payment_id(), "remarks": f"{mode} - {note}", "created_at": datetime.datetime.now()})
def get_all_fabric_stock_summary(): return list(db.fabric_rolls.aggregate([{"$match": {"status": "Available"}}, {"$group": {"_id": {"name": "$fabric_name", "color": "$color"}, "total_qty": {"$sum": "$quantity"}}}]))
def add_fabric_rolls_batch(fab, col, rolls, uom, sup, bill): db.fabric_rolls.insert_many([{"fabric_name": fab, "color": col, "batch_id": datetime.datetime.now().strftime("%Y%m%d%H%M"), "roll_no": f"{datetime.datetime.now().strftime('%Y%m%d%H%M')}-{i+1}", "quantity": float(q), "uom": uom, "supplier": sup, "bill_no": bill, "status": "Available", "date_added": datetime.datetime.now()} for i, q in enumerate(rolls)])
def update_accessory_stock(name, txn, qty, uom): db.accessories.update_one({"name": name}, {"$inc": {"quantity": float(qty) if txn == "Inward" else -float(qty)}, "$set": {"uom": uom}}, upsert=True)
def get_accessory_stock(): return list(db.accessories.find({}, {"_id": 0, "name": 1, "quantity": 1}))
def get_next_lot_no(): return f"LOT{db.lots.count_documents({}) + 101}"
def create_lot(no, itm, cod, col, sz, rls, cm): db.lots.insert_one({"lot_no": no, "item_name": itm, "item_code": cod, "color": col, "total_qty": sum(sz.values()), "size_breakdown": sz, "current_stage_stock": {"Cutting": size_brk}, "status": "Active", "created_by": cm, "date_created": datetime.datetime.now()}); db.fabric_rolls.update_many({"_id": {"$in": rls}}, {"$set": {"status": "Consumed"}})
def move_lot(lot, frm, to, kar, qty, sz): db.transactions.insert_one({"lot_no": lot, "from_stage": frm, "to_stage": to, "karigar": kar, "qty": qty, "variant": sz, "timestamp": datetime.datetime.now()}); db.lots.update_one({"lot_no": lot}, {"$inc": {f"current_stage_stock.{frm}.{sz}": -qty, f"current_stage_stock.{to}.{sz}": qty}})
def get_lot_transactions(lot): return list(db.transactions.find({"lot_no": lot}).sort("timestamp", -1))
def add_piece_rate(i, p, r): db.rates.update_one({"item": i, "process": p}, {"$set": {"rate": float(r)}}, upsert=True)
def get_rate_master_df(): return pd.DataFrame(list(db.rates.find({}, {"_id": 0})))
def mark_attendance(stf, act): db.attendance.update_one({"staff": stf, "date": datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)}, {"$set": {"in_time" if act=="In" else "out_time": datetime.datetime.now().strftime("%H:%M")}}, upsert=True)
def get_today_attendance(): return list(db.attendance.find({"date": datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)}))
def get_staff_payout(m, y):
    start = datetime.datetime(year=y, month=m, day=1)
    end = datetime.datetime(year=y+1, month=1, day=1) if m==12 else datetime.datetime(year=y, month=m+1, day=1)
    prod = list(db.transactions.aggregate([{"$match": {"timestamp": {"$gte": start, "$lt": end}}}, {"$group": {"_id": {"karigar": "$karigar", "lot": "$lot_no", "stage": "$to_stage"}, "total_qty": {"$sum": "$qty"}}}]))
    rep = []
    for p in prod:
        k=p['_id']['karigar']; lot=p['_id']['lot']; stage=p['_id']['stage'].split(' - ')[0]; q=p['total_qty']
        linfo = db.lots.find_one({"lot_no": lot}); itm = linfo['item_name'] if linfo else "Unknown"
        rdoc = db.rates.find_one({"item": itm, "process": stage}); r = rdoc['rate'] if rdoc else 0.0
        rep.append({"Staff": k, "Item": itm, "Process": stage, "Qty": q, "Rate": r, "Total Pay": q*r})
    return pd.DataFrame(rep)

def get_gst_slabs(): 
    slabs = list(db.gst_slabs.find({}, {"_id": 0, "rate": 1}).sort("rate", 1))
    return [s['rate'] for s in slabs] if slabs else [0, 2.5, 3, 5, 12, 18, 28]
def add_gst_slab(rate): db.gst_slabs.update_one({"rate": float(rate)}, {"$set": {"rate": float(rate)}}, upsert=True)
def get_gst_df(): return pd.DataFrame(list(db.gst_slabs.find({}, {"_id": 0, "rate": 1}).sort("rate", 1)))

# FETCHERS & ROLES
def get_supplier_names(): return sorted(db.suppliers.distinct("name"))
def get_item_names(): return sorted(db.items.distinct("item_name"))
def get_codes_by_item_name(n): return sorted(db.items.distinct("item_code", {"item_name": n}))
def get_colors_by_item_code(c): return sorted(db.items.distinct("color", {"item_code": c}))
def get_item_details_by_code(c): return db.items.find_one({"item_code": c})
def get_materials(): return sorted(db.materials.distinct("name"))
def get_colors(): return sorted(db.colors.distinct("name"))
def get_staff(r): return [x['name'] for x in db.staff.find({"role": r})]
def get_all_staff_names(): return sorted(db.staff.distinct("name"))
def get_all_processes(): return sorted(db.processes.distinct("name"))
def get_sizes(): return sorted(db.sizes.distinct("name"))
def get_acc_names(): return sorted(db.accessories.distinct("name"))
def get_active_lots(): return [x['lot_no'] for x in db.lots.find({"status": "Active"})]
def get_all_lot_numbers(): return [x['lot_no'] for x in db.lots.find({}, {"lot_no": 1})]
def get_lot_info(l): return db.lots.find_one({"lot_no": l})
def get_available_rolls(f, c): return list(db.fabric_rolls.find({"fabric_name": f, "color": c, "status": "Available"}))
def get_all_skus(): return sorted(db.catalog.distinct("sku"))

# --- STAFF ROLES ---
def get_all_roles():
    """Returns dynamic roles. Seeds defaults if empty."""
    roles = list(db.roles.find({}, {"_id": 0, "name": 1}))
    if not roles:
        defaults = ["Helper", "Stitching Karigar", "Cutting Master", "Finishing", "Packing"]
        db.roles.insert_many([{"name": r} for r in defaults])
        return sorted(defaults)
    return sorted([r['name'] for r in roles])

def add_role(role_name):
    db.roles.update_one({"name": role_name}, {"$set": {"name": role_name}}, upsert=True)

def get_roles_df():
    return pd.DataFrame(list(db.roles.find({}, {"_id": 0, "name": 1})))

def add_supplier(n,g,c,a): db.suppliers.insert_one({"name":n,"gst":g,"contact":c})
def add_item(n,c,cl,f): db.items.insert_one({"item_name":n,"item_code":c,"color":cl,"fabrics":f})
def add_fabric(n): db.materials.insert_one({"name":n})
def add_color(n): db.colors.insert_one({"name":n})
def add_staff(n,r): db.staff.insert_one({"name":n,"role":r})
def add_process(n): db.processes.insert_one({"name":n})
def add_size(n): db.sizes.insert_one({"name":n})
def get_suppliers_df(): return pd.DataFrame(list(db.suppliers.find({},{"_id":0})))
def get_items_df(): return pd.DataFrame(list(db.items.find({},{"_id":0})))
def get_staff_df(): return pd.DataFrame(list(db.staff.find({},{"_id":0})))
def get_fabrics_df(): return pd.DataFrame(list(db.materials.find({},{"_id":0})))
def get_colors_df(): return pd.DataFrame(list(db.colors.find({},{"_id":0})))
def get_processes_df(): return pd.DataFrame(list(db.processes.find({},{"_id":0})))
def get_sizes_df(): return pd.DataFrame(list(db.sizes.find({},{"_id":0})))

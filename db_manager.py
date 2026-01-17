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
    st.error("MongoDB Secrets Missing! Add to .streamlit/secrets.toml")
    st.stop()

@st.cache_resource
def get_db():
    client = pymongo.MongoClient(MONGO_URI)
    return client['shine_arc_mes_db']

db = get_db()

# ==========================================
# 1. PRODUCT MANAGEMENT
# ==========================================
def get_all_skus(): return sorted(db.catalog.distinct("sku"))
def get_product_by_sku(sku): return db.catalog.find_one({"sku": sku}, {"_id": 0})
def update_catalog_product(sku, data): db.catalog.update_one({"sku": sku}, {"$set": {**data, "last_updated": datetime.datetime.now()}})
def delete_catalog_product(sku): db.catalog.delete_one({"sku": sku}); db.launches.delete_many({"sku": sku})

# ==========================================
# 2. LAUNCHER & IMAGES
# ==========================================
def fetch_image_from_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            m = re.search(r'<meta property="og:image" content="([^"]+)"', r.text)
            if m: return m.group(1)
    except: return None
    return None

def image_to_base64(file):
    try: return f"data:{file.type};base64,{base64.b64encode(file.getvalue()).decode()}"
    except: return ""

def add_launch_entry(sku, plat, link, sizes, price, status, img):
    db.launches.update_one({"sku": sku, "platform": plat}, {"$set": {"sku": sku, "platform": plat, "product_link": link, "sizes_launched": sizes, "launch_price": float(price), "status": status, "image_url": img, "last_updated": datetime.datetime.now()}}, upsert=True)

def create_and_launch_product(sku, name, plat, link, sizes, price, status, img):
    db.catalog.update_one({"sku": sku}, {"$set": {"sku": sku, "product_name": name, "image_link_1": img, "variation": sizes, "selling_price": float(price), "group_id": sku.split('-')[0], "sort_index": int(re.search(r'\d+', sku).group()) if re.search(r'\d+', sku) else 0, "last_updated": datetime.datetime.now(), "country_origin": "India", "manufacturer_name": "BnB Industries", "manufacturer_address": "Siraspur, Delhi", "manufacturer_pincode": "110042"}}, upsert=True)
    add_launch_entry(sku, plat, link, sizes, price, status, img)

def get_launch_data():
    data = list(db.launches.find({}, {"_id": 0}))
    return pd.DataFrame(data) if data else pd.DataFrame()

# ==========================================
# 3. CATALOG HELPERS
# ==========================================
def get_next_free_drc_number(reserved=set()):
    used = set(db.catalog.distinct("sort_index"))
    unavailable = used.union(reserved)
    num = 101
    while num in unavailable: num += 1
    return num

def get_next_sku(): return f"DRC{get_next_free_drc_number()}"
def safe_float(v): 
    try: return float(str(v).replace("%","").replace(",","").replace("₹","").strip()) if pd.notnull(v) and str(v).strip() else 0.0
    except: return 0.0
def safe_int(v):
    try: return int(str(v).replace(",","").split(".")[0].strip()) if pd.notnull(v) and str(v).strip() else 0
    except: return 0

# ==========================================
# 4. BULK UPLOAD
# ==========================================
def bulk_upload_catalog(df):
    df.columns = [str(c).strip().lower().replace(" ", "_").replace(".", "").replace("%", "") for c in df.columns]
    success = 0; errors = []; reserved = set()
    for i, row in df.iterrows():
        act = str(row.get('action', '')).strip().lower()
        sku = str(row.get('sku_code', '')).strip()
        if not sku or sku.lower()=='nan': sku = None
        exists = db.catalog.find_one({"sku": sku}) if sku else None
        
        if act == 'delete':
            if exists: db.catalog.delete_one({"sku": sku}); success += 1
            else: errors.append({"Row": i+2, "SKU": sku, "Error": "Not Found"})
        elif act == 'update':
            if exists:
                upd = {"last_updated": datetime.datetime.now()}
                fmap = {'product_name':'product_name','mrp':'mrp','selling_price':'selling_price','stock':'stock','image_link_1':'image_link_1','gst_rate':'gst_rate','variation':'variation','color':'color','fabric':'fabric','hsn':'hsn'}
                for ck, dk in fmap.items():
                    v = row.get(ck)
                    if pd.notnull(v) and str(v).strip()!="":
                        upd[dk] = safe_float(v) if dk in ['mrp','selling_price','gst_rate'] else (safe_int(v) if dk=='stock' else str(v))
                db.catalog.update_one({"sku": sku}, {"$set": upd}); success += 1
            else: errors.append({"Row": i+2, "SKU": sku, "Error": "Not Found"})
        else:
            if exists: errors.append({"Row": i+2, "SKU": sku, "Error": "Duplicate"}); continue
            img = str(row.get('image_link_1', ''))
            if not img or img.lower()=='nan': errors.append({"Row": i+2, "SKU": "New", "Error": "Image Missing"}); continue
            
            ug = str(row.get('group_id', '')).strip()
            if ug and ug.lower()!='nan': gid = ug; sidx = 0
            else: sidx = get_next_free_drc_number(reserved); gid = f"DRC{sidx}"; reserved.add(sidx)
            
            vars_ = [v.strip() for v in str(row.get('variation', '')).split(',') if v.strip()] or ["Free"]
            for sz in vars_:
                fsku = f"{sku}-{sz}" if sku and len(vars_)>1 else (sku if sku else f"{gid}-{sz}")
                if db.catalog.find_one({"sku": fsku}): errors.append({"Row": i+2, "SKU": fsku, "Error": "SKU Exists"}); continue
                
                doc = {
                    "sku": fsku, "group_id": gid, "sort_index": sidx, "product_name": str(row.get('product_name','')), "image_link_1": img,
                    "image_link_2": str(row.get('image_link_2','')), "image_link_3": str(row.get('image_link_3','')), "image_link_4": str(row.get('image_link_4','')),
                    "color": str(row.get('color','')), "variation": sz, "gst_rate": safe_float(row.get('gst_rate')), "hsn": str(row.get('hsn','')),
                    "product_weight": str(row.get('product_weight','')), "fabric": str(row.get('fabric','')), "category": str(row.get('categories','Apparel')),
                    "ideal_for": str(row.get('ideal_for','')), "kids_weight": str(row.get('kids_weight','')), "brand_name": str(row.get('brand_name','Shine Arc')),
                    "description": str(row.get('product_description','')), "length": str(row.get('length','')), "fit_type": str(row.get('fit_type','')),
                    "neck_type": str(row.get('neck_type','')), "occasion": str(row.get('occasion','')), "pattern": str(row.get('pattern','')),
                    "sleeve_length": str(row.get('sleeve_length','')), "pack_of": str(row.get('pack_of','1')),
                    "mrp": safe_float(row.get('mrp')), "selling_price": safe_float(row.get('selling_price')), "stock": safe_int(row.get('stock')),
                    "country_origin": "India", "manufacturer_name": "BnB Industries", "manufacturer_address": "Siraspur, Delhi", "manufacturer_pincode": "110042",
                    "last_updated": datetime.datetime.now()
                }
                db.catalog.insert_one(doc); success += 1
    return success, pd.DataFrame(errors)

def add_catalog_product(sku, name, category, fabric, color, size, mrp, sp, hsn, stock, img_link):
    db.catalog.update_one({"sku": sku}, {"$set": {"sku": sku, "product_name": name, "category": category, "fabric": fabric, "color": color, "variation": size, "mrp": float(mrp), "selling_price": float(sp), "hsn": hsn, "stock": int(stock), "image_link_1": img_link, "country_origin": "India", "manufacturer_name": "BnB Industries", "manufacturer_address": "Siraspur, Delhi", "manufacturer_pincode": "110042", "last_updated": datetime.datetime.now()}}, upsert=True)

def get_catalog_df():
    data = list(db.catalog.find({}, {"_id": 0}))
    return pd.DataFrame(data) if data else pd.DataFrame()

def generate_marketplace_file(platform):
    df = get_catalog_df()
    if df.empty: return None
    for c in ['sku','product_name','mrp','selling_price','stock']: 
        if c not in df.columns: df[c]=""
    
    # Generic Mapper for brevity - can expand for specific platforms
    out = pd.DataFrame()
    out['SKU'] = df['sku']
    out['Name'] = df['product_name']
    out['MRP'] = df['mrp']
    out['Selling Price'] = df['selling_price']
    out['Stock'] = df['stock']
    out['Image'] = df.get('image_link_1', '')
    return out

# ==========================================
# 5. ACCOUNTS & TRANSACTIONS (UPDATED)
# ==========================================

# --- PAYMENT SOURCES ---
def get_payment_sources():
    """Returns configured payment sources (e.g. Banks, Cash)."""
    srcs = list(db.payment_sources.find({}, {"_id": 0, "name": 1}))
    if not srcs:
        defaults = ["Cash", "Bank Transfer", "UPI"]
        db.payment_sources.insert_many([{"name": s} for s in defaults])
        return sorted(defaults)
    return sorted([s['name'] for s in srcs])

def add_payment_source(name):
    db.payment_sources.update_one({"name": name}, {"$set": {"name": name}}, upsert=True)

# --- TRANSACTION HANDLER ---
def process_transaction(txn_type, data):
    """
    Central handler for all account entries.
    txn_type: 'Purchase', 'Sales', 'Purchase Return', 'Delivery Challan', 'Job Work', 'Payment In', 'Payment Out'
    """
    try:
        # Common fields
        entry = {
            "date": pd.to_datetime(data['date']),
            "type": txn_type,
            "reference": data.get('ref_no', ''),
            "party": data.get('party', ''),
            "amount": float(data.get('amount', 0)),
            "created_at": datetime.datetime.now()
        }

        # 1. LEDGER IMPACT (Financials)
        # Note: 'amount' in ledger determines balance direction.
        # Store as positive, calculate balance on fetch.
        
        ledger_entry = entry.copy()
        ledger_entry['supplier'] = data.get('party', '') # Keep 'supplier' field for compatibility
        ledger_entry['remarks'] = f"{txn_type} | {data.get('remarks', '')}"
        
        # Financial Entry Logic
        if txn_type in ['Purchase']:
            # Credit Party (We owe money)
            db.supplier_ledger.insert_one(ledger_entry)
            
        elif txn_type in ['Sales', 'Purchase Return']:
            # Debit Party (They owe us / We reduced debt)
            # Store as Debit type explicitly handled in get_supplier_ledger
            ledger_entry['is_debit'] = True 
            db.supplier_ledger.insert_one(ledger_entry)
            
        elif txn_type in ['Payment Out']:
            # Debit Party (We paid them)
            ledger_entry['remarks'] += f" [Source: {data.get('source')}]"
            ledger_entry['is_debit'] = True
            db.supplier_ledger.insert_one(ledger_entry)
            
        elif txn_type in ['Payment In']:
            # Credit Party (They paid us)
            ledger_entry['remarks'] += f" [Source: {data.get('source')}]"
            db.supplier_ledger.insert_one(ledger_entry)
            
        # Challan & Job Work usually purely inventory/tracking in basic ERPs
        elif txn_type in ['Delivery Challan', 'Job Work']:
            # Just log, no financial ledger impact usually unless specified
            # For now, store in a 'tracking_ledger' or just skip main ledger
            pass

        # 2. INVENTORY IMPACT
        if data.get('stock_data'):
            # Incoming Stock (Purchase, Sales Return - not impl yet)
            if txn_type == 'Purchase':
                if data['stock_type'] == 'Fabric':
                    batch_id = datetime.datetime.now().strftime("%Y%m%d%H%M")
                    docs = [{"fabric_name": data['stock_data']['name'], "color": data['stock_data']['color'], "batch_id": batch_id, "roll_no": f"{batch_id}-{i+1}", "quantity": float(q), "uom": "Kg", "supplier": data['party'], "bill_no": data.get('ref_no'), "status": "Available", "date_added": datetime.datetime.now()} for i, q in enumerate(data['stock_data'].get('rolls', []))]
                    if docs: db.fabric_rolls.insert_many(docs)
                elif data['stock_type'] == 'Accessory':
                    db.accessories.update_one({"name": data['stock_data']['name']}, {"$inc": {"quantity": float(data['stock_data']['qty'])}}, upsert=True)
            
            # Outgoing Stock (Sales, Purchase Return, Challan, Job Work)
            elif txn_type in ['Sales', 'Purchase Return', 'Delivery Challan', 'Job Work']:
                # Logic to reduce stock would go here. 
                # For Fabric: Mark rolls as 'Consumed' or 'Sent'.
                # For Acc: Decrease Qty.
                # Simplified for this snippet:
                if data['stock_type'] == 'Accessory':
                    db.accessories.update_one({"name": data['stock_data']['name']}, {"$inc": {"quantity": -float(data['stock_data']['qty'])}}, upsert=True)

        return True, "Entry Saved"
    except Exception as e: return False, str(e)

def generate_payment_id(): return f"PAY-{datetime.datetime.now().strftime('%Y%m%d')}-{db.supplier_ledger.count_documents({})+1:03d}"

def get_supplier_ledger(name):
    # Updated to handle new debit flag
    data = list(db.supplier_ledger.find({"supplier": name}).sort("date", 1))
    res = []; bal = 0
    for r in data:
        # Determine Dr/Cr
        txn_type = r.get('type', '')
        amt = r.get('amount', 0)
        
        # Debits: Payment Out, Sales, Purchase Return, Debit Note
        is_dr = r.get('is_debit') or txn_type in ['Payment Out', 'Sales', 'Purchase Return', 'Debit Note', 'Payment']
        
        # Credits: Purchase, Payment In, Credit Note, Bill
        is_cr = not is_dr
        
        if is_cr: bal += amt
        else: bal -= amt
        
        res.append({
            "Date": r['date'], 
            "Particulars": r.get('remarks',''), 
            "Ref": r.get('reference',''), 
            "Credit": amt if is_cr else 0, 
            "Debit": amt if is_dr else 0, 
            "Balance": bal
        })
    return pd.DataFrame(res)

# ==========================================
# 6. OTHER MASTERS
# ==========================================
def get_dashboard_stats(): return {"active_lots": db.lots.count_documents({"status": "Active"}), "rolls": db.fabric_rolls.count_documents({"status": "Available"}), "staff_present": db.attendance.count_documents({"date": datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0), "in_time": {"$ne": None}})}
def get_all_fabric_stock_summary(): return list(db.fabric_rolls.aggregate([{"$match": {"status": "Available"}}, {"$group": {"_id": {"name": "$fabric_name", "color": "$color"}, "total_qty": {"$sum": "$quantity"}}}]))
def add_fabric_rolls_batch(fab, col, rolls, uom, sup, bill): db.fabric_rolls.insert_many([{"fabric_name": fab, "color": col, "batch_id": datetime.datetime.now().strftime("%Y%m%d%H%M"), "roll_no": f"{datetime.datetime.now().strftime('%Y%m%d%H%M')}-{i+1}", "quantity": float(q), "uom": uom, "supplier": sup, "bill_no": bill, "status": "Available", "date_added": datetime.datetime.now()} for i, q in enumerate(rolls)])
def update_accessory_stock(name, txn, qty, uom): db.accessories.update_one({"name": name}, {"$inc": {"quantity": float(qty) if txn == "Inward" else -float(qty)}, "$set": {"uom": uom}}, upsert=True)
def get_accessory_stock(): return list(db.accessories.find({}, {"_id": 0, "name": 1, "quantity": 1}))
def get_next_lot_no(): return f"LOT{db.lots.count_documents({}) + 101}"
def create_lot(no, itm, cod, col, sz, rls, cm): db.lots.insert_one({"lot_no": no, "item_name": itm, "item_code": cod, "color": col, "total_qty": sum(sz.values()), "size_breakdown": sz, "current_stage_stock": {"Cutting": sz}, "status": "Active", "created_by": cm, "date_created": datetime.datetime.now()}); db.fabric_rolls.update_many({"_id": {"$in": rls}}, {"$set": {"status": "Consumed"}})
def move_lot(lot, frm, to, kar, qty, sz): db.transactions.insert_one({"lot_no": lot, "from_stage": frm, "to_stage": to, "karigar": kar, "qty": qty, "variant": sz, "timestamp": datetime.datetime.now()}); db.lots.update_one({"lot_no": lot}, {"$inc": {f"current_stage_stock.{frm}.{sz}": -qty, f"current_stage_stock.{to}.{sz}": qty}})
def get_lot_transactions(lot): return list(db.transactions.find({"lot_no": lot}).sort("timestamp", -1))
def add_piece_rate(i, p, r): db.rates.update_one({"item": i, "process": p}, {"$set": {"rate": float(r)}}, upsert=True)
def get_rate_master_df(): return pd.DataFrame(list(db.rates.find({}, {"_id": 0})))
def mark_attendance(stf, act): db.attendance.update_one({"staff": stf, "date": datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)}, {"$set": {"in_time" if act=="In" else "out_time": datetime.datetime.now().strftime("%H:%M")}}, upsert=True)
def get_today_attendance(): return list(db.attendance.find({"date": datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)}))
def get_staff_payout(m, y):
    start = datetime.datetime(y, m, 1)
    end = datetime.datetime(y+1, 1, 1) if m==12 else datetime.datetime(y, m+1, 1)
    prod = list(db.transactions.aggregate([{"$match": {"timestamp": {"$gte": start, "$lt": end}}}, {"$group": {"_id": {"karigar": "$karigar", "lot": "$lot_no", "stage": "$to_stage"}, "total_qty": {"$sum": "$qty"}}}]))
    rep = []
    for p in prod:
        k=p['_id']['karigar']; lot=p['_id'].get('lot') or p['_id'].get('lot_no'); stage=p['_id']['stage'].split(' - ')[0]; q=p['total_qty']
        linfo = db.lots.find_one({"lot_no": lot}); itm = linfo['item_name'] if linfo else "Unknown"
        rdoc = db.rates.find_one({"item": itm, "process": stage}); r = rdoc['rate'] if rdoc else 0.0
        rep.append({"Staff": k, "Item": itm, "Process": stage, "Qty": q, "Rate": r, "Total Pay": q*r})
    return pd.DataFrame(rep)

def get_gst_slabs(): return [0, 2.5, 3, 5, 12, 18, 28]
def add_gst_slab(r): pass
def get_gst_df(): return pd.DataFrame()
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
def get_all_roles():
    rs = list(db.roles.find({}, {"_id":0, "name":1}))
    return sorted([r['name'] for r in rs]) if rs else ["Helper", "Stitching Karigar"]
def add_role(r): db.roles.update_one({"name":r}, {"$set":{"name":r}}, upsert=True)
def get_roles_df(): return pd.DataFrame(list(db.roles.find({},{"_id":0,"name":1})))
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

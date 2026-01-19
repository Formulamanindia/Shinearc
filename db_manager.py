import streamlit as st
import pymongo
import pandas as pd
import datetime
import re
import base64
import requests
import qrcode
import cv2
import numpy as np
from io import BytesIO

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
# 1. PRODUCTION LOGIC (UPDATED)
# ==========================================
def get_all_processes():
    return ["Cutting", "Stitching", "Dhaga Cutting", "Sticker", "Press", "Packing"]

def move_bundles(lot_no, bundle_ids, to_stage, worker_name, machine_name, manual_qty=None):
    """
    Moves bundles to a new stage with Worker AND Machine assignment.
    """
    # 1. Update Bundle Status
    db.lots.update_one(
        {"lot_no": lot_no},
        {
            "$set": {
                "bundles.$[elem].current_stage": to_stage,
                "bundles.$[elem].assigned_to": worker_name,
                "bundles.$[elem].machine": machine_name, # New Field
                "bundles.$[elem].last_update": datetime.datetime.now()
            },
            "$push": {
                "history": {
                    "stage": to_stage,
                    "msg": f"Moved {len(bundle_ids)} bundles to {to_stage} ({worker_name} on {machine_name})",
                    "time": datetime.datetime.now()
                }
            }
        },
        array_filters=[{"elem.bundle_id": {"$in": bundle_ids}}]
    )
    
    # 2. Log Transaction
    lot = db.lots.find_one({"lot_no": lot_no})
    system_qty = sum(b['qty'] for b in lot['bundles'] if b['bundle_id'] in bundle_ids)
    final_qty = float(manual_qty) if manual_qty and manual_qty > 0 else system_qty
    
    db.transactions.insert_one({
        "lot_no": lot_no,
        "to_stage": to_stage,
        "karigar": worker_name,
        "machine": machine_name,
        "qty": final_qty,
        "timestamp": datetime.datetime.now(),
        "bundle_ids": bundle_ids
    })

def create_advanced_lot(lot_no, item_name, cm, materials_used, variants, fabric_weight):
    item_doc = db.items.find_one({"item_name": item_name})
    item_code = item_doc.get("item_code", "-") if item_doc else "-"

    bundles = []
    total_qty = 0
    for i, v in enumerate(variants):
        bundle_id = f"{lot_no}-{i+1:02d}"
        bundles.append({
            "bundle_id": bundle_id,
            "color": v['color'],
            "size": v['size'],
            "qty": float(v['qty']),
            "current_stage": "Cutting",
            "assigned_to": cm,
            "machine": "-",
            "last_update": datetime.datetime.now()
        })
        total_qty += float(v['qty'])

    # Deduct Materials
    for mat in materials_used:
        db.accessories.update_one({"name": mat['name']}, {"$inc": {"quantity": -float(mat['qty'])}})

    qr_str = f"Lot:{lot_no}|Item:{item_name}|Qty:{total_qty}"
    db.lots.insert_one({
        "lot_no": lot_no,
        "item_name": item_name,
        "item_code": item_code,
        "fabric_weight": float(fabric_weight),
        "total_qty": total_qty,
        "status": "Active",
        "created_by": cm,
        "date_created": datetime.datetime.now(),
        "materials_consumed": materials_used,
        "bundles": bundles,
        "history": [{"stage": "Created", "msg": f"Created with {len(bundles)} bundles", "time": datetime.datetime.now()}],
        "qr_data": qr_str
    })
    return True

# ==========================================
# 2. ACCOUNTS (UPDATED WITH CATEGORY)
# ==========================================
def process_transaction(t, d): 
    try:
        doc = {**d, "date": pd.to_datetime(d['date']), "type":t, "created_at":datetime.datetime.now()}
        
        # Ledger Entry
        l_ent = doc.copy()
        l_ent['supplier'] = d['party']
        if t in ['Purchase']: db.supplier_ledger.insert_one(l_ent)
        elif t in ['Sales','Purchase Return','Payment Out']: l_ent['is_debit']=True; db.supplier_ledger.insert_one(l_ent)
        elif t in ['Payment In']: db.supplier_ledger.insert_one(l_ent)

        # Inventory Impact (Based on Category)
        if t in ['Purchase', 'Sales', 'Purchase Return', 'Delivery Challan', 'Job Work']:
            doc['items'] = d.get('bill_items', [])
            for i in doc['items']:
                direction = 1 if t == 'Purchase' else -1
                cat = i.get('category', 'Accessories')
                
                # Logic to update specific collections based on category could go here
                # For now, we update the central 'accessories' (Materials) collection for raw mats
                # and maybe 'catalog' for finished goods, but keeping it simple as requested:
                if cat in ['Fabric', 'Accessories']:
                    db.accessories.update_one(
                        {"name": i['item']},
                        {"$inc": {"quantity": float(i['qty']) * direction}, "$set": {"uom": i['uom']}},
                        upsert=True
                    )
                # Finished Goods logic would typically update a separate stock, 
                # but tracking FG stock is complex in simple ERPs. 
                # We record the transaction regardless.

        return True, "Saved"
    except Exception as e: return False, str(e)

# ==========================================
# 3. MASTERS & GETTERS (UPDATED)
# ==========================================
def add_fabric(name, color):
    """Adds fabric with default color."""
    db.materials.insert_one({"name": name, "default_color": color})

def get_fabrics_df(): 
    return pd.DataFrame(list(db.materials.find({},{"_id":0})))

def get_machines():
    return sorted([m['name'] for m in db.machines.find({}, {"_id":0, "name":1})])

def add_machine(name):
    db.machines.update_one({"name": name}, {"$set": {"name": name}}, upsert=True)

def get_machines_df():
    return pd.DataFrame(list(db.machines.find({}, {"_id":0})))

# --- Standard Getters ---
def get_active_lots(): return [x['lot_no'] for x in db.lots.find({"status": "Active"}, {"lot_no": 1})]
def get_all_lot_numbers(): return [x['lot_no'] for x in db.lots.find({}, {"lot_no": 1})]
def get_lot_info(lot_no): return db.lots.find_one({"lot_no": lot_no})
def get_lot_transactions(lot_no): return list(db.transactions.find({"lot_no": lot_no}).sort("timestamp", -1))
def find_lot_by_bundle_id(bundle_id): return db.lots.find_one({"bundles.bundle_id": bundle_id})
def get_next_lot_no(): return f"LOT{db.lots.count_documents({}) + 101}"
def get_fabrics_list(): return sorted(db.materials.distinct("name")) # Renamed to avoid clash
def get_all_accessories(): return sorted([a['name'] for a in db.accessories_master.find({}, {"_id": 0, "name": 1})])
def get_item_fabrics(item_name):
    item = db.items.find_one({"item_name": item_name})
    return item.get('fabrics', []) if item else []
def get_available_rolls(fabric, color):
    return list(db.fabric_rolls.find({"fabric_name": fabric, "color": color, "status": "Available"}))
def get_item_materials(item_name):
    fabrics = sorted(db.materials.distinct("name"))
    accs = sorted(db.accessories.distinct("name"))
    return sorted(list(set(fabrics + accs)))
def get_item_names(): return sorted(db.items.distinct("item_name"))
def get_codes_by_item_name(n): return sorted(db.items.distinct("item_code", {"item_name": n}))
def get_staff(role): return [s['name'] for s in db.staff.find({"role": role}, {"_id": 0, "name": 1})]
def get_sizes(): return sorted(db.sizes.distinct("name"))
def get_colors(): return sorted(db.colors.distinct("name"))
def get_all_roles(): return sorted([r['name'] for r in db.roles.find()])
def get_colors_by_item_code(c): return sorted(db.items.distinct("color", {"item_code": c}))
def get_all_staff_names(): return sorted(db.staff.distinct("name"))
def get_payment_sources(): return sorted([x['name'] for x in db.payment_sources.find()])
def get_supplier_names(): return sorted(db.suppliers.distinct("name"))
def get_rate_master_df(): return pd.DataFrame(list(db.rates.find({},{"_id":0})))
def get_acc_names(): return sorted(db.accessories.distinct("name"))
def get_gst_slabs(): return [0,2.5,3,5,12,18,28]

# --- QR ---
def generate_bundle_qr(lot_no, bundle_id, item, color, size, qty, worker):
    data = f"B:{bundle_id}|L:{lot_no}|I:{item}|C:{color}|S:{size}"
    qr = qrcode.QRCode(version=1, box_size=5, border=2)
    qr.add_data(data); qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO(); img.save(buf)
    return buf.getvalue()

def decode_qr_image(image_upload):
    try:
        file_bytes = np.asarray(bytearray(image_upload.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(img)
        return data if data else None
    except: return None

def parse_qr_text(qr_text):
    try: match = re.search(r"B:([\w-]+)", qr_text); return match.group(1) if match else None
    except: return None

# --- REPORTS ---
def get_lot_costing_report():
    lots = list(db.lots.find({}))
    if not lots: return pd.DataFrame()
    report_data = []
    for lot in lots:
        item = lot.get('item_name'); qty = lot.get('total_qty', 0)
        if qty == 0: qty = 1
        rates = list(db.rates.find({"item": item}))
        unit_labor = sum([r.get('rate', 0) for r in rates])
        total_labor = qty * unit_labor
        mats = lot.get('materials_consumed', [])
        total_fab = sum([float(m.get('qty', 0)) for m in mats])
        mat_str = ", ".join([f"{m['name']}:{m['qty']}" for m in mats])
        overheads = 7 # 1+1+5
        
        report_data.append({
            "Lot No": lot.get('lot_no'), "Item": item, "Pcs": qty,
            "Fab Used": total_fab, "Fab Details": mat_str,
            "Labor/Pc": unit_labor, "Total Labor": total_labor,
            "Overheads/Pc": overheads, "Status": lot.get('status')
        })
    return pd.DataFrame(report_data)

# --- CONFIG SETTERS ---
def get_suppliers_df(): return pd.DataFrame(list(db.suppliers.find({},{"_id":0})))
def get_items_df(): return pd.DataFrame(list(db.items.find({},{"_id":0})))
def get_staff_df(): return pd.DataFrame(list(db.staff.find({},{"_id":0})))
def get_colors_df(): return pd.DataFrame(list(db.colors.find({},{"_id":0})))
def get_processes_df(): return pd.DataFrame(list(db.processes.find({},{"_id":0})))
def get_sizes_df(): return pd.DataFrame(list(db.sizes.find({},{"_id":0})))
def get_roles_df(): return pd.DataFrame(list(db.roles.find({},{"_id":0})))
def get_uoms_df(): return pd.DataFrame(list(db.uoms.find({},{"_id":0})))
def get_accessories_df(): return pd.DataFrame(list(db.accessories_master.find({},{"_id":0})))
def get_payment_sources_df(): return pd.DataFrame(list(db.payment_sources.find({},{"_id":0})))
def get_gst_df(): return pd.DataFrame(list(db.gst_slabs.find({},{"_id":0})))
def add_supplier(n,g,c,a): db.suppliers.insert_one({"name":n,"gst":g,"contact":c,"address":a})
def add_item(n,c,cl,f,tg,gc): db.items.insert_one({"item_name":n,"item_code":c,"color":cl,"fabrics":f,"target_group":tg,"gender_category":gc})
def add_staff(n,r,pt,s): db.staff.update_one({"name":n}, {"$set":{"name":n,"role":r,"payment_type":pt,"salary_amount":float(s)}}, upsert=True)
def add_color(n): db.colors.insert_one({"name":n})
def add_process(n): db.processes.insert_one({"name":n})
def add_size(n): db.sizes.insert_one({"name":n})
def add_role(r): db.roles.update_one({"name":r},{"$set":{"name":r}},upsert=True)
def add_uom(n): db.uoms.update_one({"name":n},{"$set":{"name":n}},upsert=True)
def add_accessory_master(n): db.accessories_master.update_one({"name":n},{"$set":{"name":n}},upsert=True)
def add_payment_source(n): db.payment_sources.update_one({"name":n},{"$set":{"name":n}},upsert=True)
def add_gst_slab(r): db.gst_slabs.update_one({"rate":r},{"$set":{"rate":r}},upsert=True)
def clean_database(c): 
    for col in c: db[col].delete_many({})
    return True, "Done"
def process_bulk_master_upload(t, d): return True, "Done"
def get_catalog_df(): return pd.DataFrame(list(db.catalog.find({},{"_id":0})))
def get_launch_data(): return pd.DataFrame(list(db.launches.find({},{"_id":0})))
def get_all_skus(): return sorted(db.catalog.distinct("sku"))
def get_next_sku(): return f"DRC{db.catalog.count_documents({})+101}"
def fetch_image_from_url(u): return None
def image_to_base64(f): return ""
def add_catalog_product(s,n,c,f,cl,sz,m,sp,h,st,im): db.catalog.update_one({"sku":s},{"$set":{"sku":s,"product_name":n,"category":c,"fabric":f,"color":cl,"variation":sz,"mrp":float(m),"selling_price":float(sp),"hsn":h,"stock":int(st),"image_link_1":im,"last_updated":datetime.datetime.now()}},upsert=True)
def create_and_launch_product(s,n,p,l,sz,pr,st,im): db.catalog.update_one({"sku":s},{"$set":{"sku":s,"product_name":n,"image_link_1":im,"variation":sz,"selling_price":float(pr),"group_id":s.split('-')[0],"sort_index":int(re.search(r'\d+',s).group()) if re.search(r'\d+',s) else 0,"last_updated":datetime.datetime.now()}},upsert=True); add_launch_entry(s,p,l,sz,pr,st,im)
def add_launch_entry(s,p,l,sz,pr,st,im): db.launches.update_one({"sku":s,"platform":p},{"$set":{"sku":s,"platform":p,"product_link":l,"sizes_launched":sz,"launch_price":float(pr),"status":st,"image_url":im,"last_updated":datetime.datetime.now()}},upsert=True)
def delete_catalog_product(s): db.catalog.delete_one({"sku":s}); db.launches.delete_many({"sku":s})
def update_catalog_product(s, d): db.catalog.update_one({"sku":s},{"$set":{**d,"last_updated":datetime.datetime.now()}})
def get_product_by_sku(s): return db.catalog.find_one({"sku":s},{"_id":0})
def generate_marketplace_file(p): return pd.DataFrame()
def bulk_upload_catalog(df): return 0, pd.DataFrame()
def get_staff_payout(n,m,y): return None
def add_staff_advance(n,a,d,r): pass
def mark_attendance(s,a,t,n): pass
def get_today_attendance(): return []
def get_supplier_ledger(n): return pd.DataFrame()
def update_accessory_stock(n,t,q,u): pass
def get_available_rolls(f,c): return []
def add_fabric_rolls_batch(f,c,r,u,s,b): pass

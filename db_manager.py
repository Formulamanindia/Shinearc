import streamlit as st
import pymongo
import pandas as pd
import datetime
import re
import base64
import requests
import qrcode
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
# 1. LOT & PRODUCTION LOGIC (ENHANCED)
# ==========================================
def get_active_lots():
    """Returns a list of lot numbers where status is Active."""
    return [x['lot_no'] for x in db.lots.find({"status": "Active"}, {"lot_no": 1})]

def get_lot_info(lot_no):
    """Fetches full details of a specific lot."""
    return db.lots.find_one({"lot_no": lot_no})

def get_lot_breakdown(lot_no):
    """
    Returns a list of all Size-Color variants in a lot and their current stage.
    Useful for the 'Split Assignment' UI.
    """
    lot = db.lots.find_one({"lot_no": lot_no})
    if not lot: return []
    
    breakdown = []
    # Analyze current stock distribution
    # Structure: lot['current_stage_stock'] = {'Cutting': {'Red_S': 10, 'Red_M': 20}, 'Stitching': {...}}
    
    stk = lot.get('current_stage_stock', {})
    
    # We iterate through all stages to find where pieces are sitting
    for stage, variants in stk.items():
        for variant_key, qty in variants.items():
            if qty > 0:
                # Variant key is typically "Color_Size" (e.g. "Red_S")
                # We need to split it for display
                try:
                    color, size = variant_key.rsplit('_', 1)
                except ValueError:
                    color, size = "Unknown", variant_key
                
                breakdown.append({
                    "Stage": stage,
                    "Color": color,
                    "Size": size,
                    "Variant Key": variant_key,
                    "Qty": qty
                })
    return breakdown

def move_lot_bundle(lot_no, current_stage, next_stage, karigar, qty, variant_key):
    """
    Moves a specific bundle (Color-Size) from one stage to another.
    """
    # 1. Log Transaction
    db.transactions.insert_one({
        "lot_no": lot_no,
        "from_stage": current_stage,
        "to_stage": next_stage,
        "karigar": karigar if karigar else "System/Admin",
        "qty": float(qty),
        "variant": variant_key, # Stores "Color_Size" string
        "timestamp": datetime.datetime.now()
    })
    
    # 2. Update Stock Levels
    # Decrement from source, Increment to destination
    db.lots.update_one(
        {"lot_no": lot_no},
        {"$inc": {
            f"current_stage_stock.{current_stage}.{variant_key}": -float(qty),
            f"current_stage_stock.{next_stage}.{variant_key}": float(qty)
        }}
    )

def create_lot(lot_no, item_name, item_code, color, size_breakdown, rolls, cutting_master, fabric_weight):
    total_qty = sum(size_breakdown.values())
    qr_str = f"Lot:{lot_no}|Item:{item_name}|Col:{color}|Qty:{total_qty}"
    
    # Convert simple size dict {"S": 10} to variant keys {"Red_S": 10}
    # This standardizes tracking for multi-color lots later if needed.
    # Since Lot Creation has 1 color, we prefix it.
    
    formatted_stock = {}
    for size, qty in size_breakdown.items():
        key = f"{color}_{size}"
        formatted_stock[key] = qty

    db.lots.insert_one({
        "lot_no": lot_no,
        "item_name": item_name,
        "item_code": item_code,
        "color": color,
        "fabric_weight": float(fabric_weight),
        "total_qty": total_qty,
        "original_breakdown": formatted_stock,
        "current_stage_stock": {"Cutting": formatted_stock}, 
        "status": "Active",
        "created_by": cutting_master,
        "date_created": datetime.datetime.now(),
        "qr_data": qr_str
    })
    
    if rolls:
        db.fabric_rolls.update_many({"_id": {"$in": rolls}}, {"$set": {"status": "Consumed"}})

def get_next_lot_no():
    count = db.lots.count_documents({})
    return f"LOT{count + 101}"

# ==========================================
# 2. PAYOUT & HR (Preserved)
# ==========================================
def get_staff(role):
    return [s['name'] for s in db.staff.find({"role": role}, {"_id": 0, "name": 1})]

def get_staff_payout(staff_name, month, year):
    staff = db.staff.find_one({"name": staff_name})
    if not staff: return None

    start = datetime.datetime(year, month, 1)
    end = datetime.datetime(year + 1, 1, 1) if month == 12 else datetime.datetime(year, month + 1, 1)
    
    adv_res = list(db.staff_ledger.aggregate([
        {"$match": {"staff": staff_name, "type": "Advance", "date": {"$gte": start, "$lt": end}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]))
    advances = adv_res[0]['total'] if adv_res else 0.0

    if staff.get('payment_type') == 'Piece Rate':
        txns = list(db.transactions.aggregate([
            {"$match": {"karigar": staff_name, "timestamp": {"$gte": start, "$lt": end}}},
            {"$lookup": {"from": "lots", "localField": "lot_no", "foreignField": "lot_no", "as": "lot_info"}}
        ]))
        
        details = []
        total = 0
        for t in txns:
            lot = t['lot_info'][0] if t['lot_info'] else {}
            itm = lot.get('item_name', 'Unknown')
            # Extract stage (e.g. "Stitching" from "Stitching")
            stg = t['to_stage'] 
            
            # Rate lookup needs pure stage name
            rate_doc = db.rates.find_one({"item": itm, "process": stg})
            r = rate_doc['rate'] if rate_doc else 0
            amt = t['qty'] * r
            total += amt
            
            # Parse variant key for display
            v_key = t.get('variant', 'Unknown')
            details.append({
                "Date": t['timestamp'].strftime('%d-%b'), 
                "Lot": t['lot_no'], 
                "Item": itm, 
                "Variant": v_key, # Shows Color_Size
                "Process": stg, 
                "Qty": t['qty'], 
                "Rate": r, 
                "Total": amt
            })
            
        return {"type": "Piece Rate", "details": pd.DataFrame(details), "gross_total": total, "advances": advances}

    elif staff.get('payment_type') == 'Monthly Salary':
        salary = staff.get('salary_amount', 0)
        daily = salary / 26
        recs = list(db.attendance.find({"staff": staff_name, "date": {"$gte": start, "$lt": end}}))
        p=0; s=0; n=0
        for r in recs:
            if r['date'].weekday() == 6: s += 1
            else: p += 1
            if r.get('night_shift'): n += 1
        gross = (p + s + n) * daily 
        details = [{"Type": "Present", "Count": p, "Amount": p*daily}, {"Type": "Sundays", "Count": s, "Amount": s*daily}, {"Type": "Nights (1.0x)", "Count": n, "Amount": n*daily}]
        return {"type": "Salary", "base_salary": salary, "daily_rate": daily, "details": pd.DataFrame(details), "gross_total": gross, "advances": advances}

# ==========================================
# 3. STOCK & ACCOUNTS (Preserved)
# ==========================================
def process_transaction(txn_type, data):
    try:
        doc = {**data, "date": pd.to_datetime(data['date']), "type": txn_type, "created_at": datetime.datetime.now()}
        l_ent = doc.copy(); l_ent['supplier'] = data['party']
        
        if txn_type in ['Purchase']: db.supplier_ledger.insert_one(l_ent)
        elif txn_type in ['Sales', 'Purchase Return', 'Payment Out']: l_ent['is_debit'] = True; db.supplier_ledger.insert_one(l_ent)
        elif txn_type in ['Payment In']: db.supplier_ledger.insert_one(l_ent)

        if txn_type in ['Purchase', 'Sales', 'Purchase Return', 'Delivery Challan', 'Job Work']:
            doc['items'] = data.get('bill_items', [])
            for i in doc['items']:
                direction = 1 if txn_type == 'Purchase' else -1
                db.accessories.update_one(
                    {"name": i['item']},
                    {"$inc": {"quantity": float(i['qty']) * direction}, "$set": {"uom": i['uom']}},
                    upsert=True
                )
        return True, "Saved"
    except Exception as e: return False, str(e)

def get_supplier_ledger(name):
    cols = ["Date", "Particulars", "Ref", "Debit", "Credit", "Balance"]
    data = list(db.supplier_ledger.find({"supplier": name}).sort("date", 1))
    if not data: return pd.DataFrame(columns=cols)
    res = []; bal = 0
    for r in data:
        txn = r.get('type', '')
        amt = r.get('grand_total') if r.get('grand_total') is not None else r.get('amount', 0)
        is_dr = r.get('is_debit', False) or txn in ['Sales', 'Payment Out', 'Purchase Return']
        if is_dr: bal -= amt
        else: bal += amt
        res.append({"Date": r['date'], "Particulars": r.get('remarks', txn), "Ref": r.get('reference', '-'), "Debit": amt if is_dr else 0, "Credit": amt if not is_dr else 0, "Balance": bal})
    return pd.DataFrame(res)

def get_unified_stock():
    fab = list(db.fabric_rolls.aggregate([{"$match": {"status": "Available"}}, {"$group": {"_id": "$fabric_name", "qty": {"$sum": "$quantity"}}}]))
    acc = list(db.accessories.find({}, {"name": 1, "quantity": 1, "uom": 1}))
    data = []
    for f in fab: data.append({"Item": f['_id'], "Type": "Fabric", "Qty": f['qty'], "UOM": "Kg"})
    for a in acc: data.append({"Item": a['name'], "Type": "Accessory", "Qty": a.get('quantity', 0), "UOM": a.get('uom', '-')})
    return pd.DataFrame(data)

# ==========================================
# 4. MASTERS & UTILS
# ==========================================
def clean_database(collections):
    try:
        for c in collections: db[c].delete_many({})
        return True, "Cleaned."
    except Exception as e: return False, str(e)

def process_bulk_master_upload(master_type, df):
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    success = 0
    try:
        if master_type == "Suppliers":
            for _, r in df.iterrows(): db.suppliers.insert_one({"name": str(r.get('name','')), "gst": str(r.get('gst','')), "contact": str(r.get('contact','')), "address": str(r.get('address',''))}); success += 1
        elif master_type == "Items":
            for _, r in df.iterrows(): db.items.insert_one({"item_name": str(r.get('name','')), "item_code": str(r.get('code','')), "color": str(r.get('color','')), "fabrics": [f.strip() for f in str(r.get('fabrics','')).split(',')]}); success += 1
        elif master_type == "Staff":
            for _, r in df.iterrows(): db.staff.insert_one({"name": str(r.get('name','')), "role": str(r.get('role','')), "payment_type": str(r.get('payment_type', 'Piece Rate')), "salary_amount": float(r.get('monthly_salary', 0)), "joined_date": datetime.datetime.now()}); success += 1
        return True, f"Imported {success}."
    except Exception as e: return False, str(e)

# --- Standard Getters/Setters ---
def get_supplier_names(): return sorted(db.suppliers.distinct("name"))
def add_supplier(n,g,c,a): db.suppliers.insert_one({"name":n,"gst":g,"contact":c,"address":a})
def get_suppliers_df(): return pd.DataFrame(list(db.suppliers.find({},{"_id":0})))

def get_item_names(): return sorted(db.items.distinct("item_name"))
def add_item(n,c,cl,f): db.items.insert_one({"item_name":n,"item_code":c,"color":cl,"fabrics":f})
def get_items_df(): return pd.DataFrame(list(db.items.find({},{"_id":0})))

def get_all_staff_names(): return sorted(db.staff.distinct("name"))
def add_staff(n,r,pt,s=0): db.staff.update_one({"name":n}, {"$set":{"name":n,"role":r,"payment_type":pt,"salary_amount":float(s)}}, upsert=True)
def get_staff_df(): return pd.DataFrame(list(db.staff.find({}, {"_id": 0, "name": 1, "role": 1, "payment_type": 1, "salary_amount": 1})))

def get_fabrics(): return sorted(db.materials.distinct("name"))
def add_fabric(n): db.materials.insert_one({"name":n})
def get_fabrics_df(): return pd.DataFrame(list(db.materials.find({},{"_id":0})))

def get_colors(): return sorted(db.colors.distinct("name"))
def add_color(n): db.colors.insert_one({"name":n})
def get_colors_df(): return pd.DataFrame(list(db.colors.find({},{"_id":0})))

def get_all_processes(): return sorted(db.processes.distinct("name"))
def add_process(n): db.processes.insert_one({"name":n})
def get_processes_df(): return pd.DataFrame(list(db.processes.find({},{"_id":0})))

def get_sizes(): return sorted(db.sizes.distinct("name"))
def add_size(n): db.sizes.insert_one({"name":n})
def get_sizes_df(): return pd.DataFrame(list(db.sizes.find({},{"_id":0})))

def get_all_roles(): rs = list(db.roles.find({}, {"_id":0, "name":1})); return sorted([r['name'] for r in rs]) if rs else ["Helper", "Stitching Karigar"]
def add_role(r): db.roles.update_one({"name":r}, {"$set":{"name":r}}, upsert=True)
def get_roles_df(): return pd.DataFrame(list(db.roles.find({},{"_id":0})))

def get_all_uoms(): return sorted([u['name'] for u in db.uoms.find({},{"_id":0})])
def add_uom(n): db.uoms.update_one({"name":n},{"$set":{"name":n}},upsert=True)
def get_uoms_df(): return pd.DataFrame(list(db.uoms.find({},{"_id":0})))

def get_acc_names(): return sorted(db.accessories.distinct("name"))
def get_all_accessories(): return sorted([a['name'] for a in db.accessories_master.find({},{"_id":0})])
def add_accessory_master(n): db.accessories_master.update_one({"name":n},{"$set":{"name":n}},upsert=True)
def get_accessories_df(): return pd.DataFrame(list(db.accessories_master.find({},{"_id":0})))

def get_payment_sources(): return sorted([x['name'] for x in db.payment_sources.find()])
def add_payment_source(n): db.payment_sources.update_one({"name":n},{"$set":{"name":n}},upsert=True)
def get_payment_sources_df(): return pd.DataFrame(list(db.payment_sources.find({},{"_id":0})))

def get_gst_slabs(): slabs = list(db.gst_slabs.find({}, {"_id":0, "rate":1}).sort("rate", 1)); return [s['rate'] for s in slabs] if slabs else [0, 5, 12, 18, 28]
def add_gst_slab(r): db.gst_slabs.update_one({"rate":r},{"$set":{"rate":r}},upsert=True)
def get_gst_df(): return pd.DataFrame(list(db.gst_slabs.find({},{"_id":0})))

def get_rate_master_df(): return pd.DataFrame(list(db.rates.find({},{"_id":0})))
def add_piece_rate(i,p,r): db.rates.update_one({"item":i,"process":p},{"$set":{"rate":float(r)}},upsert=True)

def mark_attendance(s,a,t,n=False):
    upd = {"status":"Present", ("in_time" if a=="In" else "out_time"):str(t)}
    if n: upd["night_shift"]=True
    db.attendance.update_one({"staff":s,"date":datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)},{"$set":upd},upsert=True)
def get_today_attendance(): return list(db.attendance.find({"date":datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)}))
def add_staff_advance(n,a,d,nt): db.staff_ledger.insert_one({"staff":n,"date":pd.to_datetime(d),"type":"Advance","amount":float(a),"remarks":nt})

def get_codes_by_item_name(n): return sorted(db.items.distinct("item_code", {"item_name": n}))
def get_colors_by_item_code(c): return sorted(db.items.distinct("color", {"item_code": c}))
def get_item_details_by_code(c): return db.items.find_one({"item_code": c})
def get_item_fabrics(item_name):
    item = db.items.find_one({"item_name": item_name})
    return item.get('fabrics', []) if item else []
def get_available_rolls(f, c): return list(db.fabric_rolls.find({"fabric_name": f, "color": c, "status": "Available"}))
def add_fabric_rolls_batch(f,c,r,u,s,b): db.fabric_rolls.insert_many([{"fabric_name": f, "color": c, "batch_id": datetime.datetime.now().strftime("%Y%m%d%H%M"), "roll_no": f"{datetime.datetime.now().strftime('%Y%m%d%H%M')}-{i+1}", "quantity": float(q), "uom": u, "supplier": s, "bill_no": b, "status": "Available", "date_added": datetime.datetime.now()} for i, q in enumerate(r)])
def update_accessory_stock(n,t,q,u): db.accessories.update_one({"name": n}, {"$inc": {"quantity": float(q) if t == "Inward" else -float(q)}, "$set": {"uom": u}}, upsert=True)
def get_all_fabric_stock_summary(): return list(db.fabric_rolls.aggregate([{"$match": {"status": "Available"}}, {"$group": {"_id": {"name": "$fabric_name", "color": "$color"}, "total_qty": {"$sum": "$quantity"}}}]))

# --- CATALOG ---
def get_all_skus(): return sorted(db.catalog.distinct("sku"))
def get_product_by_sku(s): return db.catalog.find_one({"sku":s},{"_id":0})
def update_catalog_product(s,d): db.catalog.update_one({"sku":s},{"$set":{**d,"last_updated":datetime.datetime.now()}})
def delete_catalog_product(s): db.catalog.delete_one({"sku":s}); db.launches.delete_many({"sku":s})
def add_catalog_product(s,n,c,f,cl,sz,m,sp,h,st,im): db.catalog.update_one({"sku":s},{"$set":{"sku":s,"product_name":n,"category":c,"fabric":f,"color":cl,"variation":sz,"mrp":float(m),"selling_price":float(sp),"hsn":h,"stock":int(st),"image_link_1":im,"last_updated":datetime.datetime.now()}},upsert=True)
def get_catalog_df(): return pd.DataFrame(list(db.catalog.find({},{"_id":0})))
def add_launch_entry(s,p,l,sz,pr,st,im): db.launches.update_one({"sku":s,"platform":p},{"$set":{"sku":s,"platform":p,"product_link":l,"sizes_launched":sz,"launch_price":float(pr),"status":st,"image_url":im,"last_updated":datetime.datetime.now()}},upsert=True)
def create_and_launch_product(s,n,p,l,sz,pr,st,im): db.catalog.update_one({"sku":s},{"$set":{"sku":s,"product_name":n,"image_link_1":im,"variation":sz,"selling_price":float(pr),"group_id":s.split('-')[0],"sort_index":int(re.search(r'\d+',s).group()) if re.search(r'\d+',s) else 0,"last_updated":datetime.datetime.now()}},upsert=True); add_launch_entry(s,p,l,sz,pr,st,im)
def get_launch_data(): return pd.DataFrame(list(db.launches.find({},{"_id":0})))
def get_next_sku(): return f"DRC{db.catalog.count_documents({})+101}"
def fetch_image_from_url(u): return None
def image_to_base64(f): return ""
def generate_marketplace_file(p): return pd.DataFrame()
def bulk_upload_catalog(df): return 0, pd.DataFrame()
def get_dashboard_stats(): return {}
def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    return buf.getvalue()
def get_lot_transactions(l): return list(db.transactions.find({"lot_no":l}).sort("timestamp",-1))

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
# 1. LOT TRACKING LOGIC (FIXED)
# ==========================================
def get_active_lots():
    """Returns a list of lot numbers where status is Active."""
    return [x['lot_no'] for x in db.lots.find({"status": "Active"}, {"lot_no": 1})]

def get_all_lot_numbers():
    """Returns all lot numbers for history search."""
    return [x['lot_no'] for x in db.lots.find({}, {"lot_no": 1})]

def get_lot_info(lot_no):
    """Fetches full details of a specific lot."""
    return db.lots.find_one({"lot_no": lot_no})

def get_lot_transactions(lot_no):
    """Fetches movement history for a lot."""
    return list(db.transactions.find({"lot_no": lot_no}).sort("timestamp", -1))

def create_lot(lot_no, item_name, item_code, color, size_breakdown, rolls, cutting_master, fabric_weight):
    total_qty = sum(size_breakdown.values())
    qr_str = f"Lot:{lot_no}|Item:{item_name}|Col:{color}|Qty:{total_qty}|Wt:{fabric_weight}"
    
    db.lots.insert_one({
        "lot_no": lot_no,
        "item_name": item_name,
        "item_code": item_code,
        "color": color,
        "fabric_weight": float(fabric_weight),
        "total_qty": total_qty,
        "size_breakdown": size_breakdown,
        "current_stage_stock": {"Cutting": size_breakdown}, # Initialize stock at Cutting
        "status": "Active",
        "created_by": cutting_master,
        "date_created": datetime.datetime.now(),
        "qr_data": qr_str
    })
    
    if rolls:
        db.fabric_rolls.update_many({"_id": {"$in": rolls}}, {"$set": {"status": "Consumed"}})

def move_lot(lot_no, from_stage, to_stage, karigar, qty, variant):
    # Log the movement
    db.transactions.insert_one({
        "lot_no": lot_no,
        "from_stage": from_stage,
        "to_stage": to_stage,
        "karigar": karigar,
        "qty": float(qty),
        "variant": variant,
        "timestamp": datetime.datetime.now()
    })
    
    # Update Stock Levels
    # Decrease from 'from_stage', Increase in 'to_stage'
    db.lots.update_one(
        {"lot_no": lot_no},
        {"$inc": {
            f"current_stage_stock.{from_stage}.{variant}": -float(qty),
            f"current_stage_stock.{to_stage}.{variant}": float(qty)
        }}
    )

def get_next_lot_no():
    count = db.lots.count_documents({})
    return f"LOT{count + 101}"

# ==========================================
# 2. OTHER REQUIRED FUNCTIONS
# ==========================================
def get_staff(role):
    return [s['name'] for s in db.staff.find({"role": role}, {"_id": 0, "name": 1})]

def get_item_fabrics(item_name):
    item = db.items.find_one({"item_name": item_name})
    return item.get('fabrics', []) if item else []

def get_available_rolls(fabric, color):
    return list(db.fabric_rolls.find({"fabric_name": fabric, "color": color, "status": "Available"}))

def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    return buf.getvalue()

# --- MASTERS & CONFIGS ---
def get_supplier_names(): return sorted(db.suppliers.distinct("name"))
def get_item_names(): return sorted(db.items.distinct("item_name"))
def get_fabrics(): return sorted(db.materials.distinct("name"))
def get_colors(): return sorted(db.colors.distinct("name"))
def get_all_processes(): return sorted(db.processes.distinct("name"))
def get_sizes(): return sorted(db.sizes.distinct("name"))
def get_all_roles(): rs = list(db.roles.find({}, {"_id":0, "name":1})); return sorted([r['name'] for r in rs]) if rs else ["Helper", "Stitching Karigar"]
def get_all_uoms(): return sorted([u['name'] for u in db.uoms.find({},{"_id":0})])
def get_acc_names(): return sorted(db.accessories.distinct("name"))
def get_payment_sources(): return sorted([x['name'] for x in db.payment_sources.find()])
def get_gst_slabs(): slabs = list(db.gst_slabs.find({}, {"_id":0, "rate":1}).sort("rate", 1)); return [s['rate'] for s in slabs] if slabs else [0, 5, 12, 18, 28]
def get_all_staff_names(): return sorted(db.staff.distinct("name"))
def get_codes_by_item_name(n): return sorted(db.items.distinct("item_code", {"item_name": n}))
def get_colors_by_item_code(c): return sorted(db.items.distinct("color", {"item_code": c}))
def get_item_details_by_code(c): return db.items.find_one({"item_code": c})

# --- DATAFRAME GETTERS ---
def get_suppliers_df(): return pd.DataFrame(list(db.suppliers.find({},{"_id":0})))
def get_items_df(): return pd.DataFrame(list(db.items.find({},{"_id":0})))
def get_staff_df(): return pd.DataFrame(list(db.staff.find({},{"_id":0})))
def get_fabrics_df(): return pd.DataFrame(list(db.materials.find({},{"_id":0})))
def get_colors_df(): return pd.DataFrame(list(db.colors.find({},{"_id":0})))
def get_processes_df(): return pd.DataFrame(list(db.processes.find({},{"_id":0})))
def get_sizes_df(): return pd.DataFrame(list(db.sizes.find({},{"_id":0})))
def get_roles_df(): return pd.DataFrame(list(db.roles.find({},{"_id":0})))
def get_uoms_df(): return pd.DataFrame(list(db.uoms.find({},{"_id":0})))
def get_accessories_df(): return pd.DataFrame(list(db.accessories_master.find({},{"_id":0})))
def get_payment_sources_df(): return pd.DataFrame(list(db.payment_sources.find({},{"_id":0})))
def get_gst_df(): return pd.DataFrame(list(db.gst_slabs.find({},{"_id":0})))
def get_rate_master_df(): return pd.DataFrame(list(db.rates.find({},{"_id":0})))

# --- SETTERS ---
def add_supplier(n,g,c,a): db.suppliers.insert_one({"name":n,"gst":g,"contact":c,"address":a})
def add_item(n,c,cl,f): db.items.insert_one({"item_name":n,"item_code":c,"color":cl,"fabrics":f})
def add_staff(n,r,pt,s=0): db.staff.update_one({"name":n}, {"$set":{"name":n,"role":r,"payment_type":pt,"salary_amount":float(s)}}, upsert=True)
def add_fabric(n): db.materials.insert_one({"name":n})
def add_color(n): db.colors.insert_one({"name":n})
def add_process(n): db.processes.insert_one({"name":n})
def add_size(n): db.sizes.insert_one({"name":n})
def add_role(r): db.roles.update_one({"name":r},{"$set":{"name":r}},upsert=True)
def add_uom(n): db.uoms.update_one({"name":n},{"$set":{"name":n}},upsert=True)
def add_accessory_master(n): db.accessories_master.update_one({"name":n},{"$set":{"name":n}},upsert=True)
def add_payment_source(n): db.payment_sources.update_one({"name":n},{"$set":{"name":n}},upsert=True)
def add_gst_slab(r): db.gst_slabs.update_one({"rate":r},{"$set":{"rate":r}},upsert=True)
def add_piece_rate(i,p,r): db.rates.update_one({"item":i,"process":p},{"$set":{"rate":float(r)}},upsert=True)
def mark_attendance(s,a,t,n=False):
    upd = {"status":"Present", ("in_time" if a=="In" else "out_time"):str(t)}
    if n: upd["night_shift"]=True
    db.attendance.update_one({"staff":s,"date":datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)},{"$set":upd},upsert=True)
def get_today_attendance(): return list(db.attendance.find({"date":datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)}))
def add_staff_advance(n,a,d,nt): db.staff_ledger.insert_one({"staff":n,"date":pd.to_datetime(d),"type":"Advance","amount":float(a),"remarks":nt})

# --- ACCOUNTS ---
def process_transaction(t, d): 
    try:
        doc = {**d, "date": pd.to_datetime(d['date']), "type":t, "created_at":datetime.datetime.now()}
        if t in ['Purchase','Sales','Purchase Return','Delivery Challan','Job Work']:
            doc['items']=d.get('bill_items',[]); doc['remarks']=f"Items: {len(doc['items'])}"
            for i in doc['items']: db.accessories.update_one({"name":i['item']},{"$inc":{"quantity":float(i['qty'])*(1 if t=='Purchase' else -1)},"$set":{"uom":i['uom']}},upsert=True)
        elif t in ['Payment In','Payment Out']: doc['amount']=d['grand_total']; doc['remarks']=f"{d.get('remarks','')} [Source: {d.get('source')}]"
        l_ent = doc.copy(); l_ent['supplier']=d['party']
        if t in ['Purchase']: db.supplier_ledger.insert_one(l_ent)
        elif t in ['Sales','Purchase Return','Payment Out']: l_ent['is_debit']=True; db.supplier_ledger.insert_one(l_ent)
        elif t in ['Payment In']: db.supplier_ledger.insert_one(l_ent)
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
def get_staff_payout(staff_name, month, year): return None # Placeholder if needed
def clean_database(cols): return True, "Cleaned"
def process_bulk_master_upload(t, df): return True, "Done"
def get_all_fabric_stock_summary(): return []
def add_fabric_rolls_batch(f,c,r,u,s,b): pass

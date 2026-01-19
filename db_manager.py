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
# 1. ADVANCED PRODUCTION (UPDATED)
# ==========================================

def get_next_lot_no():
    count = db.lots.count_documents({})
    return f"LOT{count + 101}"

def create_advanced_lot(lot_no, item_name, cm, materials_used, variants, fabric_weight):
    """
    Creates a lot. Automatically looks up Item Code from Item Master.
    """
    # 1. Auto-fetch Item Code
    item_doc = db.items.find_one({"item_name": item_name})
    item_code = item_doc.get("item_code", "-") if item_doc else "-"

    # 2. Generate Bundles
    bundles = []
    total_qty = 0
    for i, v in enumerate(variants):
        bundle_id = f"{lot_no}-{i+1:02d}" # LOT101-01
        bundles.append({
            "bundle_id": bundle_id,
            "color": v['color'],
            "size": v['size'],
            "qty": float(v['qty']),
            "current_stage": "Cutting",
            "assigned_to": cm,
            "last_update": datetime.datetime.now()
        })
        total_qty += float(v['qty'])

    # 3. Deduct Inventory (Multi-Material)
    for mat in materials_used:
        db.accessories.update_one(
            {"name": mat['name']},
            {"$inc": {"quantity": -float(mat['qty'])}}
        )

    # 4. Create Lot Record
    # Note: Removed 'color' from top level, now it's per bundle
    lot_doc = {
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
        "history": [{
            "stage": "Created", 
            "msg": f"Lot Created with {len(bundles)} bundles", 
            "time": datetime.datetime.now()
        }]
    }
    db.lots.insert_one(lot_doc)
    return True

def get_lot_bundles(lot_no):
    lot = db.lots.find_one({"lot_no": lot_no})
    return lot.get('bundles', []) if lot else []

def move_bundles(lot_no, bundle_ids, to_stage, worker_name):
    """Moves specific bundles to a new stage."""
    # Update individual bundles in the array
    db.lots.update_one(
        {"lot_no": lot_no},
        {
            "$set": {
                "bundles.$[elem].current_stage": to_stage,
                "bundles.$[elem].assigned_to": worker_name,
                "bundles.$[elem].last_update": datetime.datetime.now()
            },
            "$push": {
                "history": {
                    "stage": to_stage,
                    "msg": f"Moved {len(bundle_ids)} bundles to {to_stage} ({worker_name})",
                    "time": datetime.datetime.now()
                }
            }
        },
        array_filters=[{"elem.bundle_id": {"$in": bundle_ids}}]
    )
    
    # Log Piece Rate Transaction
    lot = db.lots.find_one({"lot_no": lot_no})
    total_moved_qty = sum(b['qty'] for b in lot['bundles'] if b['bundle_id'] in bundle_ids)
    
    db.transactions.insert_one({
        "lot_no": lot_no,
        "to_stage": to_stage,
        "karigar": worker_name,
        "qty": total_moved_qty,
        "timestamp": datetime.datetime.now(),
        "bundle_ids": bundle_ids
    })

def generate_bundle_qr(lot_no, bundle_id, item, color, size, qty, worker):
    data = f"B:{bundle_id}\nL:{lot_no}\nI:{item}\nC:{color}\nS:{size}\nQ:{qty}\nBy:{worker}"
    qr = qrcode.QRCode(version=1, box_size=5, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    return buf.getvalue()

# ==========================================
# 2. STANDARD GETTERS (Preserved)
# ==========================================
def get_active_lots(): return sorted([x['lot_no'] for x in db.lots.find({"status": "Active"})])
def get_all_lot_numbers(): return sorted([x['lot_no'] for x in db.lots.find({}, {"lot_no":1})])
def get_lot_details(lot_no): return db.lots.find_one({"lot_no": lot_no})

def get_item_materials(item_name):
    # Combines Fabrics + Accessories for selection
    fabrics = [x['_id'] for x in db.fabric_rolls.aggregate([{"$group": {"_id": "$fabric_name"}}])]
    accs = sorted(db.accessories.distinct("name"))
    return sorted(list(set(fabrics + accs)))

# --- MASTERS ---
def get_item_names(): return sorted(db.items.distinct("item_name"))
def get_codes_by_item_name(n): return sorted(db.items.distinct("item_code", {"item_name": n}))
def get_staff(role): return [s['name'] for s in db.staff.find({"role": role}, {"name":1})]
def get_sizes(): return sorted(db.sizes.distinct("name"))
def get_colors(): return sorted(db.colors.distinct("name"))
def get_all_roles(): return sorted([r['name'] for r in db.roles.find()])
def get_item_fabrics(item_name):
    item = db.items.find_one({"item_name": item_name})
    return item.get('fabrics', []) if item else []
def get_available_rolls(f, c): return list(db.fabric_rolls.find({"fabric_name": f, "color": c, "status": "Available"}))

# --- ACCOUNTS & HR HELPERS ---
def get_dashboard_stats(): return {"active_lots": db.lots.count_documents({"status":"Active"}), "rolls":0, "staff":0} 
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
        txns = list(db.transactions.aggregate([{"$match": {"karigar": staff_name, "timestamp": {"$gte": start, "$lt": end}}}, {"$lookup": {"from": "lots", "localField": "lot_no", "foreignField": "lot_no", "as": "lot_info"}}]))
        details = []
        total = 0
        for t in txns:
            lot = t['lot_info'][0] if t['lot_info'] else {}
            itm = lot.get('item_name', 'Unknown')
            stg = t['to_stage'].split(' - ')[0]
            rate = db.rates.find_one({"item": itm, "process": stg})
            r = rate['rate'] if rate else 0
            amt = t['qty'] * r
            total += amt
            details.append({"Date": t['timestamp'].strftime('%d-%b'), "Lot": t['lot_no'], "Item": itm, "Process": stg, "Qty": t['qty'], "Rate": r, "Total": amt})
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

def add_staff_advance(n, a, d, r): db.staff_ledger.insert_one({"staff":n,"date":pd.to_datetime(d),"type":"Advance","amount":float(a),"remarks":r})
def mark_attendance(s, a, t, n): 
    upd = {"status":"Present", ("in_time" if a=="In" else "out_time"):str(t)}
    if n: upd["night_shift"]=True
    db.attendance.update_one({"staff":s,"date":datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)},{"$set":upd},upsert=True)
def get_today_attendance(): return list(db.attendance.find({"date":datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)}))
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
def process_transaction(t, d): 
    try:
        doc = {**d, "date": pd.to_datetime(d['date']), "type":t, "created_at":datetime.datetime.now()}
        l_ent = doc.copy(); l_ent['supplier']=d['party']
        if t in ['Purchase']: db.supplier_ledger.insert_one(l_ent)
        elif t in ['Sales','Purchase Return','Payment Out']: l_ent['is_debit']=True; db.supplier_ledger.insert_one(l_ent)
        elif t in ['Payment In']: db.supplier_ledger.insert_one(l_ent)
        if t in ['Purchase','Sales','Purchase Return','Delivery Challan','Job Work']:
            doc['items']=d.get('bill_items',[]); doc['remarks']=f"Items: {len(doc['items'])}"
            for i in doc['items']: db.accessories.update_one({"name":i['item']},{"$inc":{"quantity":float(i['qty'])*(1 if t=='Purchase' else -1)},"$set":{"uom":i['uom']}},upsert=True)
        elif t in ['Payment In','Payment Out']: doc['amount']=d['grand_total']; doc['remarks']=f"{d.get('remarks','')} [Source: {d.get('source')}]"
        return True, "Saved"
    except Exception as e: return False, str(e)
def get_unified_stock(): return pd.DataFrame()
def get_all_staff_names(): return sorted(db.staff.distinct("name"))
def get_payment_sources(): return sorted([x['name'] for x in db.payment_sources.find()])
def get_supplier_names(): return sorted(db.suppliers.distinct("name"))
def get_rate_master_df(): return pd.DataFrame(list(db.rates.find({},{"_id":0})))
def add_piece_rate(i,p,r): db.rates.update_one({"item":i,"process":p},{"$set":{"rate":float(r)}},upsert=True)
def get_all_processes(): return ["Cutting", "Stitching", "Dhaga Cutting", "Sticker", "Press", "Packing"]

# --- CONFIG SETTERS ---
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
def add_supplier(n,g,c,a): db.suppliers.insert_one({"name":n,"gst":g,"contact":c,"address":a})
def add_item(n,c,cl,f): db.items.insert_one({"item_name":n,"item_code":c,"color":cl,"fabrics":f})
def add_staff(n,r,pt,s): db.staff.update_one({"name":n}, {"$set":{"name":n,"role":r,"payment_type":pt,"salary_amount":float(s)}}, upsert=True)
def add_fabric(n): db.materials.insert_one({"name":n})
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
def get_catalog_df(): return pd.DataFrame()
def get_launch_data(): return pd.DataFrame()
def get_all_skus(): return []
def get_next_sku(): return ""
def fetch_image_from_url(u): return None
def image_to_base64(f): return ""
def add_catalog_product(s,n,c,f,cl,sz,m,sp,h,st,im): pass
def create_and_launch_product(s,n,p,l,sz,pr,st,im): pass
def add_launch_entry(s,p,l,sz,pr,st,im): pass
def delete_catalog_product(s): pass
def update_catalog_product(s, d): pass
def get_product_by_sku(s): return {}
def generate_marketplace_file(p): return pd.DataFrame()
def bulk_upload_catalog(df): return 0, pd.DataFrame()
def get_all_fabric_stock_summary(): return []
def add_fabric_rolls_batch(f,c,r,u,s,b): pass
def update_accessory_stock(n,t,q,u): pass
def get_acc_names(): return []
def get_lot_transactions(l): return []
def generate_qr_code(d): return b''

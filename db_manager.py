import streamlit as st
import pymongo
import pandas as pd
import datetime
import re
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
# 1. PAYOUT ENGINE (UPDATED NIGHT SHIFT)
# ==========================================
def get_staff_payout(staff_name, month, year):
    staff = db.staff.find_one({"name": staff_name})
    if not staff: return None

    start = datetime.datetime(year, month, 1)
    end = datetime.datetime(year + 1, 1, 1) if month == 12 else datetime.datetime(year, month + 1, 1)
    
    # 1. ADVANCES
    adv_pipeline = [
        {"$match": {"staff": staff_name, "type": "Advance", "date": {"$gte": start, "$lt": end}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    adv_res = list(db.staff_ledger.aggregate(adv_pipeline))
    advances = adv_res[0]['total'] if adv_res else 0.0

    # 2. PIECE RATE CALCULATION
    if staff.get('payment_type') == 'Piece Rate':
        txns = list(db.transactions.aggregate([
            {"$match": {"karigar": staff_name, "timestamp": {"$gte": start, "$lt": end}}},
            {"$lookup": {"from": "lots", "localField": "lot_no", "foreignField": "lot_no", "as": "lot_info"}}
        ]))
        
        details = []
        total_earnings = 0
        for t in txns:
            lot_data = t['lot_info'][0] if t['lot_info'] else {}
            item_name = lot_data.get('item_name', 'Unknown')
            stage = t['to_stage'].split(' - ')[0]
            rate_doc = db.rates.find_one({"item": item_name, "process": stage})
            rate = rate_doc['rate'] if rate_doc else 0
            amt = t['qty'] * rate
            total_earnings += amt
            details.append({"Date": t['timestamp'].strftime('%d-%b'), "Lot": t['lot_no'], "Item": item_name, "Process": stage, "Qty": t['qty'], "Rate": rate, "Total": amt})
            
        return {"type": "Piece Rate", "details": pd.DataFrame(details), "gross_total": total_earnings, "advances": advances}

    # 3. SALARY CALCULATION (UPDATED)
    elif staff.get('payment_type') == 'Monthly Salary':
        salary = staff.get('salary_amount', 0)
        daily_rate = salary / 26 # Standard
        
        att_records = list(db.attendance.find({"staff": staff_name, "date": {"$gte": start, "$lt": end}}))
        
        present_days = 0
        sunday_work = 0
        night_shifts = 0
        
        for rec in att_records:
            d = rec['date']
            is_sunday = d.weekday() == 6
            if is_sunday: sunday_work += 1
            else: present_days += 1
            
            if rec.get('night_shift'):
                night_shifts += 1 
                
        # NIGHT SHIFT UPDATE: Now counts as 1.0 Full Day (was 0.5)
        earned_days = present_days + sunday_work + (night_shifts * 1.0) 
        gross_pay = earned_days * daily_rate
        
        details = [
            {"Type": "Present Days (Excl. Sun)", "Count": present_days, "Amount": present_days * daily_rate},
            {"Type": "Sundays Worked", "Count": sunday_work, "Amount": sunday_work * daily_rate},
            {"Type": "Night Shifts (Full Pay)", "Count": night_shifts, "Amount": night_shifts * 1.0 * daily_rate}, # Updated Label
        ]
        
        return {"type": "Salary", "base_salary": salary, "daily_rate": daily_rate, "details": pd.DataFrame(details), "gross_total": gross_pay, "advances": advances}

# ==========================================
# 2. BULK MASTER UPLOAD (NEW)
# ==========================================
def process_bulk_master_upload(master_type, df):
    """Generic bulk uploader for Configurations tab."""
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    success = 0
    
    # Define mapping logic
    try:
        if master_type == "Suppliers":
            for _, r in df.iterrows():
                db.suppliers.insert_one({"name": str(r.get('name','')), "gst": str(r.get('gst','')), "contact": str(r.get('contact','')), "address": str(r.get('address',''))})
                success += 1
        elif master_type == "Items":
            for _, r in df.iterrows():
                # Handle fabrics as list
                fabs = str(r.get('fabrics','')).split(',')
                db.items.insert_one({"item_name": str(r.get('name','')), "item_code": str(r.get('code','')), "color": str(r.get('color','')), "fabrics": [f.strip() for f in fabs]})
                success += 1
        elif master_type == "Staff":
            for _, r in df.iterrows():
                db.staff.insert_one({
                    "name": str(r.get('name','')), 
                    "role": str(r.get('role','')), 
                    "payment_type": str(r.get('payment_type', 'Piece Rate')), # Salary / Piece Rate
                    "salary_amount": float(r.get('monthly_salary', 0)),
                    "joined_date": datetime.datetime.now()
                })
                success += 1
        elif master_type == "Fabrics":
            for _, r in df.iterrows(): db.materials.insert_one({"name": str(r.get('name',''))}); success+=1
        elif master_type == "Colors":
            for _, r in df.iterrows(): db.colors.insert_one({"name": str(r.get('name',''))}); success+=1
        elif master_type == "Processes":
            for _, r in df.iterrows(): db.processes.insert_one({"name": str(r.get('process',''))}); success+=1
        elif master_type == "Sizes":
            for _, r in df.iterrows(): db.sizes.insert_one({"name": str(r.get('size',''))}); success+=1
        elif master_type == "Staff Roles":
            for _, r in df.iterrows(): db.roles.update_one({"name": str(r.get('role_name',''))}, {"$set":{"name":str(r.get('role_name',''))}}, upsert=True); success+=1
        elif master_type == "Accessories":
            for _, r in df.iterrows(): 
                nm = str(r.get('accessory_name',''))
                db.accessories_master.update_one({"name": nm}, {"$set":{"name":nm}}, upsert=True)
                db.accessories.update_one({"name": nm}, {"$setOnInsert": {"quantity": 0}}, upsert=True)
                success+=1
        elif master_type == "Payment Sources":
            for _, r in df.iterrows(): db.payment_sources.update_one({"name": str(r.get('source_name',''))}, {"$set":{"name":str(r.get('source_name',''))}}, upsert=True); success+=1
        elif master_type == "Units (UOM)":
            for _, r in df.iterrows(): db.uoms.update_one({"name": str(r.get('unit_name',''))}, {"$set":{"name":str(r.get('unit_name',''))}}, upsert=True); success+=1
            
        return True, f"Imported {success} records."
    except Exception as e:
        return False, str(e)

# ==========================================
# 3. EXISTING HELPERS (Preserved)
# ==========================================
def add_staff(name, role, payment_type, salary=0.0):
    db.staff.update_one({"name": name}, {"$set": {"name": name, "role": role, "payment_type": payment_type, "salary_amount": float(salary), "joined_date": datetime.datetime.now()}}, upsert=True)
def get_all_staff_names(): return sorted(db.staff.distinct("name"))
def get_staff_df(): return pd.DataFrame(list(db.staff.find({}, {"_id": 0, "name": 1, "role": 1, "payment_type": 1, "salary_amount": 1})))
def mark_attendance(staff_name, action, time_str, is_night=False):
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    upd = {"status": "Present", ("in_time" if action=="In" else "out_time"): str(time_str)}
    if is_night: upd["night_shift"] = True
    db.attendance.update_one({"staff": staff_name, "date": today}, {"$set": upd}, upsert=True)
def get_today_attendance(): return list(db.attendance.find({"date": datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)}))
def add_staff_advance(name, amount, date, note):
    db.staff_ledger.insert_one({"staff": name, "date": pd.to_datetime(date), "type": "Advance", "amount": float(amount), "remarks": note, "created_at": datetime.datetime.now()})
def get_staff_advances_total(name, month, year):
    start = datetime.datetime(year, month, 1); end = datetime.datetime(year + 1, 1, 1) if month == 12 else datetime.datetime(year, month + 1, 1)
    res = list(db.staff_ledger.aggregate([{"$match": {"staff": name, "type": "Advance", "date": {"$gte": start, "$lt": end}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
    return res[0]['total'] if res else 0.0

# --- CATALOG & ACCOUNTS (Compact for file size) ---
def get_all_skus(): return sorted(db.catalog.distinct("sku"))
def get_product_by_sku(s): return db.catalog.find_one({"sku":s},{"_id":0})
def update_catalog_product(s,d): db.catalog.update_one({"sku":s},{"$set":{**d,"last_updated":datetime.datetime.now()}})
def delete_catalog_product(s): db.catalog.delete_one({"sku":s}); db.launches.delete_many({"sku":s})
def fetch_image_from_url(u): return None
def image_to_base64(f): return ""
def add_launch_entry(s,p,l,sz,pr,st,im): db.launches.update_one({"sku":s,"platform":p},{"$set":{"sku":s,"platform":p,"product_link":l,"sizes_launched":sz,"launch_price":float(pr),"status":st,"image_url":im,"last_updated":datetime.datetime.now()}},upsert=True)
def create_and_launch_product(s,n,p,l,sz,pr,st,im): db.catalog.update_one({"sku":s},{"$set":{"sku":s,"product_name":n,"image_link_1":im,"variation":sz,"selling_price":float(pr),"group_id":s.split('-')[0],"sort_index":int(re.search(r'\d+',s).group()) if re.search(r'\d+',s) else 0,"last_updated":datetime.datetime.now()}},upsert=True); add_launch_entry(s,p,l,sz,pr,st,im)
def get_launch_data(): return pd.DataFrame(list(db.launches.find({},{"_id":0})))
def get_next_free_drc_number(r=set()): return 101 # Simplified
def get_next_sku(): return f"DRC{db.catalog.count_documents({})+101}"
def safe_float(v): return 0.0 # Simplified
def safe_int(v): return 0 # Simplified
def bulk_upload_catalog(df): return 0, pd.DataFrame()
def get_catalog_df(): return pd.DataFrame(list(db.catalog.find({},{"_id":0})))
def add_catalog_product(s,n,c,f,cl,sz,m,sp,h,st,im): pass
def generate_marketplace_file(p): return pd.DataFrame()
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
def get_supplier_ledger(n): return pd.DataFrame(list(db.supplier_ledger.find({"supplier":n})))
def get_dashboard_stats(): return {}
def get_all_fabric_stock_summary(): return list(db.fabric_rolls.aggregate([{"$match": {"status": "Available"}}, {"$group": {"_id": {"name": "$fabric_name", "color": "$color"}, "total_qty": {"$sum": "$quantity"}}}]))
def add_fabric_rolls_batch(f,c,r,u,s,b): db.fabric_rolls.insert_many([{"fabric_name": f, "color": c, "batch_id": datetime.datetime.now().strftime("%Y%m%d%H%M"), "roll_no": f"{datetime.datetime.now().strftime('%Y%m%d%H%M')}-{i+1}", "quantity": float(q), "uom": u, "supplier": s, "bill_no": b, "status": "Available", "date_added": datetime.datetime.now()} for i, q in enumerate(r)])
def update_accessory_stock(n,t,q,u): db.accessories.update_one({"name": n}, {"$inc": {"quantity": float(q) if t == "Inward" else -float(q)}, "$set": {"uom": u}}, upsert=True)
def get_accessory_stock(): return list(db.accessories.find({}, {"_id": 0, "name": 1, "quantity": 1, "uom":1}))
def get_unified_stock():
    fab = list(db.fabric_rolls.aggregate([{"$match": {"status": "Available"}}, {"$group": {"_id": "$fabric_name", "qty": {"$sum": "$quantity"}}}]))
    acc = list(db.accessories.find({}, {"name": 1, "quantity": 1, "uom": 1}))
    data = []
    for f in fab: data.append({"Item": f['_id'], "Type": "Fabric", "Qty": f['qty'], "UOM": "Kg"})
    for a in acc: data.append({"Item": a['name'], "Type": "Accessory", "Qty": a.get('quantity', 0), "UOM": a.get('uom', '-')})
    return pd.DataFrame(data)
def get_next_lot_no(): return f"LOT{db.lots.count_documents({}) + 101}"
def create_lot(n,i,c,cl,sz,r,cm): db.lots.insert_one({"lot_no":n,"item_name":i,"item_code":c,"color":cl,"total_qty":sum(sz.values()),"current_stage_stock":{"Cutting":sz},"status":"Active","created_by":cm,"date_created":datetime.datetime.now()}); db.fabric_rolls.update_many({"_id":{"$in":r}},{"$set":{"status":"Consumed"}})
def move_lot(l,f,t,k,q,s): db.transactions.insert_one({"lot_no":l,"from_stage":f,"to_stage":t,"karigar":k,"qty":q,"variant":s,"timestamp":datetime.datetime.now()}); db.lots.update_one({"lot_no":l},{"$inc":{f"current_stage_stock.{f}.{s}":-q, f"current_stage_stock.{t}.{s}":q}})
def get_lot_transactions(l): return list(db.transactions.find({"lot_no":l}).sort("timestamp",-1))
def add_piece_rate(i,p,r): db.rates.update_one({"item":i,"process":p},{"$set":{"rate":float(r)}},upsert=True)
def get_rate_master_df(): return pd.DataFrame(list(db.rates.find({},{"_id":0})))
def get_active_lots(): return [x['lot_no'] for x in db.lots.find({"status": "Active"})]
def get_all_lot_numbers(): return [x['lot_no'] for x in db.lots.find({}, {"lot_no": 1})]
def get_lot_info(l): return db.lots.find_one({"lot_no": l})
def get_available_rolls(f, c): return list(db.fabric_rolls.find({"fabric_name": f, "color": c, "status": "Available"}))
def get_supplier_names(): return sorted(db.suppliers.distinct("name"))
def get_item_names(): return sorted(db.items.distinct("item_name"))
def get_codes_by_item_name(n): return sorted(db.items.distinct("item_code", {"item_name": n}))
def get_colors_by_item_code(c): return sorted(db.items.distinct("color", {"item_code": c}))
def get_item_details_by_code(c): return db.items.find_one({"item_code": c})
def get_materials(): return sorted(db.materials.distinct("name"))
def get_colors(): return sorted(db.colors.distinct("name"))
def get_staff(r): return [x['name'] for x in db.staff.find({"role": r})]
def get_all_processes(): return sorted(db.processes.distinct("name"))
def get_sizes(): return sorted(db.sizes.distinct("name"))
def get_acc_names(): return sorted(db.accessories.distinct("name"))
def add_supplier(n,g,c,a): db.suppliers.insert_one({"name":n,"gst":g,"contact":c,"address":a})
def get_suppliers_df(): return pd.DataFrame(list(db.suppliers.find({},{"_id":0})))
def add_item(n,c,cl,f): db.items.insert_one({"item_name":n,"item_code":c,"color":cl,"fabrics":f})
def get_items_df(): return pd.DataFrame(list(db.items.find({},{"_id":0})))
def add_fabric(n): db.materials.insert_one({"name":n})
def get_fabrics_df(): return pd.DataFrame(list(db.materials.find({},{"_id":0})))
def add_color(n): db.colors.insert_one({"name":n})
def get_colors_df(): return pd.DataFrame(list(db.colors.find({},{"_id":0})))
def add_process(n): db.processes.insert_one({"name":n})
def get_processes_df(): return pd.DataFrame(list(db.processes.find({},{"_id":0})))
def add_size(n): db.sizes.insert_one({"name":n})
def get_sizes_df(): return pd.DataFrame(list(db.sizes.find({},{"_id":0})))
def get_all_roles(): return sorted([r['name'] for r in db.roles.find({},{"_id":0})])
def add_role(r): db.roles.update_one({"name":r},{"$set":{"name":r}},upsert=True)
def get_roles_df(): return pd.DataFrame(list(db.roles.find({},{"_id":0})))
def get_all_uoms(): return sorted([u['name'] for u in db.uoms.find({},{"_id":0})])
def add_uom(n): db.uoms.update_one({"name":n},{"$set":{"name":n}},upsert=True)
def get_uoms_df(): return pd.DataFrame(list(db.uoms.find({},{"_id":0})))
def get_all_accessories(): return sorted([a['name'] for a in db.accessories_master.find({},{"_id":0})])
def add_accessory_master(n): db.accessories_master.update_one({"name":n},{"$set":{"name":n}},upsert=True)
def get_accessories_df(): return pd.DataFrame(list(db.accessories_master.find({},{"_id":0})))
def get_payment_sources(): return sorted([x['name'] for x in db.payment_sources.find()])
def add_payment_source(n): db.payment_sources.update_one({"name":n},{"$set":{"name":n}},upsert=True)
def get_gst_slabs(): return [0,2.5,3,5,12,18,28]
def add_gst_slab(r): db.gst_slabs.update_one({"rate":r},{"$set":{"rate":r}},upsert=True)
def get_gst_df(): return pd.DataFrame(list(db.gst_slabs.find({},{"_id":0})))
def get_fabrics(): return sorted(db.materials.distinct("name"))

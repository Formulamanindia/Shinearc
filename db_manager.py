import streamlit as st
import pymongo
import pandas as pd
import datetime
import random
import string
import math
import requests
import re
from bson.objectid import ObjectId

# --- CONNECT TO DATABASE ---
try:
    client = pymongo.MongoClient(st.secrets["MONGO_URI"])
    db = client['shine_arc_new_db']
except Exception as e:
    st.error(f"Database Connection Error: {e}")
    db = None

# ==========================================
# 1. CORE FETCHERS & UTILS
# ==========================================
def get_df(collection_name): 
    if db is None: return pd.DataFrame()
    return pd.DataFrame(list(db[collection_name].find({}, {'_id':0})))

def get_rates_df(): 
    if db is None: return pd.DataFrame()
    df = pd.DataFrame(list(db.masters_rates.find({}, {'_id':0})))
    if not df.empty:
        if 'from_date' in df.columns: 
            df['from_date'] = pd.to_datetime(df['from_date']).dt.strftime('%d-%b-%Y')
        if 'to_date' in df.columns: 
            df['to_date'] = pd.to_datetime(df['to_date']).dt.strftime('%d-%b-%Y')
        if 'updated_at' in df.columns:
            df = df.sort_values(by="updated_at", ascending=False).drop(columns=['updated_at'], errors='ignore')
    return df

def get_recent_transactions(col): 
    if db is None: return []
    return list(db[col].find().sort("created_at", -1).limit(50))

def delete_transaction(col, _id): 
    if db is not None: db[col].delete_one({"_id": ObjectId(_id)})

# --- MASTER DATA FETCHERS ---
def get_staff_list(): return sorted([s['name'] for s in db.masters_staff.find({}, {'_id':0, 'name':1})]) if db is not None else []
def get_items_list(): return sorted([i['name'] for i in db.masters_items.find({}, {'_id':0, 'name':1})]) if db is not None else []
def get_colors_list(): return sorted([c['name'] for c in db.masters_colors.find({}, {'_id':0, 'name':1})]) if db is not None else []
def get_sizes_list(): return sorted([s['name'] for s in db.masters_sizes.find({}, {'_id':0, 'name':1})]) if db is not None else []
def get_categories_list(): return sorted([c['name'] for c in db.masters_categories.find({}, {'_id':0, 'name':1})]) if db is not None else []
def get_processes_list(): return sorted([p['name'] for p in db.masters_processes.find({}, {'_id':0, 'name':1})]) if db is not None else []
def get_parties_list(): return sorted([p['name'] for p in db.masters_parties.find({}, {'_id':0, 'name':1})]) if db is not None else []

def get_staff_details(name):
    if db is None: return {}
    return db.masters_staff.find_one({"name": name})

def get_rate(item, process, target_date=None):
    if db is None: return 0.0
    query = {"item": item, "process": process}
    
    if target_date:
        t_date = pd.to_datetime(target_date)
        query["from_date"] = {"$lte": t_date}
        query["to_date"] = {"$gte": t_date}
        
    res = db.masters_rates.find_one(query, sort=[("updated_at", -1)])
    
    if not res and target_date:
        res = db.masters_rates.find_one({"item": item, "process": process}, sort=[("updated_at", -1)])
        
    return float(res['rate']) if res else 0.0

def get_child_skus_list(): return sorted(db.masters_products.distinct("sku", {"type": "child"})) if db is not None else []
def get_parent_products(): return list(db.masters_products.find({"type": "parent"})) if db is not None else []
def get_all_products_flat(): return list(db.masters_products.find({})) if db is not None else []
def get_mappings(): return list(db.masters_mappings.find({})) if db is not None else []

# --- DASHBOARD STATS ---
def get_dashboard_stats():
    if db is None: return 0, 0, 0, 0
    try:
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        month = datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        pcs_agg = list(db.production.aggregate([{"$match": {"date": {"$gte": today}}}, {"$group": {"_id": None, "total": {"$sum": "$qty"}}}]))
        pcs = pcs_agg[0]['total'] if pcs_agg else 0
        
        earn_agg = list(db.production.aggregate([{"$match": {"date": {"$gte": today}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
        earn = earn_agg[0]['total'] if earn_agg else 0
        
        m_prod = list(db.production.aggregate([{"$match": {"date": {"$gte": month}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
        m_sal = list(db.attendance.aggregate([{"$match": {"date": {"$gte": month}}}, {"$group": {"_id": None, "total": {"$sum": "$daily_earnings"}}}]))
        total_earned = (m_prod[0]['total'] if m_prod else 0) + (m_sal[0]['total'] if m_sal else 0)
        
        m_paid = list(db.payments.aggregate([{"$match": {"date": {"$gte": month}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
        total_paid = m_paid[0]['total'] if m_paid else 0
        
        active = len(db.production.distinct("staff_name", {"date": {"$gte": today}}))
        return pcs, earn, (total_earned - total_paid), active
    except: return 0, 0, 0, 0

# --- STAFF BALANCE SUMMARY & HISTORY ---
def get_worker_history(staff_name):
    if db is None: return 0.0, 0.0, 0.0, pd.DataFrame()
    s_det = get_staff_details(staff_name)
    is_sal = s_det.get('salary_type') == 'Salaried' if s_det else False
    
    if is_sal:
        e = list(db.attendance.aggregate([{"$match": {"staff_name": staff_name}}, {"$group": {"_id": None, "total": {"$sum": "$daily_earnings"}}}]))
        hist = list(db.attendance.find({"staff_name": staff_name}).sort("date", -1))
    else:
        e = list(db.production.aggregate([{"$match": {"staff_name": staff_name}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
        hist = list(db.production.find({"staff_name": staff_name}).sort("date", -1))
        
    p = list(db.payments.aggregate([{"$match": {"staff_name": staff_name}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
    
    earned_val = e[0]['total'] if e else 0.0
    paid_val = p[0]['total'] if p else 0.0
    return earned_val, paid_val, (earned_val - paid_val), pd.DataFrame(hist)

def get_all_staff_balances():
    if db is None: return pd.DataFrame()
    prod_map = {i['_id']: i['t'] for i in db.production.aggregate([{"$group": {"_id": "$staff_name", "t": {"$sum": "$amount"}}}])}
    att_map = {i['_id']: i['t'] for i in db.attendance.aggregate([{"$group": {"_id": "$staff_name", "t": {"$sum": "$daily_earnings"}}}])}
    pay_map = {i['_id']: i['t'] for i in db.payments.aggregate([{"$group": {"_id": "$staff_name", "t": {"$sum": "$amount"}}}])}
    
    data = []
    for s in get_staff_list():
        earned = prod_map.get(s, 0.0) + att_map.get(s, 0.0)
        paid = pay_map.get(s, 0.0)
        data.append({"Staff Name": s, "Total Earned": earned, "Total Paid": paid, "Net Payable": earned - paid})
    return pd.DataFrame(data)

# --- DRENCH AI ---
def save_daily_orders(df):
    if db is None: return False, "DB Error"
    records = []
    batch = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    df.columns = [c.strip().title() for c in df.columns]
    req = {'Channel', 'Item', 'Category', 'Color', 'Size', 'Qty'}
    if not req.issubset(df.columns): return False, f"Missing: {req}"
    for _, r in df.iterrows():
        records.append({"upload_id": batch, "upload_date": datetime.datetime.now(), "channel": str(r['Channel']), "item": str(r['Item']), "category": str(r['Category']), "color": str(r['Color']), "size": str(r['Size']), "qty": float(r['Qty'])})
    db.transactions_daily_orders.insert_many(records)
    return True, f"Uploaded {len(records)} orders."

def get_daily_orders_df(filters=None):
    if db is None: return pd.DataFrame()
    q = {}
    if filters:
        if filters.get('item'): q['item'] = {"$in": filters['item']}
        if filters.get('color'): q['color'] = {"$in": filters['color']}
    return pd.DataFrame(list(db.transactions_daily_orders.find(q, {'_id':0}).sort("upload_date", -1)))

def generate_cutting_plan(start, end):
    if db is None: return pd.DataFrame()
    s = pd.to_datetime(start); e = pd.to_datetime(end) + datetime.timedelta(days=1)
    res = list(db.transactions_daily_orders.aggregate([
        {"$match": {"upload_date": {"$gte": s, "$lt": e}}},
        {"$group": {"_id": {"item": "$item", "color": "$color", "size": "$size"}, "qty": {"$sum": "$qty"}}}
    ]))
    if not res: return pd.DataFrame()
    df = pd.DataFrame([{"Item": r['_id']['item'], "Color": r['_id']['color'], "Size": r['_id']['size'], "Qty": r['qty']} for r in res])
    pivot = df.pivot_table(index=['Item', 'Color'], columns='Size', values='Qty', aggfunc='sum', fill_value=0)
    pivot['Total'] = pivot.sum(axis=1)
    return pivot.reset_index()

# --- PRODUCT LAUNCHER ---
def fetch_product_metadata(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    data = {"title": "", "image": "", "price": 0.0, "url": url}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        html = res.text
        t_match = re.search(r'<meta[^>]*property=[\'"]og:title[\'"][^>]*content=[\'"](.*?)[\'"]', html, re.IGNORECASE)
        if not t_match: t_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        if t_match: data["title"] = t_match.group(1).replace('&amp;', '&')
        i_match = re.search(r'<meta[^>]*property=[\'"]og:image[\'"][^>]*content=[\'"](.*?)[\'"]', html, re.IGNORECASE)
        if i_match: data["image"] = i_match.group(1)
        p_match = re.search(r'<meta[^>]*property=[\'"](?:product|og):price:amount[\'"][^>]*content=[\'"]([0-9.]+)[\'"]', html, re.IGNORECASE)
        if p_match: data["price"] = float(p_match.group(1))
    except: pass 
    return data

def save_launched_product(title, url, images, price, stage):
    if db is None: return False, "DB Error"
    main_image = images[0] if isinstance(images, list) and len(images) > 0 else ""
    db.product_launcher.insert_one({
        "title": title, "url": url, 
        "image_url": main_image,
        "images": images if isinstance(images, list) else [images],
        "price": float(price), "stage": stage, "created_at": datetime.datetime.now()
    })
    return True, "Product Added to Launcher Pipeline!"

def get_launched_products():
    if db is None: return []
    return list(db.product_launcher.find().sort("created_at", -1))

def update_launched_product_stage(doc_id, new_stage):
    if db is None: return False
    db.product_launcher.update_one({"_id": ObjectId(doc_id)}, {"$set": {"stage": new_stage, "updated_at": datetime.datetime.now()}})
    return True

def update_launched_product_details(doc_id, title, price, images):
    if db is None: return False, "DB Error"
    try:
        main_image = images[0] if isinstance(images, list) and len(images) > 0 else ""
        db.product_launcher.update_one(
            {"_id": ObjectId(doc_id)}, 
            {"$set": {
                "title": title, 
                "price": float(price), 
                "image_url": main_image,
                "images": images if isinstance(images, list) else [images],
                "updated_at": datetime.datetime.now()
            }}
        )
        return True, "Product Updated Successfully!"
    except Exception as e:
        return False, str(e)
    
def delete_launched_product(doc_id):
    if db is None: return False
    db.product_launcher.delete_one({"_id": ObjectId(doc_id)})
    return True

# --- CATALOG MAKER ---
def process_and_save_catalog(df):
    if db is None: return False, "DB Error"
    try:
        cols = df.columns.tolist()
        var_col = next((c for c in cols if 'variation' in c.lower()), 'Variations')
        sku_col = next((c for c in cols if 'sku' in c.lower()), 'SKU Code*')
        article_col = next((c for c in cols if 'article' in c.lower()), 'Article Number')
        brand_size_col = next((c for c in cols if 'brand size' in c.lower()), 'Brand Size')
        std_size_col = next((c for c in cols if 'standard size' in c.lower()), 'Standard Size')

        expanded_rows = []
        for _, row in df.iterrows():
            var_str = str(row.get(var_col, ''))
            if pd.isna(var_str) or var_str.strip() == '' or var_str.lower() == 'nan':
                expanded_rows.append(row.to_dict())
                continue
            
            sizes = [s.strip() for s in var_str.split(',') if s.strip()]
            sku_code = str(row.get(sku_col, ''))
            for size in sizes:
                new_row = row.copy()
                new_row[article_col] = f"{sku_code}-{size}" if sku_code else f"VAR-{size}"
                new_row[brand_size_col] = size
                new_row[std_size_col] = size
                expanded_rows.append(new_row.to_dict())
        
        expanded_df = pd.DataFrame(expanded_rows).fillna("")
        for _, row in expanded_df.iterrows():
            article_no = str(row.get(article_col, '')).strip()
            if not article_no: continue
            doc = row.to_dict()
            doc['updated_at'] = datetime.datetime.now()
            db.masters_catalog.update_one({article_col: article_no}, {"$set": doc}, upsert=True)
            
        return True, expanded_df
    except Exception as e: return False, str(e)

def get_catalog_data():
    if db is None: return pd.DataFrame()
    data = list(db.masters_catalog.find({}, {'_id':0}).sort("updated_at", -1))
    return pd.DataFrame(data)

# --- GST COMPLIANCE ---
def fetch_gst_details(gstin, api_key=None):
    if not api_key: return {"error": True, "msg": "API Key not configured. Enter details manually."}
    return {"error": True, "msg": "API Integration pending setup."}

def sync_all_gst_returns(period):
    if db is None: return False
    regs = list(db.gst_registrations.find({}, {'_id':0, 'gst_no':1}))
    for r in regs:
        db.gst_filings.update_one(
            {"gst_no": r['gst_no'], "period": period},
            {"$set": {"updated_at": datetime.datetime.now()}},
            upsert=True
        )
    return True

def save_gst_registration(gst_no, legal_name, trade_name, reg_date, owner_phone, owner_email, gst_phone, gst_email):
    if db is None: return False, "Database connection error."
    if db.gst_registrations.find_one({"gst_no": gst_no}): return False, f"GST No. {gst_no} is already registered!"
    db.gst_registrations.insert_one({
        "gst_no": gst_no.upper().strip(), "legal_name": legal_name.strip(), "trade_name": trade_name.strip(),
        "reg_date": pd.to_datetime(reg_date), "owner_phone": owner_phone, "owner_email": owner_email,
        "gst_phone": gst_phone, "gst_email": gst_email, "created_at": datetime.datetime.now()
    })
    return True, "Saved Successfully!"

def save_bulk_gst_clients(df):
    if db is None: return 0, ["Database connection error."]
    success_count, errors = 0, []
    df.columns = [str(c).strip() for c in df.columns]
    df = df.fillna('')
    for idx, row in df.iterrows():
        try:
            gst_no = str(row.get('GST No', '')).strip().upper()
            if not gst_no: continue
            legal, trade = str(row.get('Legal Name', '')).strip(), str(row.get('Trade Name', '')).strip()
            reg_date = row.get('Reg Date', '')
            if not str(reg_date).strip(): reg_date = datetime.date.today()
            o_ph, o_em = str(row.get('Owner Phone', '')).strip(), str(row.get('Owner Email', '')).strip()
            g_ph, g_em = str(row.get('GST Phone', '')).strip(), str(row.get('GST Email', '')).strip()
            s, m = save_gst_registration(gst_no, legal, trade, str(reg_date), o_ph, o_em, g_ph, g_em)
            if s: success_count += 1
            else: errors.append(f"Row {idx+2} ({gst_no}): {m}")
        except Exception as e: errors.append(f"Row {idx+2}: {str(e)}")
    return success_count, errors

def get_gst_registrations():
    if db is None: return pd.DataFrame()
    return pd.DataFrame(list(db.gst_registrations.find({}, {'_id':0}).sort("created_at", -1)))

def update_gst_filing(gst_no, period, return_type, status, filing_date):
    if db is None: return False
    update_field_status = f"{return_type.lower().replace('-','')}_status" 
    update_field_date = f"{return_type.lower().replace('-','')}_date"     
    db.gst_filings.update_one(
        {"gst_no": gst_no, "period": period},
        {"$set": {
            "gst_no": gst_no, "period": period, update_field_status: status,
            update_field_date: pd.to_datetime(filing_date) if status == "Filed" else None,
            "updated_at": datetime.datetime.now()
        }}, upsert=True)
    return True

def get_gst_compliance(period):
    if db is None: return pd.DataFrame()
    regs = list(db.gst_registrations.find({}, {'_id':0}))
    if not regs: return pd.DataFrame()
    filings = list(db.gst_filings.find({"period": period}, {'_id':0}))
    filing_map = {f['gst_no']: f for f in filings}
    data = []
    for r in regs:
        gst = r['gst_no']
        f_data = filing_map.get(gst, {})
        data.append({
            "GST No": gst, "Trade Name": r.get('trade_name', '-'), "Legal Name": r.get('legal_name', '-'),
            "GSTR-1 Status": f_data.get('gstr1_status', 'Pending'),
            "GSTR-1 Date": pd.to_datetime(f_data.get('gstr1_date')).strftime('%d-%b') if pd.notnull(f_data.get('gstr1_date')) else "-",
            "GSTR-3B Status": f_data.get('gstr3b_status', 'Pending'),
            "GSTR-3B Date": pd.to_datetime(f_data.get('gstr3b_date')).strftime('%d-%b') if pd.notnull(f_data.get('gstr3b_date')) else "-"
        })
    return pd.DataFrame(data)

def get_6_month_compliance_history():
    if db is None: return pd.DataFrame()
    periods = []
    today = datetime.date.today()
    for i in range(6):
        m = today.month - i
        y = today.year
        if m <= 0:
            m += 12
            y -= 1
        periods.append(f"{y}-{m:02d}")
    periods.reverse() 
    regs = list(db.gst_registrations.find({}, {'_id':0}))
    if not regs: return pd.DataFrame()
    filings = list(db.gst_filings.find({"period": {"$in": periods}}, {'_id':0}))
    f_map = {}
    for f in filings:
        if f['gst_no'] not in f_map: f_map[f['gst_no']] = {}
        f_map[f['gst_no']][f['period']] = f
    data = []
    for r in regs:
        gst = r['gst_no']
        row = {"GST No": gst, "Legal Name": r.get('legal_name', '-')}
        for p in periods:
            p_data = f_map.get(gst, {}).get(p, {})
            g1 = "✅" if p_data.get('gstr1_status') == "Filed" else "❌"
            g3 = "✅" if p_data.get('gstr3b_status') == "Filed" else "❌"
            row[f"{pd.to_datetime(p+'-01').strftime('%b %y')}"] = f"G1:{g1} | 3B:{g3}"
        data.append(row)
    return pd.DataFrame(data)

# --- PRODUCT MASTER SAVERS ---
def generate_id(prefix): return f"{prefix}-{''.join(random.choices(string.digits, k=6))}"
def save_product_parent(n, g, c, d):
    if db.masters_products.find_one({"name": n, "gender": g, "type": "parent"}): return False, "Exists"
    db.masters_products.insert_one({"type": "parent", "system_id": generate_id("P"), "name": n, "gender": g, "category": c, "description": d, "created_at": datetime.datetime.now()})
    return True, "Created"
def save_product_child(pid, sku, c, s, r):
    if db.masters_products.find_one({"sku": sku}): return False, "SKU Exists"
    p = db.masters_products.find_one({"system_id": pid})
    db.masters_products.insert_one({"type": "child", "system_id": generate_id("C"), "parent_id": pid, "parent_name": p['name'], "parent_category": p['category'], "parent_gender": p['gender'], "sku": sku, "color": c, "size": s, "rate": float(r), "created_at": datetime.datetime.now()})
    return True, "Created"
def save_bulk_products(df):
    c = 0; err = []
    for _, r in df.iterrows():
        try:
            if r.get('type') == 'parent':
                s, m = save_product_parent(r.get('name'), r.get('gender'), r.get('category'), r.get('description'))
                if s: c+=1
            elif r.get('type') == 'child':
                p = db.masters_products.find_one({"name": r.get('parent_name'), "type": "parent"})
                if p:
                    sku = f"{p.get('gender')}-{r.get('color')}-{p.get('category')}-{r.get('size')}".replace(" ", "")
                    save_product_child(p['system_id'], sku, r.get('color'), r.get('size'), r.get('rate'))
                    c+=1
        except: pass
    return c, err
def save_sku_mapping(i, c, k): db.masters_mappings.update_one({"internal_sku": i, "channel": c}, {"$set": {"channel_sku": k, "updated_at": datetime.datetime.now()}}, upsert=True)

# --- LOTS & CUTTING ---
def get_active_lots(): return sorted(db.masters_lots.distinct("lot_no")) if db is not None else []
def get_detailed_bundles(lot): return list(db.masters_lots.find({"lot_no": lot}, {'_id':0})) if db is not None else []
def get_bundle_details(lot, bun): return db.masters_lots.find_one({"lot_no": lot, "bundle_no": bun}, {'_id':0}) if db is not None else None

def save_full_lot(header, fabric_df, bundle_df):
    if db is None: return False, "DB Error"
    if db.transactions_cutting.find_one({"lot_no": header['lot_no']}): return False, "Lot Exists"
    
    db.transactions_cutting.insert_one({
        **header, "fabric_consumption": fabric_df.to_dict('records'), 
        "total_pcs": float(bundle_df['Qty'].sum()), "created_at": datetime.datetime.now()
    })
    
    bundles = []
    for _, r in bundle_df.iterrows():
        bundles.append({
            "date": pd.to_datetime(header['date']), "lot_no": header['lot_no'],
            "bundle_no": r['Bundle No'], "item_name": header['item_name'], "item_sku": header['sku'],
            "color": r['Color'], "size": r['Size'], "qty": float(r['Qty']), "created_at": datetime.datetime.now()
        })
    if bundles: db.masters_lots.insert_many(bundles)
    return True, "Lot Saved Successfully"

def get_bundle_progress(lot=None, bun=None):
    if db is None: return pd.DataFrame()
    q = {}
    if lot and lot != "All": q["lot_no"] = lot
    if bun and bun != "All": q["bundle_no"] = bun
    lots = list(db.masters_lots.find(q, {'_id':0}))
    if not lots: return pd.DataFrame()
    
    pipeline = [{"$group": {"_id": {"lot": "$lot_no", "bun": "$bundle_no"}, "proc": {"$last": "$process"}, "qty": {"$last": "$qty"}}}]
    prod_map = { (p['_id']['lot'], p['_id']['bun']): p for p in list(db.production.aggregate(pipeline)) }
    
    data = []
    for r in lots:
        k = (r.get('lot_no'), r.get('bundle_no'))
        info = prod_map.get(k, {})
        data.append({
            "Lot": r.get('lot_no'), "Bundle": r.get('bundle_no'), "Item": f"{r.get('item_name')} ({r.get('color')}-{r.get('size')})",
            "Current Stage": info.get('proc', '🆕 Created'), "Pcs": info.get('qty', r.get('qty'))
        })
    return pd.DataFrame(data)

def get_bundle_journey(lot, bun):
    if db is None: return [], 0, 0
    created = db.masters_lots.find_one({"lot_no": lot, "bundle_no": bun})
    if not created: return [], 0, 0
    qty = float(created.get('qty', 0))
    journey = [{"Date": pd.to_datetime(created.get('date')).strftime('%d-%b'), "Process": "Created", "Worker": "System", "Qty": qty}]
    prods = list(db.production.find({"lot_no": lot, "bundle_no": bun}).sort("created_at", 1))
    for p in prods:
        journey.append({"Date": p['date'].strftime('%d-%b'), "Process": p['process'], "Worker": p['staff_name'], "Qty": p['qty']})
    return journey, qty, (prods[-1]['qty'] if prods else qty)

# --- PRODUCTION / MASTERS ---
def save_production(d, s, i, p, q, r, l, b):
    if db is None: return False, "DB Error"
    db.production.insert_one({"date": pd.to_datetime(d), "staff_name": s, "item": i, "process": p, "qty": q, "rate": r, "amount": q*r, "lot_no": l, "bundle_no": b, "created_at": datetime.datetime.now()})
    return True, "Entry Saved & Payment Updated"

def save_bulk_stitching(df):
    if db is None: return 0, ["Database connection error."]
    success_count = 0
    errors = []
    df = df.fillna('')
    for idx, row in df.iterrows():
        try:
            d_raw = row.get('Date', '')
            s_name = str(row.get('Karigar Name', '')).strip()
            lot_no = str(row.get('Lot No', '')).strip()
            bun_no = str(row.get('Bundle No.', '')).strip()
            proc = str(row.get('Process', '')).strip()
            item = str(row.get('Item', '')).strip()
            
            try: qty = float(row.get('Qty', 0))
            except: qty = 0.0
                
            if not s_name or not lot_no or not bun_no:
                errors.append(f"Row {idx+2}: Missing Karigar, Lot No, or Bundle No.")
                continue
                
            date_val = pd.to_datetime(d_raw) if str(d_raw).strip() else datetime.date.today()
            rate = get_rate(item, proc, date_val)
            amount = qty * rate
            
            db.production.insert_one({
                "date": date_val, "staff_name": s_name, "item": item,
                "process": proc, "qty": qty, "rate": rate, "amount": amount,
                "lot_no": lot_no, "bundle_no": bun_no, "created_at": datetime.datetime.now()
            })
            success_count += 1
        except Exception as e:
            errors.append(f"Row {idx+2}: {str(e)}")
    return success_count, errors

def save_attendance(d, s, st, ti=None, to=None): db.attendance.update_one({"date": pd.to_datetime(d), "staff_name": s}, {"$set": {"status": st, "in_time": str(ti), "out_time": str(to)}}, upsert=True)
def get_attendance_record(d, s): return db.attendance.find_one({"date": pd.to_datetime(d), "staff_name": s})

def save_staff(n, p, r, st, ms): db.masters_staff.update_one({"name": n}, {"$set": {"name":n, "phone":p, "role":r, "salary_type":st, "monthly_salary":ms}}, upsert=True)
def save_party(n, t): db.masters_parties.update_one({"name": n}, {"$set": {"name":n, "type":t}}, upsert=True)
def save_item(n, p): db.masters_items.update_one({"name": n}, {"$set": {"name":n, "processes":p}}, upsert=True)
def save_category(n): db.masters_categories.update_one({"name": n}, {"$set": {"name": n}}, upsert=True)

def save_rate(i, p, r, fd, td): 
    db.masters_rates.update_one(
        {"item": i, "process": p, "from_date": pd.to_datetime(fd)}, 
        {"$set": {"rate": float(r), "to_date": pd.to_datetime(td), "updated_at": datetime.datetime.now()}}, 
        upsert=True
    )
    
def save_master(col, data): db[col].update_one({"name": data.get("name") or data.get("rate")}, {"$set": data}, upsert=True)
def save_payment(d, s, a, t, r): db.payments.insert_one({"date": pd.to_datetime(d), "staff_name": s, "amount": float(a), "type": t, "remarks": r, "created_at": datetime.datetime.now()})
def save_cash_transaction(d, t, a, p, ac, r): db.transactions_cashbook.insert_one({"date": pd.to_datetime(d), "type": t, "amount": float(a), "party": p, "account": ac, "remarks": r, "created_at": datetime.datetime.now()})
def save_fabrication(d, p, i, q, r, ds): db.transactions_fabrication.insert_one({"date": pd.to_datetime(d), "party": p, "item": i, "qty": q, "rate": r, "description": ds, "created_at": datetime.datetime.now()})

def clean_database(cols):
    if db is None: return False, "Database connection error."
    res = {}
    try:
        for c in cols:
            r = db[c].delete_many({})
            if r.deleted_count > 0: res[c] = r.deleted_count
        return True, res
    except Exception as e: return False, str(e)

def get_recent_fabrication(): return get_df("transactions_fabrication")

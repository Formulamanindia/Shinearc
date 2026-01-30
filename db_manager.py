import streamlit as st
import pymongo
import pandas as pd
import datetime
from dateutil.relativedelta import relativedelta

# --- CONNECT TO DATABASE ---
try:
    client = pymongo.MongoClient(st.secrets["MONGO_URI"])
    db = client['shine_arc_new_db']
except Exception as e:
    st.error(f"Database Connection Error: {e}")

# ==========================================
# 1. FETCHERS
# ==========================================
def get_staff_list(): return sorted([s['name'] for s in db.masters_staff.find({}, {'_id':0, 'name':1})])
def get_staff_details(name): return db.masters_staff.find_one({"name": name})

def get_items_list(): return sorted([i['name'] for i in db.masters_items.find({}, {'_id':0, 'name':1})])
def get_colors_list(): return sorted([c['name'] for c in db.masters_colors.find({}, {'_id':0, 'name':1})])
def get_sizes_list(): return sorted([s['name'] for s in db.masters_sizes.find({}, {'_id':0, 'name':1})])
def get_processes_list(): return sorted([p['name'] for p in db.masters_processes.find({}, {'_id':0, 'name':1})])

# --- PARTIES & GST ---
def get_parties_list(): return sorted([p['name'] for p in db.masters_parties.find({}, {'_id':0, 'name':1})])
def get_gst_list(): return sorted([g['rate'] for g in db.masters_gst.find({}, {'_id':0, 'rate':1})])
def get_vendors_list(): return sorted([v['name'] for v in db.masters_vendors.find({}, {'_id':0, 'name':1})])
def get_sources_list(): return sorted([s['name'] for s in db.masters_sources.find({}, {'_id':0, 'name':1})])

def get_rate(item, process):
    res = db.masters_rates.find_one({"item": item, "process": process})
    return float(res['rate']) if res else 0.0

# --- LOTS ---
def get_active_lots(): return sorted(db.masters_lots.distinct("lot_no"))
def get_bundles_for_lot(lot_no): return sorted(db.masters_lots.distinct("bundle_no", {"lot_no": lot_no}))
def get_bundle_details(lot_no, bundle_no): return db.masters_lots.find_one({"lot_no": lot_no, "bundle_no": bundle_no}, {'_id':0})

# --- LEDGER LOGIC (UPDATED) ---
def get_party_ledger(party_name):
    transactions = []
    
    # 1. Sales (Debit)
    sales = list(db.transactions_sales.find({"party": party_name}))
    for s in sales:
        transactions.append({
            "date": s['date'], 
            "bill_no": s['bill_no'],
            "description": f"{s['item']} ({s['qty']} x {s['rate']})",
            "debit": s['grand_total'], "credit": 0.0, 
            "type": "SALE"
        })
        
    # 2. Purchases (Credit / Debit for Return)
    purchases = list(db.transactions_purchase.find({"vendor": party_name}))
    for p in purchases:
        p_type = p.get('type', 'Purchase')
        desc = f"{p['item']} ({p['qty']} x {p['rate']})"
        if p_type == "Purchase Return":
            transactions.append({
                "date": p['date'], "bill_no": p['bill_no'], 
                "description": desc, "debit": p['grand_total'], "credit": 0.0, 
                "type": "PURCHASE_RET"
            })
        else:
            transactions.append({
                "date": p['date'], "bill_no": p['bill_no'], 
                "description": desc, "debit": 0.0, "credit": p['grand_total'], 
                "type": "PURCHASE"
            })
        
    # 3. Cashbook (In/Out)
    cash = list(db.transactions_cashbook.find({"party": party_name}))
    for c in cash:
        if c['type'] == "IN": 
            transactions.append({
                "date": c['date'], "bill_no": "-", 
                "description": f"Payment Recvd ({c['account']}) - {c.get('remarks','')}", 
                "debit": 0.0, "credit": c['amount'], 
                "type": "PAY_IN"
            })
        else: 
            transactions.append({
                "date": c['date'], "bill_no": "-", 
                "description": f"Payment Made ({c['account']}) - {c.get('remarks','')}", 
                "debit": c['amount'], "credit": 0.0, 
                "type": "PAY_OUT"
            })
            
    if not transactions: return pd.DataFrame()
    df = pd.DataFrame(transactions)
    df['date'] = pd.to_datetime(df['date'])
    return df.sort_values(by='date')

# --- DASHBOARD ---
def get_dashboard_stats():
    today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    pcs_res = list(db.production.aggregate([{"$match": {"date": {"$gte": today_start}}}, {"$group": {"_id": None, "total": {"$sum": "$qty"}}}]))
    pcs_today = pcs_res[0]['total'] if pcs_res else 0

    earn_res = list(db.production.aggregate([{"$match": {"date": {"$gte": today_start}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
    earn_today = earn_res[0]['total'] if earn_res else 0.0

    m_prod_earn = list(db.production.aggregate([{"$match": {"date": {"$gte": month_start}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
    total_prod = m_prod_earn[0]['total'] if m_prod_earn else 0.0
    
    m_sal_earn = list(db.attendance.aggregate([{"$match": {"date": {"$gte": month_start}}}, {"$group": {"_id": None, "total": {"$sum": "$daily_earnings"}}}]))
    total_sal = m_sal_earn[0]['total'] if m_sal_earn else 0.0
    
    total_earned = total_prod + total_sal 

    m_paid_res = list(db.payments.aggregate([{"$match": {"date": {"$gte": month_start}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
    total_paid = m_paid_res[0]['total'] if m_paid_res else 0.0
    
    pending_month = total_earned - total_paid
    active_staff = len(db.production.distinct("staff_name", {"date": {"$gte": today_start}}))

    return pcs_today, earn_today, pending_month, active_staff

def get_worker_history(staff_name):
    s_det = get_staff_details(staff_name)
    is_salaried = s_det.get('salary_type') == 'Salaried' if s_det else False
    
    earned = 0.0
    if is_salaried:
        att_res = list(db.attendance.aggregate([{"$match": {"staff_name": staff_name}}, {"$group": {"_id": None, "total": {"$sum": "$daily_earnings"}}}]))
        earned = att_res[0]['total'] if att_res else 0.0
    else:
        prod_res = list(db.production.aggregate([{"$match": {"staff_name": staff_name}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
        earned = prod_res[0]['total'] if prod_res else 0.0

    paid_res = list(db.payments.aggregate([{"$match": {"staff_name": staff_name}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
    paid = paid_res[0]['total'] if paid_res else 0.0
    
    if is_salaried:
        hist_data = list(db.attendance.find({"staff_name": staff_name}).sort("date", -1))
    else:
        hist_data = list(db.production.find({"staff_name": staff_name}).sort("date", -1))
        
    return earned, paid, (earned - paid), pd.DataFrame(hist_data)

def get_staff_month_paid(staff_name):
    month_start = datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    res = list(db.payments.aggregate([{"$match": {"staff_name": staff_name, "date": {"$gte": month_start}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
    return res[0]['total'] if res else 0.0

def get_attendance_history(staff_name):
    data = list(db.attendance.find({"staff_name": staff_name}).sort("date", -1))
    return pd.DataFrame(data)

def get_12_month_summary(staff_name, is_salaried, monthly_salary=0):
    summary_data = []
    end_date = datetime.datetime.now()
    for i in range(12):
        start_date = (end_date - relativedelta(months=i)).replace(day=1, hour=0, minute=0, second=0)
        next_month = (start_date + relativedelta(months=1))
        
        pay_res = list(db.payments.aggregate([{"$match": {"staff_name": staff_name, "date": {"$gte": start_date, "$lt": next_month}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
        paid_amt = pay_res[0]['total'] if pay_res else 0.0
        
        earned_amt = 0.0
        if is_salaried:
            att_res = list(db.attendance.aggregate([{"$match": {"staff_name": staff_name, "date": {"$gte": start_date, "$lt": next_month}}}, {"$group": {"_id": None, "total": {"$sum": "$daily_earnings"}}}]))
            earned_amt = att_res[0]['total'] if att_res else 0.0
        else:
            prod_res = list(db.production.aggregate([{"$match": {"staff_name": staff_name, "date": {"$gte": start_date, "$lt": next_month}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
            earned_amt = prod_res[0]['total'] if prod_res else 0.0
            
        summary_data.append({"Month": start_date.strftime("%b %Y"), "Earned": earned_amt, "Paid": paid_amt, "Balance": earned_amt - paid_amt})
    return pd.DataFrame(summary_data)

# ==========================================
# 2. SAVERS
# ==========================================
def save_master(collection, data):
    key_field = "rate" if collection == "masters_gst" else "name"
    try: db[collection].update_one({key_field: data[key_field]}, {"$set": data}, upsert=True); return True
    except: return False

def save_party(name, type_):
    db.masters_parties.update_one({"name": name}, {"$set": {"name": name, "type": type_, "updated_at": datetime.datetime.now()}}, upsert=True)

def save_staff(name, phone, role, salary_type, monthly_salary):
    data = {"name": name, "phone": phone, "role": role, "salary_type": salary_type, "monthly_salary": monthly_salary, "updated_at": datetime.datetime.now()}
    db.masters_staff.update_one({"name": name}, {"$set": data}, upsert=True)

def save_rate(item, process, rate):
    db.masters_rates.update_one({"item": item, "process": process}, {"$set": {"rate": float(rate)}}, upsert=True)

def save_payment(date, staff, amount, p_type, remarks):
    db.payments.insert_one({"date": pd.to_datetime(date), "staff_name": staff, "amount": float(amount), "type": p_type, "remarks": remarks, "created_at": datetime.datetime.now()})

def save_production(date, staff, item, process, qty, rate, lot_no, bundle_no):
    total = float(qty) * float(rate)
    db.production.insert_one({"date": pd.to_datetime(date), "staff_name": staff, "item": item, "process": process, "qty": float(qty), "rate": float(rate), "amount": total, "lot_no": lot_no, "bundle_no": bundle_no, "created_at": datetime.datetime.now()})

def save_attendance(date_str, staff, status, in_time, out_time, note=""):
    s_det = get_staff_details(staff)
    m_sal = float(s_det.get('monthly_salary', 0)) if s_det else 0
    daily_rate = m_sal / 30.0 if m_sal else 0.0
    hourly_rate = daily_rate / 10.0
    
    calculated_pay, ot_hours, worked_hours = 0.0, 0.0, 0.0
    date_obj = pd.to_datetime(date_str)
    is_sunday = (date_obj.weekday() == 6)
    
    if status == "Present" and in_time and out_time:
        t1, t2 = datetime.datetime.combine(date_obj, in_time), datetime.datetime.combine(date_obj, out_time)
        worked_hours = round((t2 - t1).total_seconds() / 3600.0, 2)
        base_pay = daily_rate * 2.0 if is_sunday else daily_rate
        std_hours = 7.5 if is_sunday else 10.0
        
        if worked_hours > std_hours:
            ot_hours = worked_hours - std_hours
            calculated_pay = base_pay + (ot_hours * hourly_rate)
        else: calculated_pay = base_pay
        
    elif status == "Half Day": calculated_pay = daily_rate * 0.5
        
    db.attendance.update_one(
        {"date": date_obj, "staff_name": staff},
        {"$set": {"status": status, "in_time": str(in_time), "out_time": str(out_time), "worked_hours": worked_hours, "ot_hours": ot_hours, "daily_earnings": round(calculated_pay, 2), "note": note, "updated_at": datetime.datetime.now()}}, upsert=True)

def save_bulk_lots(df):
    clean = []
    for r in df.to_dict('records'):
        clean.append({"date": pd.to_datetime(r.get('date', datetime.datetime.now())), "lot_no": str(r.get('Lot No', '')), "item_name": str(r.get('Item name', '')), "bundle_no": str(r.get('Bundle no.', '')), "color": str(r.get('Color Name', '')), "size": str(r.get('Size', '')), "qty": float(r.get('Qty', 0)), "created_at": datetime.datetime.now()})
    if clean: db.masters_lots.insert_many(clean); return True
    return False

# --- BULK INVOICE SAVERS WITH GST ---
def save_purchase_invoice(date, vendor, p_type, bill_no, cart_items, global_gst):
    records = []
    for item in cart_items:
        base = float(item['qty']) * float(item['rate'])
        tax_amt = base * (float(global_gst) / 100.0)
        grand = base + tax_amt
        
        records.append({
            "date": pd.to_datetime(date), "vendor": vendor, "type": p_type,
            "item": item['item'], "qty": float(item['qty']), "rate": float(item['rate']),
            "gst_rate": float(global_gst), "base_amount": base, "tax_amount": tax_amt,
            "grand_total": grand, "bill_no": bill_no, "created_at": datetime.datetime.now()
        })
    if records: db.transactions_purchase.insert_many(records); return True
    return False

def save_sale_invoice(date, party, bill_no, cart_items, global_gst):
    records = []
    for item in cart_items:
        base = float(item['qty']) * float(item['rate'])
        tax_amt = base * (float(global_gst) / 100.0)
        grand = base + tax_amt
        
        records.append({
            "date": pd.to_datetime(date), "party": party,
            "item": item['item'], "qty": float(item['qty']), "rate": float(item['rate']),
            "gst_rate": float(global_gst), "base_amount": base, "tax_amount": tax_amt,
            "grand_total": grand, "bill_no": bill_no, "created_at": datetime.datetime.now()
        })
    if records: db.transactions_sales.insert_many(records); return True
    return False

def save_cash_transaction(date, type_, amount, party, account, remarks):
    db.transactions_cashbook.insert_one({"date": pd.to_datetime(date), "type": type_, "amount": float(amount), "party": party, "account": account, "remarks": remarks, "created_at": datetime.datetime.now()})

def clean_database(selected_collections):
    final_targets = set(selected_collections)
    if "masters_staff" in final_targets: final_targets.update(["production", "payments", "attendance"])
    try:
        for col in final_targets: db[col].delete_many({})
        return True, list(final_targets)
    except: return False, []

# ==========================================
# 3. DATAFRAME HELPERS
# ==========================================
def get_df(collection_name):
    data = list(db[collection_name].find({}, {'_id':0}))
    return pd.DataFrame(data)

def get_rates_df():
    return pd.DataFrame(list(db.masters_rates.find({}, {'_id':0})))

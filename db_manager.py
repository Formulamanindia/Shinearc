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
def get_staff_list():
    return sorted([s['name'] for s in db.masters_staff.find({}, {'_id':0, 'name':1})])

def get_staff_details(name):
    return db.masters_staff.find_one({"name": name})

def get_items_list(): return sorted([i['name'] for i in db.masters_items.find({}, {'_id':0, 'name':1})])
def get_colors_list(): return sorted([c['name'] for c in db.masters_colors.find({}, {'_id':0, 'name':1})])
def get_sizes_list(): return sorted([s['name'] for s in db.masters_sizes.find({}, {'_id':0, 'name':1})])
def get_processes_list(): return sorted([p['name'] for p in db.masters_processes.find({}, {'_id':0, 'name':1})])

def get_rate(item, process):
    res = db.masters_rates.find_one({"item": item, "process": process})
    return float(res['rate']) if res else 0.0

# --- LOTS ---
def get_active_lots(): return sorted(db.masters_lots.distinct("lot_no"))
def get_bundles_for_lot(lot_no): return sorted(db.masters_lots.distinct("bundle_no", {"lot_no": lot_no}))
def get_bundle_details(lot_no, bundle_no): return db.masters_lots.find_one({"lot_no": lot_no, "bundle_no": bundle_no}, {'_id':0})

# --- DASHBOARD ---
def get_dashboard_stats():
    today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Production Stats
    pcs_res = list(db.production.aggregate([{"$match": {"date": {"$gte": today_start}}}, {"$group": {"_id": None, "total": {"$sum": "$qty"}}}]))
    pcs_today = pcs_res[0]['total'] if pcs_res else 0

    earn_res = list(db.production.aggregate([{"$match": {"date": {"$gte": today_start}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
    earn_today = earn_res[0]['total'] if earn_res else 0.0

    # Financials (Month)
    # Production Earned
    m_prod_earn = list(db.production.aggregate([{"$match": {"date": {"$gte": month_start}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
    total_prod = m_prod_earn[0]['total'] if m_prod_earn else 0.0
    
    # Salary Earned (Attendance Based)
    m_sal_earn = list(db.attendance.aggregate([{"$match": {"date": {"$gte": month_start}}}, {"$group": {"_id": None, "total": {"$sum": "$daily_earnings"}}}]))
    total_sal = m_sal_earn[0]['total'] if m_sal_earn else 0.0
    
    total_earned = total_prod + total_sal # Total Liability

    # Paid
    m_paid_res = list(db.payments.aggregate([{"$match": {"date": {"$gte": month_start}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
    total_paid = m_paid_res[0]['total'] if m_paid_res else 0.0
    
    pending_month = total_earned - total_paid
    active_staff = len(db.production.distinct("staff_name", {"date": {"$gte": today_start}}))

    return pcs_today, earn_today, pending_month, active_staff

def get_worker_history(staff_name):
    # Check if Salaried or Piece Rate
    s_det = get_staff_details(staff_name)
    is_salaried = s_det.get('salary_type') == 'Salaried'
    
    # Financials
    earned = 0.0
    if is_salaried:
        # Sum from Attendance
        att_res = list(db.attendance.aggregate([{"$match": {"staff_name": staff_name}}, {"$group": {"_id": None, "total": {"$sum": "$daily_earnings"}}}]))
        earned = att_res[0]['total'] if att_res else 0.0
    else:
        # Sum from Production
        prod_res = list(db.production.aggregate([{"$match": {"staff_name": staff_name}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
        earned = prod_res[0]['total'] if prod_res else 0.0

    paid_res = list(db.payments.aggregate([{"$match": {"staff_name": staff_name}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
    paid = paid_res[0]['total'] if paid_res else 0.0
    
    # Detailed Data for Table
    if is_salaried:
        # Get Attendance Logs
        hist_data = list(db.attendance.find({"staff_name": staff_name}).sort("date", -1))
    else:
        # Get Production Logs
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
        
        # Paid Amount
        pay_res = list(db.payments.aggregate([{"$match": {"staff_name": staff_name, "date": {"$gte": start_date, "$lt": next_month}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
        paid_amt = pay_res[0]['total'] if pay_res else 0.0
        
        # Earned Amount
        earned_amt = 0.0
        if is_salaried:
            # Sum 'daily_earnings' from attendance
            att_res = list(db.attendance.aggregate([{"$match": {"staff_name": staff_name, "date": {"$gte": start_date, "$lt": next_month}}}, {"$group": {"_id": None, "total": {"$sum": "$daily_earnings"}}}]))
            earned_amt = att_res[0]['total'] if att_res else 0.0
        else:
            # Sum production
            prod_res = list(db.production.aggregate([{"$match": {"staff_name": staff_name, "date": {"$gte": start_date, "$lt": next_month}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]))
            earned_amt = prod_res[0]['total'] if prod_res else 0.0
            
        summary_data.append({
            "Month": start_date.strftime("%b %Y"),
            "Earned": earned_amt,
            "Paid": paid_amt,
            "Balance": earned_amt - paid_amt
        })
        
    return pd.DataFrame(summary_data)

# ==========================================
# 2. SAVERS & CALCULATIONS
# ==========================================
def save_master(collection, data):
    try: db[collection].update_one({"name": data['name']}, {"$set": data}, upsert=True); return True
    except: return False

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
    """
    Calculates salary based on:
    - Base Rate: Monthly/30
    - Sunday: Double Pay (2x Base)
    - Weekday Standard: 9AM-7PM (10hrs)
    - Sunday Standard: 9AM-4:30PM (7.5hrs)
    - OT: Paid hourly for time worked beyond standard.
    """
    
    # Get Salary Info
    s_det = get_staff_details(staff)
    m_sal = float(s_det.get('monthly_salary', 0))
    daily_rate = m_sal / 30.0 if m_sal else 0.0
    hourly_rate = daily_rate / 10.0 # Assuming 10hr standard day basis for rate
    
    calculated_pay = 0.0
    ot_hours = 0.0
    worked_hours = 0.0
    
    date_obj = pd.to_datetime(date_str)
    is_sunday = (date_obj.weekday() == 6) # 0=Mon, 6=Sun
    
    if status == "Present" and in_time and out_time:
        # Calculate Worked Hours
        t1 = datetime.datetime.combine(date_obj, in_time)
        t2 = datetime.datetime.combine(date_obj, out_time)
        diff = (t2 - t1).total_seconds() / 3600.0
        worked_hours = round(diff, 2)
        
        # --- CALCULATION ENGINE ---
        if is_sunday:
            # Sunday Logic: Double Pay Base + OT beyond 7.5 hrs
            base_pay = daily_rate * 2.0 
            standard_hours = 7.5
        else:
            # Weekday Logic: Single Pay Base + OT beyond 10 hrs
            base_pay = daily_rate
            standard_hours = 10.0
            
        # OT Logic
        if worked_hours > standard_hours:
            ot_hours = worked_hours - standard_hours
            ot_pay = ot_hours * hourly_rate
        else:
            ot_hours = 0.0
            ot_pay = 0.0
            
        calculated_pay = base_pay + ot_pay
        
    elif status == "Half Day":
        calculated_pay = daily_rate * 0.5
        
    # Save Record
    db.attendance.update_one(
        {"date": date_obj, "staff_name": staff},
        {"$set": {
            "status": status,
            "in_time": str(in_time),
            "out_time": str(out_time),
            "worked_hours": worked_hours,
            "ot_hours": ot_hours,
            "daily_earnings": round(calculated_pay, 2),
            "note": note,
            "updated_at": datetime.datetime.now()
        }},
        upsert=True
    )

def save_bulk_lots(df):
    records = df.to_dict('records')
    clean = []
    for r in records:
        clean.append({
            "date": pd.to_datetime(r.get('date', datetime.datetime.now())),
            "lot_no": str(r.get('Lot No', '')),
            "item_name": str(r.get('Item name', '')),
            "bundle_no": str(r.get('Bundle no.', '')),
            "color": str(r.get('Color Name', '')),
            "size": str(r.get('Size', '')),
            "qty": float(r.get('Qty', 0)),
            "created_at": datetime.datetime.now()
        })
    if clean: db.masters_lots.insert_many(clean); return True
    return False

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

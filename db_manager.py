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
# 1. FETCHERS (GET DATA)
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

def get_dashboard_stats():
    today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 1. Total Pcs Today
    pipeline_pcs = [{"$match": {"date": {"$gte": today_start}}}, {"$group": {"_id": None, "total": {"$sum": "$qty"}}}]
    pcs_res = list(db.production.aggregate(pipeline_pcs))
    pcs_today = pcs_res[0]['total'] if pcs_res else 0

    # 2. Staff Earnings Today
    pipeline_earn = [{"$match": {"date": {"$gte": today_start}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
    earn_res = list(db.production.aggregate(pipeline_earn))
    earn_today = earn_res[0]['total'] if earn_res else 0.0

    # 3. Pending Payment (Global)
    pipeline_m_earn = [{"$match": {"date": {"$gte": month_start}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
    m_earn_res = list(db.production.aggregate(pipeline_m_earn))
    total_earned = m_earn_res[0]['total'] if m_earn_res else 0.0

    pipeline_m_paid = [{"$match": {"date": {"$gte": month_start}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
    m_paid_res = list(db.payments.aggregate(pipeline_m_paid))
    total_paid = m_paid_res[0]['total'] if m_paid_res else 0.0
    
    pending_month = total_earned - total_paid
    active_staff = len(db.production.distinct("staff_name", {"date": {"$gte": today_start}}))

    return pcs_today, earn_today, pending_month, active_staff

def get_worker_history(staff_name):
    # Production History
    prod_data = list(db.production.find({"staff_name": staff_name}).sort("date", -1))
    df_prod = pd.DataFrame(prod_data)
    
    # Financials (Lifetime)
    pipeline_earned = [{"$match": {"staff_name": staff_name}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
    earned_res = list(db.production.aggregate(pipeline_earned))
    earned = earned_res[0]['total'] if earned_res else 0.0

    pipeline_paid = [{"$match": {"staff_name": staff_name}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
    paid_res = list(db.payments.aggregate(pipeline_paid))
    paid = paid_res[0]['total'] if paid_res else 0.0
    
    return earned, paid, (earned - paid), df_prod

def get_staff_month_paid(staff_name):
    """Returns amount paid to staff in current month"""
    month_start = datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    pipeline = [{"$match": {"staff_name": staff_name, "date": {"$gte": month_start}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
    res = list(db.payments.aggregate(pipeline))
    return res[0]['total'] if res else 0.0

def get_attendance_history(staff_name):
    """Fetches attendance records"""
    data = list(db.attendance.find({"staff_name": staff_name}).sort("date", -1))
    return pd.DataFrame(data)

def get_12_month_summary(staff_name, is_salaried, monthly_salary=0):
    """
    Generates a 12-month summary DataFrame.
    - Salaried: Earned = (Salary/30) * Days Present
    - Piece Rate: Earned = Sum of Production Amount
    """
    summary_data = []
    end_date = datetime.datetime.now()
    
    # Loop back 12 months
    for i in range(12):
        start_date = (end_date - relativedelta(months=i)).replace(day=1, hour=0, minute=0, second=0)
        next_month = (start_date + relativedelta(months=1))
        
        # 1. Fetch Payments (Common)
        pay_pipe = [{"$match": {"staff_name": staff_name, "date": {"$gte": start_date, "$lt": next_month}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
        pay_res = list(db.payments.aggregate(pay_pipe))
        paid_amt = pay_res[0]['total'] if pay_res else 0.0
        
        # 2. Fetch Earnings
        earned_amt = 0.0
        if is_salaried:
            # Count "Present" days
            att_count = db.attendance.count_documents({"staff_name": staff_name, "status": "Present", "date": {"$gte": start_date, "$lt": next_month}})
            half_count = db.attendance.count_documents({"staff_name": staff_name, "status": "Half Day", "date": {"$gte": start_date, "$lt": next_month}})
            
            # Simple Calculation: (Salary / 30) * (Present + 0.5*Half)
            daily_rate = monthly_salary / 30.0 if monthly_salary else 0
            earned_amt = (att_count + (half_count * 0.5)) * daily_rate
        else:
            # Piece Rate: Sum production
            prod_pipe = [{"$match": {"staff_name": staff_name, "date": {"$gte": start_date, "$lt": next_month}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
            prod_res = list(db.production.aggregate(prod_pipe))
            earned_amt = prod_res[0]['total'] if prod_res else 0.0
            
        summary_data.append({
            "Month": start_date.strftime("%b %Y"),
            "Earned": earned_amt,
            "Paid": paid_amt,
            "Balance": earned_amt - paid_amt
        })
        
    return pd.DataFrame(summary_data)

# ==========================================
# 2. SAVERS
# ==========================================
def save_master(collection, data):
    try:
        db[collection].update_one({"name": data['name']}, {"$set": data}, upsert=True)
        return True
    except: return False

def save_staff(name, phone, role, salary_type, monthly_salary):
    data = {
        "name": name, "phone": phone, "role": role,
        "salary_type": salary_type, "monthly_salary": monthly_salary,
        "updated_at": datetime.datetime.now()
    }
    db.masters_staff.update_one({"name": name}, {"$set": data}, upsert=True)

def save_rate(item, process, rate):
    db.masters_rates.update_one({"item": item, "process": process}, {"$set": {"rate": float(rate)}}, upsert=True)

def save_payment(date, staff, amount, p_type, remarks):
    db.payments.insert_one({
        "date": pd.to_datetime(date), "staff_name": staff, "amount": float(amount),
        "type": p_type, "remarks": remarks, "created_at": datetime.datetime.now()
    })

def save_production(date, staff, item, process, qty, rate, lot_no, bundle_no):
    total = float(qty) * float(rate)
    db.production.insert_one({
        "date": pd.to_datetime(date), "staff_name": staff, "item": item, "process": process,
        "qty": float(qty), "rate": float(rate), "amount": total,
        "lot_no": lot_no, "bundle_no": bundle_no, "created_at": datetime.datetime.now()
    })

def save_attendance(date, staff, status, note=""):
    db.attendance.update_one(
        {"date": pd.to_datetime(date), "staff_name": staff},
        {"$set": {"status": status, "note": note, "updated_at": datetime.datetime.now()}},
        upsert=True
    )

def clean_database(selected_collections):
    final_targets = set(selected_collections)
    if "masters_staff" in final_targets:
        final_targets.add("production")
        final_targets.add("payments")
        final_targets.add("attendance")
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

import streamlit as st
import pymongo
import pandas as pd
import datetime
from bson.objectid import ObjectId

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
    """Returns list of active staff names"""
    return sorted([s['name'] for s in db.masters_staff.find({}, {'_id':0, 'name':1})])

def get_staff_details(name):
    """Returns full details including salary info"""
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

    # 2. Staff Earnings Today (Only for Piece Rate work recorded)
    pipeline_earn = [{"$match": {"date": {"$gte": today_start}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
    earn_res = list(db.production.aggregate(pipeline_earn))
    earn_today = earn_res[0]['total'] if earn_res else 0.0

    # 3. Pending Payment
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
    """
    Calculates detailed history.
    Note: For 'Salaried' staff, 'Earned' usually implies their Monthly Salary, 
    but for now this tracks 'Production Value'.
    """
    # Production History
    prod_data = list(db.production.find({"staff_name": staff_name}).sort("date", -1))
    df_prod = pd.DataFrame(prod_data)
    
    # Financials (Piece Rate Logic)
    total_earned = db.production.aggregate([{"$match": {"staff_name": staff_name}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}])
    total_paid = db.payments.aggregate([{"$match": {"staff_name": staff_name}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}])
    
    earned = list(total_earned)[0]['total'] if list(total_earned) else 0.0
    paid = list(total_paid)[0]['total'] if list(total_paid) else 0.0
    
    return earned, paid, (earned - paid), df_prod

# ==========================================
# 2. SAVERS (INSERT/UPDATE)
# ==========================================
def save_master(collection, data):
    """Generic saver for simple masters like Color/Size"""
    try:
        db[collection].update_one({"name": data['name']}, {"$set": data}, upsert=True)
        return True
    except: return False

def save_staff(name, phone, role, salary_type, monthly_salary):
    """Specific saver for Staff to handle Salary Type"""
    data = {
        "name": name,
        "phone": phone,
        "role": role,
        "salary_type": salary_type,         # 'Salaried' or 'Piece Rate'
        "monthly_salary": monthly_salary,   # 0 if Piece Rate
        "updated_at": datetime.datetime.now()
    }
    db.masters_staff.update_one({"name": name}, {"$set": data}, upsert=True)

def save_rate(item, process, rate):
    db.masters_rates.update_one(
        {"item": item, "process": process},
        {"$set": {"rate": float(rate)}},
        upsert=True
    )

def save_payment(date, staff, amount, p_type, remarks):
    db.payments.insert_one({
        "date": pd.to_datetime(date),
        "staff_name": staff,
        "amount": float(amount),
        "type": p_type,
        "remarks": remarks,
        "created_at": datetime.datetime.now()
    })

def save_production(date, staff, item, process, qty, rate):
    total = float(qty) * float(rate)
    db.production.insert_one({
        "date": pd.to_datetime(date),
        "staff_name": staff,
        "item": item,
        "process": process,
        "qty": float(qty),
        "rate": float(rate),
        "amount": total,
        "created_at": datetime.datetime.now()
    })

# ==========================================
# 3. DATAFRAME HELPERS
# ==========================================
def get_df(collection_name):
    data = list(db[collection_name].find({}, {'_id':0}))
    return pd.DataFrame(data)

def get_rates_df():
    return pd.DataFrame(list(db.masters_rates.find({}, {'_id':0})))

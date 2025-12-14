import streamlit as st
import pymongo
import pandas as pd
import datetime

# --- CONNECT TO DATABASE ---
# This safely loads the password from Streamlit Secrets
try:
    MONGO_URI = st.secrets["MONGO_URI"]
except:
    st.error("MongoDB Connection String not found in secrets!")
    st.stop()

@st.cache_resource
def get_db():
    client = pymongo.MongoClient(MONGO_URI)
    return client['shine_arc_db']

db = get_db()

# --- 1. INVENTORY FUNCTIONS ---
def add_product(name, design_no, category, cost_price, sell_price, stock_qty):
    collection = db['inventory']
    item = {
        "name": name,
        "design_no": design_no,
        "category": category,
        "cost_price": cost_price,
        "sell_price": sell_price,
        "stock_qty": stock_qty,
        "date_added": datetime.datetime.now()
    }
    collection.insert_one(item)

def get_inventory():
    collection = db['inventory']
    items = list(collection.find())
    return pd.DataFrame(items)

# --- 2. SALES FUNCTIONS ---
def create_order(customer, product_name, quantity, total_amount):
    collection = db['sales']
    order = {
        "customer": customer,
        "product": product_name,
        "quantity": quantity,
        "total": total_amount,
        "status": "Pending",
        "date": datetime.datetime.now()
    }
    collection.insert_one(order)
    
    # Decrease Stock
    db['inventory'].update_one(
        {"name": product_name},
        {"$inc": {"stock_qty": -quantity}}
    )

def get_orders():
    collection = db['sales']
    return pd.DataFrame(list(collection.find()))

# --- 3. PARTY & KARIGAR FUNCTIONS ---
def add_party(name, phone, role):
    collection = db['parties']
    collection.insert_one({
        "name": name,
        "phone": phone,
        "role": role,
        "date_added": datetime.datetime.now()
    })

def get_parties():
    collection = db['parties']
    return pd.DataFrame(list(collection.find()))

import streamlit as st
import pymongo
import pandas as pd
import datetime

# --- CONNECT TO DATABASE ---
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

# --- 1. INVENTORY FUNCTIONS (UPDATED FOR DICTIONARY) ---
def add_product(product_data):
    """
    Accepts a single dictionary containing all product details.
    """
    collection = db['inventory']
    
    # Add a timestamp automatically
    product_data['date_added'] = datetime.datetime.now()
    
    # Ensure critical fields exist (prevents crashes)
    if 'stock_qty' not in product_data:
        product_data['stock_qty'] = 0
    if 'sell_price' not in product_data:
        product_data['sell_price'] = 0.0
        
    collection.insert_one(product_data)

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

# --- 3. PARTY FUNCTIONS ---
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

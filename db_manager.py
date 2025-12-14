import pymongo
from bson.objectid import ObjectId
import pandas as pd
import datetime

# --- CONFIGURATION ---
# REPLACE THIS with your actual connection string from MongoDB Atlas
MONGO_URI = "mongodb+srv://<username>:<password>@cluster0.example.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "shine_are_db"

def get_db():
    client = pymongo.MongoClient(MONGO_URI)
    return client[DB_NAME]

db = get_db()

# --- INVENTORY FUNCTIONS ---
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

# --- SALES FUNCTIONS ---
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
    
    # Update Stock
    db['inventory'].update_one(
        {"name": product_name},
        {"$inc": {"stock_qty": -quantity}}
    )

def get_orders():
    collection = db['sales']
    return pd.DataFrame(list(collection.find()))

# --- KARIGAR FUNCTIONS ---
def issue_material(karigar_name, material, qty_issued):
    collection = db['karigar_logs']
    log = {
        "karigar_name": karigar_name,
        "material": material,
        "qty_issued": qty_issued,
        "status": "With Karigar",
        "date_issued": datetime.datetime.now()
    }
    collection.insert_one(log)

def get_karigar_logs():
    collection = db['karigar_logs']
    return pd.DataFrame(list(collection.find()))

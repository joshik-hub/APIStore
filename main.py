from fastapi import FastAPI, HTTPException, Depends, status
from pymongo import MongoClient
from bson import ObjectId

app = FastAPI()

# ------------------- MongoDB -------------------
client = MongoClient("mongodb+srv://mongo_db_user:ACsH2Jmp9qrsk3nt@customer.amld2yw.mongodb.net/")
db = client["AI"]

# Helper to convert ObjectId to string
def fix_id(doc):
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    if "customerId" in doc:
        doc["customerId"] = str(doc["customerId"])
    if "items" in doc:
        for item in doc["items"]:
            if "productId" in doc:
                doc["productId"] = str(doc["productId"])
    return doc

# ------------------- Authentication -------------------
from fastapi.security import OAuth2PasswordBearer
VALID_TOKENS = ["mysecrettoken123"]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_token(token: str = Depends(oauth2_scheme)):
    if token not in VALID_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

# ------------------- Generic CRUD helper -------------------
def get_collection(name: str):
    return db[name]

# ------------------- Customers -------------------
@app.post("/customers", dependencies=[Depends(verify_token)])
def create_customer(customer: dict):
    res = db.customers.insert_one(customer)
    return {"_id": str(res.inserted_id)}

@app.get("/customers", dependencies=[Depends(verify_token)])
def list_customers():
    return [fix_id(c) for c in db.customers.find()]

@app.get("/customers/{customer_id}", dependencies=[Depends(verify_token)])
def get_customer(customer_id: str):
    customer = db.customers.find_one({"_id": ObjectId(customer_id)})
    if not customer:
        raise HTTPException(404, "Customer not found")
    return fix_id(customer)

@app.put("/customers/{customer_id}", dependencies=[Depends(verify_token)])
def update_customer(customer_id: str, update: dict):
    res = db.customers.update_one({"_id": ObjectId(customer_id)}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(404, "Customer not found")
    return {"status": "updated"}

@app.delete("/customers/{customer_id}", dependencies=[Depends(verify_token)])
def delete_customer(customer_id: str):
    res = db.customers.delete_one({"_id": ObjectId(customer_id)})
    if res.deleted_count == 0:
        raise HTTPException(404, "Customer not found")
    return {"status": "deleted"}

# ------------------- Addresses -------------------
@app.post("/addresses", dependencies=[Depends(verify_token)])
def create_address(address: dict):
    res = db.addresses.insert_one(address)
    return {"_id": str(res.inserted_id)}

@app.get("/addresses", dependencies=[Depends(verify_token)])
def list_addresses():
    return [fix_id(a) for a in db.addresses.find()]

@app.get("/addresses/{address_id}", dependencies=[Depends(verify_token)])
def get_address(address_id: str):
    addr = db.addresses.find_one({"_id": ObjectId(address_id)})
    if not addr:
        raise HTTPException(404, "Address not found")
    return fix_id(addr)

@app.put("/addresses/{address_id}", dependencies=[Depends(verify_token)])
def update_address(address_id: str, update: dict):
    res = db.addresses.update_one({"_id": ObjectId(address_id)}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(404, "Address not found")
    return {"status": "updated"}

@app.delete("/addresses/{address_id}", dependencies=[Depends(verify_token)])
def delete_address(address_id: str):
    res = db.addresses.delete_one({"_id": ObjectId(address_id)})
    if res.deleted_count == 0:
        raise HTTPException(404, "Address not found")
    return {"status": "deleted"}

# ------------------- Orders -------------------
@app.post("/orders", dependencies=[Depends(verify_token)])
def create_order(order: dict):
    res = db.orders.insert_one(order)
    return {"_id": str(res.inserted_id)}

@app.get("/orders", dependencies=[Depends(verify_token)])
def list_orders():
    return [fix_id(o) for o in db.orders.find()]

@app.get("/orders/{order_id}", dependencies=[Depends(verify_token)])
def get_order(order_id: str):
    order = db.orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(404, "Order not found")
    return fix_id(order)

@app.put("/orders/{order_id}", dependencies=[Depends(verify_token)])
def update_order(order_id: str, update: dict):
    res = db.orders.update_one({"_id": ObjectId(order_id)}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(404, "Order not found")
    return {"status": "updated"}

@app.delete("/orders/{order_id}", dependencies=[Depends(verify_token)])
def delete_order(order_id: str):
    res = db.orders.delete_one({"_id": ObjectId(order_id)})
    if res.deleted_count == 0:
        raise HTTPException(404, "Order not found")
    return {"status": "deleted"}

# ------------------- Products -------------------
@app.post("/products", dependencies=[Depends(verify_token)])
def create_product(product: dict):
    res = db.products.insert_one(product)
    return {"_id": str(res.inserted_id)}

@app.get("/products", dependencies=[Depends(verify_token)])
def list_products():
    return [fix_id(p) for p in db.products.find()]

@app.get("/products/{product_id}", dependencies=[Depends(verify_token)])
def get_product(product_id: str):
    product = db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(404, "Product not found")
    return fix_id(product)

@app.put("/products/{product_id}", dependencies=[Depends(verify_token)])
def update_product(product_id: str, update: dict):
    res = db.products.update_one({"_id": ObjectId(product_id)}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(404, "Product not found")
    return {"status": "updated"}

@app.delete("/products/{product_id}", dependencies=[Depends(verify_token)])
def delete_product(product_id: str):
    res = db.products.delete_one({"_id": ObjectId(product_id)})
    if res.deleted_count == 0:
        raise HTTPException(404, "Product not found")
    return {"status": "deleted"}

@app.get("/customers/{customer_id}/full", dependencies=[Depends(verify_token)])
def get_customer_full(customer_id: str):
    # Fetch customer
    customer = db.customers.find_one({"_id": ObjectId(customer_id)})
    if not customer:
        raise HTTPException(404, "Customer not found")
    customer = fix_id(customer)

    # Fetch addresses
    addresses = [fix_id(a) for a in db.addresses.find({"customerId": ObjectId(customer_id)})]

    # Fetch orders
    orders = [fix_id(o) for o in db.orders.find({"customerId": ObjectId(customer_id)})]

    # Combine everything
    return {
        "customer": customer,
        "addresses": addresses,
        "orders": orders
    }

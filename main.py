from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from bson import ObjectId
from bson.son import SON
from pymongo import MongoClient

# Mongo connection
client = MongoClient("mongodb+srv://mongo_db_user:ACsH2Jmp9qrsk3nt@customer.amld2yw.mongodb.net/")
db = client["AI"]

# Helpers
def validate_object_id(id_str: str) -> ObjectId:
    if not ObjectId.is_valid(id_str):
        raise HTTPException(status_code=400, detail=f"Invalid ObjectId: {id_str}")
    return ObjectId(id_str)

def fix_id(doc: dict) -> dict:
    if not doc:
        return doc
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            doc[key] = str(value)
        elif isinstance(value, list):
            doc[key] = [str(v) if isinstance(v, ObjectId) else v for v in value]
    return doc


# -------------------------------
# Pydantic Models (Create + Update)
# -------------------------------

class CustomerCreate(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    phone: str
    status: str = Field(default="active", pattern="^(active|inactive)$")

class CustomerUpdate(BaseModel):
    firstName: Optional[str]
    lastName: Optional[str]
    email: Optional[EmailStr]
    phone: Optional[str]
    status: Optional[str] = Field(default=None, pattern="^(active|inactive)$")

class AddressCreate(BaseModel):
    customerId: str
    street: str
    city: str
    state: str
    zipCode: str
    country: str
    type: Optional[str] = Field(default="shipping", pattern="^(billing|shipping)$")

class AddressUpdate(BaseModel):
    street: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zipCode: Optional[str]
    country: Optional[str]
    type: Optional[str] = Field(default=None, pattern="^(billing|shipping)$")

class OrderItem(BaseModel):
    productId: str
    quantity: int = Field(..., gt=0)
    price: float = Field(..., ge=0)

class OrderCreate(BaseModel):
    customerId: str
    orderDate: str
    status: str = Field(..., pattern="^(pending|shipped|completed)$")
    items: List[OrderItem]

class OrderUpdate(BaseModel):
    orderDate: Optional[str]
    status: Optional[str] = Field(default=None, pattern="^(pending|shipped|completed)$")
    items: Optional[List[OrderItem]]

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float = Field(..., ge=0)
    stock: int = Field(..., ge=0)
    category: str
    status: str = Field(default="active", pattern="^(active|inactive)$")
    tags: Optional[List[str]] = []

class ProductUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    price: Optional[float] = Field(default=None, ge=0)
    stock: Optional[int] = Field(default=None, ge=0)
    category: Optional[str]
    status: Optional[str] = Field(default=None, pattern="^(active|inactive)$")
    tags: Optional[List[str]]


# -------------------------------
# FastAPI app
# -------------------------------

app = FastAPI()

# ---- Customers ----
@app.post("/customers")
def create_customer(customer: CustomerCreate):
    doc = customer.dict()
    result = db.customers.insert_one(doc)
    return {"inserted_id": str(result.inserted_id)}

@app.get("/customers/{customer_id}")
def get_customer(customer_id: str):
    doc = db.customers.find_one({"_id": validate_object_id(customer_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Customer not found")
    return fix_id(doc)

@app.get("/customers")
def list_customers(status: Optional[str] = Query(None, regex="^(active|inactive)$")):
    query = {}
    if status:
        query["status"] = status
    docs = list(db.customers.find(query))
    return [fix_id(doc) for doc in docs]

@app.patch("/customers/{customer_id}")
def update_customer(customer_id: str, updates: CustomerUpdate):
    update_data = {k: v for k, v in updates.dict(exclude_unset=True).items()}
    result = db.customers.update_one(
        {"_id": validate_object_id(customer_id)},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return get_customer(customer_id)

@app.delete("/customers/{customer_id}")
def delete_customer(customer_id: str):
    result = db.customers.delete_one({"_id": validate_object_id(customer_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": f"Customer {customer_id} deleted successfully"}

# ---- Addresses ----
@app.post("/addresses")
def create_address(address: AddressCreate):
    doc = address.dict()
    doc["customerId"] = validate_object_id(doc["customerId"])
    result = db.addresses.insert_one(doc)
    return {"inserted_id": str(result.inserted_id)}

@app.get("/addresses/{address_id}")
def get_address(address_id: str):
    doc = db.addresses.find_one({"_id": validate_object_id(address_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Address not found")
    return fix_id(doc)

@app.get("/addresses")
def list_addresses(customerId: Optional[str] = None):
    query = {}
    if customerId:
        query["customerId"] = validate_object_id(customerId)
    docs = list(db.addresses.find(query))
    return [fix_id(doc) for doc in docs]

@app.patch("/addresses/{address_id}")
def update_address(address_id: str, updates: AddressUpdate):
    update_data = {k: v for k, v in updates.dict(exclude_unset=True).items()}
    result = db.addresses.update_one(
        {"_id": validate_object_id(address_id)},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Address not found")
    return get_address(address_id)

@app.delete("/addresses/{address_id}")
def delete_address(address_id: str):
    result = db.addresses.delete_one({"_id": validate_object_id(address_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Address not found")
    return {"message": f"Address {address_id} deleted successfully"}

# ---- Orders ----
@app.post("/orders")
def create_order(order: OrderCreate):
    items = []
    for item in order.items:
        items.append({
            "productId": validate_object_id(item.productId),
            "quantity": item.quantity,
            "price": item.price
        })
    doc = {
        "customerId": validate_object_id(order.customerId),
        "orderDate": order.orderDate,
        "status": order.status,
        "items": items
    }
    result = db.orders.insert_one(doc)
    return {"inserted_id": str(result.inserted_id)}

@app.get("/orders/{order_id}")
def get_order(order_id: str):
    doc = db.orders.find_one({"_id": validate_object_id(order_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Order not found")
    return fix_id(doc)

@app.get("/orders")
def list_orders(customerId: Optional[str] = None, status: Optional[str] = None):
    query = {}
    if customerId:
        query["customerId"] = validate_object_id(customerId)
    if status:
        query["status"] = status
    docs = list(db.orders.find(query))
    return [fix_id(doc) for doc in docs]

@app.patch("/orders/{order_id}")
def update_order(order_id: str, updates: OrderUpdate):
    update_data = updates.dict(exclude_unset=True)
    if "items" in update_data:
        update_data["items"] = [
            {
                "productId": validate_object_id(item.productId),
                "quantity": item.quantity,
                "price": item.price
            }
            for item in update_data["items"]
        ]
    result = db.orders.update_one(
        {"_id": validate_object_id(order_id)},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    return get_order(order_id)

@app.delete("/orders/{order_id}")
def delete_order(order_id: str):
    result = db.orders.delete_one({"_id": validate_object_id(order_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": f"Order {order_id} deleted successfully"}

# ---- Products ----
@app.post("/products")
def create_product(product: ProductCreate):
    doc = product.dict()
    result = db.products.insert_one(doc)
    return {"inserted_id": str(result.inserted_id)}

@app.get("/products/{product_id}")
def get_product(product_id: str):
    doc = db.products.find_one({"_id": validate_object_id(product_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    return fix_id(doc)

@app.get("/products")
def list_products(category: Optional[str] = None, status: Optional[str] = None):
    query = {}
    if category:
        query["category"] = category
    if status:
        query["status"] = status
    docs = list(db.products.find(query))
    return [fix_id(doc) for doc in docs]

@app.patch("/products/{product_id}")
def update_product(product_id: str, updates: ProductUpdate):
    update_data = {k: v for k, v in updates.dict(exclude_unset=True).items()}
    result = db.products.update_one(
        {"_id": validate_object_id(product_id)},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return get_product(product_id)

@app.delete("/products/{product_id}")
def delete_product(product_id: str):
    result = db.products.delete_one({"_id": validate_object_id(product_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": f"Product {product_id} deleted successfully"}

# ---- Customer Details ----
@app.get("/customers/{customer_id}/details")
def get_customer_details(customer_id: str):
    customer = db.customers.find_one({"_id": validate_object_id(customer_id)})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Fetch addresses
    addresses = list(db.addresses.find({"customerId": validate_object_id(customer_id)}))

    # Fetch orders
    orders = list(db.orders.find({"customerId": validate_object_id(customer_id)}))
    for order in orders:
        # For each order, replace productId with actual product details
        for item in order.get("items", []):
            product = db.products.find_one({"_id": item["productId"]})
            if product:
                item["product"] = fix_id(product)

    # Build response
    customer_details = {
        "customer": fix_id(customer),
        "addresses": [fix_id(addr) for addr in addresses],
        "orders": [fix_id(order) for order in orders]
    }

    return customer_details

from fastapi import FastAPI, Depends, HTTPException
from mangum import Mangum
import os
import sys
sys.path.append('/opt/python')
sys.path.append('../../shared')

from shared.auth import get_current_user, require_role
from shared.utils import TenantRepository, UserRepository, ItemRepository
from shared.models import Tenant, User, Item

app = FastAPI(title="SaaS API")

# Initialize repositories
tenant_repo = TenantRepository(os.environ['TENANTS_TABLE'])
user_repo = UserRepository(os.environ['USERS_TABLE'])
item_repo = ItemRepository(os.environ['ITEMS_TABLE'])

@app.get("/_health")
def health_check():
    return {"status": "healthy"}

# Tenant endpoints
@app.post("/tenants")
def create_tenant(name: str, current_user: dict = Depends(require_role(["admin"]))):
    return tenant_repo.create(name)

@app.get("/tenants/{tenant_id}")
def get_tenant(tenant_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["tenant_id"] != tenant_id and "admin" not in current_user["roles"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return tenant_repo.get(tenant_id)

# User endpoints
@app.post("/users")
def create_user(email: str, role: str, current_user: dict = Depends(require_role(["admin"]))):
    return user_repo.create(current_user["tenant_id"], email, role)

@app.get("/users")
def list_users(current_user: dict = Depends(require_role(["admin"]))):
    return user_repo.list_by_tenant(current_user["tenant_id"])

# Item endpoints
@app.post("/items")
def create_item(name: str, description: str = None, current_user: dict = Depends(get_current_user)):
    return item_repo.create(current_user["tenant_id"], name, description)

@app.get("/items")
def list_items(current_user: dict = Depends(get_current_user)):
    return item_repo.list_by_tenant(current_user["tenant_id"])

@app.put("/items/{item_id}")
def update_item(item_id: str, name: str, description: str = None, current_user: dict = Depends(get_current_user)):
    return item_repo.update(current_user["tenant_id"], item_id, name, description)

@app.delete("/items/{item_id}")
def delete_item(item_id: str, current_user: dict = Depends(get_current_user)):
    item_repo.delete(current_user["tenant_id"], item_id)
    return {"message": "Item deleted"}

handler = Mangum(app)

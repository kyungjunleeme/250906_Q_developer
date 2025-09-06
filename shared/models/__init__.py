from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Tenant(BaseModel):
    tenant_id: str
    name: str
    created_at: datetime
    status: str = "active"

class User(BaseModel):
    user_id: str
    tenant_id: str
    email: str
    role: str
    created_at: datetime
    status: str = "active"

class Item(BaseModel):
    tenant_id: str
    item_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

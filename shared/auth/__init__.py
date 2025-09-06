import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List
import os

security = HTTPBearer()

def decode_jwt(token: str) -> Dict:
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    payload = decode_jwt(credentials.credentials)
    tenant_id = payload.get("custom:tenant_id")
    roles = payload.get("cognito:groups", [])
    
    if not tenant_id:
        raise HTTPException(status_code=401, detail="No tenant_id in token")
    
    return {
        "user_id": payload.get("sub"),
        "tenant_id": tenant_id,
        "email": payload.get("email"),
        "roles": roles
    }

def require_role(required_roles: List[str]):
    def role_checker(current_user: Dict = Depends(get_current_user)):
        user_roles = current_user.get("roles", [])
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

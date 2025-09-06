from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import requests
import os
import boto3

app = FastAPI()
templates = Jinja2Templates(directory="templates")

ssm = boto3.client('ssm')
stage = os.environ.get('STAGE', 'dev')

def get_api_url():
    try:
        response = ssm.get_parameter(Name=f'/saas/{stage}/api/url')
        return response['Parameter']['Value']
    except:
        return "http://localhost:8000"

API_URL = get_api_url()

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/tenants", response_class=HTMLResponse)
def tenants_page(request: Request):
    return templates.TemplateResponse("tenants.html", {"request": request})

@app.post("/tenants")
def create_tenant(name: str = Form(...), request: Request = None):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token:
        try:
            requests.post(f"{API_URL}/tenants", 
                         params={"name": name},
                         headers={"Authorization": f"Bearer {token}"})
        except:
            pass
    return RedirectResponse("/tenants")

@app.get("/users", response_class=HTMLResponse)
def users_page(request: Request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    users = []
    if token:
        try:
            response = requests.get(f"{API_URL}/users", headers={"Authorization": f"Bearer {token}"})
            users = response.json() if response.status_code == 200 else []
        except:
            pass
    
    return templates.TemplateResponse("users.html", {"request": request, "users": users})

@app.get("/metrics", response_class=HTMLResponse)
def metrics_page(request: Request):
    return templates.TemplateResponse("metrics.html", {"request": request})

@app.get("/_health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

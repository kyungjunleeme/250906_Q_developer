from fastapi import FastAPI, Request, Form, Depends, HTTPException
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

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/items", response_class=HTMLResponse)
def items_page(request: Request):
    # In real app, get token from session/cookie
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return RedirectResponse("/login")
    
    try:
        response = requests.get(f"{API_URL}/items", headers={"Authorization": f"Bearer {token}"})
        items = response.json() if response.status_code == 200 else []
    except:
        items = []
    
    return templates.TemplateResponse("items.html", {"request": request, "items": items})

@app.post("/items")
def create_item(name: str = Form(...), description: str = Form(""), request: Request = None):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return RedirectResponse("/login")
    
    try:
        requests.post(f"{API_URL}/items", 
                     params={"name": name, "description": description},
                     headers={"Authorization": f"Bearer {token}"})
    except:
        pass
    
    return RedirectResponse("/items")

@app.get("/_health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

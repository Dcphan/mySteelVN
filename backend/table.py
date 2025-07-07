import os
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
from table_db import TableDatabase
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATIC_DIR = os.path.join(BASE_DIR, "..", "frontend", "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "..", "frontend")
DB_PATH = os.path.join(BASE_DIR, "..", "database", "san_luong.db")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

db_manager = TableDatabase(path=DB_PATH)

@app.get("/table/sanluong", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse("table.html", {"request": request})

@app.get("/api/table-data")
def get_table_data(products: str = Query(...), month: str = Query(...)):
    product_list = products.split(",")
    return db_manager.table_data(product_list, month)

@app.get("/table/tonghopthang", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse("monthly_table.html", {"request": request})

@app.get("/api/monthly-summary")
def get_monthly_summary(
    table: str = Query(...),
    product: List[str] = Query(...), 
    start: str = Query(...),
    end: str = Query(...)
):
    return db_manager.get_month_summary(table, product, start, end)

@app.get("/api/product-data")
def get_product_data():
    data = db_manager.get_product_and_company()
    print("Returned product data:", data)
    return data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("table:app", host="127.0.0.1", port=8000, reload=True)
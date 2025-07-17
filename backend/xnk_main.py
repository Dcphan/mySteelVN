import os
from fastapi import FastAPI, Request, Query, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
from table_db import TableDatabase
from db import SteelDatabaseManager
from Import import SteelDataProcessor
from xnk_pipeline import XNK_pipeline
from pydantic import BaseModel
from pathlib import Path
import uvicorn
from starlette.background import BackgroundTask
from export import Export
import shutil
import pandas as pd
from sqlalchemy import text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATIC_DIR = os.path.join(BASE_DIR, "..", "frontend", "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "..", "frontend")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

db_manager = SteelDatabaseManager(dbname="steel_database", user="mysteelvn", password="cjLVuBdaSd5vtst")
table_db = TableDatabase(dbname="steel_database", user="mysteelvn", password="cjLVuBdaSd5vtst")
export_handler = Export(dbname="steel_database", user="mysteelvn", password="cjLVuBdaSd5vtst")

@app.get('/upload_selection')
def upload_selection_page(request: Request):
    return templates.TemplateResponse("xnk_upload.html", {"request": request})

@app.get('/upload_single_address')
def upload_single_address_page(request: Request):
    return templates.TemplateResponse("upload_single_address.html", {"request": request})

@app.get('/upload_multi_address')
def upload_multi_address_page(request: Request):
    return templates.TemplateResponse("upload_multi_address.html", {"request": request})

@app.post("/upload_excel_xnk")
async def upload_excel_file(file: UploadFile = File(...)):
    try:
        temp_dir = os.path.join(BASE_DIR, "temp_uploads")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, file.filename)

        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        processor = XNK_pipeline(file_path=temp_path)
        processor.import_function()

        return {"message": f"✅ File '{file.filename}' uploaded and processed."}

    except Exception as e:
        return {"error": f"❌ Failed to process file: {str(e)}"}

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/api/pivot-country-summary")
def pivot_country_summary(date: str=Query(...), item: list=Query(...)):
    data = db_manager.xnk_get_total_data("country", date, item)
    return data

@app.get("/api/pivot-hscode-summary")
def pivot_product_summary(date: str=Query(...), item: list=Query(...)):
    data = db_manager.xnk_get_total_data("commodity", date, item)
    return data

@app.get("/table/total-product-summary", response_class=HTMLResponse)
async def read_table(request: Request):
    return templates.TemplateResponse("total_table_xnk.html", {"request": request})

@app.get("/api/commodity-options")
def get_commodity_options():
    return db_manager.get_distinct_commodities("commodity")

@app.get("/api/country-options")
def get_country_options():
    return db_manager.get_distinct_commodities("country")

@app.get("/table/total-country-summary", response_class=HTMLResponse)
async def read_table(request: Request):
    return templates.TemplateResponse("country_total_table_xnk.html", {"request": request})

@app.get("/api/pivot-country")
def pivot_summary(
    commodities: List[str] = Query(default=["Alloy Bar", "Alloy Ingot"]),
    country: str = Query(default="Japan"),
    date: str = Query(default="2025-05")
):
    data = db_manager.xnk_get_info_by_country(country, commodities, date)
    return data

@app.get("/table/country-summary-table")
def read_table(request: Request):
    return templates.TemplateResponse("summary.html", {"request": request})

@app.get("/api/pivot-commodity")
def pivot_summary(
    countries: List[str] = Query(default=["Japan", "China"]),
    commodity: str = Query(default="Alloy Bar"),
    date: str = Query(default="2025-05")
):
    data = db_manager.xnk_get_info_by_commodity(countries, commodity, date)
    return data

@app.get("/table/product-summary-table")
def read_table(request: Request):
    return templates.TemplateResponse("summary_product.html", {"request": request})





    




if __name__ == "__main__":
    uvicorn.run("xnk_main:app", host="127.0.0.1", port=8000, reload=True)

import os
from fastapi import FastAPI, Request, Query, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from backend.table_db import TableDatabase
from backend.db import SteelDatabaseManager
from backend.Import import SteelDataProcessor
from pydantic import BaseModel
from pathlib import Path
import uvicorn
from backend.xnk_pipeline import XNK_pipeline
from starlette.background import BackgroundTask
from backend.export import Export
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATIC_DIR = os.path.join(BASE_DIR, "..", "frontend", "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "..", "frontend")
print(TEMPLATE_DIR)

class DataRequest(BaseModel):
    main_table: str
    ID: List[str]
    start_date: str
    end_date: str 

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

@app.get("/upload", response_class=HTMLResponse)
async def upload_san_luong(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload_excel")
async def upload_excel_file(file: UploadFile = File(...)):
    try:
        temp_dir = os.path.join(BASE_DIR, "temp_uploads")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, file.filename)

        # Save uploaded file to temp folder
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Run your processor
        processor = SteelDataProcessor(file_path=temp_path)
        processor.import_function()

        return {"message": f"✅ File '{file.filename}' uploaded and processed."}

    except Exception as e:
        return {"error": f"❌ Failed to process file: {str(e)}"}

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/chart/bar", response_class=HTMLResponse)
async def bar_chart_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/get_data")
def get_monthly_summary(
    table: str = Query(...),
    product: List[str] = Query(...), 
    start: str = Query(...),
    end: str = Query(...)
):
    return db_manager.get_data(table, product, start, end)


@app.get("/chart/pie", response_class=HTMLResponse)
async def pie_chart_page(request: Request):
    return templates.TemplateResponse("piechart.html", {"request": request})

@app.get("/api/pie-market-share")
def get_market_share(product_type: str, date: str):
    return JSONResponse(content = db_manager.pie_market_share(product_type, date))

@app.get("/api/product-data")
def get_product_data():
    data = table_db.get_product_and_company()
    print("Returned product data:", data)
    return data

@app.get("/api/product-option")
def get_product_option():
    data = table_db.get_product()
    return data


@app.get("/excel-tool", response_class=HTMLResponse)
async def serve_excel_tool_frontend(request: Request):
    return templates.TemplateResponse("export.html", {"request": request})

@app.get("/export-excel")
async def export_excel(filename: str = "san_luong_report.xlsx"):
    downloads_path = Path.home() / "Downloads"
    downloads_path.mkdir(parents=True, exist_ok=True)

    excel_output_path = downloads_path / filename

    success = export_handler.convert_to_excel(str(excel_output_path))

    if success:
        if not excel_output_path.exists():
            raise HTTPException(status_code=500, detail="Generated Excel file not found.")

        return FileResponse(
            path=str(excel_output_path),
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            background=BackgroundTask(os.remove, str(excel_output_path))
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to generate Excel file. Check DB or export logic.")

@app.get("/get-all-pivot-data")
async def get_all_pivot_data():

    try:
        data = export_handler.get_all_pivot_data()
        if not data:
            return JSONResponse(content={}, status_code=200)
        return JSONResponse(content=data)
    except Exception as e:
        if isinstance(e, HTTPException) and e.status_code == 500:
            raise
        raise HTTPException(status_code=500, detail=f"Error fetching preview data: {e}. Ensure your database is correctly set up.")

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
    return table_db.get_month_summary(table, product, start, end)

@app.get("/api/product-data")
def get_product_data():
    data = table_db.get_product_and_company()
    print("Returned product data:", data)
    return data


# FILE XUAT NHAP KHAU
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

@app.get("/api/pivot-data")
def pivot_summary(
      filter_field: Optional[str] = Query(
        default=None,
        examples={"example": {"value": "commodity"}}
    ),
    filter_value: Optional[str] = Query(
        default=None,
        examples={"example": {"value": "Alloy Bar"}}
    ),
    rows_field: List[str] = Query(default=["country", "company"]),
    rows_value: List[str] = Query(default=["Japan", "China"]),
    value_fields: List[str] = Query(default=["quantity", "amount"]),
    date: str = Query(default="2025-05")
):
    data = db_manager.xnk_get_info(
        filter_field=filter_field,
        filter_value=filter_value,
        rows_fields=rows_field,
        rows_values=rows_value,
        values_fields=value_fields,
        date=date
    )
    return JSONResponse(content=data)

@app.get("/api/single-pivot-summary")
def pivot_country_summary(row_field: str=Query(...), date: str=Query(...), item: Optional[List]=Query(None), value_fields: List[str]=Query(...)):
    data = db_manager.xnk_get_total_data(row_field, date, item, value_fields)
    return data

@app.get("/table/pivot-table")
def read_table(request: Request):
    return templates.TemplateResponse("pivottable.html", {"request": request})


@app.get("/api/filtering-data")
def filtering_data(
    filter: str = Query(default=None),
    date: str = Query(default=None),
):
    data = db_manager.xnk_get_distinct_filter(filter, date)
    return data

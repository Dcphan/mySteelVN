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



if __name__ == "__main__":
    uvicorn.run("xnk_main:app", host="127.0.0.1", port=8000, reload=True)

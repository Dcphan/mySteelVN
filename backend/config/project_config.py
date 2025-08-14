import os
from dotenv import load_dotenv

# Load .env only when not running on Render
if os.getenv("RENDER") != "true":
    load_dotenv(dotenv_path=".env")

def load_config(prefix: str):
    return {
        "dbname": os.getenv(f"{prefix}_DBNAME"),
        "user": os.getenv(f"{prefix}_USER"),
        "password": os.getenv(f"{prefix}_PASSWORD"),
        "host": os.getenv(f"{prefix}_HOST"),
        "port": int(os.getenv(f"{prefix}_PORT", 5432)),
        "sslmode": os.getenv(f"{prefix}_SSLMODE", "require")
    }

# Load configs once
SAN_LUONG_CONFIG = load_config("SAN_LUONG")
NHAP_KHAU_CONFIG = load_config("NHAP_KHAU")
XUAT_KHAU_CONFIG = load_config("XUAT_KHAU")

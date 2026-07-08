import os
from pathlib import Path

# Load env variables from .env file manually to minimize external dependency issues
ENV_PATH = Path(__file__).parent / ".env"

if ENV_PATH.exists():
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

# Notion Configs
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_CUSTOMERS_DB_ID = os.environ.get("NOTION_CUSTOMERS_DB_ID", "")
NOTION_ORDERS_DB_ID = os.environ.get("NOTION_ORDERS_DB_ID", "")

# Printer Configs
PRINTER_PORT = os.environ.get("PRINTER_PORT", "COM4")
PRINTER_BAUDRATE = int(os.environ.get("PRINTER_BAUDRATE", "9600"))

# Server Configs
PORT = int(os.environ.get("PORT", "5000"))
HOST = os.environ.get("HOST", "127.0.0.1")

def is_notion_configured():
    return bool(NOTION_TOKEN and NOTION_CUSTOMERS_DB_ID and NOTION_ORDERS_DB_ID)

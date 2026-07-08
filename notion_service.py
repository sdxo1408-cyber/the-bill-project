import requests
from datetime import datetime
import config

NOTION_VERSION = "2022-06-28"

def _get_headers():
    return {
        "Authorization": f"Bearer {config.NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }

def find_customer_by_phone(phone):
    """
    Search for a customer by phone number in the Notion database.
    Returns customer details if found, or None.
    """
    if not config.is_notion_configured():
        print("[!] Notion credentials not fully configured.")
        return None

    url = f"https://api.notion.com/v1/databases/{config.NOTION_CUSTOMERS_DB_ID}/query"
    payload = {
        "filter": {
            "property": "Phone",
            "phone_number": {
                "equals": phone
            }
        }
    }
    
    try:
        response = requests.post(url, headers=_get_headers(), json=payload, timeout=10)
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results:
                page = results[0]
                page_id = page["id"]
                props = page["properties"]
                
                # Extract Name
                name = ""
                title_objs = props.get("Name", {}).get("title", [])
                if title_objs:
                    name = title_objs[0].get("text", {}).get("content", "")
                
                # Extract Address
                address = ""
                address_objs = props.get("Address", {}).get("rich_text", [])
                if address_objs:
                    address = address_objs[0].get("text", {}).get("content", "")
                
                return {
                    "page_id": page_id,
                    "name": name,
                    "phone": phone,
                    "address": address
                }
        else:
            print(f"[!] Notion query customer failed ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"[!] Notion query customer connection error: {e}")
        
    return None

def create_or_update_customer(name, phone, address):
    """
    Creates a new customer or updates an existing one if the address/name changed.
    """
    if not config.is_notion_configured():
        return None

    existing = find_customer_by_phone(phone)
    
    if existing:
        # Check if details changed
        if existing["name"] != name or existing["address"] != address:
            print(f"[*] Updating existing customer: {phone}")
            url = f"https://api.notion.com/v1/pages/{existing['page_id']}"
            payload = {
                "properties": {
                    "Name": {
                        "title": [{"text": {"content": name}}]
                    },
                    "Address": {
                        "rich_text": [{"text": {"content": address}}]
                    }
                }
            }
            try:
                response = requests.patch(url, headers=_get_headers(), json=payload, timeout=10)
                if response.status_code == 200:
                    return {
                        "page_id": existing["page_id"],
                        "name": name,
                        "phone": phone,
                        "address": address
                    }
                else:
                    print(f"[!] Notion update customer failed: {response.text}")
            except Exception as e:
                print(f"[!] Notion update customer error: {e}")
        return existing

    # Create new customer
    print(f"[*] Creating new customer: {name} ({phone})")
    url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": config.NOTION_CUSTOMERS_DB_ID},
        "properties": {
            "Name": {
                "title": [{"text": {"content": name}}]
            },
            "Phone": {
                "phone_number": phone
            },
            "Address": {
                "rich_text": [{"text": {"content": address}}]
            }
        }
    }
    
    try:
        response = requests.post(url, headers=_get_headers(), json=payload, timeout=10)
        if response.status_code == 200:
            res_data = response.json()
            return {
                "page_id": res_data["id"],
                "name": name,
                "phone": phone,
                "address": address
            }
        else:
            print(f"[!] Notion create customer failed ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"[!] Notion create customer connection error: {e}")
        
    return None

def create_order(bill_no, customer_name, customer_phone, items_summary, total_amount):
    """
    Log a transaction in the Notion Orders database.
    """
    if not config.is_notion_configured():
        return False

    url = "https://api.notion.com/v1/pages"
    now_iso = datetime.now().isoformat()
    
    payload = {
        "parent": {"database_id": config.NOTION_ORDERS_DB_ID},
        "properties": {
            "Bill No": {
                "title": [{"text": {"content": bill_no}}]
            },
            "Customer Name": {
                "rich_text": [{"text": {"content": customer_name}}]
            },
            "Phone": {
                "phone_number": customer_phone
            },
            "Items": {
                "rich_text": [{"text": {"content": items_summary}}]
            },
            "Total Amount": {
                "number": float(total_amount)
            },
            "Date": {
                "date": {"start": now_iso}
            }
        }
    }
    
    try:
        response = requests.post(url, headers=_get_headers(), json=payload, timeout=10)
        if response.status_code == 200:
            print(f"[OK] Transaction saved in Notion Orders database!")
            return True
        else:
            print(f"[!] Notion create order failed ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"[!] Notion create order connection error: {e}")
        
    return False

from flask import Flask, jsonify, request, render_template
from datetime import datetime
import os
import config
import notion_service
import db_service
from escpos.printer import Serial

app = Flask(__name__)

# Default Inventory Items
DEFAULT_INVENTORY = [
    {"id": "leg_chest", "name": "Leg & Chest", "unit": "kg", "price": 320},
    {"id": "ch_boneless", "name": "Ch. Boneless", "unit": "kg", "price": 285},
    {"id": "chicken_tikka", "name": "Chicken Tikka", "unit": "kg", "price": 350},
    {"id": "chicken_drumsticks", "name": "Chicken Drumsticks", "unit": "kg", "price": 340},
    {"id": "chicken_wings", "name": "Chicken Wings", "unit": "kg", "price": 220},
    {"id": "whole_chicken", "name": "Whole Chicken", "unit": "pc", "price": 250}
]

def generate_bill_no():
    try:
        conn = db_service.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM orders")
        count = cursor.fetchone()["count"]
        conn.close()
    except Exception:
        count = 0
    b_no = f"#DD-{(count + 1):04d}"
    return b_no

# Helper functions for receipt layout
def two_col(left, right, w=32):
    gap = w - len(left) - len(right)
    if gap < 1:
        gap = 1
    return left + " " * gap + right

def item_row(name, qty, price):
    name_col = f"{name:<13}"[:13]
    qty_col = f"{qty:<9}"[:9]
    price_col = f"Rs.{int(price):>6}"[:10]
    return name_col + qty_col + price_col

def wrap_address(address, w=22):
    words = address.split()
    lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 <= w:
            current = (current + " " + word).strip()
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

@app.route("/")
def index():
    import time
    return render_template("index.html", version=int(time.time()))

@app.route("/api/config-status", methods=["GET"])
def get_config_status():
    return jsonify({
        "notion_connected": config.is_notion_configured(),
        "printer_port": config.PRINTER_PORT,
        "printer_baudrate": config.PRINTER_BAUDRATE
    })

@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    try:
        items = db_service.get_inventory()
        return jsonify(items)
    except Exception as e:
        print(f"[!] Error fetching inventory from SQLite: {e}")
        return jsonify(DEFAULT_INVENTORY)

@app.route("/api/products", methods=["POST"])
def add_product_api():
    data = request.get_json() or {}
    product_id = data.get("id", "").strip()
    name = data.get("name", "").strip()
    unit = data.get("unit", "").strip()
    price = data.get("price")
    
    if not product_id or not name or not unit or price is None:
        return jsonify({"success": False, "error": "All fields (ID, Name, Unit, Price) are required."}), 400
        
    try:
        price = float(price)
    except ValueError:
        return jsonify({"success": False, "error": "Price must be a valid number."}), 400
        
    success = db_service.add_product(product_id, name, unit, price)
    if success:
        return jsonify({"success": True, "message": f"Product '{name}' added successfully."})
    else:
        return jsonify({"success": False, "error": "Product ID already exists or database error occurred."}), 400

@app.route("/api/products/<product_id>", methods=["PUT"])
def update_product_api(product_id):
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    unit = data.get("unit", "").strip()
    price = data.get("price")
    
    if not name or not unit or price is None:
        return jsonify({"success": False, "error": "Name, Unit, and Price are required."}), 400
        
    try:
        price = float(price)
    except ValueError:
        return jsonify({"success": False, "error": "Price must be a valid number."}), 400
        
    success = db_service.update_product(product_id, name, unit, price)
    if success:
        return jsonify({"success": True, "message": f"Product updated successfully."})
    else:
        return jsonify({"success": False, "error": "Product not found or database error occurred."}), 404

@app.route("/api/products/<product_id>", methods=["DELETE"])
def delete_product_api(product_id):
    success = db_service.delete_product(product_id)
    if success:
        return jsonify({"success": True, "message": f"Product deleted successfully."})
    else:
        return jsonify({"success": False, "error": "Product not found or database error occurred."}), 404

@app.route("/api/customer-search", methods=["GET"])
def search_customer():
    phone = request.args.get("phone", "").strip()
    if not phone:
        return jsonify({"found": False, "message": "Phone parameter required."}), 400
    
    # 1. Search in local SQL database first
    try:
        customer = db_service.find_user_by_phone(phone)
        if customer:
            return jsonify({
                "found": True,
                "name": customer["name"],
                "address": customer["address"]
            })
    except Exception as e:
        print(f"[!] Error searching customer in SQLite: {e}")

    # 2. Fallback to Notion if configured
    if config.is_notion_configured():
        customer = notion_service.find_customer_by_phone(phone)
        if customer:
            return jsonify({
                "found": True,
                "name": customer["name"],
                "address": customer["address"]
            })
        
    return jsonify({"found": False})

@app.route("/api/customers", methods=["GET"])
def get_customers_api():
    try:
        users = db_service.get_users()
        return jsonify(users)
    except Exception as e:
        print(f"[!] Error fetching customers from SQLite: {e}")
        return jsonify([]), 500

@app.route("/api/customers", methods=["POST"])
def add_customer_api():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    address = data.get("address", "").strip()
    
    if not name or not phone:
        return jsonify({"success": False, "error": "Name and Phone are required."}), 400
        
    try:
        existing = db_service.find_user_by_phone(phone)
        if existing:
            return jsonify({"success": False, "error": f"Customer with phone {phone} already exists."}), 400
            
        user_id = db_service.create_or_update_user(name, phone, address)
        
        # Sync to Notion if configured
        notion_synced = False
        if config.is_notion_configured():
            try:
                notion_service.create_or_update_customer(name, phone, address)
                notion_synced = True
            except Exception as e:
                print(f"[!] Notion sync error: {e}")
                
        return jsonify({
            "success": True, 
            "message": f"Customer '{name}' added successfully.",
            "user_id": user_id,
            "notion_synced": notion_synced
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/customers/<int:user_id>", methods=["PUT"])
def update_customer_api(user_id):
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    address = data.get("address", "").strip()
    
    if not name or not phone:
        return jsonify({"success": False, "error": "Name and Phone are required."}), 400
        
    try:
        existing = db_service.find_user_by_phone(phone)
        if existing and existing["id"] != user_id:
            return jsonify({"success": False, "error": f"Another customer already has phone {phone}."}), 400
            
        success = db_service.update_user(user_id, name, phone, address)
        if not success:
            return jsonify({"success": False, "error": "Customer not found or update failed."}), 404
            
        # Sync to Notion if configured
        notion_synced = False
        if config.is_notion_configured():
            try:
                notion_service.create_or_update_customer(name, phone, address)
                notion_synced = True
            except Exception as e:
                print(f"[!] Notion sync error: {e}")
                
        return jsonify({
            "success": True,
            "message": "Customer updated successfully.",
            "notion_synced": notion_synced
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/customers/<int:user_id>", methods=["DELETE"])
def delete_customer_api(user_id):
    try:
        success = db_service.delete_user(user_id)
        if success:
            return jsonify({"success": True, "message": "Customer deleted successfully."})
        else:
            return jsonify({"success": False, "error": "Customer not found or delete failed."}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/customers/search", methods=["GET"])
def search_customers_api():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])
    try:
        users = db_service.search_users(query)
        return jsonify(users)
    except Exception as e:
        print(f"[!] Error searching customers in SQLite: {e}")
        return jsonify([]), 500


@app.route("/api/print-and-save", methods=["POST"])
def print_and_save():
    data = request.get_json() or {}
    
    customer_name = data.get("customer_name", "").strip()
    customer_phone = data.get("customer_phone", "").strip()
    customer_address = data.get("customer_address", "").strip()
    items = data.get("items", [])
    
    if not customer_name or not customer_phone:
        return jsonify({"success": False, "error": "Customer Name and Phone are required."}), 400
        
    if not items:
        return jsonify({"success": False, "error": "Cannot bill an empty cart."}), 400
        
    # Generate bill number
    bill_no = generate_bill_no()
    
    # Calculate Total
    total_amount = sum(float(item["price"]) * float(item["qty"]) for item in items)
    
    # Construct Items summary string for Notion
    items_summary_list = []
    for item in items:
        items_summary_list.append(f"{item['name']} ({item['qty']} {item.get('unit', 'kg')})")
    items_summary = ", ".join(items_summary_list)
    
    # ── LOCAL SQL DATABASE INTEGRATION ──
    sql_saved = False
    try:
        # 1. Create/Update user details
        db_service.create_or_update_user(customer_name, customer_phone, customer_address)
        # 2. Save order transaction
        sql_saved = db_service.save_order(bill_no, customer_phone, items, total_amount)
    except Exception as e:
        print(f"[!] Error saving transaction to SQLite: {e}")

    # ── NOTION INTEGRATION ──
    notion_saved = False
    notion_error = None
    
    if config.is_notion_configured():
        try:
            # 1. Create/Update Customer Profile in Notion
            cust_res = notion_service.create_or_update_customer(customer_name, customer_phone, customer_address)
            # 2. Record Transaction Entry in Notion
            if cust_res:
                notion_saved = notion_service.create_order(
                    bill_no=bill_no,
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    items_summary=items_summary,
                    total_amount=total_amount
                )
            if not notion_saved:
                notion_error = "Failed to create order transaction entry in Notion database."
        except Exception as e:
            notion_error = str(e)
    else:
        notion_error = "Notion is not configured. Running in Local-Only Print Mode."

    # ── PRINTER INTEGRATION ──
    print_success = False
    print_error = None
    try:
        p = Serial(
            devfile=config.PRINTER_PORT,
            baudrate=config.PRINTER_BAUDRATE,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=2,
            dsrdtr=True,
            profile="default"
        )
        
        # ── Print Header ──
        p.set(align="center", bold=True, width=2, height=2)
        p.textln("DELHI DARBAR")
        p.set(align="center", bold=False, normal_textsize=True)
        p.textln("Raw Chicken Shop")
        p.textln("Ph: 1800-XXX-XXXX")
        p.textln("=" * 32)
        
        # ── Date / Time / Bill No ──
        now = datetime.now()
        p.textln(two_col(f"Date: {now.strftime('%d/%m/%Y')}", f"Time: {now.strftime('%I:%M %p')}"))
        p.textln(two_col(f"Bill: {bill_no}", ""))
        p.textln("-" * 32)
        
        # ── Customer Info ──
        p.textln(f"Customer : {customer_name}")
        p.ln(1)
        p.textln(f"Phone    : {customer_phone}")
        if customer_address:
            p.ln(1)
            addr_lines = wrap_address(customer_address)
            p.textln(f"Address  : {addr_lines[0]}")
            for line in addr_lines[1:]:
                p.textln(f"           {line}")
        p.textln("-" * 32)
        
        # ── Items Table ──
        p.set(bold=True)
        p.textln(f"{'ITEM':<13}{'QTY':<9}{'AMOUNT':>10}")
        p.set(bold=False)
        p.textln("-" * 32)
        
        for item in items:
            qty_label = f"{item['qty']} {item.get('unit', 'kg')}"
            row_price = float(item['price']) * float(item['qty'])
            p.textln(item_row(item['name'], qty_label, row_price))
            
        p.textln("-" * 32)
        p.set(bold=True)
        p.textln(two_col("TOTAL AMOUNT", f"Rs. {int(total_amount)}"))
        p.set(bold=False)
        p.textln("=" * 32)
        
        # ── Footer ──
        p.ln(1)
        p.set(align="center")
        p.textln("Thank you for Ordering")
        p.set(align="center", bold=True)
        p.textln("from Delhi Darbar!")
        p.set(bold=False)
        p.ln(3)
        p.cut()
        p.close()
        
        print_success = True
    except Exception as e:
        print_error = f"Printer error on {config.PRINTER_PORT}: {str(e)}"
        print(f"[!] {print_error}")

    return jsonify({
        "success": print_success,
        "sql_saved": sql_saved,
        "notion_saved": notion_saved,
        "notion_error": notion_error,
        "print_error": print_error,
        "bill_no": bill_no,
        "total_amount": total_amount
    })

if __name__ == "__main__":
    # Initialize the local SQL database
    db_service.init_db()
    
    print(f"[*] Starting local POS server on http://{config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=True)

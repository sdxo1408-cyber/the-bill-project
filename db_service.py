import sqlite3
import json
from pathlib import Path

DB_FILE = Path(__file__).parent / "pos_database.db"

def get_connection():
    """Returns a sqlite3 connection with Row factory enabled."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys support
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes tables in the SQLite database and seeds default products if empty."""
    print(f"[*] Initializing local SQL database at: {DB_FILE}")
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Create Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        address TEXT
    );
    """)

    # 2. Create Products Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        unit TEXT NOT NULL,
        price REAL NOT NULL
    );
    """)

    # 3. Create Orders Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bill_no TEXT UNIQUE NOT NULL,
        user_id INTEGER,
        items_json TEXT NOT NULL,
        total_amount REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)
    conn.commit()

    # 4. Seed Products if empty
    cursor.execute("SELECT COUNT(*) as count FROM products")
    if cursor.fetchone()["count"] == 0:
        print("[*] Seeding default product inventory catalog...")
        default_products = [
            ("leg_chest", "Leg & Chest", "kg", 320.0),
            ("ch_boneless", "Ch. Boneless", "kg", 285.0),
            ("chicken_tikka", "Chicken Tikka", "kg", 350.0),
            ("chicken_drumsticks", "Chicken Drumsticks", "kg", 340.0),
            ("chicken_wings", "Chicken Wings", "kg", 220.0),
            ("whole_chicken", "Whole Chicken", "pc", 250.0)
        ]
        cursor.executemany(
            "INSERT INTO products (id, name, unit, price) VALUES (?, ?, ?, ?)",
            default_products
        )
        conn.commit()

    conn.close()
    print("[OK] Local SQL database initialization completed.")

def get_inventory():
    """Fetch all products from database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    inventory = [dict(row) for row in rows]
    conn.close()
    return inventory

def find_user_by_phone(phone):
    """Find user profile by phone number."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE phone = ?", (phone,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_or_update_user(name, phone, address):
    """Create or update user details."""
    conn = get_connection()
    cursor = conn.cursor()
    
    existing = find_user_by_phone(phone)
    if existing:
        # Check if updates needed
        if existing["name"] != name or existing["address"] != address:
            cursor.execute(
                "UPDATE users SET name = ?, address = ? WHERE phone = ?",
                (name, address, phone)
            )
            conn.commit()
        user_id = existing["id"]
    else:
        cursor.execute(
            "INSERT INTO users (name, phone, address) VALUES (?, ?, ?)",
            (name, phone, address)
        )
        conn.commit()
        user_id = cursor.lastrowid
        
    conn.close()
    return user_id

def save_order(bill_no, customer_phone, items_list, total_amount):
    """Save order and link it to the user. Serializes items_list to JSON."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Fetch user ID
    user = find_user_by_phone(customer_phone)
    user_id = user["id"] if user else None
    
    # 2. Serialize items to JSON
    items_json = json.dumps(items_list)
    
    try:
        cursor.execute(
            "INSERT INTO orders (bill_no, user_id, items_json, total_amount) VALUES (?, ?, ?, ?)",
            (bill_no, user_id, items_json, total_amount)
        )
        conn.commit()
        success = True
    except sqlite3.IntegrityError as e:
        print(f"[!] SQLite Save Order IntegrityError: {e}")
        success = False
    finally:
        conn.close()
        
    return success

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
            # Veg Starters
            ("haryali_kebab", "Haryali Kebab", "pc", 230.0),
            ("dahi_kebab", "Dahi Kebab", "pc", 260.0),
            ("spring_roll", "Spring Roll", "pc", 230.0),
            ("cheese_cigar", "Cheese Cigar", "pc", 300.0),
            ("crispy_corn", "Crispy Corn", "pc", 260.0),
            ("chilli_paneer", "Chilli Paneer", "pc", 340.0),
            ("peanut_masala", "Peanut Masala", "pc", 220.0),
            ("chilli_potato", "Chilli Potato", "pc", 300.0),
            ("paneer_tikka", "Paneer Tikka", "pc", 380.0),

            # Non-Veg Starters
            ("tandoori_chicken_half", "Tandoori Chicken (H)", "pc", 270.0),
            ("tandoori_chicken_full", "Tandoori Chicken (F)", "pc", 500.0),
            ("tandoori_kalimirch_half", "Tandoori Kalimirch (H)", "pc", 280.0),
            ("tandoori_kalimirch_full", "Tandoori Kalimirch (F)", "pc", 520.0),
            ("chicken_tikka", "Chicken Tikka", "pc", 330.0),
            ("malai_tikka", "Malai Tikka", "pc", 370.0),
            ("chilli_chicken", "Chilli Chicken", "pc", 380.0),
            ("chicken_seekh", "Chicken Seekh", "pc", 300.0),
            ("fish_fry", "Fish Fry", "pc", 300.0),
            ("fish_finger", "Fish Finger", "pc", 330.0),
            ("tandoori_fish", "Tandoori Fish", "pc", 380.0),

            # Veg Main Course
            ("dal_makhani", "Dal Makhani", "pc", 300.0),
            ("dal_tadka", "Dal Tadka", "pc", 280.0),
            ("handi_paneer", "Handi Paneer", "pc", 360.0),
            ("kadai_paneer", "Kadai Paneer", "pc", 360.0),
            ("paneer_masala", "Paneer Masala", "pc", 360.0),
            ("matar_paneer", "Matar Paneer", "pc", 300.0),
            ("mushroom_paneer", "Mushroom Paneer", "pc", 370.0),

            # Non-Veg Main Course
            ("butter_chicken_half", "Butter Chicken (H)", "pc", 450.0),
            ("butter_chicken_full", "Butter Chicken (F)", "pc", 750.0),
            ("kadai_chicken_half", "Kadai Chicken (H)", "pc", 450.0),
            ("kadai_chicken_full", "Kadai Chicken (F)", "pc", 750.0),
            ("handi_chicken_half", "Handi Chicken (H)", "pc", 450.0),
            ("handi_chicken_full", "Handi Chicken (F)", "pc", 750.0),
            ("chicken_masala_half", "Chicken Masala (H)", "pc", 450.0),
            ("chicken_masala_full", "Chicken Masala (F)", "pc", 750.0),
            ("chicken_do_pyaza_half", "Chicken Do Pyaza (H)", "pc", 450.0),
            ("chicken_do_pyaza_full", "Chicken Do Pyaza (F)", "pc", 750.0),
            ("chicken_patiyala_half", "Chicken Patiyala (H)", "pc", 450.0),
            ("chicken_patiyala_full", "Chicken Patiyala (F)", "pc", 750.0),
            ("fish_curry", "Fish Curry", "pc", 450.0),
            ("egg_curry", "Egg Curry", "pc", 320.0),

            # Rice / Biryani
            ("chicken_biryani", "Chicken Biryani", "pc", 260.0),
            ("chicken_tikka_rice", "Chicken Tikka Rice", "pc", 320.0),

            # Breads
            ("naan", "Naan", "pc", 50.0),
            ("butter_naan", "Butter Naan", "pc", 50.0),
            ("tawa_roti", "Tawa Roti", "pc", 15.0),

            # Beverages
            ("mineral_water", "Mineral Water", "pc", 20.0)
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

def add_product(product_id, name, unit, price):
    """Add a new product to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO products (id, name, unit, price) VALUES (?, ?, ?, ?)",
            (product_id, name, unit, price)
        )
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    finally:
        conn.close()
    return success

def update_product(product_id, name, unit, price):
    """Update an existing product's details in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE products SET name = ?, unit = ?, price = ? WHERE id = ?",
            (name, unit, price, product_id)
        )
        conn.commit()
        success = cursor.rowcount > 0
    except sqlite3.Error:
        success = False
    finally:
        conn.close()
    return success

def delete_product(product_id):
    """Delete a product from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        success = cursor.rowcount > 0
    except sqlite3.Error:
        success = False
    finally:
        conn.close()
    return success

def get_users():
    """Fetch all users from database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY name ASC")
    rows = cursor.fetchall()
    users = [dict(row) for row in rows]
    conn.close()
    return users

def update_user(user_id, name, phone, address):
    """Update an existing user's details."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET name = ?, phone = ?, address = ? WHERE id = ?",
            (name, phone, address, user_id)
        )
        conn.commit()
        success = cursor.rowcount > 0
    except sqlite3.IntegrityError:
        success = False  # Phone number already exists
    except sqlite3.Error:
        success = False
    finally:
        conn.close()
    return success

def delete_user(user_id):
    """Delete a user from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        success = cursor.rowcount > 0
    except sqlite3.Error:
        success = False
    finally:
        conn.close()
    return success

def search_users(query):
    """Search users by name or phone containing query."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE name LIKE ? OR phone LIKE ? LIMIT 10",
        (f"%{query}%", f"%{query}%")
    )
    rows = cursor.fetchall()
    users = [dict(row) for row in rows]
    conn.close()
    return users


"""
DELHI DARBAR - Raw Chicken Shop
Bill Printing Script
=====================
Prints a professional formatted bill on the MPT-II Bluetooth thermal printer.
"""

from escpos.printer import Serial
from datetime import datetime

# ─────────────────────────────────────────────────────────────────
# PRINTER CONFIG
# ─────────────────────────────────────────────────────────────────
COM_PORT = "COM4"
BAUDRATE = 9600
PROFILE  = "default"
WIDTH    = 32  # 58mm printer = 32 chars per line

# ─────────────────────────────────────────────────────────────────
# BILL DATA  (edit these for each customer)
# ─────────────────────────────────────────────────────────────────
CUSTOMER = {
    "name"    : "Rahul Kumar",
    "phone"   : "9876543210",
    "address" : "123, Main Street, Karol Bagh, New Delhi - 110001",
}

ITEMS = [
    {"name": "Leg & Chest",   "qty": "1 kg",    "price": 320.00},
    {"name": "Ch. Boneless",  "qty": "0.75 kg",  "price": 285.00},
]

# ─────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────

def SEP():
    """Thin separator line."""
    return "-" * WIDTH

def THICK():
    """Thick separator line."""
    return "=" * WIDTH

def two_col(left, right, w=WIDTH):
    """Left-align text, right-align value on same line."""
    gap = w - len(left) - len(right)
    if gap < 1:
        gap = 1
    return left + " " * gap + right

def wrap_address(address, w=WIDTH - 10):
    """Wrap long address to multiple lines with indent."""
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

def item_row(name, qty, price):
    """Format one item row: Name  Qty  Price right-aligned."""
    name_col  = f"{name:<13}"          # 13 chars
    qty_col   = f"{qty:<9}"            # 9 chars
    price_col = f"Rs.{price:>6.0f}"   # 10 chars  → total 32
    return name_col + qty_col + price_col

def header_row():
    """Column headers matching item_row layout."""
    return f"{'ITEM':<13}{'QTY':<9}{'AMOUNT':>10}"

# ─────────────────────────────────────────────────────────────────
# BILL BUILDER
# ─────────────────────────────────────────────────────────────────

def print_bill():
    p = Serial(
        devfile=COM_PORT,
        baudrate=BAUDRATE,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=1,
        dsrdtr=True,
        profile=PROFILE,
    )

    # ── HEADER ─────────────────────────────────────────────────
    p.set(align="center", bold=True, width=2, height=2)
    p.textln("DELHI DARBAR")

    p.set(align="center", bold=False, normal_textsize=True)
    p.textln("Raw Chicken Shop")
    p.textln("Ph: 1800-XXX-XXXX")

    p.set(align="left", normal_textsize=True)
    p.textln(THICK())

    # ── DATE & BILL NO ─────────────────────────────────────────
    now     = datetime.now()
    date_str = now.strftime("%d/%m/%Y")
    time_str = now.strftime("%I:%M %p")

    p.textln(two_col(f"Date: {date_str}", f"Time: {time_str}"))
    p.textln(two_col("Bill No: #001", f""))

    p.textln(SEP())

    # ── CUSTOMER DETAILS ───────────────────────────────────────
    p.ln(1)
    p.textln(f"Customer : {CUSTOMER['name']}")
    p.ln(1)
    p.textln(f"Phone    : {CUSTOMER['phone']}")
    p.ln(1)

    # Wrap long address
    addr_lines = wrap_address(CUSTOMER["address"])
    p.textln(f"Address  : {addr_lines[0]}")
    for extra_line in addr_lines[1:]:
        p.textln(f"           {extra_line}")

    p.ln(1)
    p.textln(SEP())

    # ── ITEMS TABLE ────────────────────────────────────────────
    p.set(bold=True)
    p.textln(header_row())
    p.set(bold=False)
    p.textln(SEP())

    total = 0
    for item in ITEMS:
        p.textln(item_row(item["name"], item["qty"], item["price"]))
        total += item["price"]

    # ── TOTAL ──────────────────────────────────────────────────
    p.textln(SEP())
    p.set(bold=True)
    p.textln(two_col("TOTAL AMOUNT", f"Rs. {total:.0f}"))
    p.set(bold=False)
    p.textln(THICK())

    # ── FOOTER ─────────────────────────────────────────────────
    p.ln(1)
    p.set(align="center")
    p.textln("Thank you for Ordering")
    p.set(align="center", bold=True)
    p.textln("from Delhi Darbar!")
    p.set(bold=False, align="center")
    p.ln(3)

    p.cut()
    p.close()
    print("[OK] Bill printed successfully!")


# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Printing Delhi Darbar bill...")
    print_bill()

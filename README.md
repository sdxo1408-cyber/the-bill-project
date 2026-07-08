# 🐔 Delhi Darbar — Bill Printing System

A Python-based thermal receipt printer system for **Delhi Darbar Raw Chicken Shop**, built using [`python-escpos`](https://python-escpos.readthedocs.io/).

Prints professional bills to a **Bluetooth thermal printer (MPT-II)** connected via Windows.

---

## 📋 Features

- Branded bill header (shop name, type, phone)
- Customer details (name, phone, address)
- Itemized order table with quantity and price
- Auto-calculated total
- Professional separators and layout
- Prints via Bluetooth on Windows (COM4 @ 9600 baud)

---

## 🖨️ Printer Setup

- **Printer**: MPT-II Bluetooth Thermal Printer (58mm)
- **Connection**: Bluetooth → Windows virtual COM port
- **Port**: `COM4` | **Baudrate**: `9600`

### Pairing the Printer on Windows
1. Turn on the printer
2. Go to **Settings → Bluetooth & devices** → Pair `MPT-II`
3. Windows will assign **COM3** (incoming) and **COM4** (outgoing)
4. Use **COM4** for printing

---

## 🚀 Getting Started

### Install dependencies
```bash
pip install python-escpos[serial]
```

### Print a bill
Edit customer and item details in `main.py`, then:
```bash
python main.py
```

---

## 📁 Files

| File | Description |
|---|---|
| `main.py` | Main billing script — edit this for each order |
| `print_hello.py` | Basic test print script |
| `discover_printers.py` | Scans for printers (COM ports + network) |
| `raw_test.py` | Raw byte test — finds working COM port & baudrate |

---

## 🧾 Bill Format

```
================================
      DELHI DARBAR
    Raw Chicken Shop
================================
Date: 08/07/2026    Time: 12:50 PM
Bill No: #001
--------------------------------

Customer : Rahul Kumar

Phone    : 9876543210

Address  : 123, Main Street,
           New Delhi - 110001

--------------------------------
ITEM         QTY      AMOUNT
--------------------------------
Leg & Chest  1 kg     Rs. 320
Ch. Boneless 0.75 kg  Rs. 285
--------------------------------
TOTAL AMOUNT          Rs. 605
================================

   Thank you for Ordering
      from Delhi Darbar!
```

---

## ⚙️ Configuration (`main.py`)

```python
CUSTOMER = {
    "name"    : "Customer Name",
    "phone"   : "9876543210",
    "address" : "Full address here",
}

ITEMS = [
    {"name": "Leg & Chest",  "qty": "1 kg",   "price": 320.00},
    {"name": "Ch. Boneless", "qty": "0.75 kg", "price": 285.00},
    # Add more items...
]
```

---

## 📦 Dependencies

- [`python-escpos`](https://pypi.org/project/python-escpos/) — ESC/POS printer control
- [`pyserial`](https://pypi.org/project/pyserial/) — Serial port communication

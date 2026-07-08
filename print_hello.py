"""
Bluetooth Thermal Printer - Hello World
=======================================
Prints "Hello World" to a Bluetooth thermal printer connected to Windows.

Supports two methods:
  1. Serial (via virtual COM port assigned by Windows after BT pairing) -- recommended
  2. Raw Bluetooth socket (using the printer's MAC address)             -- fallback

Requirements:
    pip install python-escpos[serial]

HOW TO FIND YOUR COM PORT:
    Option A: Device Manager
        - Open Device Manager (Win+X -> Device Manager)
        - Expand "Ports (COM & LPT)"
        - Look for your printer (e.g., "Standard Serial over Bluetooth link (COM7)")

    Option B: PowerShell
        Run this to list all COM ports:
            Get-WmiObject Win32_SerialPort | Select-Object Name, DeviceID

    Option C: This script auto-detects it -- just run it!
"""

import sys
import serial.tools.list_ports


# ─────────────────────────────────────────────────────────────────
# CONFIGURATION -- Edit these if auto-detection fails
# ─────────────────────────────────────────────────────────────────

# COM4 confirmed working by raw_test.py (MPT-II Bluetooth printer)
# COM3 = write-timeout, COM4 = SUCCESS @ 9600 baud
MANUAL_COM_PORT = "COM4"

# Common baudrates for thermal printers: 9600, 19200, 38400, 115200
BAUDRATE = 9600   # MPT-II default baudrate

# Your printer's Bluetooth MAC address (only needed for socket method)
# Format: "AA:BB:CC:DD:EE:FF"
PRINTER_MAC = None   # e.g. "98:DA:60:00:11:22"

# Printer profile (optional but recommended)
# Common: "TM-T88III", "TM-T20", "POS-5890", "default"
PROFILE = "default"   # MPT-II -- use "default" since no named profile exists

# ─────────────────────────────────────────────────────────────────


def find_bluetooth_com_ports():
    """Scan all COM ports and return ones that look like Bluetooth."""
    bluetooth_ports = []
    all_ports = serial.tools.list_ports.comports()

    print("\n[*] Scanning COM ports...")
    for port in all_ports:
        desc = (port.description or "").lower()
        print(f"    Found: {port.device:10} -- {port.description}")
        if "bluetooth" in desc or "rfcomm" in desc or "serial" in desc:
            bluetooth_ports.append(port.device)

    return bluetooth_ports, all_ports


def print_via_serial(com_port):
    """
    Method 1: Print using python-escpos Serial class.
    Works when Windows has assigned a virtual COM port to the Bluetooth printer.
    """
    try:
        from escpos.printer import Serial

        print(f"\n[>] Trying Serial connection on {com_port} @ {BAUDRATE} baud...")

        p = Serial(
            devfile=com_port,
            baudrate=BAUDRATE,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=1,
            dsrdtr=True,
            profile=PROFILE,
        )

        # ── Print content ──────────────────────────────────────
        p.set(align="center", bold=True, width=2, height=4)
        p.textln("hey sd.xo!")

        p.ln(3)   # Feed 3 lines before cut
        p.cut()
        # ───────────────────────────────────────────────────────

        p.close()
        print(f"[OK] Print successful via Serial on {com_port}!")
        return True

    except ImportError:
        print("[!] python-escpos not installed. Run: pip install python-escpos[serial]")
        return False
    except Exception as e:
        print(f"[!] Serial connection failed on {com_port}: {e}")
        return False


def print_via_bluetooth_socket(mac_address):
    """
    Method 2: Print using raw Bluetooth RFCOMM socket.
    Works without a COM port -- uses the printer's MAC address directly.
    Requires Python 3.9+ on Windows (AF_BLUETOOTH is built-in).
    """
    import socket

    try:
        from escpos.printer import Dummy

        print(f"\n[>] Trying Bluetooth socket to {mac_address}...")

        # Build the ESC/POS bytes using Dummy (in-memory, no printer needed)
        d = Dummy(profile=PROFILE)

        d.set(align="center", bold=True, width=2, height=2)
        d.textln("Hello World!")

        d.set(align="center", bold=False, normal_textsize=True)
        d.textln("Printed via python-escpos")
        d.textln("Bluetooth Socket on Windows")

        d.ln(2)
        d.cut()

        # Connect over RFCOMM (Bluetooth SPP channel 1)
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        sock.settimeout(10)
        sock.connect((mac_address, 1))
        sock.sendall(d.output)
        sock.close()

        print(f"[OK] Print successful via Bluetooth socket to {mac_address}!")
        return True

    except AttributeError:
        print("[!] AF_BLUETOOTH not available. Requires Python 3.9+ on Windows.")
        return False
    except OSError as e:
        print(f"[!] Bluetooth socket failed: {e}")
        print("    Make sure the printer is ON and paired in Windows Bluetooth settings.")
        return False
    except Exception as e:
        print(f"[!] Unexpected error: {e}")
        return False


def main():
    print("=" * 55)
    print("   Bluetooth Thermal Printer -- Hello World")
    print("=" * 55)

    # ── Step 1: Find or use the configured COM port ────────────
    com_port = MANUAL_COM_PORT

    if com_port is None:
        bt_ports, all_ports = find_bluetooth_com_ports()

        if bt_ports:
            com_port = bt_ports[0]
            print(f"\n[OK] Auto-detected Bluetooth COM port: {com_port}")
            if len(bt_ports) > 1:
                print(f"     Other Bluetooth ports found: {bt_ports[1:]}")
                print("     If print fails, try setting MANUAL_COM_PORT at the top of this file.")
        elif all_ports:
            # Fallback: try the last COM port found (often the BT one)
            com_port = all_ports[-1].device
            print(f"\n[!] No obvious Bluetooth COM port found. Trying last port: {com_port}")
            print("    Tip: Set MANUAL_COM_PORT at the top of this file if this is wrong.")
        else:
            print("\n[!] No COM ports found at all!")
            com_port = None

    # ── Step 2: Try Serial method ──────────────────────────────
    if com_port:
        success = print_via_serial(com_port)
        if success:
            return

    # ── Step 3: Try raw Bluetooth socket method ────────────────
    if PRINTER_MAC:
        success = print_via_bluetooth_socket(PRINTER_MAC)
        if success:
            return

    # ── Step 4: Nothing worked -- show help ────────────────────
    print("\n" + "=" * 55)
    print("  Could not print. Try the following:")
    print("=" * 55)
    print("""
  1. Make sure printer is ON and paired in Windows:
     Settings -> Bluetooth & devices -> find your printer

  2. Find your COM port:
     - Open Device Manager (Win+X -> Device Manager)
     - Expand "Ports (COM & LPT)"
     - Look for "Standard Serial over Bluetooth link"
     - Note the COM number (e.g., COM7)

  3. Set MANUAL_COM_PORT at the top of this file:
     MANUAL_COM_PORT = "COM7"   <- replace with your port

  4. If that still fails, find your printer's MAC address:
     - Settings -> Bluetooth & devices -> your printer -> More info
     - Set PRINTER_MAC at the top of this file:
       PRINTER_MAC = "AA:BB:CC:DD:EE:FF"

  5. Check baudrate -- common values: 9600, 115200
     Change BAUDRATE at the top of this file.
""")


if __name__ == "__main__":
    main()

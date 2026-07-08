"""
Printer Discovery Tool
======================
Scans for printers on:
  1. COM ports (Bluetooth/Serial)
  2. Local network (TCP port 9100 - standard ESC/POS)
  3. Paired Bluetooth devices (Windows WMI)

Run this first to find your printer, then update print_hello.py with the result.
"""

import socket
import concurrent.futures
import subprocess
import sys

import serial.tools.list_ports


# ─────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────

# Your local network subnet to scan (change if your router uses a different range)
# Common: 192.168.1, 192.168.0, 10.0.0
SUBNET = "192.168.1"

# TCP port used by ESC/POS network printers (almost always 9100)
PRINTER_PORT = 9100

# How many threads to use for network scan (higher = faster)
THREADS = 50

# Connection timeout per host (seconds)
TIMEOUT = 0.5

# ─────────────────────────────────────────────────────────────────


def section(title):
    print(f"\n{'=' * 55}")
    print(f"  {title}")
    print(f"{'=' * 55}")


# ────────────────────────────────────────────────────────────────
# 1. COM PORT SCAN (Bluetooth / Serial)
# ────────────────────────────────────────────────────────────────

def scan_com_ports():
    section("1. COM Port Scan (Bluetooth / Serial)")

    ports = list(serial.tools.list_ports.comports())

    if not ports:
        print("  No COM ports found.")
        return []

    found = []
    for p in ports:
        tag = ""
        desc_lower = (p.description or "").lower()
        if "bluetooth" in desc_lower:
            tag = "  <-- BLUETOOTH (likely your printer)"
        elif "serial" in desc_lower:
            tag = "  <-- Serial device"
        elif "usb" in desc_lower:
            tag = "  <-- USB Serial"

        print(f"  {p.device:10}  {p.description}{tag}")
        found.append((p.device, p.description))

    return found


# ────────────────────────────────────────────────────────────────
# 2. NETWORK SCAN (TCP port 9100)
# ────────────────────────────────────────────────────────────────

def check_host(ip):
    """Return IP if port 9100 is open (likely a network printer)."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        result = sock.connect_ex((ip, PRINTER_PORT))
        sock.close()
        if result == 0:
            return ip
    except Exception:
        pass
    return None


def get_local_ip():
    """Get this machine's local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def scan_network():
    section("2. Network Scan (TCP port 9100)")

    local_ip = get_local_ip()
    if local_ip:
        # Auto-detect subnet from local IP
        detected_subnet = ".".join(local_ip.split(".")[:3])
        print(f"  Your local IP  : {local_ip}")
        print(f"  Scanning subnet: {detected_subnet}.1 - {detected_subnet}.254")
        subnet = detected_subnet
    else:
        print(f"  Could not detect local IP. Using configured subnet: {SUBNET}")
        subnet = SUBNET

    hosts = [f"{subnet}.{i}" for i in range(1, 255)]

    print(f"  Scanning {len(hosts)} hosts on port {PRINTER_PORT}...")
    print("  (This may take a few seconds...)\n")

    found_printers = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
        results = executor.map(check_host, hosts)

    for ip in results:
        if ip:
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except Exception:
                hostname = "unknown"
            print(f"  [FOUND] {ip:16} -- hostname: {hostname}")
            found_printers.append(ip)

    if not found_printers:
        print("  No network printers found on port 9100.")
        print("  Make sure the printer is connected to the same Wi-Fi/network.")

    return found_printers


# ────────────────────────────────────────────────────────────────
# 3. BLUETOOTH DEVICE SCAN (Windows WMI)
# ────────────────────────────────────────────────────────────────

def scan_bluetooth_devices():
    section("3. Paired Bluetooth Devices (Windows)")

    try:
        # Use PowerShell to list paired Bluetooth devices
        cmd = [
            "powershell", "-Command",
            "Get-PnpDevice -Class Bluetooth | "
            "Where-Object { $_.Status -eq 'OK' } | "
            "Select-Object FriendlyName, DeviceID, Status | "
            "Format-Table -AutoSize"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode == 0 and result.stdout.strip():
            print(result.stdout)
        else:
            print("  No Bluetooth devices found via WMI, trying alternate method...")

        # Also check via Get-BluetoothRadio
        cmd2 = [
            "powershell", "-Command",
            "[Windows.Devices.Bluetooth.BluetoothDevice,Windows.Devices.Bluetooth,ContentType=WindowsRuntime] | Out-Null;"
            "Write-Host 'Bluetooth stack available'"
        ]
        result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=10)
        if "available" in result2.stdout.lower():
            print("  Windows Bluetooth stack: Available")

    except subprocess.TimeoutExpired:
        print("  WMI query timed out.")
    except Exception as e:
        print(f"  Could not query Bluetooth devices: {e}")

    # List COM ports that are Bluetooth
    print("\n  Bluetooth COM ports (from serial scan):")
    ports = list(serial.tools.list_ports.comports())
    bt_ports = [p for p in ports if "bluetooth" in (p.description or "").lower()]
    if bt_ports:
        for p in bt_ports:
            print(f"    {p.device} -- {p.description}")
    else:
        print("    None found.")


# ────────────────────────────────────────────────────────────────
# SUMMARY
# ────────────────────────────────────────────────────────────────

def print_summary(com_ports, net_printers):
    section("SUMMARY & NEXT STEPS")

    if not com_ports and not net_printers:
        print("""
  No printers found automatically. Try:

  1. Make sure the printer is POWERED ON
  2. For Bluetooth: Confirm it is paired in Windows
     Settings -> Bluetooth & devices
  3. For Network: Confirm printer is on the same Wi-Fi
  4. Try changing SUBNET in this script if your router
     uses a different IP range (e.g., 192.168.0 or 10.0.0)
""")
        return

    print("\n  To print via BLUETOOTH (Serial COM port):")
    for port, desc in com_ports:
        if "bluetooth" in desc.lower():
            print(f"    Set in print_hello.py:  MANUAL_COM_PORT = \"{port}\"")

    if net_printers:
        print("\n  To print via NETWORK (TCP/IP):")
        for ip in net_printers:
            print(f"    Use Network printer:    Network(host=\"{ip}\")")
            print(f"    Or in print_hello.py use Network class instead of Serial.")

    print("""
  After finding your printer, open print_hello.py and
  set MANUAL_COM_PORT (for Bluetooth) or use Network class.
  Then run:  python print_hello.py
""")


def main():
    print("=" * 55)
    print("   Printer Discovery Tool")
    print("=" * 55)

    com_ports = scan_com_ports()
    net_printers = scan_network()
    scan_bluetooth_devices()
    print_summary(com_ports, net_printers)


if __name__ == "__main__":
    main()

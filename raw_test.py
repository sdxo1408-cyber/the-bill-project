"""
Raw Bluetooth Printer Test
===========================
Bypasses python-escpos completely.
Sends raw bytes directly to COM3/COM4 to test the connection.
Tries every baudrate and both COM ports.
"""

import serial
import time

# All common thermal printer baudrates
BAUDRATES = [9600, 19200, 38400, 57600, 115200]
PORTS = ["COM3", "COM4"]

# Raw ESC/POS bytes:
# ESC @ = Initialize printer
# Text bytes
# 0x0A = Line Feed (newline)
# GS V 0x42 0x00 = Full cut
RAW_INIT    = b'\x1b\x40'                    # ESC @ - initialize
RAW_TEXT    = b'Hello World!\n'              # plain text
RAW_NEWLINE = b'\n\n\n'                      # feed lines
RAW_CUT     = b'\x1d\x56\x42\x00'           # GS V B - full cut


def try_port(port, baudrate, timeout=3):
    """Try to open port, send raw bytes, and report result."""
    print(f"\n  Trying {port} @ {baudrate} baud...", end="", flush=True)
    try:
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout,
            write_timeout=timeout,
            dsrdtr=False,
            rtscts=False,
            xonxoff=False,
        )

        if not ser.isOpen():
            ser.open()

        time.sleep(0.5)  # let the port settle

        # Send data
        ser.write(RAW_INIT)
        time.sleep(0.1)
        ser.write(RAW_TEXT)
        time.sleep(0.1)
        ser.write(RAW_NEWLINE)
        time.sleep(0.1)
        ser.write(RAW_CUT)
        ser.flush()

        time.sleep(1)
        ser.close()
        print(f"  SUCCESS - bytes sent to {port} @ {baudrate}")
        return True

    except serial.SerialTimeoutException:
        print(f"  TIMEOUT - port opened but write timed out (printer may be off?)")
        return False
    except serial.SerialException as e:
        err = str(e)
        if "PermissionError" in err or "Access is denied" in err:
            print(f"  BUSY - port is in use by another program")
        elif "FileNotFoundError" in err or "could not open port" in err.lower():
            print(f"  NOT FOUND - port does not exist")
        else:
            print(f"  ERROR - {e}")
        return False
    except Exception as e:
        print(f"  ERROR - {e}")
        return False


def main():
    print("=" * 55)
    print("  Raw Bluetooth Printer Test")
    print("=" * 55)
    print()
    print("Sending raw ESC/POS bytes to all COM ports + baudrates.")
    print("Watch your printer -- it should print 'Hello World!'")
    print()

    results = []
    for port in PORTS:
        for baud in BAUDRATES:
            ok = try_port(port, baud)
            if ok:
                results.append((port, baud))
                # If it worked, no need to try other baudrates on this port
                print(f"\n  [FOUND] Printer responds on {port} @ {baud} baud!")
                break  # next port

    print("\n" + "=" * 55)
    print("  RESULTS")
    print("=" * 55)

    if results:
        print(f"\n  Successful connections:")
        for port, baud in results:
            print(f"    Port: {port}  Baudrate: {baud}")
        print()
        print("  Update print_hello.py with these values:")
        port, baud = results[0]
        print(f"    MANUAL_COM_PORT = \"{port}\"")
        print(f"    BAUDRATE = {baud}")
    else:
        print("""
  No successful connection found.

  Possible reasons:
    1. Printer is OFF -- turn it on and try again
    2. Printer is not paired -- go to Windows Bluetooth settings
       and pair the MPT-II printer again
    3. COM port changed -- run discover_printers.py to re-scan
    4. The printer may use a different protocol (not ESC/POS)
       -- check if the printer prints a self-test page by
          holding the feed button while powering on

  Also try:
    - Disconnect and reconnect the Bluetooth pairing in Windows
      Settings -> Bluetooth & devices -> Remove -> Re-pair
""")


if __name__ == "__main__":
    main()

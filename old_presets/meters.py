import serial
import threading
import time

REAL_PORT = 'COM3'      # FT-991A physical port
PROXY_PORT = 'COM13'    # Win4Yaesu connects here
BAUD = 38400            # Match FT-991A Menu 031

def forward(src, dst, direction, log_full_command=True):
    buffer = ""
    while True:
        try:
            byte = src.read()
            if not byte:
                continue
            dst.write(byte)
            time.sleep(0.002)  # smooth out bursts
            char = byte.decode(errors="ignore")
            if log_full_command:
                buffer += char
                if char == ";":
                    print(f"[{direction}] >> {buffer.strip()}")
                    buffer = ""
        except serial.SerialException as e:
            print(f"[{direction} SERIAL ERROR] {e}")
            break
        except Exception as e:
            print(f"[{direction} ERROR] {e}")
            break

def main():
    try:
        real_serial = serial.Serial(REAL_PORT, BAUD, timeout=0.2)
        proxy_serial = serial.Serial(PROXY_PORT, BAUD, timeout=0.2)
    except serial.SerialException as e:
        print(f"❌ Could not open ports: {e}")
        return

    print(f"🔁 Bridging COM13 → FT-991A COM3 at {BAUD} baud...\n")

    threading.Thread(target=forward, args=(proxy_serial, real_serial, "PC → Radio"), daemon=True).start()
    threading.Thread(target=forward, args=(real_serial, proxy_serial, "Radio → PC"), daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        real_serial.close()
        proxy_serial.close()
        print("💤 Closed.")

if __name__ == "__main__":
    main()

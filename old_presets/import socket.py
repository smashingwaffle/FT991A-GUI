import socket

RADIO_IP = "192.168.10.10"  # SDS200 IP
PORT     = 50536            # virtual serial UDP port

def send_glt_fl():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2.0)
    try:
        sock.sendto(b"GLT,FL\r", (RADIO_IP, PORT))
        data, addr = sock.recvfrom(65535)

        print("From:", addr)
        print("RAW BYTES LEN:", len(data))
        print("RAW BYTES REPR:", repr(data))
        print("\nDecoded text:\n")
        text = data.decode("latin-1", errors="ignore")
        print(text)

        # Try to isolate the XML portion if it exists
        start = text.find("<")
        if start != -1:
            xml_candidate = text[start:]
            print("\n--- XML CANDIDATE ---")
            print(xml_candidate)
        else:
            print("\n(No '<' found in response – looks non-XML)")

    except socket.timeout:
        print("Timeout waiting for GLT,FL over UDP.")
    finally:
        sock.close()


if __name__ == "__main__":
    send_glt_fl()

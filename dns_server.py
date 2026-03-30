import socket
import threading
import time

DNS_RECORDS = {
    "example.local": "192.168.1.10",
    "test.local": "10.0.0.5"
}

CACHE = {}
CACHE_TTL = 60

UPSTREAM_DNS = ("8.8.8.8", 53)
PORT = 53

request_count = 0
start_server_time = time.time()

lock = threading.Lock()
cache_lock = threading.Lock()


# ================= HELPERS =================
def get_domain_name(data):
    domain = []
    i = 12

    try:
        length = data[i]
        while length != 0:
            i += 1
            domain.append(data[i:i+length].decode(errors="ignore"))
            i += length
            length = data[i]
    except:
        return None

    return ".".join(domain)


def get_query_type(data):
    i = 12
    while data[i] != 0:
        i += data[i] + 1
    i += 1
    return data[i:i+2]


def build_error_response(query, rcode):
    transaction_id = query[:2]
    flags = b'\x81' + bytes([0x80 | rcode])

    header = transaction_id + flags + b'\x00\x01\x00\x00\x00\x00\x00\x00'
    question = query[12:]

    return header + question


def build_response(query, ip):
    transaction_id = query[:2]
    flags = b'\x81\x80'

    header = (
        transaction_id +
        flags +
        b'\x00\x01' +
        b'\x00\x01' +
        b'\x00\x00' +
        b'\x00\x00'
    )

    question = query[12:]

    answer = (
        b'\xc0\x0c' +
        b'\x00\x01' +
        b'\x00\x01' +
        b'\x00\x00\x00\x3c' +
        b'\x00\x04' +
        socket.inet_aton(ip)
    )

    return header + question + answer


# ================= CORE =================
def process_request(data, addr, sock):
    global request_count

    start_time = time.time()

    if len(data) < 12:
        print("[ERROR] Invalid packet")
        return

    domain = get_domain_name(data)
    qtype = get_query_type(data)

    if not domain:
        print("[ERROR] Could not parse domain")
        return

    print(f"\n[CLIENT {addr}] {domain}")

    if qtype != b'\x00\x01':
        print("[ERROR] Unsupported query type")
        response = build_error_response(data, 4)  # NOTIMP
        sock.sendto(response, addr)
        return

    current_time = time.time()
    status = ""

    # ================= CACHE =================
    with cache_lock:
        if domain in CACHE:
            ip, expiry = CACHE[domain]
            if current_time < expiry:
                print("[CACHE HIT]")
                sock.sendto(build_response(data, ip), addr)
                status = "CACHE"
            else:
                del CACHE[domain]

    # ================= LOCAL =================
    if status == "" and domain in DNS_RECORDS:
        ip = DNS_RECORDS[domain]
        print("[LOCAL RESOLUTION]")

        with cache_lock:
            CACHE[domain] = (ip, current_time + CACHE_TTL)

        sock.sendto(build_response(data, ip), addr)
        status = "LOCAL"

    # ================= FORWARD =================
    if status == "":
        print("[FORWARDING]")

        upstream = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        upstream.settimeout(2)

        success = False

        for attempt in range(2):  # retry logic
            try:
                upstream.sendto(data, UPSTREAM_DNS)
                response, _ = upstream.recvfrom(512)

                sock.sendto(response, addr)
                success = True
                status = "FORWARDED"
                break

            except socket.timeout:
                print(f"[RETRY {attempt+1}] Upstream timeout")

        upstream.close()

        if not success:
            print("[SERVFAIL]")
            sock.sendto(build_error_response(data, 2), addr)
            status = "FAILED"

    # ================= NXDOMAIN =================
    if status == "":
        print("[NXDOMAIN]")
        sock.sendto(build_error_response(data, 3), addr)
        status = "NXDOMAIN"

    # ================= METRICS =================
    latency = (time.time() - start_time) * 1000

    with lock:
        request_count += 1
        elapsed = time.time() - start_server_time
        throughput = request_count / elapsed if elapsed > 0 else 0

    print(f"[STATUS] {status}")
    print(f"[LATENCY] {latency:.2f} ms")
    print(f"[THROUGHPUT] {throughput:.2f} req/sec")
    print(f"[CLIENTS] {threading.active_count() - 1}")


def handle_client(data, addr, sock):
    try:
        process_request(data, addr, sock)
    except Exception as e:
        print(f"[FATAL ERROR] {addr}: {e}")


# ================= SERVER =================
def start_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        sock.bind(("0.0.0.0", PORT))
    except Exception as e:
        print(f"[FATAL] Bind failed: {e}")
        return

    print(f"DNS Server running on port {PORT}")

    while True:
        try:
            data, addr = sock.recvfrom(512)

            threading.Thread(
                target=handle_client,
                args=(data, addr, sock)
            ).start()

        except Exception as e:
            print(f"[ERROR] Receive failed: {e}")


if __name__ == "__main__":
    start_server()
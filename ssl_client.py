
import socket
import ssl

HOST = "192.168.137.44"   # CHANGE to your server IP
PORT = 8443

context = ssl._create_unverified_context()

with socket.create_connection((HOST, PORT)) as sock:
    with context.wrap_socket(sock, server_hostname=HOST) as ssock:
        ssock.send(b"Checking secure DNS server")

        data = ssock.recv(1024)
        print("Server reply:", data.decode())

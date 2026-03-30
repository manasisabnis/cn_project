
import socket
import ssl
import threading

HOST = "0.0.0.0"
PORT = 8443

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile="server.crt", keyfile="server.key")


def handle_client(conn, addr):
    with context.wrap_socket(conn, server_side=True) as ssock:
        print("Secure client connected:", addr)

        data = ssock.recv(1024)
        print("Encrypted message:", data.decode())

        ssock.send(b"Secure DNS server connection established")


def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, PORT))
        sock.listen(5)

        print("SSL Server running on port 8443")

        while True:
            conn, addr = sock.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()


if __name__ == "__main__":
    start_server()


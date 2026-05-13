import socket

HOST = "127.0.0.1"
PORT = 49123

with socket.create_connection((HOST, PORT), timeout=5) as sock:
    print("Connected to RL Stats API")

    while True:
        data = sock.recv(4096)
        if not data:
            break

        print(data.decode("utf-8", errors="replace"))
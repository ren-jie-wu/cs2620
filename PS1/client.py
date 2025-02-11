import socket
import json

HOST = "127.0.0.1"
PORT = 54400

def send_request(action, data=None):
    """Sends a JSON request to the server and prints the response."""
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    request = {"action": action, "data": data or {}}
    client.send(json.dumps(request).encode("utf-8"))

    response = json.loads(client.recv(1024).decode("utf-8"))
    print(f"[SERVER RESPONSE] {response}")

    client.close()

if __name__ == "__main__":
    send_request("ping")
import socket
import json

HOST = "127.0.0.1"
PORT = 54400

def send_request(action, data=None):
    """Sends a request to the server and prints the response."""
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    request = {"action": action, "data": data or {}}
    client.send(json.dumps(request).encode("utf-8"))

    response = json.loads(client.recv(1024).decode("utf-8"))
    print(f"[SERVER RESPONSE] {response}")

    client.close()

if __name__ == "__main__":
    # Test account creation
    send_request("create_account", {"username": "test_user", "password": ""}) # Empty password
    send_request("create_account", {"password": "secure123"}) # Missing username
    send_request("create_account", {"username": "test_user", "password": "secure123"})
    send_request("create_account", {"username": "test_user", "password": "hello123"}) # Existing username
    
    # Test login
    send_request("login", {"username": "test_user", "password": "hello123"}) # Incorrect password
    send_request("login", {"username": "test_user", "password": "secure123"})
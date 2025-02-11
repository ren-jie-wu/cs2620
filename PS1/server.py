import socket
import threading
import json
import time  # noqa: F401
from utils import hash_password

# Server Configuration
HOST = "127.0.0.1"
PORT = 54400

#TODO: Implement a database for storing user data
users = {}  # Stores {username: password_hash}
clients = {}  # Dictionary to store connected clients

def handle_client(client_socket, address):
    """Handles communication with a single client."""
    print(f"\n[NEW CONNECTION] {address} connected.")

    try:
        while True:
            data = client_socket.recv(1024).decode("utf-8")
            if not data:
                break

            request = json.loads(data)
            print(f"[REQUEST FROM {address}] {request}")

            response = process_request(request)
            client_socket.send(json.dumps(response).encode("utf-8"))

    except (ConnectionResetError, json.JSONDecodeError):
        print(f"[DISCONNECTED] {address} disconnected.")
    finally:
        client_socket.close()

def process_request(request):
    """Processes the client's request and returns a response."""
    action = request.get("action")
    data = request.get("data", {})

    if action == "create_account":
        username, password = data.get("username"), data.get("password")
        if not username or not password:
            return {"action": "create_account", "status": "error", "error": "Missing username or password"}
        
        if username in users:
            return {"action": "create_account", "status": "error", "error": "Username already exists"}
        
        users[username] = hash_password(password)
        return {"action": "create_account", "status": "success", "message": "Account created successfully"}
    
    elif action == "login":
        username, password = data.get("username"), data.get("password")
        if username not in users:
            return {"action": "login", "status": "error", "error": "User does not exist"}
        
        if users[username] != hash_password(password):
            return {"action": "login", "status": "error", "error": "Incorrect password"}
        
        return {"action": "login", "status": "success", "message": "Login successful"}
    
    
    return {"action": action, "status": "error", "error": "Invalid request"}

def start_server():
    """Starts the server and listens for incoming connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen(5)
        print(f"[SERVER STARTED] Listening on {HOST}:{PORT}")

        while True:
            client_socket, addr = server.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            client_thread.start()

if __name__ == "__main__":
    start_server()

# TODO list: 
# Implement thread safety for managing concurrent clients (e.g., using locks)
# Implement another wire protocol other than JSON (e.g., Protocol Buffers like)
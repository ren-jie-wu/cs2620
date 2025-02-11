import socket
import threading
import json
import time

# Server Configuration
HOST = "127.0.0.1"
PORT = 54400
clients = {}  # Dictionary to store connected clients

def handle_client(client_socket, address):
    """Handles communication with a single client."""
    print(f"[NEW CONNECTION] {address} connected.")

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
    """Processes the client's request and returns a JSON response."""
    action = request.get("action")

    time.sleep(3)  # Simulate processing time

    if action == "ping":
        return {"action": "ping", "status": "success", "message": "Pong!"}
    
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
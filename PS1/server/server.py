# server.py
# Finally, we create the server class that uses the components above. 
# It listens for connections, uses the protocol to decode/encode messages, 
# and dispatches the request to the RequestHandler.

import socket
import threading
from .config import HOST, PORT, PROTOCOL, STORAGE
from ..shared.protocol import JSONProtocol, CustomizedProtocol
from .storage import MemoryStorage, DatabaseStorage
from .request_handler import RequestHandler

class ChatServer:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.protocol = JSONProtocol() if PROTOCOL == "JSON" else CustomizedProtocol()
        self.storage = MemoryStorage() if STORAGE == "memory" else DatabaseStorage()
        self.request_handler = RequestHandler(self.storage, self.protocol)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[SERVER STARTED] Listening on {self.host}:{self.port}")
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                print(f"\n[NEW CONNECTION] {addr} connected.")
                threading.Thread(target=self.handle_client, args=(client_socket, addr), daemon=True).start()
        except KeyboardInterrupt:
            print("\n[SERVER STOPPED] Exiting...")

    def handle_client(self, client_socket, addr):
        with client_socket:
            try:
                while True:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    request = self.protocol.decode(data)
                    print(f"[REQUEST FROM {addr}] {request}")
                    response = self.request_handler.process_request(request, client_socket)
                    print(f"[RESPONSE TO {addr}] {response}")
                    client_socket.send(self.protocol.encode(response))
            except Exception as e:
                print(f"[ERROR] {e} occurred with {addr}")
            finally:
                print(f"\n[DISCONNECTED] {addr} disconnected.")

if __name__ == "__main__":
    server = ChatServer()
    # Start a background thread to clean up expired sessions.
    threading.Thread(target=server.storage.cleanup_expired_sessions, daemon=True).start()
    server.start()

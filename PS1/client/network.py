# client/network.py
import socket
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from client.config import HOST, PORT, PROTOCOL, BUFFER_SIZE
from shared.protocol import JSONProtocol, CustomizedProtocol

class ChatNetwork:
    """Handles network communication between the client and server."""
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((HOST, PORT))
        self.protocol = JSONProtocol() if PROTOCOL == "JSON" else CustomizedProtocol()

    def send_request(self, action, data):
        """Send a request to the server and receive a response."""
        try:
            self.socket.send(self.protocol.encode({"action": action, "data": data}))
            response = self.protocol.decode(self.socket.recv(BUFFER_SIZE))[0]
            # Typically only one response; to be optimized for multiple responses
            return response
        except Exception as e:
            return {"action": action, "status": "error", "error": f"{str(e.__class__)}: {str(e)}"}

    def receive_message(self):
        """Wait for and return a message from the server."""
        try:
            data = self.socket.recv(BUFFER_SIZE)
            if not data:
                return None
            return self.protocol.decode(data)
        except Exception:
            return None

    def close(self):
        """Close the connection to the server."""
        self.socket.close()

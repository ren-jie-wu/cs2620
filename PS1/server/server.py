# server.py
# Finally, we create the server class that uses the components above. 
# It listens for connections, uses the protocol to decode/encode messages, 
# and dispatches the request to the RequestHandler.

import socket
import threading
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from server.config import HOST, PORT, PROTOCOL, STORAGE, BUFFER_SIZE
from shared.protocol import JSONProtocol, CustomizedProtocol
from server.storage import MemoryStorage, DatabaseStorage
from server.request_handler import RequestHandler

class ChatServer:
    def __init__(self, host=HOST, port=PORT, verbose=True):
        """
        Initialize the server with the given host and port.
        
        Parameters
        ----------
        host : str
            The host to listen on.
        port : int
            The port to listen on.
        verbose : bool
            Whether to print verbose messages.
        """
        self.host = host
        self.port = port
        self.verbose = verbose
        self.protocol = JSONProtocol() if PROTOCOL == "JSON" else CustomizedProtocol()
        self.storage = MemoryStorage() if STORAGE == "memory" else DatabaseStorage()
        self.request_handler = RequestHandler(self.storage, self.protocol)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def verbose_print(self, *args, **kwargs):
        """
        Print messages if verbose mode is enabled.
        
        Parameters
        ----------
        *args : mixed
            The arguments to be passed to the print function.
        **kwargs : mixed
            The keyword arguments to be passed to the print function.
        """
        if self.verbose:
            print(*args, **kwargs)
        else:
            pass

    def start(self):
        """
        Start the server by binding the socket to the given host and port, 
        listen for incoming connections, and spawn a new thread for each 
        connection to handle the client request.

        When a new connection is established, print a message that a new 
        connection is established.

        The server runs in an infinite loop until a KeyboardInterrupt is 
        encountered. When the server is stopped, print a message that the 
        server has stopped and exit.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.verbose_print(f"[SERVER STARTED] Listening on {self.host}:{self.port}")
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                self.verbose_print(f"\n[NEW CONNECTION] {addr} connected.")
                threading.Thread(target=self.handle_client, args=(client_socket, addr), daemon=True).start()
        except KeyboardInterrupt:
            self.verbose_print("\n[SERVER STOPPED] Exiting...")

    def handle_client(self, client_socket, addr):
        """
        Handle an incoming connection from a client.
        
        Parameters
        ----------
        client_socket : socket
            The socket object of the client connection.
        addr : tuple
            The address of the client.
        
        Returns
        -------
        None
        
        Notes
        -----
        Runs in an infinite loop until a KeyboardInterrupt is encountered.
        When an invalid request is received, an error response is sent back to
        the client. When an exception occurs during request processing, the
        exception is printed to the console and the connection is closed.
        Finally, when the connection is closed, a message is printed to the
        console to indicate that the connection has been closed.
        """
        with client_socket:
            try:
                while True:
                    data = client_socket.recv(BUFFER_SIZE)
                    if not data:
                        break
                    requests = self.protocol.decode(data)
                    if not requests:
                        response = {"status": "error", "error": "Invalid request"}
                        self.verbose_print(f"[RESPONSE TO {addr}] {response}")
                        client_socket.send(self.protocol.encode(response))
                    for request in requests:
                        self.verbose_print(f"[REQUEST FROM {addr}] {request}")
                        response = self.request_handler.process_request(request, client_socket)
                        self.verbose_print(f"[RESPONSE TO {addr}] {response}")
                        client_socket.send(self.protocol.encode(response))
            except Exception as e:
                self.verbose_print(f"[ERROR] {e} occurred with {addr}")
            finally:
                self.verbose_print(f"\n[DISCONNECTED] {addr} disconnected.")

if __name__ == "__main__":
    server = ChatServer()
    # Start a background thread to clean up expired sessions.
    threading.Thread(target=server.storage.cleanup_expired_sessions, daemon=True).start()
    server.start()

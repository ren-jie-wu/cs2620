import unittest
from unittest.mock import patch, MagicMock
import threading
import time
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from server.server import ChatServer
from shared.config import HOST, PORT

class TestChatServer(unittest.TestCase):
    """Unit tests for the ChatServer class, assuming dependencies are correct."""

    @patch("server.server.JSONProtocol")
    @patch("server.server.MemoryStorage")
    @patch("server.server.RequestHandler")
    def setUp(self, MockRequestHandler, MockStorage, MockProtocol):
        """Set up a ChatServer with mocked dependencies."""
        self.mock_protocol = MockProtocol.return_value
        self.mock_storage = MockStorage.return_value
        self.mock_handler = MockRequestHandler.return_value

        self.server = ChatServer(verbose=False)
        self.server.protocol = self.mock_protocol
        self.server.storage = self.mock_storage
        self.server.request_handler = self.mock_handler

    def test_server_initialization(self):
        """Test that the server initializes with correct components."""
        self.assertIsInstance(self.server.protocol, MagicMock)
        self.assertIsInstance(self.server.storage, MagicMock)
        self.assertIsInstance(self.server.request_handler, MagicMock)
    
    @patch("server.server.socket.socket")
    def test_server_start(self, MockSocket):
        """Test that the server starts successfully."""
        mock_client_socket = MagicMock()
        self.server.server_socket = MockSocket.return_value
        self.server.server_socket.accept.return_value = (mock_client_socket, ("127.0.0.1", 5000))

        server_thread = threading.Thread(target=self.server.start, daemon=True)
        server_thread.start()

        time.sleep(0.01)  # Give it a moment to start

        self.server.server_socket.accept.return_value = None
        self.server.server_socket.close()
        server_thread.join()
        
        self.server.server_socket.bind.assert_called_once_with((HOST, PORT))
        self.server.server_socket.listen.assert_called_once_with(5)
        self.server.server_socket.accept.assert_called()
    
    @patch("server.server.socket.socket")
    def test_server_stop(self, MockSocket):
        """Test that the server stops successfully."""
        self.server.server_socket = MockSocket.return_value
        self.server.server_socket.accept.side_effect = KeyboardInterrupt

        server_thread = threading.Thread(target=self.server.start, daemon=True)
        server_thread.start()

        time.sleep(0.1)  # Give it a moment to start

        self.server.server_socket.close()
        server_thread.join()

    @patch("server.server.socket.socket")
    def test_handle_client_successful(self, MockSocket):
        """Test handling a valid client request."""
        mock_client_socket = MockSocket.return_value
        mock_client_socket.recv.side_effect = [b'{"action": "ping"}', b""]  # One request, then disconnect

        self.mock_protocol.decode.return_value = {"action": "ping"}
        self.mock_handler.process_request.return_value = {"status": "success"}

        self.server.handle_client(mock_client_socket, ("127.0.0.1", 5000))

        self.mock_protocol.decode.assert_called_once()
        self.mock_handler.process_request.assert_called_once()
        self.mock_protocol.encode.assert_called_once()

    @patch("server.server.socket.socket")
    def test_handle_client_malformed_request(self, MockSocket):
        """Test handling a client sending invalid JSON."""
        mock_client_socket = MockSocket.return_value
        mock_client_socket.recv.side_effect = [b'INVALID_JSON', b""]  # Malformed, then disconnect

        self.mock_protocol.decode.side_effect = ValueError("Decoding Error")

        self.server.handle_client(mock_client_socket, ("127.0.0.1", 5000))

        self.mock_protocol.decode.assert_called_once()
        self.mock_handler.process_request.assert_not_called()  # Should fail before reaching request processing

    @patch("server.server.socket.socket")
    def test_handle_client_disconnect(self, MockSocket):
        """Test handling client disconnection mid-communication."""
        mock_client_socket = MockSocket.return_value
        mock_client_socket.recv.side_effect = [b'{"action": "ping"}', ConnectionResetError]  # Normal then error

        self.mock_protocol.decode.return_value = {"action": "ping"}
        self.mock_handler.process_request.return_value = {"status": "success"}

        self.server.handle_client(mock_client_socket, ("127.0.0.1", 5000))

        self.mock_protocol.decode.assert_called_once()
        self.mock_handler.process_request.assert_called_once()

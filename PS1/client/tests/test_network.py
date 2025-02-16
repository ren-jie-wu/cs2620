import unittest
from unittest.mock import patch
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from client.network import ChatNetwork
from shared.protocol import JSONProtocol, CustomizedProtocol
from shared.config import PROTOCOL

class TestChatNetwork(unittest.TestCase):
    @patch("client.network.socket.socket")  # Mock the socket class
    def setUp(self, mock_socket):
        """Set up a mock socket connection for ChatNetwork."""
        self.mock_socket = mock_socket.return_value
        self.network = ChatNetwork()
        self.protocol = JSONProtocol() if PROTOCOL == "JSON" else CustomizedProtocol()

    def test_send_request_success(self):
        """Test sending a valid request and receiving a successful response."""
        self.mock_socket.recv.return_value = self.protocol.encode({"action": "login", "status": "success"})
        response = self.network.send_request("login", {"username": "alice", "password": "1234"})
        self.assertEqual(response["status"], "success")

    def test_send_request_failure(self):
        """Test sending a request when the server is unreachable."""
        self.mock_socket.send.side_effect = Exception("Socket error")
        response = self.network.send_request("login", {"username": "alice", "password": "1234"})
        self.assertEqual(response["status"], "error")
        self.assertIn("Socket error", response["error"])

    def test_receive_message(self):
        """Test receiving a message from the server."""
        self.mock_socket.recv.return_value = self.protocol.encode({"action": "receive_message", "data": {"sender": "bob", "message": "Hi Alice"}})
        message = self.network.receive_message()[0]
        self.assertEqual(message["data"]["sender"], "bob")
        self.assertEqual(message["data"]["message"], "Hi Alice")

    def test_receive_message_empty(self):
        """Test receiving an empty message (connection closed)."""
        self.mock_socket.recv.return_value = b""
        message = self.network.receive_message()
        self.assertIsNone(message)
    
    def test_receive_message_failure(self):
        """Test receiving a message when the server is unreachable."""
        self.mock_socket.recv.side_effect = Exception("Socket error")
        message = self.network.receive_message()
        self.assertIsNone(message)

    def test_close_connection(self):
        """Test closing the network connection."""
        self.network.close()
        self.mock_socket.close.assert_called_once()

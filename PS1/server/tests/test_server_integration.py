import unittest
import threading
import socket
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from server.server import ChatServer
from server.config import HOST, PORT

class TestChatServerIntegration(unittest.TestCase):
    """Integration tests for the full server with real components."""

    @classmethod
    def setUpClass(cls):
        """Start the server in a background thread before tests."""
        cls.server = ChatServer(verbose=False)
        cls.server_thread = threading.Thread(target=cls.server.start, daemon=True)
        cls.server_thread.start()

    def setUp(self):
        """Set up the client socket and clear the database before each test."""
        self.server.storage._clear_db()  # Clear the database before tests
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((HOST, PORT))

    def send_request(self, action, data={}):
        """Helper function to send a request to the server."""
        request = json.dumps({"action": action, "data": data}).encode("utf-8")
        self.client_socket.send(request)
        response = json.loads(self.client_socket.recv(1024).decode("utf-8"))
        return response

    def test_create_account(self):
        """Test creating a new user account."""
        response = self.send_request("create_account", {"username": "alice", "password": "1234"})
        self.assertEqual(response["status"], "success")

    def test_create_duplicate_account(self):
        """Test that creating a duplicate account fails."""
        self.send_request("create_account", {"username": "alice", "password": "1234"})  # First creation
        response = self.send_request("create_account", {"username": "alice", "password": "5678"})  # Duplicate
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Username already exists")

    def test_login_success(self):
        """Test logging into an existing account."""
        self.send_request("create_account", {"username": "bob", "password": "securepass"})
        response = self.send_request("login", {"username": "bob", "password": "securepass"})
        self.assertEqual(response["status"], "success")

    def test_login_wrong_password(self):
        """Test logging in with a wrong password."""
        self.send_request("create_account", {"username": "charlie", "password": "mypassword"})
        response = self.send_request("login", {"username": "charlie", "password": "wrongpass"})
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Incorrect password")

    def test_send_and_receive_message(self):
        """Test sending a message from Alice to Bob and retrieving it."""
        self.send_request("create_account", {"username": "alice", "password": "1234"})
        self.send_request("create_account", {"username": "bob", "password": "5678"})

        login_response = self.send_request("login", {"username": "alice", "password": "1234"})
        token = login_response["data"]["session_token"]

        send_response = self.send_request("send_message", {"session_token": token, "recipient": "bob", "message": "Hello Bob!"})
        self.assertEqual(send_response["status"], "success")

        login_response_bob = self.send_request("login", {"username": "bob", "password": "5678"})
        token_bob = login_response_bob["data"]["session_token"]

        read_response = self.send_request("read_messages", {"session_token": token_bob, "num_to_read": 1})
        self.assertEqual(read_response["status"], "success")
        self.assertEqual(read_response["data"]["unread_messages"][0]["message"], "Hello Bob!")

    def test_invalid_request(self):
        """Test sending an invalid action."""
        response = self.send_request("invalid_action")
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Invalid request")

    def test_malformed_json(self):
        """Test sending malformed JSON."""
        self.client_socket.send(b'INVALID_JSON')  # Send invalid data
        response = self.client_socket.recv(1024)  # Should not crash the server
        self.assertEqual(response, b'')  # No valid response expected

    @classmethod
    def tearDownClass(cls):
        """Stop the server after tests."""
        cls.server.server_socket.close()

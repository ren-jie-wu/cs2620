import unittest
from unittest.mock import MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from server.storage import MemoryStorage
from server.request_handler import RequestHandler
from shared.protocol import JSONProtocol

class TestRequestHandler(unittest.TestCase):
    def setUp(self):
        """Setup mock storage and protocol for testing. This will isolate the RequestHandler from the actual storage and protocol for testing."""
        self.mock_storage = MagicMock(spec=MemoryStorage)
        self.mock_storage.clients = {}
        self.mock_protocol = MagicMock(spec=JSONProtocol)
        self.handler = RequestHandler(self.mock_storage, self.mock_protocol)
    
    def test_create_account_success(self):
        """Test successful account creation."""
        self.mock_storage.create_account.return_value = (True, None)

        request = {"action": "create_account", "data": {"username": "alice", "password": "1234"}}
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "success")
        self.mock_storage.create_account.assert_called_once_with("alice", "1234")

    def test_create_account_missing_data(self):
        """Test account creation fails when data is missing."""
        request = {"action": "create_account", "data": {"username": "alice"}}
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Missing username or password")
    
    def test_create_account_duplicate(self):
        """Test account creation fails when username already exists."""
        self.mock_storage.create_account.return_value = (False, "Username already exists")

        request = {"action": "create_account", "data": {"username": "alice", "password": "1234"}}
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Username already exists")

    def test_login_success(self):
        """Test successful login."""
        self.mock_storage.login.return_value = (True, None, "token123", 5)

        request = {"action": "login", "data": {"username": "alice", "password": "1234"}}
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"]["session_token"], "token123")
        self.assertEqual(response["data"]["unread_message_count"], 5)

    def test_login_invalid_credentials(self):
        """Test login failure due to incorrect password."""
        self.mock_storage.login.return_value = (False, "Incorrect password", None, None)

        request = {"action": "login", "data": {"username": "alice", "password": "wrongpass"}}
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Incorrect password")
    
    def test_listen_success(self):
        """Test successful listening."""
        self.mock_storage.listen.return_value = (True, None, "token123")

        request = {"action": "listen", "data": {"username": "alice", "password": "1234"}}
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"]["session_token"], "token123")

    def test_listen_invalid_credentials(self):
        """Test listening failure due to incorrect password."""
        self.mock_storage.listen.return_value = (False, "Incorrect password", None)

        request = {"action": "listen", "data": {"username": "alice", "password": "wrongpass"}}
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Incorrect password")

    def test_list_accounts_success(self):
        """Test listing accounts successfully."""
        self.mock_storage.validate_session.return_value = "alice"
        self.mock_storage.list_accounts.return_value = (["alice", "bob"], 1, 1)

        request = {"action": "list_accounts", "data": {"session_token": "valid_token"}}
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"]["accounts"], ["alice", "bob"])
    
    def test_list_accounts_invalid_values(self):
        """Test list accounts failure due to invalid values."""
        self.mock_storage.validate_session.return_value = "alice"

        request = {"action": "list_accounts", "data": {"session_token": "valid_token", "page_size": -1}}
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Invalid page or page size")

        request = {"action": "list_accounts", "data": {"session_token": "valid_token", "page": "first"}}
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Invalid page or page size")

    def test_list_accounts_invalid_session(self):
        """Test list accounts failure due to invalid session."""
        self.mock_storage.validate_session.return_value = None

        request = {"action": "list_accounts", "data": {"session_token": "invalid_token"}}
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Invalid session")

    def test_send_message_success(self):
        """Test sending a message successfully."""
        self.mock_storage.validate_session.return_value = "alice"
        self.mock_storage.account_exist.return_value = True
        self.mock_storage.clients["bob"] = {"token123": (mock_socket:=MagicMock()), # Mock socket for recipient
                                            "token456": None} # Mock closed socket

        request = {
            "action": "send_message",
            "data": {"session_token": "valid_token", "recipient": "bob", "message": "Hello Bob!"}
        }
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "success")
        mock_socket.send.assert_called_once_with(self.mock_protocol.encode({"action": "receive_message", "data": {"sender": "alice", "message": "Hello Bob!"}}))
    
    def test_send_message_realtime(self):
        """Test sending a message in real-time."""
        self.mock_storage.validate_session.return_value = "alice"
        self.mock_storage.account_exist.return_value = True

        request = {
            "action": "send_message",
            "data": {"session_token": "valid_token", "recipient": "bob", "message": "Hello Bob!"}
        }
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "success")
        self.mock_storage.add_message.assert_called_once_with("bob", {"from": "alice", "message": "Hello Bob!"})
    
    def test_send_message_invalid_data(self):
        """Test sending a message with missing recipient, missing message, or invalid recipient."""
        self.mock_storage.validate_session.return_value = "alice"

        request = {
            "action": "send_message",
            "data": {"session_token": "valid_token", "recipient": "", "message": "Hello Bob!"}
        }
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Missing recipient or message")

        request = {
            "action": "send_message",
            "data": {"session_token": "valid_token", "recipient": "bob", "message": ""}
        }
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Missing recipient or message")

        self.mock_storage.account_exist.return_value = False  # Simulate recipient not existing

        request = {
            "action": "send_message",
            "data": {"session_token": "valid_token", "recipient": "invalid_recipient", "message": "Hello Bob!"}
        }
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Recipient does not exist")

    def test_send_message_invalid_session(self):
        """Test sending a message with an invalid session token."""
        self.mock_storage.validate_session.return_value = None

        request = {
            "action": "send_message",
            "data": {"session_token": "invalid_token", "recipient": "bob", "message": "Hello Bob!"}
        }
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Invalid session")

    def test_read_messages_success(self):
        """Test reading messages successfully."""
        self.mock_storage.validate_session.return_value = "alice"
        self.mock_storage.get_and_clear_messages.return_value = ([{"from": "bob", "message": "Hey!"}], 0)

        request = {"action": "read_messages", "data": {"session_token": "valid_token", "num_to_read": 1}}
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"]["unread_messages"][0]["message"], "Hey!")
    
    def test_read_messages_invalid_values(self):
        """Test reading messages with invalid values."""
        self.mock_storage.validate_session.return_value = "alice"

        request = {"action": "read_messages", "data": {"session_token": "valid_token", "num_to_read": "one"}}
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Invalid number of messages to read")
    
    def test_read_messages_invalid_session(self):
        """Test reading messages with an invalid session token."""
        self.mock_storage.validate_session.return_value = None

        request = {"action": "read_messages", "data": {"session_token": "invalid_token", "num_to_read": 1}}
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Invalid session")
    
    def test_delete_messages_success(self):
        """Test deleting messages successfully."""
        self.mock_storage.validate_session.return_value = "alice"
        self.mock_storage.delete_messages.return_value = 3

        request = {"action": "delete_messages", "data": {"session_token": "valid_token", "num_to_delete": 3}}
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"]["num_messages_deleted"], 3)
    
    def test_delete_messages_invalid_values(self):
        """Test deleting messages with invalid values."""
        self.mock_storage.validate_session.return_value = "alice"

        request = {"action": "delete_messages", "data": {"session_token": "valid_token", "num_to_delete": "one"}}
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Invalid number of messages to delete")
    
    def test_delete_messages_invalid_session(self):
        """Test deleting messages with an invalid session token."""
        self.mock_storage.validate_session.return_value = None

        request = {"action": "delete_messages", "data": {"session_token": "invalid_token", "num_to_delete": 1}}
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Invalid session")

    def test_delete_account_success(self):
        """Test deleting an account successfully."""
        self.mock_storage.validate_session.return_value = "alice"

        request = {"action": "delete_account", "data": {"session_token": "valid_token"}}
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "success")
        self.mock_storage.delete_account.assert_called_once_with("alice")
    
    def test_delete_account_invalid_session(self):
        """Test deleting an account with an invalid session token."""
        self.mock_storage.validate_session.return_value = None

        request = {"action": "delete_account", "data": {"session_token": "invalid_token"}}
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Invalid session")

    def test_logout_success(self):
        """Test logging out successfully."""
        self.mock_storage.validate_session.return_value = "alice"

        request = {"action": "logout", "data": {"session_token": "valid_token"}}
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "success")
        self.mock_storage.logout.assert_called_once_with("valid_token")
    
    def test_logout_invalid_session(self):
        """Test logging out with an invalid session token."""
        self.mock_storage.validate_session.return_value = None

        request = {"action": "logout", "data": {"session_token": "invalid_token"}}
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Invalid session")

    def test_invalid_action(self):
        """Test processing a request with an invalid action."""
        request = {"action": "invalid_action", "data": {}}
        response = self.handler.process_request(request, None)

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Invalid request")
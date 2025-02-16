import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import time
import threading
import unittest
from unittest.mock import MagicMock
import tkinter as tk
from client.gui import ChatClient
from utils import disable_messagebox, enable_messagebox, set_askstring, setback_askstring, set_askinteger, setback_askinteger

class TestChatClient(unittest.TestCase):
    def setUp(self):
        """Set up a mock network connection and a Tkinter root window."""
        disable_messagebox()
        self.root = tk.Tk()
        self.client = ChatClient(self.root, network=MagicMock)  # Use mocked network

    def tearDown(self):
        """Destroy Tkinter root after each test."""
        self.root.destroy()
        enable_messagebox()
    
    def test_create_account(self):
        """Test account creation."""
        self.client.username_entry.insert(0, "alice")
        self.client.password_entry.insert(0, "1234")
        self.client.connection.send_request.return_value = {"status": "success"}
        self.client.create_account()

        self.client.connection.send_request.assert_called_with("create_account", {"username": "alice", "password": "1234"})

    def test_login_success(self):
        """Test successful login."""
        self.client.connection.send_request.return_value = {"status": "success", "data": {"session_token": "abc123", "unread_message_count": 2}}
        self.client.username_entry.insert(0, "alice")
        self.client.password_entry.insert(0, "1234")
        self.client.login()

        self.assertEqual(self.client.session_token, "abc123")

    def test_send_message(self):
        """Test sending a message."""
        self.client.build_chat_screen(background=False)
        set_askstring("bob")
        self.client.message_entry.insert(0, "Hi Bob!")
        self.client.session_token = "abc123"
        self.client.connection.send_request.return_value = {"status": "success"}

        self.client.send_message()

        self.client.connection.send_request.assert_called()
        self.assertEqual(self.client.chat_display.get("1.0", tk.END), "You -> bob: Hi Bob!\n" + '-'*50 + '\n\n')
        self.assertEqual(self.client.message_entry.get(), "")
        setback_askstring()

    def test_listen(self):
        """Test listening for messages."""
        self.client.build_chat_screen(background=False)
        self.client.running = True
        self.client.background_connection = MagicMock()
        self.client.background_connection.send_request.return_value = {"status": "success", "data": {"session_token": "abc123"}}
        self.client.background_connection.receive_message.return_value = {"action": "receive_message", "data": {"sender": "bob", "message": "Hi Alice"}}
        listener_thread = threading.Thread(target=self.client.listen_for_messages, args=("alice", "1234"), daemon=True)
        listener_thread.start()
        
        time.sleep(0.01) 
        self.client.running = False

        self.client.background_connection.receive_message.assert_called()

    def test_read_messages(self):
        """Test reading messages."""
        self.client.build_chat_screen(background=False)
        self.client.session_token = "abc123"
        self.client.connection.send_request.return_value = {"status": "success", "data": {"unread_messages": [
            {"sender": "bob", "message": "Hi Alice"}, {"sender": "charlie", "message": "Hello Alice"}]}}
        
        self.client.read_messages()

        self.client.connection.send_request.assert_called_with("read_messages", {"session_token": "abc123", "num_to_read": 3})

        self.client.connection.send_request.return_value = {"status": "success", "data": {"unread_messages": []}}

        self.client.read_messages()

        self.client.connection.send_request.assert_called_with("read_messages", {"session_token": "abc123", "num_to_read": 3})
    
    def test_delete_messages(self):
        """Test deleting messages."""
        pass

    # def test_logout(self):
    #     """Test user logout."""
    #     self.client.session_token = "abc123"
    #     self.client.connection.send_request.return_value = {"status": "success"}
    #     self.client.root.after(0, self.client.logout)
    #     self.assertIsNone(self.client.session_token)

    # def test_delete_account(self):
    #     """Test deleting an account."""
    #     self.client.session_token = "abc123"
    #     self.client.connection.send_request.return_value = {"status": "success"}
    #     self.client.root.after(0, self.client.delete_account)
    #     self.assertIsNone(self.client.session_token)

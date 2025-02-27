import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from server.storage import MemoryStorage
from unittest.mock import MagicMock

class TestMemoryStorage(unittest.TestCase):
    def setUp(self):
        """Initialize a new MemoryStorage for each test."""
        self.storage = MemoryStorage()
    
    def test_create_account(self):
        """
        Test account creation in memory storage.
        
        It creates a new account, tests for successful creation, and tests for
        duplicate username.
        """
        success, error = self.storage.create_account("alice", "password123")
        self.assertTrue(success)
        self.assertIsNone(error)

        # Test duplicate username
        success, error = self.storage.create_account("alice", "anotherpass")
        self.assertFalse(success)
        self.assertEqual(error, "Username already exists")
    
    def test_login(self):
        """
        Test logging in to memory storage.
        
        It tests for successful login, invalid username, and wrong password.
        """
        self.storage.create_account("alice", "password123")
        success, error, token, unread_count = self.storage.login("alice", "password123")
        self.assertTrue(success)
        self.assertIsNotNone(token)
        self.assertEqual(unread_count, 0)

        # Invalid username
        success, error, _, _ = self.storage.login("invaliduser", "password123")
        self.assertFalse(success)
        self.assertEqual(error, "User does not exist")

        # Wrong password
        success, error, _, _ = self.storage.login("alice", "wrongpass")
        self.assertFalse(success)
        self.assertEqual(error, "Incorrect password")
    
    def test_listen(self):
        """
        Test listening to a client socket in memory storage.
        
        It tests for successful login to listen, invalid username, and wrong password.
        """
        self.storage.create_account("alice", "password123")
        success, error, token = self.storage.listen("alice", "password123", MagicMock())
        self.assertTrue(success)
        self.assertIsNotNone(token)
        self.assertIn(token, self.storage.clients['alice'])

        success, error, token = self.storage.listen("alice0", "password123", MagicMock())
        self.assertFalse(success)
        success, error, token = self.storage.listen("alice", "password1234", MagicMock())
        self.assertFalse(success)
    
    def test_list_accounts(self):
        """
        Test listing accounts in memory storage.
        
        It tests listing all accounts in two pages.
        """
        self.storage.create_account("alice", "password123")
        self.storage.create_account("bob", "password123")
        self.storage.create_account("charlie", "password123")
        accounts, page, total_pages = self.storage.list_accounts("*", 1, 2)
        self.assertEqual(len(accounts), 2)
        self.assertEqual(accounts[0], "alice")
        self.assertEqual(accounts[1], "bob")
        self.assertEqual(page, 1)
        self.assertEqual(total_pages, 2)
    
    def test_add_and_retrieve_messages(self):
        """
        Test adding and retrieving messages in memory storage.
        
        It tests adding multiple messages, retrieving the latest message, retrieving multiple messages from the latest, retrieving multiple messages from the earliest, and the remaining message count.
        """
        self.storage.create_account("bob", "password")
        self.storage.add_message("bob", {"sender": "alice", "message": "Hello Bob!"})
        self.storage.add_message("bob", {"sender": "alice", "message": "How are you?"})
        messages, remaining = self.storage.get_and_clear_messages("bob", 1)

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["sender"], "alice")
        self.assertEqual(messages[0]["message"], "How are you?")
        self.assertEqual(remaining, 1)

        self.storage.add_message("bob", {"sender": "alice", "message": "How are you?"})
        self.storage.add_message("bob", {"sender": "alice", "message": "I'm good, thanks!"})
        self.storage.add_message("bob", {"sender": "alice", "message": "How about you?"})

        messages, remaining = self.storage.get_and_clear_messages("bob", -2)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["message"], "Hello Bob!")
        self.assertEqual(messages[1]["message"], "How are you?")
        self.assertEqual(remaining, 2)
    
    def test_delete_messages(self):
        """
        Test deleting messages in memory storage.

        It tests deleting two messages, deleting messages from the earliest, and deleting messages from the latest.
        """
        self.storage.create_account("bob", "password")
        self.storage.add_message("bob", {"sender": "alice", "message": "Hello Bob!"})
        self.storage.add_message("bob", {"sender": "alice", "message": "How are you?"})
        self.storage.add_message("bob", {"sender": "alice", "message": "I'm good, thanks!"})
        self.storage.add_message("bob", {"sender": "alice", "message": "How about you?"})

        count = self.storage.delete_messages("bob", 2)
        self.assertEqual(count, 2)

        count = self.storage.delete_messages("bob", -4)
        self.assertEqual(count, 2)
    
    def test_logout(self):
        """
        Test logging out in memory storage.

        It tests logging out a user, given a valid session token.
        """
        self.storage.create_account("alice", "password123")
        success, error, token, _ = self.storage.login("alice", "password123")
        self.storage.logout(token)
    
    def test_delete_account(self):
        """
        Test deleting an account in memory storage.

        It tests deleting an account, given that the user is logged in.
        """
        self.storage.create_account("alice", "password123")
        self.storage.login("alice", "password123")
        self.storage.delete_account("alice")
    
    def test_validate_session(self):
        """
        Test validating a session in memory storage.

        It tests validating a session, given a valid session token,
        and validating a session after logging out.
        """
        self.storage.create_account("alice", "password123")
        success, error, token, _ = self.storage.login("alice", "password123")
        self.assertEqual(self.storage.validate_session(token), "alice")
        self.storage.logout(token)
        self.assertIsNone(self.storage.validate_session(token))
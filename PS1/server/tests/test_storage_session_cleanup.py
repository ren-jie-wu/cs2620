import unittest
import time
import threading
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from server.storage import MemoryStorage

class TestSessionCleanup(unittest.TestCase):
    def setUp(self):
        """Initialize MemoryStorage before each test."""
        self.storage = MemoryStorage()
        self.storage.sessions = {
            "token1": {"username": "alice", "expiry_time": time.time() - 10},  # Expired
            "token2": {"username": "bob", "expiry_time": time.time() + 1000}, # Active
        }
        self.storage.clients = {
            "alice": {"token1": MagicMock()},
            "bob": {"token2": MagicMock()},
        }

    def test_cleanup_expired_sessions(self):
        """Test that expired sessions are removed, while active ones remain."""
        # Run cleanup for a short time in a separate thread
        cleanup_thread = threading.Thread(target=self.storage.cleanup_expired_sessions, daemon=True)
        cleanup_thread.start()
        
        # Give it a moment to process (since it's running in a thread)
        time.sleep(0.1)

        # Check that "token1" (expired) is removed, but "token2" (active) remains
        self.assertNotIn("token1", self.storage.sessions)
        self.assertNotIn("token1", self.storage.clients.get("alice", {}))
        self.assertIn("token2", self.storage.sessions)

    def test_cleanup_handles_socket_exceptions(self):
        """Test that cleanup continues even if closing a socket raises an error."""
        self.storage.clients["alice"]["token1"].close.side_effect = Exception("Socket error")

        cleanup_thread = threading.Thread(target=self.storage.cleanup_expired_sessions, daemon=True)
        cleanup_thread.start()
        time.sleep(0.1)

        self.assertNotIn("token1", self.storage.sessions)  # Should still remove expired session
        self.assertNotIn("token1", self.storage.clients.get("alice", {}))  # Should remove from clients

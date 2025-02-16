import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from server.storage import DatabaseStorage
from server.tests.test_storage_memory import TestMemoryStorage

class TestDatabaseStorage(TestMemoryStorage):
    def setUp(self):
        """Initialize a new DatabaseStorage for each test."""
        self.storage = DatabaseStorage()
        self.storage._clear_db()
    
    # Simply clear the database after each test
    def test_create_account(self):
        super().test_create_account()
        self.storage._clear_db()
    
    def test_login(self):
        super().test_login()
        self.storage._clear_db()

    def test_listen(self):
        super().test_listen()
        self.storage._clear_db()
    
    def test_list_accounts(self):
        super().test_list_accounts()
        self.storage._clear_db()
    
    def test_add_and_retrieve_messages(self):
        super().test_add_and_retrieve_messages()
        self.storage._clear_db()
    
    def test_delete_messages(self):
        super().test_delete_messages()
        self.storage._clear_db()
    
    def test_logout(self):
        super().test_logout()
        self.storage._clear_db()
    
    def test_delete_account(self):
        super().test_delete_account()
        self.storage._clear_db()
    
    def test_validate_session(self):
        super().test_validate_session()
        self.storage._clear_db()

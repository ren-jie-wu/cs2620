# storage.py
# This module encapsulates the in‐memory storage or database storage 
# for users, sessions, messages, and client sockets. It also includes 
# methods for account management and session cleanup. 
# (Note: For thread safety, we use a lock here.)

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import threading
import time
import fnmatch
import sqlite3
from abc import ABC, abstractmethod
from server.config import TOKEN_EXPIRY_TIME, CLEAN_SESSION_INTERVAL
from server.utils import hash_password, generate_token

class Storage(ABC):
    """
    Abstract base class for storage of user accounts, sessions, messages, and client sockets.
    
    Subclasses must implement all the methods below so that the rest of the system
    can interact with storage in a uniform way.
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.clients = {}  # {username: {session_token: client_socket, ...}}
        self.sessions = {} # {session_token: {"username": username, "expiry_time": ...}}

    @abstractmethod
    def account_exist(self, username: str):
        """
        Check if the given username exists.
        """
        pass
    
    @abstractmethod
    def create_account(self, username: str, password: str):
        """
        Create a new account with the given username and password.
        Returns (True, None) if successful, or (False, error_message) if not.
        """
        pass

    @abstractmethod
    def login(self, username: str, password: str):
        """
        Authenticate the user and create a session.
        Returns (True, None, session_token, unread_count) if successful,
        or (False, error_message, None, None) if not.
        """
        pass
    
    @abstractmethod
    def listen(self, username: str, password: str, client_socket):
        """
        Authenticate the user, create a session, and associate the client socket.
        Returns (True, None, session_token) if successful, or (False, error_message, None) if not.
        """
        pass

    @abstractmethod
    def validate_session(self, session_token: str):
        """
        Validate the given session token.
        Returns the associated username if valid, or None otherwise.
        """
        pass

    @abstractmethod
    def list_accounts(self, pattern: str = "*", page: int = 1, page_size: int = 10):
        """
        List accounts matching the wildcard pattern, paginated.
        Returns a tuple (accounts_list, page, total_pages).
        """
        pass

    @abstractmethod
    def add_message(self, recipient: str, message: dict):
        """
        Add a message for the given recipient.
        """
        pass

    @abstractmethod
    def get_and_clear_messages(self, username: str, num_to_read: int):
        """
        Retrieve and remove messages for the user.
        Returns a tuple (list_of_messages, remaining_message_count).
        """
        pass

    @abstractmethod
    def delete_messages(self, username: str, num_to_delete: int):
        """
        Delete a specified number of messages for the user.
        Returns the number of messages deleted.
        """
        pass

    @abstractmethod
    def delete_account(self, username: str):
        """
        Delete the user's account and all associated data.
        """
        pass

    @abstractmethod
    def logout(self, session_token: str):
        """
        Log out the session identified by session_token.
        """
        pass

    def cleanup_expired_sessions(self):
        """Periodically clean up expired sessions (close connection, remove from clients and sessions)."""
        while True:
            with self.lock:
                current_time = time.time()
                expired_tokens = [token for token, data in self.sessions.items() if current_time > data["expiry_time"]]
                for token in expired_tokens:
                    username = self.sessions[token]["username"]
                    if username in self.clients and token in self.clients[username]:
                        try:
                            self.clients[username][token].close()
                        except Exception:
                            pass
                        self.clients[username].pop(token, None)
                    self.sessions.pop(token, None)
            time.sleep(CLEAN_SESSION_INTERVAL)

class MemoryStorage(Storage):
    """
    In-memory storage implementation. This is suitable for testing or low-load usage.
    """
    def __init__(self):
        self.users = {}       # {username: password_hash}
        self.messages = {}    # {username: [message, ...]}
        super().__init__()

    def account_exist(self, username: str):
        with self.lock:
            return username in self.users

    def create_account(self, username: str, password: str):
        if_exists = self.account_exist(username)
        with self.lock:
            if if_exists:
                return False, "Username already exists"
            self.users[username] = hash_password(password)
            self.messages[username] = []
            return True, None

    def login(self, username: str, password: str):
        with self.lock:
            if username not in self.users:
                return False, "User does not exist", None, None
            if self.users[username] != hash_password(password):
                return False, "Incorrect password", None, None
            session_token = generate_token()
            expiry_time = time.time() + TOKEN_EXPIRY_TIME
            self.sessions[session_token] = {"username": username, "expiry_time": expiry_time}
            unread_count = len(self.messages.get(username, []))
            return True, None, session_token, unread_count
    
    def listen(self, username: str, password: str, client_socket):
        with self.lock:
            if username not in self.users:
                return False, "User does not exist", None
            if self.users[username] != hash_password(password):
                return False, "Incorrect password", None
            session_token = generate_token()
            expiry_time = time.time() + TOKEN_EXPIRY_TIME
            self.sessions[session_token] = {"username": username, "expiry_time": expiry_time}
            if username not in self.clients:
                self.clients[username] = {}
            self.clients[username][session_token] = client_socket
            return True, None, session_token

    def validate_session(self, session_token: str):
        with self.lock:
            session = self.sessions.get(session_token)
            if session and time.time() <= session["expiry_time"]:
                return session["username"]
            return None

    def list_accounts(self, pattern: str = "*", page: int = 1, page_size: int = 10):
        with self.lock:
            matched = sorted(fnmatch.filter(self.users.keys(), pattern))
            total_pages = (len(matched) - 1) // page_size + 1 if matched else 1
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            return matched[start_index:end_index], page, total_pages

    def add_message(self, recipient: str, message: dict):
        with self.lock:
            if recipient in self.messages:
                self.messages[recipient].append(message)

    def get_and_clear_messages(self, username: str, num_to_read: int):
        with self.lock:
            msgs = self.messages.get(username, [])
            if num_to_read < 0:
                # Read the earliest |num_to_read| messages
                result = msgs[:abs(num_to_read)]
                self.messages[username] = msgs[abs(num_to_read):]
            else:
                # Read the latest num_to_read messages
                result = msgs[-num_to_read:][::-1]
                self.messages[username] = msgs[:-num_to_read]
            remaining = len(self.messages.get(username, []))
            return result, remaining

    def delete_messages(self, username: str, num_to_delete: int):
        with self.lock:
            msgs = self.messages.get(username, [])
            count_before = len(msgs)
            if num_to_delete >= 0:
                self.messages[username] = msgs[num_to_delete:]
            else:
                self.messages[username] = msgs[:num_to_delete]
            count_after = len(self.messages.get(username, []))
            return count_before - count_after

    def delete_account(self, username: str):
        with self.lock:
            self.users.pop(username, None)
            self.messages.pop(username, None)
            self.clients.pop(username, None)
            expired_tokens = [token for token, data in self.sessions.items() if data["username"] == username]
            for token in expired_tokens:
                self.sessions.pop(token, None)

    def logout(self, session_token: str):
        with self.lock:
            session = self.sessions.get(session_token)
            if session:
                username = session["username"]
                if username in self.clients:
                    self.clients[username].pop(session_token, None)
                self.sessions.pop(session_token, None)

class DatabaseStorage(Storage):
    """
    Database storage implementation using SQLite.
    A single persistent connection is maintained to handle high concurrency.
    Note: SQLite connection is opened with check_same_thread=False, and a lock is used
    to serialize access.
    """
    def __init__(self, db_path=None):
        super().__init__()
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), "chat.db")
        # Open a persistent connection (allowing usage from multiple threads)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._initialize_db()
        
    def _initialize_db(self):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipient TEXT,
                    sender TEXT,
                    message TEXT
                )
            ''')
            self.conn.commit()
    
    def _clear_db(self):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM users")
            cursor.execute("DELETE FROM messages")
            self.conn.commit()

    def account_exist(self, username: str):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT username FROM users WHERE username=?", (username,))
            return bool(cursor.fetchone())
    
    def create_account(self, username: str, password: str):
        if_exists = self.account_exist(username)
        with self.lock:
            if if_exists:
                return False, "Username already exists"
            password_hash = hash_password(password)
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?,?)", (username, password_hash))
            self.conn.commit()
            return True, None

    def login(self, username: str, password: str):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE username=?", (username,))
            row = cursor.fetchone()
            if not row:
                return False, "User does not exist", None, None
            stored_hash = row["password_hash"]
            if stored_hash != hash_password(password):
                return False, "Incorrect password", None, None
            session_token = generate_token()
            expiry_time = time.time() + TOKEN_EXPIRY_TIME
            self.sessions[session_token] = {"username": username, "expiry_time": expiry_time}
            cursor.execute("SELECT COUNT(*) FROM messages WHERE recipient=?", (username,))
            unread_count = cursor.fetchone()[0]
            return True, None, session_token, unread_count

    def listen(self, username: str, password: str, client_socket):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE username=?", (username,))
            row = cursor.fetchone()
            if not row:
                return False, "User does not exist", None
            stored_hash = row["password_hash"]
            if stored_hash != hash_password(password):
                return False, "Incorrect password", None
            session_token = generate_token()
            expiry_time = time.time() + TOKEN_EXPIRY_TIME
            self.sessions[session_token] = {"username": username, "expiry_time": expiry_time}
            if username not in self.clients:
                self.clients[username] = {}
            self.clients[username][session_token] = client_socket
            return True, None, session_token
            

    def validate_session(self, session_token: str):
        with self.lock:
            session = self.sessions.get(session_token)
            if session and time.time() <= session["expiry_time"]:
                return session["username"]
            return None

    def list_accounts(self, pattern: str = "*", page: int = 1, page_size: int = 10):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT username FROM users")
            all_users = [row["username"] for row in cursor.fetchall()]
            matched = sorted(fnmatch.filter(all_users, pattern))
            total_pages = (len(matched) - 1) // page_size + 1 if matched else 1
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            return matched[start_index:end_index], page, total_pages

    def add_message(self, recipient: str, message: dict):
        with self.lock:
            cursor = self.conn.cursor()
            sender = message.get("from")
            msg_text = message.get("message")
            cursor.execute("INSERT INTO messages (recipient, sender, message) VALUES (?,?,?)", (recipient, sender, msg_text))
            self.conn.commit()

    def get_and_clear_messages(self, username: str, num_to_read: int):
        with self.lock:
            cursor = self.conn.cursor()
            if num_to_read < 0:
                # Retrieve earliest messages
                cursor.execute("SELECT id, sender, message FROM messages WHERE recipient=? ORDER BY id ASC LIMIT ?", (username, abs(num_to_read)))
            else:
                # Retrieve latest messages
                cursor.execute("SELECT id, sender, message FROM messages WHERE recipient=? ORDER BY id DESC LIMIT ?", (username, num_to_read))
            rows = cursor.fetchall()
            msgs = [{"from": row["sender"], "message": row["message"]} for row in rows]
            if rows:
                ids = [str(row["id"]) for row in rows]
                query = "DELETE FROM messages WHERE id IN (" + ",".join("?" for _ in ids) + ")"
                cursor.execute(query, ids)
                self.conn.commit()
            cursor.execute("SELECT COUNT(*) FROM messages WHERE recipient=?", (username,))
            remaining = cursor.fetchone()[0]
            return msgs, remaining

    def delete_messages(self, username: str, num_to_delete: int):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM messages WHERE recipient=?", (username,))
            count_before = cursor.fetchone()[0]
            if num_to_delete >= 0:
                cursor.execute("SELECT id FROM messages WHERE recipient=? ORDER BY id ASC LIMIT ?", (username, num_to_delete))
            else:
                cursor.execute("SELECT id FROM messages WHERE recipient=? ORDER BY id DESC LIMIT ?", (username, abs(num_to_delete)))
            rows = cursor.fetchall()
            if rows:
                ids = [str(row["id"]) for row in rows]
                query = "DELETE FROM messages WHERE id IN (" + ",".join("?" for _ in ids) + ")"
                cursor.execute(query, ids)
                self.conn.commit()
            cursor.execute("SELECT COUNT(*) FROM messages WHERE recipient=?", (username,))
            count_after = cursor.fetchone()[0]
            return count_before - count_after

    def delete_account(self, username: str):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM users WHERE username=?", (username,))
            cursor.execute("DELETE FROM messages WHERE recipient=?", (username,))
            self.conn.commit()
            self.clients.pop(username, None)
            expired_tokens = [token for token, data in self.sessions.items() if data["username"] == username]
            for token in expired_tokens:
                self.sessions.pop(token, None)

    def logout(self, session_token: str):
        with self.lock:
            session = self.sessions.get(session_token)
            if session:
                username = session["username"]
                if username in self.clients and session_token in self.clients[username]:
                    self.clients[username].pop(session_token, None)
                self.sessions.pop(session_token, None)

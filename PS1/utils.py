import hashlib
import uuid
import sqlite3  # noqa: F401
import time

def hash_password(password):
    """Returns the SHA256 hash of a password."""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token():
    """Generates a unique session token."""
    return str(uuid.uuid4())

# Server Configuration
HOST = "127.0.0.1"
PORT = 64400
CLEAN_SESSION_INTERVAL = 60
TOKEN_EXPIRY_TIME = 3000

# Server State (in-memory storage)
users = {}  # Stores {username: password_hash}
messages = {}  # Stores {recipient: [unread_message1, unread_message2, ...]}
clients = {}  # Stores {logged_in_username: {session_token1: client_socket1, ...}} # one user can have multiple socket connections
sessions = {}  # Stores {session_token: {username, expiry_time}} # though one session token can only be associated with one username, one username can have multiple session tokens

def cleanup_expired_sessions():
    try:
        while True:
            current_time = time.time()
            for session_token, session_data in list(sessions.items()):
                if current_time > session_data["expiry_time"]:
                    del sessions[session_token]
                    socket = clients.get(session_data["username"], {}).get(session_token)
                    if socket:
                        socket.close()
                        del clients[session_data["username"]][session_token]
            time.sleep(CLEAN_SESSION_INTERVAL)
    except KeyboardInterrupt:
        return

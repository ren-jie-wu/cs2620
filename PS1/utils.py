import hashlib
import uuid
import sqlite3
import time

def hash_password(password):
    """Returns the SHA256 hash of a password."""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token():
    """Generates a unique session token."""
    return str(uuid.uuid4())

# Server Configuration
HOST = "127.0.0.1"
PORT = 54400
CLEAN_SESSION_INTERVAL = 1
TOKEN_EXPIRY_TIME = 5

def cleanup_expired_sessions(sessions, clients):
    try:
        while True:
            current_time = time.time()
            for session_token, session_data in list(sessions.items()):
                if current_time > session_data["expiry_time"]:
                    del sessions[session_token]
                    clients[session_data["username"]].close()
                    del clients[session_data["username"]]
            time.sleep(CLEAN_SESSION_INTERVAL)
    except KeyboardInterrupt:
        return

# utils.py
import hashlib
import uuid

def hash_password(password: str) -> str:
    """Returns the SHA256 hash of a password."""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token() -> str:
    """Generates a unique session token."""
    return str(uuid.uuid4())

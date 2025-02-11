import hashlib
import uuid

def hash_password(password):
    """Returns the SHA256 hash of a password."""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token():
    """Generates a unique session token."""
    return str(uuid.uuid4())

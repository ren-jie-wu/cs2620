import hashlib

def hash_password(password):
    """Returns the SHA256 hash of a password."""
    return hashlib.sha256(password.encode()).hexdigest()
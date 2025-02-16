# config.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.config import HOST, PORT, PROTOCOL

TOKEN_EXPIRY_TIME = 3000  # how long the token is valid for in seconds
CLEAN_SESSION_INTERVAL = 60  # how often to clean the session in seconds
BUFFER_SIZE = 4096  # buffer size for socket

STORAGE = "db"  # how to store the data ("memory" or "db")
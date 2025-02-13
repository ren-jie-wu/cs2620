# config.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.config import HOST, PORT, PROTOCOL

TOKEN_EXPIRY_TIME = 3000  # seconds
CLEAN_SESSION_INTERVAL = 60  # seconds

STORAGE = "db"
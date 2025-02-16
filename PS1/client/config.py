# client/config.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.config import HOST, PORT, PROTOCOL

BUFFER_SIZE = 4096  # Increased buffer for larger messages
PAGE_SIZE = 5  # Number of accounts to display per page
MSG_NUM = 3  # Number of messages to display per request
REFRESH_INTERVAL = 0.1  # Refresh interval in seconds for message display
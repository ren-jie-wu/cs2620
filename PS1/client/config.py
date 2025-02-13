# client/config.py
from ..shared.config import HOST, PORT, PROTOCOL
BUFFER_SIZE = 4096  # Increased buffer for larger messages
PAGE_SIZE = 5  # Number of accounts to display per page
MSG_NUM = 3  # Number of messages to display per request
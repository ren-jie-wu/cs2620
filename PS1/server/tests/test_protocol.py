import unittest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from shared.protocol import JSONProtocol, CustomizedProtocol

class TestJSONProtocol(unittest.TestCase):
    def setUp(self):
        self.protocol = JSONProtocol()

    def test_encode_decode(self):
        message = {"action": "send_message", "data": {"message": "Hello", "sender": "Alice"}}
        encoded = self.protocol.encode(message)
        decoded = self.protocol.decode(encoded)
        self.assertEqual(decoded, message)


class TestCustomizedProtocol(unittest.TestCase):
    def setUp(self):
        self.protocol = CustomizedProtocol()

    def test_encode_decode(self):
        pass
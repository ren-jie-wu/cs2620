import unittest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from shared.protocol import JSONProtocol, CustomizedProtocol

class TestJSONProtocol(unittest.TestCase):
    def setUp(self):
        """
        Set up the test by initializing the protocol instance.
        """
        self.protocol = JSONProtocol()

    def test_encode_decode(self):
        """
        Test the encoding and decoding functions of the protocol.
        
        The first test checks a single message, while the second test checks
        two messages concatenated together.
        """
        message = {"action": "send_message", "data": {"message": "Hello", "sender": "Alice"}}
        encoded = self.protocol.encode(message)
        decoded = self.protocol.decode(encoded)
        self.assertEqual(decoded, [message])

        encoded = (self.protocol.encode(message).decode("utf-8") * 2).encode("utf-8")
        decoded = self.protocol.decode(encoded)
        self.assertEqual(decoded, [message, message])


class TestCustomizedProtocol(unittest.TestCase):
    def setUp(self):
        self.protocol = CustomizedProtocol()
    
    # Simply inherit the JSONProtocol test cases

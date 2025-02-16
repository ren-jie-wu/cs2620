# protocol.py
# Here we define a base Protocol class and a JSONProtocol that encodes/decodes messages. 
# Changing protocols later will only require implementing a new subclass.

import json
from typing import Any, Dict

class Protocol:
    def encode(self, message: Dict[str, Any]) -> bytes:
        raise NotImplementedError

    def decode(self, data: bytes) -> Dict[str, Any]:
        raise NotImplementedError

class JSONProtocol(Protocol):
    def encode(self, message: Dict[str, Any]) -> bytes:
        return json.dumps(message).encode("utf-8")

    def decode(self, data: bytes) -> Dict[str, Any]:
        return json.loads(data.decode("utf-8"))
        #TODO: handle json stream

class CustomizedProtocol(Protocol):
    def encode(self, message: Dict[str, Any]) -> bytes:
        raise NotImplementedError

    def decode(self, data: bytes) -> Dict[str, Any]:
        raise NotImplementedError
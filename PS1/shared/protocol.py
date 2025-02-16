# protocol.py
# Here we define a base Protocol class and a JSONProtocol that encodes/decodes messages. 
# Changing protocols later will only require implementing a new subclass.

import json
from typing import Any, Dict, List, Union

class Protocol:
    def encode(self, message: Dict[str, Any]) -> bytes:
        raise NotImplementedError

    def decode(self, data: bytes) -> Union[Dict[str, Any] | List[Dict[str, Any]]]:
        raise NotImplementedError

class JSONProtocol(Protocol):
    def encode(self, message: Dict[str, Any]) -> bytes:
        return json.dumps(message).encode("utf-8")

    def decode(self, data: bytes) -> List[Dict[str, Any]]:
        data = data.decode("utf-8").strip()
        output = []
        beg = 0
        stack = 0
        for i, c in enumerate(data):
            if c == "{":
                stack += 1
            elif c == "}":
                stack -= 1
            if stack == 0:
                try:
                    output.append(json.loads(data[beg:i+1].strip()))
                except json.decoder.JSONDecodeError:
                    pass
                beg = i + 1
        return output

class CustomizedProtocol(Protocol):
    def encode(self, message: Dict[str, Any]) -> bytes:
        # TODO: Your code here
        raise NotImplementedError

    def decode(self, data: bytes) -> List[Dict[str, Any]]:
        # TODO: Your code here
        raise NotImplementedError

# protocol.py
# Here we define a base Protocol class and a JSONProtocol that encodes/decodes messages. 
# Changing protocols later will only require implementing a new subclass.

import json
from typing import Any, Dict, List, Union

class Protocol:
    def encode(self, message: Dict[str, Any]) -> bytes:
        raise NotImplementedError

    def decode(self, bytes: bytes) -> Union[Dict[str, Any] | List[Dict[str, Any]]]:
        raise NotImplementedError

class JSONProtocol(Protocol):
    def encode(self, message: Dict[str, Any]) -> bytes:
        return json.dumps(message).encode("utf-8")

    def decode(self, bytes: bytes) -> List[Dict[str, Any]]:
        data = bytes.decode("utf-8").strip()
        messages = []
        beg = 0
        stack = 0
        for i, c in enumerate(data):
            if c == "{":
                stack += 1
            elif c == "}":
                stack -= 1
            if stack == 0:
                try:
                    messages.append(json.loads(data[beg:i+1].strip()))
                except json.decoder.JSONDecodeError:
                    pass
                beg = i + 1
        return messages

ACTIONS = [
    "create_account",
    "login",
    "listen",
    "list_accounts",
    "send_message",
    "receive_message",
    "read_messages",
    "delete_messages",
    "logout",
    "delete_account"
]
class CustomizedProtocol(Protocol):
    def encode(self, message: Dict[str, Any]) -> bytes:
        action, status, error, data = message.get("action"), message.get("status"), message.get("error"), message.get("data")
        action = '1' + str(ACTIONS.index(action)) if action in ACTIONS else '00' # 00/10-19
        status = ('11' if status == 'success' else '10') if status else '00' # request can have no status
        error = str(len(error)) + ':' + error if error else '0'
        data = json.dumps(data) if data else '0'
        length = str(len(action) + len(status) + len(error) + len(data))
        return f"{length}:{action}{status}{error}{data}".encode("utf-8")

    def decode(self, bytes: bytes) -> List[Dict[str, Any]]:
        text = bytes.decode("utf-8").strip()
        messages = []
        idx = 0

        while idx < len(bytes):
            try:
                length_end = text.index(":", idx)
                msg_length = int(text[idx:length_end])
                idx = length_end + 1

                if idx + msg_length > len(text):
                    break  # Incomplete message

                msg_text = text[idx:idx + msg_length]
                idx += msg_length

                messages.append(self.parse_components(msg_text))
            
            except (ValueError, IndexError):
                break

        return messages

    def parse_components(self, msg_text: str):
        action = msg_text[0:2]
        status = msg_text[2:4]
        remainder = msg_text[4:]

        action = ACTIONS[int(action[1])] if len(action) == 2 and action[0] == '1' and action[1].isdigit() else None
        status = 'success' if status == '11' else 'error' if status == '10' else None

        error = None
        if remainder[0] != '0':
            error_length_end = remainder.index(":")
            error_length = int(remainder[0:error_length_end])
            error = remainder[error_length_end + 1:error_length_end + 1 + error_length]
            data = remainder[error_length_end + 1 + error_length:]
        else:
            data = remainder[1:]
        data = json.loads(data) if data else None

        output = {}
        if action:
            output["action"] = action
        if status:
            output["status"] = status
        if error:
            output["error"] = error
        if data:
            output["data"] = data
        return output

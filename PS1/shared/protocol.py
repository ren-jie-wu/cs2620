# protocol.py
# Here we define a base Protocol class and a JSONProtocol that encodes/decodes messages. 
# Changing protocols later will only require implementing a new subclass.

import json
from typing import Any, Dict, List

class Protocol:
    def encode(self, message: Dict[str, Any]) -> bytes:
        """
        Encode a message dictionary to bytes.

        Args:
        message (Dict[str, Any]): Message to encode.

        Returns:
        bytes: Encoded message.
        """
        raise NotImplementedError

    def decode(self, bytes: bytes) -> List[Dict[str, Any]]:
        """
        Decode a bytes object to a list of message dictionaries.

        Args:
        bytes (bytes): Encoded message(s).

        Returns:
        List[Dict[str, Any]]: A list of decoded message dictionaries.
        """
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
        """
        Parse the given message text into its components.

        The components are:
        - action: The action that the message represents (e.g. "create_account", "login", etc.)
        - status: The status of the message (e.g. "success", "error", etc.)
        - error: The error message if the status is "error"
        - data: The data associated with the message

        :param msg_text: The message text to parse
        :return: A dictionary with the components of the message
        """
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

def test():
    """This is for testing purposes only. The results are showed in the README.md file."""
    json_protocol = JSONProtocol()
    custom_protocol = CustomizedProtocol()

    # Test Messages
    test_cases = {
        "Login Request": {"action": "login", "data": {"username": "alice", "password": "securepass"}},
        "Send Message Request": {"action": "send_message", "data": {"recipient": "bob", "message": "Hello, Bob!"}},
        "List Accounts Response": {
            "action": "list_accounts",
            "status": "success",
            "data": {"accounts": ["alice", "bob", "charlie", "dave", "eve"]}
        }
    }

    # Measure size for each protocol
    print(f"|{'Case':<25}|{'JSONProtocol (bytes)':<25}|{'CustomizedProtocol (bytes)':<30}|{'Reduction (%)':<20}|")
    print(f"|{'-'*25}|{'-'*25}|{'-'*30}|{'-'*20}|")

    for scenario, message in test_cases.items():
        json_encoded = json_protocol.encode(message)
        custom_encoded = custom_protocol.encode(message)

        json_size = len(json_encoded)
        custom_size = len(custom_encoded)
        reduction = (1 - (custom_size / json_size)) * 100  # Percentage reduction

        print(f"|{scenario:<25}|{json_size:<25}|{custom_size:<30}|{str(round(reduction, 1))+'%':<20}|")

if __name__ == "__main__":
    test()
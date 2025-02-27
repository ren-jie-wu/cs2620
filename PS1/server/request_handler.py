# request_handler.py
# This module defines a RequestHandler class that maps incoming requests 
# (by action) to storage operations. 
# Notice that the logic is now decoupled from raw socket handling.

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.protocol import Protocol
from server.storage import Storage

class RequestHandler:
    def __init__(self, storage: Storage, protocol: Protocol):
        """
        Initialize the RequestHandler with the given storage and protocol.

        :param storage: the Storage object to use for data operations
        :param protocol: the Protocol object to use for encoding/decoding
        """
        self.storage = storage
        self.protocol = protocol

    def process_request(self, request: dict, client_socket) -> dict:
        """
        Process an incoming request and return a response dictionary.

        This function takes the request dictionary and client socket as input,
        and returns a response dictionary according to the action specified in
        the request.

        It will call the corresponding method in self.storage and return the
        result in the response dictionary.

        If the request is invalid or the action is unsupported, it will return
        a response with status "error" and an appropriate error message.

        :param request: The request dictionary
        :param client_socket: The socket object of the client
        :return: A response dictionary
        """
        action = request.get("action")
        data = request.get("data", {})

        if action == "create_account":
            username = data.get("username")
            password = data.get("password")
            if not username or not password:
                return {"action": "create_account", "status": "error", "error": "Missing username or password"}
            success, error = self.storage.create_account(username, password)
            if success:
                return {"action": "create_account", "status": "success"}
            else:
                return {"action": "create_account", "status": "error", "error": error}

        elif action == "login":
            username = data.get("username")
            password = data.get("password")
            success, error, session_token, unread_count = self.storage.login(username, password)
            if success:
                return {"action": "login", "status": "success", "data": {"session_token": session_token, "unread_message_count": unread_count}}
            else:
                return {"action": "login", "status": "error", "error": error}
        
        elif action == "listen":
            username = data.get("username")
            password = data.get("password")
            success, error, session_token = self.storage.listen(username, password, client_socket)
            if success:
                return {"action": "listen", "status": "success", "data": {"session_token": session_token}}
            else:
                return {"action": "listen", "status": "error", "error": error}

        elif action == "list_accounts":
            session_token = data.get("session_token")
            if not self.storage.validate_session(session_token):
                return {"action": "list_accounts", "status": "error", "error": "Invalid session"}
            pattern = data.get("pattern", "*")
            try:
                page = int(data.get("page", 1))
                page_size = int(data.get("page_size", 10))
                if page <= 0 or page_size <= 0:
                    raise ValueError
            except Exception:
                return {"action": "list_accounts", "status": "error", "error": "Invalid page or page size"}
            accounts, page, total_pages = self.storage.list_accounts(pattern, page, page_size)
            return {"action": "list_accounts", "status": "success", "data": {"accounts": accounts, "page": page, "total_pages": total_pages}}

        elif action == "send_message":
            session_token = data.get("session_token")
            sender = self.storage.validate_session(session_token)
            recipient = data.get("recipient")
            message = data.get("message")
            if not sender:
                return {"action": "send_message", "status": "error", "error": "Invalid session"}
            if not recipient or not message:
                return {"action": "send_message", "status": "error", "error": "Missing recipient or message"}
            if not self.storage.account_exist(recipient):
                return {"action": "send_message", "status": "error", "error": "Recipient does not exist"}
            delivered = False
            if recipient in self.storage.clients:
                for sock in self.storage.clients[recipient].values():
                    try:
                        sock.send(self.protocol.encode({"action": "receive_message", "data": {"sender": sender, "message": message}}))
                        delivered = True
                    except Exception:
                        continue
            if not delivered:
                self.storage.add_message(recipient, {"sender": sender, "message": message})
            return {"action": "send_message", "status": "success"}

        elif action == "read_messages":
            session_token = data.get("session_token")
            username = self.storage.validate_session(session_token)
            if not username:
                return {"action": "read_messages", "status": "error", "error": "Invalid session"}
            try:
                num_to_read = int(data.get("num_to_read", 1))
            except Exception:
                return {"action": "read_messages", "status": "error", "error": "Invalid number of messages to read"}
            msgs, remaining = self.storage.get_and_clear_messages(username, num_to_read)
            return {"action": "read_messages", "status": "success", "data": {"unread_messages": msgs, "remaining_unread_count": remaining}}

        elif action == "delete_messages":
            session_token = data.get("session_token")
            username = self.storage.validate_session(session_token)
            if not username:
                return {"action": "delete_messages", "status": "error", "error": "Invalid session"}
            try:
                num_to_delete = int(data.get("num_to_delete"))
            except Exception:
                return {"action": "delete_messages", "status": "error", "error": "Invalid number of messages to delete"}
            deleted_count = self.storage.delete_messages(username, num_to_delete)
            return {"action": "delete_messages", "status": "success", "data": {"num_messages_deleted": deleted_count}}

        elif action == "delete_account":
            session_token = data.get("session_token")
            username = self.storage.validate_session(session_token)
            if not username:
                return {"action": "delete_account", "status": "error", "error": "Invalid session"}
            self.storage.delete_account(username)
            return {"action": "delete_account", "status": "success"}

        elif action == "logout":
            session_token = data.get("session_token")
            username = self.storage.validate_session(session_token)
            if not username:
                return {"action": "logout", "status": "error", "error": "Invalid session"}
            self.storage.logout(session_token)
            return {"action": "logout", "status": "success"}

        else:
            return {"action": action, "status": "error", "error": "Invalid request"}

import socket
import threading
import json
import time  # noqa: F401
import fnmatch
from utils import hash_password, generate_token, cleanup_expired_sessions, HOST, PORT, TOKEN_EXPIRY_TIME, users, messages, clients, sessions

def handle_client(client_socket, address):
    """Handles communication with a single client."""
    print(f"\n[NEW CONNECTION] {address} connected.")

    try:
        while True:
            # If the client-side socket is dead or closed, it will enter the break block and then disconnect
            # If the server-side socket is closed, it will throw "Bad file descriptor" error, and then disconnect
            data = client_socket.recv(1024).decode("utf-8")
            if not data:
                break

            request = json.loads(data)
            print(f"[REQUEST FROM {address}] {request}")

            response = process_request(request, client_socket)
            client_socket.send(json.dumps(response).encode("utf-8"))
    except OSError:
        pass  # Ignore "Bad file descriptor" error, which occurs when the socket has been closed
    except Exception as e:
        print(f"[ERROR] {e.__class__.__name__} {e} occurred for {address}")
    finally:
        client_socket.close()
        print(f"\n[DISCONNECTED] {address} disconnected.")

def process_request(request, client_socket):
    """Processes the client's request and returns a response."""
    action = request.get("action")
    data = request.get("data", {})

    if action == "create_account":
        username, password = data.get("username"), data.get("password")

        if not username or not password:
            return {"action": "create_account", "status": "error", "error": "Missing username or password"}
        
        if username in users:
            return {"action": "create_account", "status": "error", "error": "Username already exists"}
        
        users[username] = hash_password(password)
        messages[username] = [] # Initialize an empty list for the user's messages
        return {"action": "create_account", "status": "success"}
    
    elif action == "login":
        username, password = data.get("username"), data.get("password")

        if username not in users:
            return {"action": "login", "status": "error", "error": "User does not exist"}
        
        if users[username] != hash_password(password):
            return {"action": "login", "status": "error", "error": "Incorrect password"}
        
        session_token = generate_token()
        sessions[session_token] = {"username": username, "expiry_time": time.time() + TOKEN_EXPIRY_TIME}
        if username not in clients:
            clients[username] = {}
        clients[username][session_token] = client_socket
        unread_count = len(messages.get(username, []))
        return {"action": "login", "status": "success", "data": {"session_token": session_token, "unread_message_count": unread_count}}
    
    elif action == "list_accounts":
        session_token = data.get("session_token")

        if not session_token:
            return {"action": "list_accounts", "status": "error", "error": "Invalid session"}
        
        pattern = data.get("pattern", "*")
        page = data.get("page", 1)
        page_size = data.get("page_size", 10)
        try:
            page = int(page)
            page_size = int(page_size)
            assert page > 0 and page_size > 0
        except Exception:
            return {"action": "list_accounts", "status": "error", "error": "Invalid page or page size"}

        matched_users = sorted(fnmatch.filter(users.keys(), pattern))
        
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_users = matched_users[start_index:end_index]

        return {"action": "list_accounts", "status": "success", "data": {"accounts": paginated_users, "page": page, "total_pages": (len(matched_users) - 1) // page_size + 1}}

    elif action == "send_message":
        session_token = data.get("session_token")
        sender = sessions.get(session_token, {}).get("username")  # Validate session token
        recipient, message = data.get("recipient"), data.get("message")

        if not sender:
            return {"action": "send_message", "status": "error", "error": "Invalid session"}
        
        if not recipient or not message:
            return {"action": "send_message", "status": "error", "error": "Missing recipient or message"}

        if recipient not in users:
            return {"action": "send_message", "status": "error", "error": "Recipient does not exist"}

        flag = False
        if recipient in clients:
            for recipient_socket in clients[recipient].values():
                if recipient_socket.fileno() != -1:  # Check if recipient is online
                    flag = True
                    recipient_socket.send(json.dumps({"action": "receive_message", "data": {"sender": sender, "message": message}}).encode("utf-8"))
        if not flag:
            messages[recipient].append({"from": sender, "message": message})  # Store if offline

        return {"action": "send_message", "status": "success"}

    elif action == "read_messages":
        session_token = data.get("session_token")
        username = sessions.get(session_token, {}).get("username")  # Validate session token

        num_to_read = data.get("num_to_read", 1)  # if num_to_read is positive, read from the latest message; if negative, read from the oldest message
        try:
            num_to_read = int(num_to_read)
        except Exception:
            return {"action": "read_messages", "status": "error", "error": "Invalid number of messages to read"}

        if not username:
            return {"action": "read_messages", "status": "error", "error": "Invalid session"}
        
        if num_to_read < 0:
            user_messages = messages.get(username, [])[:-num_to_read]
            messages[username] = messages.get(username, [])[-num_to_read:]  # Remove read messages
        else:
            user_messages = messages.get(username, [])[-num_to_read:]
            messages[username] = messages.get(username, [])[:-num_to_read]  # Remove read messages
        return {"action": "read_messages", "status": "success", "data": {"unread_messages": user_messages, "remaining_unread_count": len(messages.get(username, []))}}
    
    elif action == "delete_messages":
        session_token = data.get("session_token")
        username = sessions.get(session_token, {}).get("username")  # Validate session token
        if not username:
            return {"action": "delete_messages", "status": "error", "error": "Invalid session"}
        
        num_to_delete = data.get("num_to_delete")
        try:
            num_to_delete = int(num_to_delete)
        except Exception:
            return {"action": "delete_messages", "status": "error", "error": "Invalid number of messages to delete"}
        num_to_read = len(messages.get(username, []))
        if num_to_delete >= 0:  # Delete from the earliest message
            messages[username] = messages.get(username, [])[num_to_delete:]
        else:  # Delete from the latest message
            messages[username] = messages.get(username, [])[:num_to_delete]
        
        tmp =  {"action": "delete_messages", "status": "success", "data": {"num_messages_deleted": num_to_read - len(messages.get(username, []))}}
        return tmp

    elif action == "delete_account":
        session_token = data.get("session_token")
        username = sessions.get(session_token, {}).get("username")  # Validate session token

        if not username:
            return {"action": "delete_account", "status": "error", "error": "Invalid session"}

        # Delete all session tokens, close all sockets, and remove all data associated with the user
        for session_token, login_socket in clients[username].items():
            del sessions[session_token]
            # login_socket.close()
        del clients[username]
        del users[username]
        del messages[username]
        return {"action": "delete_account", "status": "success"}

    elif action == "logout":
        session_token = data.get("session_token")
        username = sessions.get(session_token, {}).get("username")  # Validate session token

        if not username:
            return {"action": "logout", "status": "error", "error": "Invalid session"}

        # Delete session token and close socket for this session
        # clients[username][session_token].close()
        del clients[username][session_token]
        del sessions[session_token]
        return {"action": "logout", "status": "success"}
    
    return {"action": action, "status": "error", "error": "Invalid request"}

def start_server():
    """Starts the server and listens for incoming connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen(5)
        print(f"[SERVER STARTED] Listening on {HOST}:{PORT}")

        while True:
            try:
                client_socket, addr = server.accept()
            except KeyboardInterrupt:
                print("\n[SERVER STOPPED] Exiting...")
                break
            client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            client_thread.start()
    return

if __name__ == "__main__":
    threading.Thread(target=cleanup_expired_sessions, daemon=True).start()
    start_server()
